"""Command-line program that precomputes the tests the page looks up by J, K, gap and universe."""

import json
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
from jegadeesh_titman_momentum_india.momentum.grouped_decile_runs import (
    GroupedDecileRuns,
)
from jegadeesh_titman_momentum_india.momentum.iima_factors import IimaFactors
from jegadeesh_titman_momentum_india.momentum.joint_tests import JointTests
from jegadeesh_titman_momentum_india.momentum.profit_sources import (
    ProfitSources,
)
from jegadeesh_titman_momentum_india.momentum.strategy_summary import (
    StrategySummary,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner

START = pd.Period('2005-01', freq='M')
END = pd.Period(StudyPeriod.end(), freq='M')
PERIODS = (3, 6, 9, 12)
GROUPS = ('All', 'S1 (small)', 'S2', 'S3 (large)', 'B1 (low beta)', 'B2',
          'B3 (high beta)')


class MakeLiveTablesApplication:
    """Computes, for every specification, the results the page cannot recompute.

    The output is results/live/live_tables.json, keyed universe|skip|J|K,
    and results/live/equal_market.csv, the equally weighted market.
    """

    def run(self) -> None:
        """Runs every specification and writes the files.

        Returns:
            None.
        """
        self.out = Path('results/live')
        self.out.mkdir(parents=True, exist_ok=True)
        self._load_market()
        daily = pd.read_parquet('data/derived/daily_returns.parquet')
        daily['date'] = pd.to_datetime(daily['date'])
        self.runner = StudyRunner(daily)
        del daily
        self.groups = GroupedDecileRuns(self.runner)
        size = self.groups.size_groups()
        beta = self.groups.beta_groups()
        self.group_parts = {
            'All': (None, None),
            'S1 (small)': (size, 1),
            'S2': (size, 2),
            'S3 (large)': (size, 3),
            'B1 (low beta)': (beta, 1),
            'B2': (beta, 2),
            'B3 (high beta)': (beta, 3),
        }
        self._equal_market()
        results = {}
        for universe in ('U1', 'U2'):
            for skip in (0, 1):
                for formation in PERIODS:
                    for holding in PERIODS:
                        key = f'{universe}|{skip}|{formation}|{holding}'
                        results[key] = self._one(
                            universe, skip, formation, holding
                        )
                        print(key, flush=True)
        (self.out / 'live_tables.json').write_text(
            json.dumps(results, separators=(',', ':'))
        )

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

    def _equal_market(self) -> None:
        """Writes the equally weighted return of every eligible share.

        Returns:
            None.
        """
        runner = self.runner
        eligible = runner.universes['U1'].shift(1, fill_value=False)
        market = runner.monthly_returns.where(eligible).mean(axis=1)
        market.loc[START:END].rename('equal_market').to_csv(
            self.out / 'equal_market.csv'
        )

    def _main(self, series: pd.Series) -> pd.Series:
        """Cuts a series to the main sample.

        Args:
            series (pd.Series): Monthly values.

        Returns:
            pd.Series: January 2005 to the last complete month.
        """
        return series.dropna().loc[START:END]

    def _one(
        self,
        universe: str,
        skip: int,
        formation: int,
        holding: int,
    ) -> dict:
        """Computes every precomputed table for one specification.

        Args:
            universe (str): U1 or U2.
            skip (int): 1 to leave out the last week before buying.
            formation (int): J.
            holding (int): K.

        Returns:
            dict: Section III, buy-and-hold and joint-test results.
        """
        runner = self.runner
        deciles = runner.deciles(universe, formation, bool(skip))
        return {
            'section3': self._section_three(
                universe, skip, formation, holding, deciles
            ),
            'hold': self._buy_and_hold(deciles, holding),
            'joint': self._joint(universe, skip, formation, holding),
        }

    def _section_three(
        self,
        universe: str,
        skip: int,
        formation: int,
        holding: int,
        deciles: pd.DataFrame,
    ) -> dict:
        """Computes the weighted strategy, decomposition and lead-lag test.

        Args:
            universe (str): U1 or U2.
            skip (int): The gap switch.
            formation (int): J.
            holding (int): K.
            deciles (pd.DataFrame): Deciles at each month-end.

        Returns:
            dict: The results, with numbers rounded for the page.
        """
        runner = self.runner
        start = '2004-01'
        past = runner.past_returns(formation, bool(skip)).loc[start:]
        monthly = runner.monthly_returns.loc[start:]
        eligible = runner.universes[universe].loc[start:]
        sources = ProfitSources(monthly, eligible, past, holding)
        wrss = sources.wrss_profits().loc[START:END]
        cohort = sources.decile_profits(deciles.loc[start:]).loc[START:END]
        result = {
            'correlation': self._round(float(wrss.corr(cohort))),
            'series': {},
            'decomposition': [],
        }
        for name, series in (('wrss', wrss), ('deciles', cohort)):
            summary = sources.summarize(series)
            result['series'][name] = {
                'months': summary['months'],
                'mean': self._round(summary['mean']),
                't': self._round(summary['t_newey_west']),
                'lead_lag': [
                    {
                        'sample': part['sample'],
                        'theta': self._round(part['theta']),
                        't': self._round(part['t']),
                    }
                    for part in sources.lead_lag(series, self.market_total)
                ],
            }
        result['decomposition'].append(
            self._decomposition(sources.decomposition(), 'as built')
        )
        if universe == 'U1':
            period = sources.compounded(ending=True)
            extreme = list(period.columns[(period > 10).any()])
            if extreme:
                trimmed = ProfitSources(
                    monthly.drop(columns=extreme),
                    eligible.drop(columns=extreme),
                    past.drop(columns=extreme),
                    holding,
                ).decomposition()
                result['decomposition'].append(
                    self._decomposition(
                        trimmed, f'{len(extreme)} extreme shares dropped'
                    )
                )
        return result

    def _decomposition(self, values: dict, label: str) -> dict:
        """Rounds a decomposition for the page.

        Args:
            values (dict): The decomposition.
            label (str): Its label.

        Returns:
            dict: The labelled, rounded decomposition.
        """
        return {
            'label': label,
            'total': self._round(values['total']),
            'dispersion': self._round(values['dispersion']),
            'factor': self._round(values['factor']),
            'idiosyncratic': self._round(values['idiosyncratic']),
        }

    def _buy_and_hold(self, deciles: pd.DataFrame, holding: int) -> dict:
        """Computes the buy-and-hold winners-minus-losers spread.

        Args:
            deciles (pd.DataFrame): Deciles at each month-end.
            holding (int): K.

        Returns:
            dict: Mean and Newey-West t.
        """
        holder = BuyAndHold(self.runner.monthly_returns)
        winners = holder.portfolio_returns(deciles == 10, holding)
        losers = holder.portfolio_returns(deciles == 1, holding)
        spread = self._main(winners - losers)
        result = StrategySummary().summarize(spread)
        return {
            'mean': self._round(result['mean']),
            't': self._round(result['newey_west_t']),
        }

    def _joint(
        self,
        universe: str,
        skip: int,
        formation: int,
        holding: int,
    ) -> dict:
        """Computes the joint decile tests for the universe and, for all shares, the groups.

        Args:
            universe (str): U1 or U2.
            skip (int): The gap switch.
            formation (int): J.
            holding (int): K.

        Returns:
            dict: For each group, the F tests and their p-values.
        """
        tests = JointTests()
        calendar = CalendarMonthTable()
        names = GROUPS if universe == 'U1' else ('All',)
        output = {}
        for name in names:
            labels, group = self.group_parts[name]
            frame = self.groups.decile_returns(
                labels, group, formation, holding, universe, bool(skip)
            )
            deciles = frame[list(range(1, 11))].loc[START:END].dropna()
            f_equal, p_equal = tests.equal_means(deciles)
            excess = deciles.sub(self.risk_free.reindex(deciles.index), axis=0)
            f_alpha, p_alpha = tests.zero_alphas(excess, self.market_excess)
            spread = self._main(frame['10-1'])
            f_all, p_all = calendar.equal_means_test(spread)
            f_feb, p_feb = calendar.equal_means_test(
                spread, list(range(2, 13))
            )
            output[name] = {
                'equal': [self._round(f_equal), self._round(p_equal, 5)],
                'alpha': [self._round(f_alpha), self._round(p_alpha, 5)],
                'calendar': [self._round(f_all), self._round(p_all, 5)],
                'calendar_feb_dec': [
                    self._round(f_feb),
                    self._round(p_feb, 5),
                ],
            }
        return output

    @staticmethod
    def _round(value: float, places: int = 4) -> float | None:
        """Rounds a number, turning NaN into None for JSON.

        Args:
            value (float): The number.
            places (int): Decimal places to keep.

        Returns:
            float | None: The rounded number or None.
        """
        if value is None or not np.isfinite(value):
            return None
        return round(float(value), places)


if __name__ == '__main__':
    MakeLiveTablesApplication().run()
