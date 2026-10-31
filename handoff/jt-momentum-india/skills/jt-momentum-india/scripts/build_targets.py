"""Builds the month's target portfolio for the India momentum strategy.

The strategy is Jegadeesh and Titman's (1993) relative-strength rule, long only. At the close of each month the top 500 NSE shares by traded value are ranked on their past 6-month price return, the top tenth is bought in equal weights, and each month's choice is held for 6 months, so the portfolio is six overlapping cohorts of one sixth each.

This program only reads prices and writes a CSV of targets. It never places, modifies or cancels an order.

Typical usage example:

  python build_targets.py targets_2026-11.csv --previous targets_2026-10.csv
"""

import argparse
import datetime
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

RANKING_MONTHS = 6
HOLDING_MONTHS = 6
UNIVERSE_SIZE = 500
MINIMUM_PRICE = 10.0
LIQUIDITY_DAYS = 126
RECENT_DAYS = 5
STALE_DAYS = 10
DECILES = 10
DROP_LIMIT = -0.45
RISE_LIMIT = 1.0
FUND_PATTERN = re.compile(
    r'(-RE\d*$|BEES$|ETF|^LIQUID|^GILT|IETF$|^NIFTY|^SENSEX)',
    re.IGNORECASE,
)


class MomentumTargets:
    """Turns daily closes and volumes into the target weights.

    Attributes:
        prices: Long table with columns symbol, date, close and volume,
            closes adjusted for splits and bonuses.
        ranking_months: J, the months of past return that rank the shares.
        holding_months: K, the months each cohort is held.
        universe_size: How many shares are ranked.
        minimum_price: The lowest last close allowed in the universe.
    """

    def __init__(
        self,
        prices: pd.DataFrame,
        ranking_months: int = RANKING_MONTHS,
        holding_months: int = HOLDING_MONTHS,
        universe_size: int = UNIVERSE_SIZE,
        minimum_price: float = MINIMUM_PRICE,
    ) -> None:
        """Pivots the prices.

        Args:
            prices (pd.DataFrame): Columns symbol, date, close and volume.
            ranking_months (int): J.
            holding_months (int): K.
            universe_size (int): Size of the ranked universe.
            minimum_price (float): Lowest last close in the universe.

        Returns:
            None.
        """
        frame = prices.copy()
        frame['date'] = pd.to_datetime(frame['date']).dt.normalize()
        frame = frame.drop_duplicates(['symbol', 'date'], keep='last')
        self.close = frame.pivot(
            index='date', columns='symbol', values='close'
        ).sort_index()
        self.close = self.close.sort_index(axis=1)
        volume = frame.pivot(
            index='date', columns='symbol', values='volume'
        ).reindex(index=self.close.index, columns=self.close.columns)
        self.traded_value = self.close * volume
        self.level = self.close.ffill(limit=STALE_DAYS)
        self.ranking_months = ranking_months
        self.holding_months = holding_months
        self.universe_size = universe_size
        self.minimum_price = minimum_price

    def month_ends(self) -> pd.DatetimeIndex:
        """Gives the last trading day in the data of every month.

        Returns:
            pd.DatetimeIndex: One date per month, in order.
        """
        dates = pd.Series(self.close.index, index=self.close.index)
        grouped = dates.groupby(self.close.index.to_period('M')).max()
        return pd.DatetimeIndex(grouped.to_numpy())

    def completed_month_ends(self, as_of: datetime.date) -> pd.DatetimeIndex:
        """Gives the month-ends of the months that finished before a date.

        Args:
            as_of (datetime.date): The day the targets are built.

        Returns:
            pd.DatetimeIndex: Month-end trading days before the as-of month.

        Raises:
            ValueError: The data stops before the last completed month ended.
        """
        ends = self.month_ends()
        month = pd.Period(as_of, freq='M')
        done = ends[ends.to_period('M') < month]
        if len(done) == 0:
            raise ValueError('No completed month in the data')
        last = done[-1]
        month_last_day = last.to_period('M').end_time.normalize()
        if (month_last_day - last).days > 4:
            raise ValueError(
                f'The data reaches {last.date()} but the month ended on '
                f'{month_last_day.date()}; wait for the last prices'
            )
        return done

    def suspect_symbols(self, since: pd.Timestamp) -> list[str]:
        """Finds shares with a daily move too big to believe.

        A fall of more than 45% or a rise of more than 100% in a day usually
        means a split or bonus that the price file has not adjusted.

        Args:
            since (pd.Timestamp): Look at moves from this date on.

        Returns:
            list[str]: The symbols, in order.
        """
        moves = self.close.loc[since:].pct_change(fill_method=None)
        bad = (moves < DROP_LIMIT) | (moves > RISE_LIMIT)
        return sorted(bad.columns[bad.any(axis=0)])

    def cohort(
        self,
        formation: pd.Timestamp,
        start: pd.Timestamp,
        excluded: set[str],
    ) -> list[str]:
        """Picks the winners decile at one month-end.

        Args:
            formation (pd.Timestamp): The month-end trading day.
            start (pd.Timestamp): The month-end ranking_months earlier.
            excluded (set[str]): Symbols never to hold.

        Returns:
            list[str]: The shares in the top tenth, in symbol order.
        """
        position = self.close.index.get_loc(formation)
        first = max(position - RECENT_DAYS + 1, 0)
        recent = self.close.iloc[first : position + 1]
        traded = recent.notna().any(axis=0).to_numpy()
        last_close = recent.ffill().iloc[-1].to_numpy(dtype=float)
        window_start = max(position - LIQUIDITY_DAYS + 1, 0)
        window = self.traded_value.iloc[window_start : position + 1]
        median_value = window.fillna(0.0).median(axis=0).to_numpy(dtype=float)
        symbols = self.close.columns
        not_excluded = np.array([name not in excluded for name in symbols])
        allowed = traded & (last_close >= self.minimum_price) & not_excluded
        score = np.where(allowed, median_value, -1.0)
        top = np.argsort(-score, kind='stable')[: self.universe_size]
        top = top[score[top] >= 0.0]
        in_universe = np.zeros(len(symbols), dtype=bool)
        in_universe[top] = True
        ending = self.level.loc[formation].to_numpy(dtype=float)
        starting = self.level.loc[start].to_numpy(dtype=float)
        with np.errstate(all='ignore'):
            past_return = ending / starting - 1.0
        eligible = in_universe & ~np.isnan(past_return)
        positions = np.flatnonzero(eligible)
        count = len(positions)
        if count < DECILES:
            return []
        order = np.argsort(past_return[positions], kind='stable')
        ranks = np.empty(count)
        ranks[order] = np.arange(count)
        deciles = np.floor(ranks * DECILES / count) + 1
        return [symbols[i] for i in positions[deciles == DECILES]]

    def targets(
        self,
        as_of: datetime.date,
        excluded: set[str] | None = None,
    ) -> tuple[pd.Series, dict[str, Any]]:
        """Builds the target weights.

        Each of the last holding_months month-ends forms one cohort holding
        1 / holding_months of the money, split equally among its members that
        still trade; a share chosen in several cohorts gets the sum.

        Args:
            as_of (datetime.date): The day the targets are built.
            excluded (set[str] | None): Symbols never to hold.

        Returns:
            tuple[pd.Series, dict[str, Any]]: Weights by symbol, summing to
                1, and details of the cohorts.

        Raises:
            ValueError: The data is too short or stops too early.
        """
        excluded = excluded or set()
        ends = self.completed_month_ends(as_of)
        needed = self.holding_months + self.ranking_months
        if len(ends) < needed:
            raise ValueError(
                f'Need {needed} month-ends of data, have {len(ends)}'
            )
        cohort_ends = ends[-self.holding_months :]
        starts = ends[-needed : -self.holding_months]
        latest = self.close.iloc[-RECENT_DAYS:].notna().any(axis=0)
        weights = pd.Series(0.0, index=self.close.columns)
        details = {
            'formation_dates': [],
            'cohort_sizes': [],
        }
        for formation, start in zip(cohort_ends, starts):
            members = self.cohort(formation, start, excluded)
            still = [name for name in members if latest[name]]
            details['formation_dates'].append(str(formation.date()))
            details['cohort_sizes'].append(len(still))
            if not still:
                continue
            for name in still:
                weights[name] += 1.0 / self.holding_months / len(still)
        weights = weights[weights > 0.0]
        weights = weights / weights.sum()
        return weights.sort_values(ascending=False, kind='stable'), details


