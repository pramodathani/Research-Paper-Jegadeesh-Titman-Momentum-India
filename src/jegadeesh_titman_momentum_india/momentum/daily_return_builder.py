"""Builds adjusted daily total returns from raw NSE closes."""

from typing import ClassVar

import numpy as np
import pandas as pd

from jegadeesh_titman_momentum_india.momentum.action_parser import (
    ActionParser,
)
from jegadeesh_titman_momentum_india.momentum.security_filter import (
    SecurityFilter,
)


class DailyReturnBuilder:
    """Turns bhavcopy rows and corporate actions into daily total returns.

    A day's return is (close + dividend) / (previous close * price factor) - 1,
    where the factor and dividend come from NSE's corporate action list for
    that ex-date. A big move that no listed action explains is tested against
    the usual split and bonus ratios and, if it matches one, treated as a
    missed action. Any move still below -50% or above +100% is set to zero
    and reported.

    Attributes:
        lower_limit: The lowest believable one-day adjusted return.
        upper_limit: The highest believable one-day adjusted return.
        ratios: The price ratios of common splits, bonuses and consolidations.
        ratio_tolerance: How close a move must be to a ratio to be matched.
        minimum_price_for_inference: Lowest previous close for which a missed
            action is inferred.
        reversal: The rebound within five days that marks a real crash.
    """

    SERIES_PRIORITY: ClassVar[dict[str, int]] = {
        'EQ': 0,
        'BE': 1,
        'BZ': 2,
    }

    def __init__(
        self,
        lower_limit: float = -0.5,
        upper_limit: float = 1.0,
        ratio_tolerance: float = 0.05,
        minimum_price_for_inference: float = 5.0,
        reversal: float = 0.30,
    ) -> None:
        """Sets the limits.

        Args:
            lower_limit (float): Lowest believable daily return.
            upper_limit (float): Highest believable daily return.
            ratio_tolerance (float): How close to a ratio counts as a match.
            minimum_price_for_inference (float): Moves of shares priced below
                this are real tick-size jumps, so no action is inferred.
            reversal (float): A rebound this large within five days marks a
                move as a real crash, not a split.

        Returns:
            None.
        """
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.ratio_tolerance = ratio_tolerance
        self.minimum_price_for_inference = minimum_price_for_inference
        self.reversal = reversal
        self.ratios = np.array(
            [
                0.5,
                1 / 3,
                0.25,
                0.2,
                0.1,
                0.05,
                0.4,
                2 / 3,
                0.75,
                0.8,
                2.0,
                5.0,
                10.0,
            ]
        )
        self.parser = ActionParser()
        self.security_filter = SecurityFilter()

    def build(
        self,
        prices: pd.DataFrame,
        actions: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Builds the returns.

        Args:
            prices (pd.DataFrame): Columns date, symbol, series, isin, close,
                previous_close and traded_value, unadjusted.
            actions (pd.DataFrame): Columns ex_date, symbol, subject and
                face_value.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: The returns, with columns date,
                symbol, close, traded_value and ret, and the flags, with
                columns date, symbol, ret_raw and kind for every day whose
                return was inferred or zeroed.
        """
        table = self._one_row_per_day(prices)
        table = self._attach_actions(table, actions)
        table = table.sort_values(['symbol', 'date']).reset_index(drop=True)
        base_price = table['previous_close'] * table['factor']
        table['ret'] = (table['close'] + table['dividend']) / base_price - 1.0
        table.loc[table['previous_close'] <= 0, 'ret'] = np.nan
        self._add_neighbour_closes(table)
        flags = []
        inferred = self._infer_missed_actions(table)
        flags.append(inferred)
        zeroed = self._zero_implausible(table)
        flags.append(zeroed)
        returns = table[['date', 'symbol', 'close', 'traded_value', 'ret']]
        return returns.reset_index(drop=True), pd.concat(flags).reset_index(
            drop=True
        )

    def _one_row_per_day(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Keeps company shares and one row per share per day.

        Args:
            prices (pd.DataFrame): The raw rows.

        Returns:
            pd.DataFrame: One row per symbol and date, EQ before BE before BZ.
        """
        pairs = prices[['symbol', 'isin']].drop_duplicates().copy()
        pairs['keep'] = [
            self.security_filter.is_company_share(symbol, isin)
            for symbol, isin in zip(pairs['symbol'], pairs['isin'])
        ]
        table = prices.merge(pairs, on=['symbol', 'isin'], how='left')
        table = table[table['keep']].drop(columns=['keep']).copy()
        table['priority'] = table['series'].map(self.SERIES_PRIORITY)
        table = table.sort_values(['symbol', 'date', 'priority'])
        table = table.drop_duplicates(subset=['symbol', 'date'], keep='first')
        return table.drop(columns=['priority']).reset_index(drop=True)

    def _attach_actions(
        self,
        table: pd.DataFrame,
        actions: pd.DataFrame,
    ) -> pd.DataFrame:
        """Adds each action's factor and dividend on its first trading day.

        Args:
            table (pd.DataFrame): One row per symbol and date.
            actions (pd.DataFrame): The corporate actions.

        Returns:
            pd.DataFrame: The table with columns factor and dividend.
        """
        table = table.copy()
        table['factor'] = 1.0
        table['dividend'] = 0.0
        if actions.empty:
            return table
        parsed = [
            self.parser.parse(subject, face_value)
            for subject, face_value in zip(
                actions['subject'], actions['face_value']
            )
        ]
        events = pd.DataFrame(
            {
                'symbol': actions['symbol'].to_numpy(),
                'ex_date': pd.to_datetime(actions['ex_date']).to_numpy(),
                'factor': [p.price_factor for p in parsed],
                'dividend': [p.dividend for p in parsed],
            }
        )
        factors = events[events['factor'] != 1.0].drop_duplicates(
            subset=['symbol', 'ex_date', 'factor']
        )
        factors = factors.groupby(['symbol', 'ex_date'], as_index=False)[
            'factor'
        ].prod()
        dividends = events[events['dividend'] > 0.0]
        dividends = dividends.groupby(['symbol', 'ex_date'], as_index=False)[
            'dividend'
        ].max()
        table = table.drop(columns=['factor', 'dividend'])
        table = self._merge_forward(table, factors, 'factor', 1.0)
        return self._merge_forward(table, dividends, 'dividend', 0.0)

    def _merge_forward(
        self,
        table: pd.DataFrame,
        events: pd.DataFrame,
        column: str,
        neutral: float,
    ) -> pd.DataFrame:
        """Puts each event on the first trading day on or after its ex-date.

        Args:
            table (pd.DataFrame): One row per symbol and date.
            events (pd.DataFrame): Columns symbol, ex_date and the column.
            column (str): The event column name.
            neutral (float): The value on days with no event.

        Returns:
            pd.DataFrame: The table with the column added.
        """
        if events.empty:
            table[column] = neutral
            return table
        trading_days = table[['symbol', 'date']].sort_values('date')
        events = events.sort_values('ex_date')
        placed = pd.merge_asof(
            events,
            trading_days.rename(columns={'date': 'trading_day'}),
            left_on='ex_date',
            right_on='trading_day',
            by='symbol',
            direction='forward',
            tolerance=pd.Timedelta(days=10),
        ).dropna(subset=['trading_day'])
        if column == 'factor':
            placed = placed.groupby(['symbol', 'trading_day'], as_index=False)[
                column
            ].prod()
        else:
            placed = placed.groupby(['symbol', 'trading_day'], as_index=False)[
                column
            ].sum()
        placed = placed.rename(columns={'trading_day': 'date'})
        table = table.merge(placed, on=['symbol', 'date'], how='left')
        table[column] = table[column].fillna(neutral)
        return table

    def _add_neighbour_closes(self, table: pd.DataFrame) -> None:
        """Adds the prior row's close and the next days' highest and lowest.

        Changes the table in place; it must be sorted by symbol and date.

        Args:
            table (pd.DataFrame): One row per symbol and date.

        Returns:
            None.
        """
        closes = table.groupby('symbol')['close']
        table['prior_close'] = closes.shift(1)
        later = [closes.shift(-step) for step in range(1, 6)]
        stacked = np.column_stack([series.to_numpy() for series in later])
        with np.errstate(all='ignore'):
            table['later_high'] = np.nanmax(
                np.where(np.isnan(stacked), -np.inf, stacked), axis=1
            )
            table['later_low'] = np.nanmin(
                np.where(np.isnan(stacked), np.inf, stacked), axis=1
            )
        table.loc[np.isinf(table['later_high']), 'later_high'] = np.nan
        table.loc[np.isinf(table['later_low']), 'later_low'] = np.nan

    def _reverses(self, rows: pd.DataFrame) -> pd.Series:
        """Says whether a big move is undone within the next five days.

        A drop reverses when the price climbs more than 30% from the new
        close; a rise reverses when it falls more than 23%.

        Args:
            rows (pd.DataFrame): Rows with close, ret, later_high, later_low.

        Returns:
            pd.Series: True where the move reverses.
        """
        drop = rows['ret'] < 0
        rebound = rows['later_high'] / rows['close'] - 1.0 > self.reversal
        fall_back = rows['later_low'] / rows['close'] - 1.0 < -(
            1.0 - 1.0 / (1.0 + self.reversal)
        )
        return (drop & rebound) | (~drop & fall_back)

    def _returns_to_old_level(self, rows: pd.DataFrame) -> pd.Series:
        """Says whether the price comes back within 10% of its old level.

        Args:
            rows (pd.DataFrame): Rows with previous_close, factor, ret,
                later_high and later_low.

        Returns:
            pd.Series: True for a one-day misprint.
        """
        old_level = rows['previous_close'] * rows['factor']
        drop = rows['ret'] < 0
        back_up = rows['later_high'] >= 0.9 * old_level
        back_down = rows['later_low'] <= 1.1 * old_level
        return (drop & back_up) | (~drop & back_down)

    def _infer_missed_actions(self, table: pd.DataFrame) -> pd.DataFrame:
        """Fixes big moves that match a split or bonus ratio and persist.

        A move that is undone within five days is a real crash or a
        misprint, not a split, so it is left for the limit check.
        Changes the table's ret in place.

        Args:
            table (pd.DataFrame): The table with ret, factor, dividend and the
                neighbour closes.

        Returns:
            pd.DataFrame: The flags for the days changed.
        """
        unexplained = (
            (table['factor'] == 1.0)
            & (table['previous_close'] >= self.minimum_price_for_inference)
            & table['ret'].notna()
            & ((table['ret'] < -0.38) | (table['ret'] > 0.6))
        )
        candidates = table[unexplained].copy()
        if candidates.empty:
            return self._empty_flags()
        candidates = candidates[~self._reverses(candidates)]
        if candidates.empty:
            return self._empty_flags()
        ratio = (candidates['close'] / candidates['previous_close']).to_numpy()
        distance = np.abs(ratio[:, None] / self.ratios[None, :] - 1.0)
        best = distance.argmin(axis=1)
        matched = distance.min(axis=1) <= self.ratio_tolerance
        factor = np.where(matched, self.ratios[best], 1.0)
        candidates['ret_raw'] = candidates['ret']
        adjusted = (candidates['close'] + candidates['dividend']) / (
            candidates['previous_close'] * factor
        ) - 1.0
        candidates['ret'] = np.where(matched, adjusted, candidates['ret'])
        applied = candidates[matched]
        table.loc[applied.index, 'ret'] = applied['ret']
        flags = applied[['date', 'symbol', 'ret_raw']].copy()
        flags['kind'] = 'inferred_action'
        return flags

    def _zero_implausible(self, table: pd.DataFrame) -> pd.DataFrame:
        """Deals with returns still beyond the limits.

        A wrong previous close in NSE's file is replaced by the prior row's
        close when that gives a believable return. A move undone within five
        days is a misprint and set to zero. A lasting fall is kept as a real
        loss. Anything else is set to zero. Changes the table's ret in place.

        Args:
            table (pd.DataFrame): The table with ret and the neighbour closes.

        Returns:
            pd.DataFrame: The flags for the days changed or kept.
        """
        bad = (table['ret'] < self.lower_limit) | (
            table['ret'] > self.upper_limit
        )
        rows = table[bad].copy()
        if rows.empty:
            return self._empty_flags()
        rows['ret_raw'] = rows['ret']
        rows['kind'] = 'zeroed'
        repaired_ret = (rows['close'] + rows['dividend']) / (
            rows['prior_close'] * rows['factor']
        ) - 1.0
        field_wrong = (
            rows['prior_close'] / rows['previous_close'] - 1.0
        ).abs() > 0.02
        believable = (repaired_ret >= self.lower_limit) & (
            repaired_ret <= self.upper_limit
        )
        repair = field_wrong & believable
        misprint = ~repair & self._returns_to_old_level(rows)
        real_fall = ~repair & ~misprint & (rows['ret'] < self.lower_limit)
        rows.loc[repair, 'ret'] = repaired_ret[repair]
        rows.loc[repair, 'kind'] = 'previous_close_repaired'
        rows.loc[misprint, 'ret'] = 0.0
        rows.loc[misprint, 'kind'] = 'zeroed_misprint'
        rows.loc[real_fall, 'kind'] = 'kept_real_fall'
        other = ~repair & ~misprint & ~real_fall
        rows.loc[other, 'ret'] = 0.0
        table.loc[rows.index, 'ret'] = rows['ret']
        return rows[['date', 'symbol', 'ret_raw', 'kind']]

    def _empty_flags(self) -> pd.DataFrame:
        """Gives an empty flag table.

        Returns:
            pd.DataFrame: No rows, with the flag columns.
        """
        return pd.DataFrame(columns=['date', 'symbol', 'ret_raw', 'kind'])
