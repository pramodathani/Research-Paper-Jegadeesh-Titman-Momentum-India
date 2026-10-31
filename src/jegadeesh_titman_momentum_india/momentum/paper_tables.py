"""The paper's Tables II, III and VII computed on Indian data."""

import pandas as pd
from data_and_analytics.backtesting.return_statistics import (
    ReturnStatistics,
)

from jegadeesh_titman_momentum_india.momentum.event_time_returns import (
    EventTimeReturns,
)
from jegadeesh_titman_momentum_india.momentum.grouped_decile_runs import (
    GroupedDecileRuns,
)


class PaperTables:
    """Builds the decile, size, beta and event-time tables.

    Attributes:
        runner: The study runner with its tables.
        market_excess: The market's monthly return less the risk-free rate.
        risk_free: The monthly risk-free rate.
        start: The first holding month of the main sample.
        end: The last holding month.
    """

    def __init__(
        self,
        runner: object,
        market_excess: pd.Series,
        risk_free: pd.Series,
        start: str = '2005-01',
        end: str = '2026-10',
    ) -> None:
        """Keeps the runner and the market series.

        Args:
            runner (object): A StudyRunner.
            market_excess (pd.Series): Market return less risk-free.
            risk_free (pd.Series): Monthly risk-free rate.
            start (str): First holding month of the sample.
            end (str): Last holding month.

        Returns:
            None.
        """
        self.runner = runner
        self.market_excess = market_excess
        self.risk_free = risk_free
        self.start = pd.Period(start)
        self.end = pd.Period(end)
        self.statistics = ReturnStatistics()
        self.groups = GroupedDecileRuns(runner)

    def _score(self, series: pd.Series) -> dict[str, float]:
        """Scores a decile series: mean, plain t, alpha and its t.

        Args:
            series (pd.Series): Gross monthly returns.

        Returns:
            dict[str, float]: mean, t_statistic, alpha, alpha_t and beta.
        """
        series = series.loc[self.start : self.end].dropna()
        mean, t_value = self.statistics.mean_and_t(series)
        excess = series - self.risk_free.reindex(series.index)
        if series.name == '10-1':
            excess = series
        model = self.statistics.market_model(excess, self.market_excess)
        return {
            'mean': mean,
            't_statistic': t_value,
            'alpha': model['alpha'],
            'alpha_t': model['alpha_t'],
            'beta': model['beta'],
            'months': len(series),
        }

    def table_two(self, universe: str) -> pd.DataFrame:
        """Betas and average liquidity of the 6/6 decile portfolios.

        Args:
            universe (str): U1 or U2.

        Returns:
            pd.DataFrame: One row per decile with its beta against the market
                and the average of its members' median daily traded value, in
                rupees crore, at formation.
        """
        returns = self.groups.decile_returns(
            None, None, 6, 6, universe=universe
        )
        deciles = self.groups.last_deciles
        liquidity = self.runner.liquidity
        rows = []
        for decile in range(1, 11):
            members = deciles == decile
            average = liquidity.where(members).mean(axis=1)
            average = average.loc[self.start : self.end].mean() / 1.0e7
            row = self._score(returns[decile].rename(decile))
            row['decile'] = decile
            row['average_traded_value_crore'] = average
            rows.append(row)
        row = self._score(returns['10-1'].rename('10-1'))
        row['decile'] = '10-1'
        row['average_traded_value_crore'] = None
        rows.append(row)
        return pd.DataFrame(rows)

    def group_parts(self) -> dict[str, tuple]:
        """Names the groups of the all-shares universe used in Table III.

        Returns:
            dict[str, tuple]: For each group name, the label table and the
                group number, or None and None for everyone.
        """
        size = self.groups.size_groups()
        beta = self.groups.beta_groups()
        return {
            'All': (None, None),
            'S1 (small)': (size, 1),
            'S2': (size, 2),
            'S3 (large)': (size, 3),
            'B1 (low beta)': (beta, 1),
            'B2': (beta, 2),
            'B3 (high beta)': (beta, 3),
        }

    def decile_frames(self) -> dict[str, pd.DataFrame]:
        """Runs all ten deciles, gross, for every group.

        Returns:
            dict[str, pd.DataFrame]: For each group, a table with one column
                per decile 1 to 10 and the spread 10-1.
        """
        if not hasattr(self, '_frames'):
            self._frames = {}
            for name, (labels, group) in self.group_parts().items():
                self._frames[name] = self.groups.decile_returns(
                    labels, group, 6, 6
                )
        return self._frames

    def table_three(self) -> pd.DataFrame:
        """Deciles within size and beta terciles of the all-shares universe.

        Returns:
            pd.DataFrame: One row per group and decile, with the average
                gross return, plain t and the alpha and its t.
        """
        rows = []
        for name, table in self.decile_frames().items():
            for column in list(range(1, 11)) + ['10-1']:
                row = self._score(table[column].rename(str(column)))
                row['group'] = name
                row['decile'] = column
                rows.append(row)
        return pd.DataFrame(rows)

    def table_seven(self, universe: str) -> pd.DataFrame:
        """Winners minus losers in event time for the 6-month ranking.

        Only formation months from the start of the main sample are used.

        Args:
            universe (str): U1 or U2.

        Returns:
            pd.DataFrame: 36 rows with monthly and cumulative returns and t.
        """
        deciles = self.runner.deciles(universe, 6, False)
        deciles.loc[deciles.index < self.start] = float('nan')
        return EventTimeReturns().winners_minus_losers(
            deciles, self.runner.monthly_returns, 36
        )
