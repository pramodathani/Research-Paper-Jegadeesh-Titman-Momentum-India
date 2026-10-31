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
    ) -> None:
        """Sets the limits.

        Args:
            lower_limit (float): Lowest believable daily return.
            upper_limit (float): Highest believable daily return.
            ratio_tolerance (float): How close to a ratio counts as a match.
            minimum_price_for_inference (float): Moves of shares priced below
                this are real tick-size jumps, so no action is inferred.

        Returns:
            None.
        """
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.ratio_tolerance = ratio_tolerance
        self.minimum_price_for_inference = minimum_price_for_inference
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
        base = table['close'] / (table['previous_close'] * table['factor'])
        table['ret'] = (
            base
            + table['dividend'] / (table['previous_close'] * table['factor'])
        ) - 1.0
        table.loc[table['previous_close'] <= 0, 'ret'] = np.nan
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

    def _infer_missed_actions(self, table: pd.DataFrame) -> pd.DataFrame:
        """Fixes big moves that match a split or bonus ratio.

        Changes the table's ret in place.

        Args:
            table (pd.DataFrame): The table with ret, factor and dividend.

        Returns:
            pd.DataFrame: The flags for the days changed.
        """
        unexplained = (
            (table['factor'] == 1.0)
            & (table['previous_close'] >= self.minimum_price_for_inference)
            & table['ret'].notna()
            & ((table['ret'] < -0.38) | (table['ret'] > 0.6))
        )
        raw_ratio = table['close'] / table['previous_close']
        candidates = table[unexplained].copy()
        if candidates.empty:
            return self._empty_flags()
        ratio = raw_ratio[unexplained].to_numpy()
        distance = np.abs(ratio[:, None] / self.ratios[None, :] - 1.0)
        best = distance.argmin(axis=1)
        matched = distance.min(axis=1) <= self.ratio_tolerance
        chosen = self.ratios[best]
        factor = np.where(matched, chosen, 1.0)
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
        """Sets returns beyond the limits to zero.

        Changes the table's ret in place.

        Args:
            table (pd.DataFrame): The table with ret.

        Returns:
            pd.DataFrame: The flags for the days changed.
        """
        bad = (table['ret'] < self.lower_limit) | (
            table['ret'] > self.upper_limit
        )
        flags = table.loc[bad, ['date', 'symbol', 'ret']].rename(
            columns={'ret': 'ret_raw'}
        )
        flags['kind'] = 'zeroed'
        table.loc[bad, 'ret'] = 0.0
        return flags

    def _empty_flags(self) -> pd.DataFrame:
        """Gives an empty flag table.

        Returns:
            pd.DataFrame: No rows, with the flag columns.
        """
        return pd.DataFrame(columns=['date', 'symbol', 'ret_raw', 'kind'])
