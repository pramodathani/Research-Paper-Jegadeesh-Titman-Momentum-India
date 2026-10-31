"""Turns the grid of strategy returns into the study's results tables."""

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.calendar_month_table import (
    CalendarMonthTable,
)
from jegadeesh_titman_momentum_india.momentum.strategy_summary import (
    StrategySummary,
)


class GridTables:
    """Scores every strategy in the grid and builds the calendar tables.

    Attributes:
        grid: Long table of monthly strategy returns from StudyRunner.grid.
        market_excess: The market's monthly return less the risk-free rate.
        risk_free: The monthly risk-free rate.
    """

    KEYS = (
        'universe',
        'skip',
        'formation_months',
        'holding_months',
        'leg',
    )

    def __init__(
        self,
        grid: pd.DataFrame,
        market_excess: pd.Series,
        risk_free: pd.Series,
    ) -> None:
        """Keeps the grid and market series.

        Args:
            grid (pd.DataFrame): The strategy returns.
            market_excess (pd.Series): Market return less risk-free, by month
                period.
            risk_free (pd.Series): Monthly risk-free rate, by month period.

        Returns:
            None.
        """
        self.grid = grid.copy()
        self.grid['period'] = self.grid['month'].dt.to_period('M')
        self.market_excess = market_excess
        self.risk_free = risk_free
        self.summary = StrategySummary()
        self.calendar = CalendarMonthTable()

    def series(
        self,
        keys: tuple,
        column: str,
        start: str,
        end: str,
    ) -> pd.Series:
        """Picks one strategy's monthly series.

        Args:
            keys (tuple): Values of the KEYS columns.
            column (str): gross, net or turnover.
            start (str): First month, such as 2005-01.
            end (str): Last month.

        Returns:
            pd.Series: The series indexed by month period, NaN months dropped.
        """
        mask = pd.Series(True, index=self.grid.index)
        for name, value in zip(self.KEYS, keys):
            mask &= self.grid[name] == value
        frame = self.grid[mask].set_index('period')[column].dropna()
        return frame.loc[pd.Period(start) : pd.Period(end)]

    def table_one(self, start: str, end: str) -> pd.DataFrame:
        """Scores every strategy over a sample.

        Args:
            start (str): First holding month.
            end (str): Last holding month.

        Returns:
            pd.DataFrame: One row per universe, skip, J, K and leg, with the
                average monthly return, plain and Newey-West t, alpha, beta,
                drawdown and turnover before and after costs.
        """
        rows = []
        keys = self.grid[list(self.KEYS)].drop_duplicates()
        for key in keys.itertuples(index=False):
            key = tuple(key)
            gross = self.series(key, 'gross', start, end)
            net = self.series(key, 'net', start, end)
            turnover = self.series(key, 'turnover', start, end)
            long_only = key[4] != 'long_short'
            gross_stats = self.summary.summarize(
                gross, self.market_excess, self.risk_free, long_only
            )
            net_stats = self.summary.summarize(
                net, self.market_excess, self.risk_free, long_only
            )
            row = dict(zip(self.KEYS, key))
            row['months'] = gross_stats['periods']
            for name in (
                'mean',
                't_statistic',
                'newey_west_t',
                'maximum_drawdown',
                'compound_annual',
                'alpha',
                'alpha_t',
                'beta',
            ):
                row[f'gross_{name}'] = gross_stats.get(name)
                row[f'net_{name}'] = net_stats.get(name)
            row['turnover_monthly'] = turnover.mean()
            rows.append(row)
        return pd.DataFrame(rows)

    def calendar_table(self, keys: tuple, start: str, end: str) -> pd.DataFrame:
        """Builds the calendar-month table for one strategy's gross returns.

        Args:
            keys (tuple): Values of the KEYS columns.
            start (str): First month.
            end (str): Last month.

        Returns:
            pd.DataFrame: Twelve rows, with the F-test p-values in the
                attributes `all_months_p` and `february_december_p`.
        """
        series = self.series(keys, 'gross', start, end)
        table = self.calendar.table(series)
        table.attrs['all_months_p'] = self.calendar.equal_means_test(series)[1]
        table.attrs['february_december_p'] = self.calendar.equal_means_test(
            series, list(range(2, 13))
        )[1]
        return table

    def subperiods(
        self,
        keys: tuple,
        boundaries: list[tuple[str, str]],
    ) -> pd.DataFrame:
        """Scores one strategy in each subperiod, with and without January.

        Args:
            keys (tuple): Values of the KEYS columns.
            boundaries (list[tuple[str, str]]): First and last month of each
                subperiod.

        Returns:
            pd.DataFrame: Rows for each subperiod and month set, with the
                average gross return, its plain t and the month count.
        """
        series = self.series(keys, 'gross', boundaries[0][0], boundaries[-1][1])
        return self.subperiods_of(series, boundaries)

    def subperiods_of(
        self,
        series: pd.Series,
        boundaries: list[tuple[str, str]],
    ) -> pd.DataFrame:
        """Scores any monthly series in each subperiod, with and without January.

        Args:
            series (pd.Series): Monthly returns indexed by month period.
            boundaries (list[tuple[str, str]]): First and last month of each
                subperiod.

        Returns:
            pd.DataFrame: Rows for each subperiod and month set, with the
                average return, its plain t and the month count.
        """
        rows = []
        for start, end in boundaries:
            part = series.dropna().loc[pd.Period(start) : pd.Period(end)]
            sets = {
                'all months': part,
                'January': part[part.index.month == 1],
                'February to December': part[part.index.month != 1],
                'March and April': part[part.index.month.isin([3, 4])],
            }
            for name, subset in sets.items():
                mean, t_value = self.calendar.statistics.mean_and_t(subset)
                rows.append(
                    {
                        'subperiod': f'{start} to {end}',
                        'months': name,
                        'count': len(subset),
                        'mean': mean,
                        't_statistic': t_value,
                    }
                )
        return pd.DataFrame(rows)
