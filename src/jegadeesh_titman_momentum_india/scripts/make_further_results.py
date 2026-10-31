"""Command-line program for the paper's remaining tests, written to results/further."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg

from jegadeesh_titman_momentum_india.momentum.study_period import (
    StudyPeriod,
)
from jegadeesh_titman_momentum_india.data.timescale_store import (
    TimescaleStore,
)
from jegadeesh_titman_momentum_india.momentum.buy_and_hold import BuyAndHold
from jegadeesh_titman_momentum_india.momentum.calendar_month_table import (
    CalendarMonthTable,
)
from jegadeesh_titman_momentum_india.momentum.event_time_returns import (
    EventTimeReturns,
)
from jegadeesh_titman_momentum_india.momentum.grid_tables import GridTables
from jegadeesh_titman_momentum_india.momentum.iima_factors import IimaFactors
from jegadeesh_titman_momentum_india.momentum.joint_tests import JointTests
from jegadeesh_titman_momentum_india.momentum.paper_tables import PaperTables
from jegadeesh_titman_momentum_india.momentum.profit_sources import (
    ProfitSources,
)
from jegadeesh_titman_momentum_india.momentum.strategy_summary import (
    StrategySummary,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner

START = pd.Period('2005-01', freq='M')
END = pd.Period(StudyPeriod.end(), freq='M')


class MakeFurtherResultsApplication:
    """Runs the paper's tests that the main results leave out."""

    SIZE_GROUPS = ('All', 'S1 (small)', 'S2', 'S3 (large)')

    def run(self) -> None:
        """Runs every test and writes CSV files.

        Returns:
            None.
        """
        self.out = Path('results/further')
        self.out.mkdir(parents=True, exist_ok=True)
        self._load_market()
        daily = pd.read_parquet('data/derived/daily_returns.parquet')
        daily['date'] = pd.to_datetime(daily['date'])
        self.grid = pd.read_parquet('data/derived/grid.parquet')
        self.runner = StudyRunner(daily)
        del daily
        self.tables = GridTables(self.grid, self.market_excess, self.risk_free)
        self._section_three()
        self._size_group_tables()
        self._event_time_betas_and_extension()
        self._buy_and_hold()
        self._flat_cost_test()
        self._equal_weighted_market()
        self._january_reversal()

    def _load_market(self) -> None:
        """Reads the IIMA factors from the database.

        Returns:
            None.
        """
        schema = TimescaleStore.SCHEMA
        connection = psycopg.connect(
            os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL']
        )
        rows = connection.execute(
            f'SELECT month, smb, hml, wml, mf, rf FROM '
            f'{schema}.iima_factors_monthly ORDER BY month'
        ).fetchall()
        iima = IimaFactors(
            pd.DataFrame(
                rows, columns=['month', 'smb', 'hml', 'wml', 'mf', 'rf']
            )
        )
        months = pd.period_range('1996-01', END, freq='M')
        self.risk_free = iima.risk_free(months)
        self.market_excess = iima.factors['mf']
        self.market_total = iima.market_return()

    def _main(self, series: pd.Series) -> pd.Series:
        """Cuts a series to the main sample.

        Args:
            series (pd.Series): Monthly values by month period.

        Returns:
            pd.Series: The values from January 2005 to the last complete month.
        """
        return series.dropna().loc[START:END]

    def _section_three(self) -> None:
        """Writes the weighted strategy, decomposition and lead-lag tests.

        Returns:
            None.
        """
        summaries = []
        decompositions = []
        lead_lags = []
        start = '2004-01'
        past = self.runner.past_returns(6, False)
        for universe in ('U1', 'U2'):
            sources = ProfitSources(
                self.runner.monthly_returns.loc[start:],
                self.runner.universes[universe].loc[start:],
                past.loc[start:],
            )
            deciles = self.runner.deciles(universe, 6, False).loc[start:]
            wrss = sources.wrss_profits().loc[START:]
            cohort = sources.decile_profits(deciles).loc[START:]
            correlation = float(wrss.corr(cohort))
            for name, series in (
                ('weighted relative strength strategy', wrss),
                ('decile winners minus losers', cohort),
            ):
                row = sources.summarize(series)
                row.update({'universe': universe, 'series': name})
                row['correlation_with_other'] = correlation
                summaries.append(row)
                for part in sources.lead_lag(series, self.market_total):
                    part.update({'universe': universe, 'series': name})
                    lead_lags.append(part)
            result = sources.decomposition()
            result['universe'] = universe
            result['note'] = 'as built'
            decompositions.append(result)
            if universe == 'U1':
                period = sources.compounded(ending=True)
                extreme = period.columns[(period > 10).any()]
                trimmed = ProfitSources(
                    self.runner.monthly_returns.loc[start:].drop(
                        columns=extreme
                    ),
                    self.runner.universes[universe].loc[start:].drop(
                        columns=extreme
                    ),
                    past.loc[start:].drop(columns=extreme),
                ).decomposition()
                trimmed['universe'] = universe
                trimmed['note'] = (
                    'shares with a six-month return above +1000% dropped: '
                    + ', '.join(map(str, extreme))
                )
                decompositions.append(trimmed)
        pd.DataFrame(summaries).to_csv(
            self.out / 'section3_profit_summary.csv', index=False
        )
        pd.DataFrame(decompositions).to_csv(
            self.out / 'section3_decomposition.csv', index=False
        )
        pd.DataFrame(lead_lags).to_csv(
            self.out / 'section3_lead_lag.csv', index=False
        )

    def _size_group_tables(self) -> None:
        """Writes Tables IV to VI by size group and the joint tests.

        Returns:
            None.
        """
        paper = PaperTables(
            self.runner,
            self.market_excess,
            self.risk_free,
            '2005-01',
            str(END),
        )
        frames = paper.decile_frames()
        calendar = CalendarMonthTable()
        rows = []
        ftests = []
        subperiods = []
        boundaries = [
            ('2005-01', '2009-12'),
            ('2010-01', '2014-12'),
            ('2015-01', '2019-12'),
            ('2020-01', str(END)),
        ]
        for name in self.SIZE_GROUPS:
            series = self._main(frames[name]['10-1'])
            table = calendar.table(series)
            table['group'] = name
            rows.append(table.reset_index(names='month'))
            ftests.append(
                {
                    'group': name,
                    'all_months_f': calendar.equal_means_test(series)[0],
                    'all_months_p': calendar.equal_means_test(series)[1],
                    'feb_dec_f': calendar.equal_means_test(
                        series, list(range(2, 13))
                    )[0],
                    'feb_dec_p': calendar.equal_means_test(
                        series, list(range(2, 13))
                    )[1],
                }
            )
            part = self.tables.subperiods_of(series, boundaries)
            part['group'] = name
            subperiods.append(part)
        pd.concat(rows).to_csv(self.out / 'table4_by_size.csv', index=False)
        pd.DataFrame(ftests).to_csv(
            self.out / 'table4_by_size_ftests.csv', index=False
        )
        pd.concat(subperiods).to_csv(
            self.out / 'table6_by_size.csv', index=False
        )
        joint = []
        tests = JointTests()
        for name, frame in frames.items():
            deciles = frame[list(range(1, 11))].loc[START:END]
            f_equal, p_equal = tests.equal_means(deciles)
            excess = deciles.sub(self.risk_free.reindex(deciles.index), axis=0)
            f_alpha, p_alpha = tests.zero_alphas(excess, self.market_excess)
            joint.append(
                {
                    'group': name,
                    'equal_returns_f': f_equal,
                    'equal_returns_p': p_equal,
                    'zero_alphas_f': f_alpha,
                    'zero_alphas_p': p_alpha,
                }
            )
        pd.DataFrame(joint).to_csv(
            self.out / 'table3_joint_tests.csv', index=False
        )

    def _event_time_betas_and_extension(self) -> None:
        """Writes event-time betas and the 1997 to 2004 event-time table.

        Returns:
            None.
        """
        maker = EventTimeReturns()
        for universe in ('U1', 'U2'):
            deciles = self.runner.deciles(universe, 6, False)
            main = deciles.copy()
            main.loc[main.index < START] = np.nan
            betas = maker.betas(
                main, self.runner.monthly_returns, self.market_excess
            )
            betas.to_csv(self.out / f'table7_betas_{universe}.csv')
            early = deciles.copy()
            early.loc[early.index < pd.Period('1997-01', freq='M')] = np.nan
            early.loc[early.index > pd.Period('2004-12', freq='M')] = np.nan
            maker.winners_minus_losers(
                early, self.runner.monthly_returns, 36
            ).to_csv(self.out / f'table7_extension_1997_2004_{universe}.csv')

    def _buy_and_hold(self) -> None:
        """Compares buy-and-hold with monthly rebalanced portfolios.

        Returns:
            None.
        """
        runner = self.runner
        holder = BuyAndHold(runner.monthly_returns)
        statistics = StrategySummary()
        rows = []
        for universe in ('U1', 'U2'):
            for formation in (3, 6, 9, 12):
                deciles = runner.deciles(universe, formation, False)
                for holding in (3, 6, 9, 12):
                    winners = holder.portfolio_returns(deciles == 10, holding)
                    losers = holder.portfolio_returns(deciles == 1, holding)
                    spread = self._main(winners - losers)
                    kept = self.tables.series(
                        (universe, False, formation, holding, 'long_short'),
                        'gross',
                        '2005-01',
                        str(END),
                    )
                    held = statistics.summarize(spread)
                    rows.append(
                        {
                            'universe': universe,
                            'formation_months': formation,
                            'holding_months': holding,
                            'buy_and_hold_mean': held['mean'],
                            'buy_and_hold_nw_t': held['newey_west_t'],
                            'rebalanced_mean': kept.mean(),
                            'months': held['periods'],
                        }
                    )
        pd.DataFrame(rows).to_csv(
            self.out / 'buy_and_hold_vs_rebalanced.csv', index=False
        )

    def _flat_cost_test(self) -> None:
        """Applies the paper's flat 0.5% one-way cost to the long-short.

        Returns:
            None.
        """
        statistics = StrategySummary()
        rows = []
        for universe in ('U1', 'U2'):
            for formation in (3, 6, 9, 12):
                for holding in (3, 6, 9, 12):
                    keys = (universe, False, formation, holding)
                    gross = self.tables.series(
                        keys + ('long_short',), 'gross', '2005-01', str(END)
                    )
                    buy = self.tables.series(
                        keys + ('buy',), 'turnover', '2005-01', str(END)
                    )
                    sell = self.tables.series(
                        keys + ('sell',), 'turnover', '2005-01', str(END)
                    )
                    cost = 0.005 * (buy + sell).reindex(gross.index)
                    net = gross - cost
                    result = statistics.summarize(net, self.market_excess)
                    free = statistics.summarize(gross, self.market_excess)
                    rows.append(
                        {
                            'universe': universe,
                            'formation_months': formation,
                            'holding_months': holding,
                            'one_way_turnover_per_six_months': float(
                                (buy.mean() + sell.mean()) / 2.0 * 6.0 / 2.0
                            ),
                            'gross_mean': free['mean'],
                            'gross_alpha_annual': free['alpha'] * 12,
                            'after_half_percent_mean': result['mean'],
                            'after_half_percent_alpha_annual': result['alpha']
                            * 12,
                            'after_half_percent_alpha_t': result['alpha_t'],
                        }
                    )
        pd.DataFrame(rows).to_csv(self.out / 'flat_cost_test.csv', index=False)

    def _equal_weighted_market(self) -> None:
        """Gives alphas against both the value- and equally weighted markets.

        Returns:
            None.
        """
        runner = self.runner
        eligible = runner.universes['U1'].shift(1, fill_value=False)
        equal_market = runner.monthly_returns.where(eligible).mean(axis=1)
        equal_excess = equal_market - self.risk_free.reindex(equal_market.index)
        equal_excess = equal_excess.loc[START:END]
        statistics = StrategySummary()
        rows = []
        for universe in ('U1', 'U2'):
            for leg in ('long_short', 'buy', 'sell'):
                series = self.tables.series(
                    (universe, False, 6, 6, leg), 'gross', '2005-01', str(END)
                )
                for name, market in (
                    ('value weighted (IIMA)', self.market_excess),
                    ('equally weighted (all shares)', equal_excess),
                ):
                    result = statistics.summarize(
                        series, market, self.risk_free, leg != 'long_short'
                    )
                    rows.append(
                        {
                            'universe': universe,
                            'portfolio': leg,
                            'market': name,
                            'alpha': result['alpha'],
                            'alpha_t': result['alpha_t'],
                            'beta': result['beta'],
                        }
                    )
        pd.DataFrame(rows).to_csv(
            self.out / 'alpha_by_market_weighting.csv', index=False
        )

    def _january_reversal(self) -> None:
        """Tests footnote 15: reverse the positions in January only.

        Returns:
            None.
        """
        statistics = StrategySummary()
        summary = []
        by_year = []
        for universe in ('U1', 'U2'):
            for formation, holding in ((6, 6), (12, 3)):
                series = self.tables.series(
                    (universe, False, formation, holding, 'long_short'),
                    'gross',
                    '2005-01',
                    str(END),
                )
                reversed_series = series.where(series.index.month != 1, -series)
                januaries = series[series.index.month == 1]
                normal = statistics.summarize(series, self.market_excess)
                changed = statistics.summarize(
                    reversed_series, self.market_excess
                )
                january_only = -januaries
                summary.append(
                    {
                        'universe': universe,
                        'formation_months': formation,
                        'holding_months': holding,
                        'normal_mean': normal['mean'],
                        'normal_compound_annual': normal['compound_annual'],
                        'normal_alpha_annual': normal['alpha'] * 12,
                        'reversed_mean': changed['mean'],
                        'reversed_compound_annual': changed['compound_annual'],
                        'reversed_alpha_annual': changed['alpha'] * 12,
                        'average_january_spread': januaries.mean(),
                        'reversal_average_january_return': january_only.mean(),
                        'januaries': len(januaries),
                        'januaries_where_reversal_loses': int(
                            (january_only < 0).sum()
                        ),
                        'januaries_where_reversal_gains': int(
                            (january_only > 0).sum()
                        ),
                        'worst_january_for_reversal': january_only.min(),
                        'best_january_for_reversal': january_only.max(),
                        'january_reversal_t': statistics.summarize(
                            january_only
                        )['t_statistic'],
                    }
                )
                for month, value in januaries.items():
                    by_year.append(
                        {
                            'universe': universe,
                            'formation_months': formation,
                            'holding_months': holding,
                            'year': month.year,
                            'normal_january_spread': value,
                            'reversal_return': -value,
                        }
                    )
        pd.DataFrame(summary).to_csv(
            self.out / 'january_reversal.csv', index=False
        )
        pd.DataFrame(by_year).to_csv(
            self.out / 'january_reversal_by_year.csv', index=False
        )


if __name__ == '__main__':
    MakeFurtherResultsApplication().run()
