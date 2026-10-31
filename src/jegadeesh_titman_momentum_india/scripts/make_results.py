"""Command-line program that runs every results step and writes results/."""

import argparse
import os
from pathlib import Path

import pandas as pd
import psycopg

from jegadeesh_titman_momentum_india.data.timescale_store import (
    TimescaleStore,
)
from jegadeesh_titman_momentum_india.momentum.delisting_stress import (
    DelistingStress,
)
from jegadeesh_titman_momentum_india.momentum.fno_universe import FnoUniverse
from jegadeesh_titman_momentum_india.momentum.futures_portfolios import (
    FuturesPortfolios,
)
from jegadeesh_titman_momentum_india.momentum.grid_tables import GridTables
from jegadeesh_titman_momentum_india.momentum.iima_factors import IimaFactors
from jegadeesh_titman_momentum_india.momentum.index_returns import (
    IndexReturns,
)
from jegadeesh_titman_momentum_india.momentum.paper_tables import PaperTables
from jegadeesh_titman_momentum_india.momentum.strategy_summary import (
    StrategySummary,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner

START = '2005-01'
END = '2026-10'
NIFTY_500 = ('S&P CNX 500', 'CNX 500', 'Nifty 500')
NIFTY_50 = ('S&P CNX Nifty', 'CNX Nifty', 'Nifty 50')
MOMENTUM_30 = ('Nifty200 Momentum 30',)


class MakeResultsApplication:
    """Runs the grid tables, paper tables, extensions and robustness checks."""

    def run(self) -> None:
        """Parses arguments and runs every step.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--out', default='results')
        parser.add_argument(
            '--daily', default='data/derived/daily_returns.parquet'
        )
        parser.add_argument('--grid', default='data/derived/grid.parquet')
        arguments = parser.parse_args()
        self.out = Path(arguments.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self._load_market()
        daily = pd.read_parquet(arguments.daily)
        daily['date'] = pd.to_datetime(daily['date'])
        grid = pd.read_parquet(arguments.grid)
        self._grid_tables(grid)
        self._benchmarks(grid)
        runner = StudyRunner(daily)
        self._paper_tables(runner)
        self._futures(runner)
        self._robustness(runner, daily, grid)
        self._variant_count(grid)

    def _load_market(self) -> None:
        """Reads the IIMA factors and index files from the database.

        Returns:
            None.
        """
        schema = TimescaleStore.SCHEMA
        connection = psycopg.connect(
            os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL']
        )
        iima = pd.DataFrame(
            connection.execute(
                f'SELECT month, smb, hml, wml, mf, rf FROM '
                f'{schema}.iima_factors_monthly ORDER BY month'
            ).fetchall(),
            columns=['month', 'smb', 'hml', 'wml', 'mf', 'rf'],
        )
        self.factors = IimaFactors(iima)
        self.index_daily = pd.DataFrame(
            connection.execute(
                f'SELECT date, index_name, close, div_yield '
                f'FROM {schema}.index_daily'
            ).fetchall(),
            columns=['date', 'index_name', 'close', 'div_yield'],
        )
        self.fno = pd.DataFrame(
            connection.execute(
                f'SELECT date, symbol FROM {schema}.fno_stock_futures_daily'
            ).fetchall(),
            columns=['date', 'symbol'],
        )
        months = pd.period_range('1996-01', END, freq='M')
        self.risk_free = self.factors.risk_free(months)
        self.market_excess = self.factors.factors['mf']

    def _grid_tables(self, grid: pd.DataFrame) -> None:
        """Writes Table I for the main sample and the extension, and more.

        Args:
            grid (pd.DataFrame): The strategy returns.

        Returns:
            None.
        """
        tables = GridTables(grid, self.market_excess, self.risk_free)
        tables.table_one(START, END).to_csv(
            self.out / 'table1_main_2005_2026.csv', index=False
        )
        tables.table_one('1997-01', '2004-12').to_csv(
            self.out / 'table1_extension_1997_2004.csv', index=False
        )
        for universe in ('U1', 'U2'):
            keys = (universe, False, 6, 6, 'long_short')
            calendar = tables.calendar_table(keys, START, END)
            calendar.to_csv(self.out / f'table4_calendar_{universe}.csv')
            pd.Series(calendar.attrs).to_csv(
                self.out / f'table4_ftests_{universe}.csv'
            )
            boundaries = [
                ('2005-01', '2009-12'),
                ('2010-01', '2014-12'),
                ('2015-01', '2019-12'),
                ('2020-01', '2026-10'),
            ]
            for leg in ('long_short', 'buy'):
                keys = (universe, False, 6, 6, leg)
                tables.subperiods(keys, boundaries).to_csv(
                    self.out / f'table6_subperiods_{universe}_{leg}.csv',
                    index=False,
                )
        self.tables = tables

    def _benchmarks(self, grid: pd.DataFrame) -> None:
        """Compares the long-only and long-short series with benchmarks.

        Args:
            grid (pd.DataFrame): The strategy returns.

        Returns:
            None.
        """
        summary = StrategySummary()
        nifty500 = IndexReturns().monthly(self.index_daily, NIFTY_500)
        nifty50 = IndexReturns().monthly(self.index_daily, NIFTY_50)
        momentum = IndexReturns().monthly(self.index_daily, MOMENTUM_30)
        nifty500.to_csv(self.out / 'benchmark_nifty500_monthly.csv')
        nifty50.to_csv(self.out / 'benchmark_nifty50_monthly.csv')
        momentum.to_csv(self.out / 'benchmark_nifty200_momentum30.csv')
        rows = []
        benchmarks = {
            'NIFTY 500 (price + yield/12)': nifty500['total_return'],
            'NIFTY200 Momentum 30 (price + yield/12)': momentum['total_return'],
            'IIMA market (MF + RF)': self.factors.market_return(),
        }
        for universe in ('U1', 'U2'):
            for formation, holding in ((6, 6), (12, 3), (6, 3)):
                keys = (universe, False, formation, holding, 'buy')
                net = self.tables.series(keys, 'net', START, END)
                gross = self.tables.series(keys, 'gross', START, END)
                for name, benchmark in benchmarks.items():
                    common = net.index.intersection(benchmark.dropna().index)
                    if len(common) < 24:
                        continue
                    excess = benchmark.loc[common] - self.risk_free.reindex(
                        common
                    )
                    for label, series in (('gross', gross), ('net', net)):
                        stats = summary.summarize(
                            series.loc[common],
                            excess,
                            self.risk_free,
                            True,
                        )
                        bench_stats = summary.summarize(benchmark.loc[common])
                        stats.update(
                            {
                                'strategy': f'{universe} buy J{formation} '
                                f'K{holding} {label}',
                                'benchmark': name,
                                'benchmark_mean': bench_stats['mean'],
                                'benchmark_compound_annual': bench_stats[
                                    'compound_annual'
                                ],
                                'benchmark_maximum_drawdown': bench_stats[
                                    'maximum_drawdown'
                                ],
                            }
                        )
                        rows.append(stats)
        pd.DataFrame(rows).to_csv(
            self.out / 'long_only_vs_benchmarks.csv', index=False
        )
        wml = self.factors.factors['wml']
        rows = []
        for universe in ('U1', 'U2'):
            for formation, holding in ((6, 6), (12, 3), (6, 3), (12, 12)):
                keys = (universe, False, formation, holding, 'long_short')
                for label in ('gross', 'net'):
                    series = self.tables.series(keys, label, START, END)
                    common = series.index.intersection(wml.dropna().index)
                    rows.append(
                        {
                            'strategy': f'{universe} J{formation} '
                            f'K{holding} {label}',
                            'months': len(common),
                            'mean': series.loc[common].mean(),
                            'wml_mean': wml.loc[common].mean(),
                            'correlation': series.loc[common].corr(
                                wml.loc[common]
                            ),
                        }
                    )
        pd.DataFrame(rows).to_csv(self.out / 'vs_iima_wml.csv', index=False)

    def _paper_tables(self, runner: StudyRunner) -> None:
        """Writes Tables II, III and VII.

        Args:
            runner (StudyRunner): The study runner.

        Returns:
            None.
        """
        tables = PaperTables(
            runner, self.market_excess, self.risk_free, START, END
        )
        for universe in ('U1', 'U2'):
            tables.table_two(universe).to_csv(
                self.out / f'table2_deciles_{universe}.csv', index=False
            )
            tables.table_seven(universe).to_csv(
                self.out / f'table7_event_time_{universe}.csv'
            )
        tables.table_three().to_csv(
            self.out / 'table3_size_beta_groups.csv', index=False
        )

    def _futures(self, runner: StudyRunner) -> None:
        """Runs portfolios C and D.

        Args:
            runner (StudyRunner): The study runner.

        Returns:
            None.
        """
        summary = StrategySummary()
        members = FnoUniverse().build(
            self.fno,
            runner.formation_dates,
            runner.monthly_returns.columns,
        )
        members.index = runner.months
        portfolios = FuturesPortfolios(runner)
        nifty50 = IndexReturns().monthly(self.index_daily, NIFTY_50)
        rows = []
        monthly = {}
        for formation, holding in ((6, 6), (12, 3), (6, 3), (3, 3)):
            result = portfolios.fno_long_short(members, formation, holding)
            for label, series in (
                ('gross', result.gross()),
                ('net', result.net()),
            ):
                series = series.loc[pd.Period(START) : pd.Period(END)]
                stats = summary.summarize(series, self.market_excess)
                stats['portfolio'] = (
                    f'D F&O long-short J{formation} K{holding} {label}'
                )
                rows.append(stats)
                monthly[stats['portfolio']] = series
            hedged = portfolios.hedged_long_only(
                nifty50['total_return'], self.risk_free, formation, holding
            )
            for label in ('gross', 'net'):
                series = hedged[label].loc[pd.Period('2012-03') :]
                stats = summary.summarize(series, self.market_excess)
                stats['portfolio'] = (
                    f'C top-500 winners hedged with NIFTY futures '
                    f'J{formation} K{holding} {label}'
                )
                rows.append(stats)
                monthly[stats['portfolio']] = series
        pd.DataFrame(rows).to_csv(self.out / 'portfolios_c_d.csv', index=False)
        pd.DataFrame(monthly).to_csv(self.out / 'portfolios_c_d_monthly.csv')
        self.fno_members = members

    def _robustness(
        self,
        runner: StudyRunner,
        daily: pd.DataFrame,
        grid: pd.DataFrame,
    ) -> None:
        """Runs the delisting stress, brokerage and trading delay checks.

        Args:
            runner (StudyRunner): The study runner.
            daily (pd.DataFrame): The daily returns.
            grid (pd.DataFrame): The base grid.

        Returns:
            None.
        """
        choices = {
            'formation_choices': (6, 12),
            'holding_choices': (3, 6),
        }
        frames = []
        base = grid[
            grid['formation_months'].isin((6, 12))
            & grid['holding_months'].isin((3, 6))
            & ~grid['skip']
        ].copy()
        base['check'] = 'base'
        frames.append(base)
        original = runner.monthly_returns
        for terminal in (-1.0, -0.3):
            runner.monthly_returns = DelistingStress().apply(original, terminal)
            result = runner.grid(**choices)
            result = result[~result['skip']].copy()
            result['check'] = f'delisting stress {terminal:+.0%}'
            frames.append(result)
        runner.monthly_returns = original
        runner.brokerage = 0.0003
        result = runner.grid(**choices)
        result = result[~result['skip']].copy()
        result['check'] = 'brokerage 0.03% per side'
        frames.append(result)
        runner.brokerage = 0.0
        delayed = StudyRunner(daily, delay_days=1)
        result = delayed.grid(**choices)
        result = result[~result['skip']].copy()
        result['check'] = 'trade one day after formation'
        frames.append(result)
        stacked = pd.concat(frames, ignore_index=True)
        stacked.to_parquet(self.out / 'robustness_monthly.parquet')
        rows = []
        keys = [
            'check',
            'universe',
            'formation_months',
            'holding_months',
            'leg',
        ]
        for key, group in stacked.groupby(keys):
            group = group.copy()
            group['period'] = group['month'].dt.to_period('M')
            group = group[
                (group['period'] >= pd.Period(START))
                & (group['period'] <= pd.Period(END))
            ].dropna(subset=['gross'])
            stats_gross = StrategySummary().summarize(
                group.set_index('period')['gross']
            )
            stats_net = StrategySummary().summarize(
                group.set_index('period')['net']
            )
            rows.append(
                dict(zip(keys, key))
                | {
                    'months': stats_gross['periods'],
                    'gross_mean': stats_gross['mean'],
                    'gross_newey_west_t': stats_gross['newey_west_t'],
                    'net_mean': stats_net['mean'],
                    'net_newey_west_t': stats_net['newey_west_t'],
                }
            )
        pd.DataFrame(rows).to_csv(
            self.out / 'robustness_checks.csv', index=False
        )

    def _variant_count(self, grid: pd.DataFrame) -> None:
        """Counts the variants tried.

        Args:
            grid (pd.DataFrame): The base grid.

        Returns:
            None.
        """
        strategies = grid[
            ['universe', 'skip', 'formation_months', 'holding_months', 'leg']
        ].drop_duplicates()
        count = len(strategies)
        text = (
            f'Core grid: {count} series (2 universes x 2 skip settings x 4 J '
            f'x 4 K x 3 legs). Robustness: 2 delisting stresses + brokerage '
            f'+ one-day delay on 4 J/K pairs x 2 universes x 3 legs = 96. '
            f'Portfolios C and D: 4 J/K pairs each, 2 portfolios = 8. '
            f'Table II, III, VII and benchmark comparisons reuse the '
            f'6/6 strategy.\n'
        )
        (self.out / 'variants_tried.txt').write_text(text)
        print(text)


if __name__ == '__main__':
    MakeResultsApplication().run()