class UbiPrices:
    """Reads daily NSE share prices from UBI through tradingmachine."""

    BATCH = 100

    def load(self, as_of: datetime.date, days: int = 460) -> pd.DataFrame:
        """Fetches adjusted daily closes and volumes for every NSE share.

        Args:
            as_of (datetime.date): The day the targets are built.
            days (int): How many calendar days of history to fetch.

        Returns:
            pd.DataFrame: Columns symbol, date, close and volume.

        Raises:
            RuntimeError: UBI returned no prices.
        """
        from tradingmachine.unified_broker_interface import client

        ubi = client.UnifiedBrokerInterface()
        master = ubi.get(
            '/api/instruments/master',
            params={'exchange': 'nse', 'segment': 'equities'},
        )
        funds = self._fund_symbols(ubi)
        listed = [
            (row['instrument_id'], row['symbol'])
            for row in master
            if row['symbol'] not in funds
            and not FUND_PATTERN.search(row['symbol'])
        ]
        start = (as_of - datetime.timedelta(days=days)).isoformat()
        frames = []
        for first in range(0, len(listed), self.BATCH):
            batch = listed[first : first + self.BATCH]
            body = {
                'instruments': [{'instrument_id': item[0]} for item in batch],
                'interval': 'day',
                'adjusted': True,
                'from': start,
                'to': as_of.isoformat(),
            }
            answer = ubi.post('/api/instruments/prices', body=body)
            for result in answer['results']:
                if result['status'] != 200 or not result['data']['candles']:
                    continue
                data = result['data']
                frame = pd.DataFrame(data['candles'], columns=data['columns'])
                frame['symbol'] = batch[result['request_index']][1]
                frames.append(frame)
        if not frames:
            raise RuntimeError('UBI returned no prices')
        table = pd.concat(frames, ignore_index=True)
        table['date'] = (
            pd.to_datetime(table['time'], utc=True)
            .dt.tz_convert('Asia/Kolkata')
            .dt.tz_localize(None)
            .dt.normalize()
        )
        return table[['symbol', 'date', 'close', 'volume']]

    def _fund_symbols(self, ubi: Any) -> set[str]:
        """Reads the symbols of exchange traded funds from UBI's funds segment.

        Args:
            ubi (Any): The UBI client.

        Returns:
            set[str]: Fund symbols, empty if UBI has no such segment.
        """
        from tradingmachine.unified_broker_interface import exceptions

        try:
            rows = ubi.get(
                '/api/instruments/master',
                params={'exchange': 'nse', 'segment': 'funds'},
            )
        except exceptions.UnifiedBrokerInterfaceError:
            return set()
        return {row['symbol'] for row in rows}


class BuildTargetsApplication:
    """Reads prices, builds the targets and writes the CSV."""

    def run(self) -> None:
        """Parses the command line, builds the targets and prints a summary.

        Returns:
            None.

        Raises:
            ValueError: The data is too short or stops too early.
        """
        parser = argparse.ArgumentParser(
            description="Build the month's target weights."
        )
        parser.add_argument('output', help='CSV of symbol,weight to write')
        parser.add_argument('--previous', help="last month's CSV, for changes")
        parser.add_argument(
            '--as-of', help='date to build for, YYYY-MM-DD; default today'
        )
        parser.add_argument(
            '--prices-file',
            help='parquet or CSV of symbol,date,close,volume instead of UBI',
        )
        parser.add_argument(
            '--exclude', nargs='*', default=[], help='symbols never to hold'
        )
        parser.add_argument(
            '--capital', type=float, help='rupees, to show whole-share fit'
        )
        arguments = parser.parse_args()
        as_of = datetime.date.today()
        if arguments.as_of:
            as_of = datetime.date.fromisoformat(arguments.as_of)
        if arguments.prices_file:
            prices = self._read_file(arguments.prices_file)
        else:
            prices = UbiPrices().load(as_of)
        builder = MomentumTargets(prices)
        ends = builder.completed_month_ends(as_of)
        since = ends[-(HOLDING_MONTHS + RANKING_MONTHS)]
        suspects = builder.suspect_symbols(since)
        excluded = set(arguments.exclude) | set(suspects)
        weights, details = builder.targets(as_of, excluded)
        output = Path(arguments.output)
        weights.rename('weight').rename_axis('symbol').reset_index().to_csv(
            output, index=False, float_format='%.8f'
        )
        self._print_summary(
            weights, details, suspects, ends[-1], arguments.previous
        )
        if arguments.capital:
            self._print_fit(weights, builder, arguments.capital)

    def _read_file(self, path: str) -> pd.DataFrame:
        """Reads a prices file.

        Args:
            path (str): A parquet or CSV file with symbol, date, close, volume.

        Returns:
            pd.DataFrame: The prices.
        """
        if path.endswith('.csv'):
            return pd.read_csv(path)
        return pd.read_parquet(path)

    def _print_summary(
        self,
        weights: pd.Series,
        details: dict[str, Any],
        suspects: list[str],
        month_end: pd.Timestamp,
        previous: str | None,
    ) -> None:
        """Prints what was built.

        Args:
            weights (pd.Series): The targets.
            details (dict[str, Any]): The cohorts' details.
            suspects (list[str]): Shares left out for suspect price moves.
            month_end (pd.Timestamp): The latest formation date.
            previous (str | None): Last month's CSV, or None.

        Returns:
            None.
        """
        print(f'Targets for the month after {month_end.date()}')
        print(f'Holdings: {len(weights)}')
        print(
            f'Largest weight: {weights.iloc[0] * 100:.2f}% ({weights.index[0]})'
        )
        print(f'Cohort sizes, oldest first: {details["cohort_sizes"]}')
        print(f'Shares left out for suspect price moves: {len(suspects)}')
        if previous:
            old = pd.read_csv(previous).set_index('symbol')['weight']
            joiners = sorted(set(weights.index) - set(old.index))
            leavers = sorted(set(old.index) - set(weights.index))
            turnover = (
                weights.reindex(weights.index.union(old.index), fill_value=0.0)
                - old.reindex(weights.index.union(old.index), fill_value=0.0)
            ).abs().sum() / 2.0
            print(
                f'Joiners ({len(joiners)}): {", ".join(joiners[:20])}'
                f'{" ..." if len(joiners) > 20 else ""}'
            )
            print(
                f'Leavers ({len(leavers)}): {", ".join(leavers[:20])}'
                f'{" ..." if len(leavers) > 20 else ""}'
            )
            print(f'One-way turnover: {turnover * 100:.1f}% of the portfolio')

    def _print_fit(
        self,
        weights: pd.Series,
        builder: MomentumTargets,
        capital: float,
    ) -> None:
        """Shows how much of the capital whole shares can invest.

        Args:
            weights (pd.Series): The targets.
            builder (MomentumTargets): The builder, for last closes.
            capital (float): Rupees to invest.

        Returns:
            None.
        """
        last = builder.close.ffill().iloc[-1]
        shares = np.floor(weights * capital / last.reindex(weights.index))
        invested = float((shares * last.reindex(weights.index)).sum())
        missing = int((shares < 1).sum())
        print(
            f'With Rs {capital:,.0f}: {invested / capital * 100:.1f}% invested '
            f'in whole shares; {missing} of {len(weights)} targets round to '
            f'zero shares'
        )


if __name__ == '__main__':
    BuildTargetsApplication().run()
