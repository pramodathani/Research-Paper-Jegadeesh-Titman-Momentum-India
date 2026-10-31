"""Turns the study's derived results into the companion page's JSON snapshot."""

import datetime
import json
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd


from jegadeesh_titman_momentum_india.momentum.study_period import (
    StudyPeriod,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner


class SiteSnapshot:
    """Builds a compact snapshot of monthly returns and result tables.

    Returns are stored as integers in units of 0.01% (one basis point), so
    1.42% is 142; turnover is stored the same way as a fraction of one leg.

    Attributes:
        grid: The long table of strategy returns.
        results: The results folder.
        first_month: The first month kept.
        last_month: The last month kept.
    """

    SCALE = 10000

    def __init__(
        self,
        grid: pd.DataFrame,
        results: Path,
        first_month: str = '1997-01',
        last_month: str | None = None,
    ) -> None:
        """Keeps the inputs.

        Args:
            grid (pd.DataFrame): The strategy returns from StudyRunner.grid.
            results (Path): The results folder with the CSV files.
            first_month (str): The first month kept.
            last_month (str): The last month kept.

        Returns:
            None.
        """
        self.grid = grid.copy()
        self.grid['period'] = self.grid['month'].dt.to_period('M')
        self.results = results
        self.months = pd.period_range(
            first_month, last_month or StudyPeriod.end(), freq='M'
        )

    def _encode(self, series: pd.Series) -> list[int | None]:
        """Turns a monthly series into integers aligned with the months.

        Args:
            series (pd.Series): Decimal values indexed by month period.

        Returns:
            list[int | None]: One value per month, None where missing.
        """
        aligned = series.reindex(self.months)
        values = []
        for value in aligned:
            if value is None or pd.isna(value):
                values.append(None)
            else:
                values.append(round(float(value) * self.SCALE))
        return values

    def _clean(self, value: Any) -> Any:
        """Makes a value safe for JSON, rounding floats.

        Args:
            value (Any): A value from a table.

        Returns:
            Any: The value, with NaN turned into None.
        """
        if isinstance(value, float):
            if math.isnan(value):
                return None
            return round(value, 6)
        return value

    def _records(self, table: pd.DataFrame) -> list[dict[str, Any]]:
        """Turns a table into JSON-safe records.

        Args:
            table (pd.DataFrame): The table.

        Returns:
            list[dict[str, Any]]: One dictionary per row.
        """
        records = []
        for row in table.to_dict('records'):
            records.append(
                {key: self._clean(value) for key, value in row.items()}
            )
        return records

    def series(self) -> dict[str, dict[str, list]]:
        """Encodes every strategy's gross, net and turnover series.

        The key is universe|skip|J|K|leg. The long-short leg has no turnover
        series, because the page adds the two legs' turnover.

        Returns:
            dict[str, dict[str, list]]: Series by key.
        """
        encoded = {}
        keys = [
            'universe',
            'skip',
            'formation_months',
            'holding_months',
            'leg',
        ]
        for key, group in self.grid.groupby(keys):
            universe, skip, formation, holding, leg = key
            frame = group.set_index('period')
            name = f'{universe}|{int(skip)}|{formation}|{holding}|{leg}'
            encoded[name] = {
                'g': self._encode(frame['gross']),
                'n': self._encode(frame['net']),
            }
            if leg != 'long_short':
                encoded[name]['t'] = self._encode(frame['turnover'])
        return encoded

    def market(self) -> dict[str, list]:
        """Encodes the market, risk-free and benchmark series.

        Returns:
            dict[str, list]: market (IIMA total market return), rf, wml and
                nifty500 (price plus a twelfth of the dividend yield).
        """
        market = pd.read_csv(self.results / 'market_monthly.csv', index_col=0)
        market.index = pd.PeriodIndex(market.index, freq='M')
        nifty = pd.read_csv(
            self.results / 'benchmark_nifty500_monthly.csv', index_col=0
        )
        nifty.index = pd.PeriodIndex(nifty.index, freq='M')
        risk_free = market['risk_free'].reindex(self.months).ffill()
        equal = pd.read_csv(
            self.results / 'live' / 'equal_market.csv', index_col=0
        ).iloc[:, 0]
        equal.index = pd.PeriodIndex(equal.index, freq='M')
        return {
            'equal_market': self._encode(equal),
            'market': self._encode(market['market_return']),
            'rf': self._encode(risk_free),
            'wml': self._encode(market['wml']),
            'nifty500': self._encode(nifty['total_return']),
        }

    def extensions(self) -> dict[str, dict[str, list]]:
        """Encodes portfolios C and D.

        Returns:
            dict[str, dict[str, list]]: Gross and net series by name.
        """
        table = pd.read_csv(
            self.results / 'portfolios_c_d_monthly.csv', index_col=0
        )
        table.index = pd.PeriodIndex(table.index, freq='M')
        encoded = {}
        names = sorted({column.rsplit(' ', 1)[0] for column in table.columns})
        for name in names:
            encoded[name] = {
                'g': self._encode(table[f'{name} gross']),
                'n': self._encode(table[f'{name} net']),
            }
        return encoded

    def tables(self) -> dict[str, Any]:
        """Collects the fixed result tables of the main sample.

        Returns:
            dict[str, Any]: Tables II, III, VII and IX, the robustness checks,
                portfolios C and D and the comparison with IIMA's WML.
        """
        folder = self.results
        tables = {
            'table2': {
                universe: self._records(
                    pd.read_csv(folder / f'table2_deciles_{universe}.csv')
                )
                for universe in ('U1', 'U2')
            },
            'table3': self._records(
                pd.read_csv(folder / 'table3_size_beta_groups.csv')
            ),
            'table7': {
                universe: self._records(
                    pd.read_csv(folder / f'table7_event_time_{universe}.csv')
                )
                for universe in ('U1', 'U2')
            },
            'table9': {
                universe: self._records(
                    pd.read_csv(folder / f'table9_announcements_{universe}.csv')
                )
                for universe in ('U1', 'U2')
            },
            'robustness': self._records(
                pd.read_csv(folder / 'robustness_checks.csv')
            ),
            'portfolios_c_d': self._records(
                pd.read_csv(folder / 'portfolios_c_d.csv')
            ),
            'iima': self._records(pd.read_csv(folder / 'vs_iima_wml.csv')),
            'long_only': self._records(
                pd.read_csv(folder / 'long_only_vs_benchmarks.csv')
            ),
        }
        further = folder / 'further'
        names = (
            'january_reversal',
            'section3_profit_summary',
            'section3_decomposition',
            'section3_lead_lag',
            'table3_joint_tests',
            'table4_by_size_ftests',
            'flat_cost_test',
            'alpha_by_market_weighting',
            'buy_and_hold_vs_rebalanced',
        )
        tables['further'] = {
            name: self._records(pd.read_csv(further / f'{name}.csv'))
            for name in names
            if (further / f'{name}.csv').exists()
        }
        return tables

    def iima_end(self) -> str:
        """Gives the month name when the market factor series ends.

        Returns:
            str: Such as December 2025.
        """
        market = pd.read_csv(self.results / 'market_monthly.csv', index_col=0)
        market.index = pd.PeriodIndex(market.index, freq='M')
        last = market['market_return'].dropna().index.max()
        return last.strftime('%B %Y')

    def prose(self) -> dict[str, str]:
        """Gives the dates and counts the page's text quotes.

        Returns:
            dict[str, str]: The last month, the last data date, and the
                numbers of trading days and symbols in the price files.
        """
        import psycopg

        from jegadeesh_titman_momentum_india.data.timescale_store import (
            TimescaleStore,
        )

        connection = psycopg.connect(
            os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL']
        )
        days, symbols = connection.execute(
            'SELECT count(DISTINCT date), count(DISTINCT symbol) FROM '
            f'{TimescaleStore.SCHEMA}.daily_prices_raw'
        ).fetchone()
        daily = pd.read_parquet(
            'data/derived/daily_returns.parquet', columns=['date']
        )
        last = pd.to_datetime(daily['date']).max()
        return {
            'end_label': self.months[-1].strftime('%B %Y'),
            'data_to': f'{last.day} {last:%B %Y}',
            'iima_end': self.iima_end(),
            'trading_days': f'{days:,}',
            'symbols': f'{symbols:,}',
        }

    def build(self) -> dict[str, Any]:
        """Builds the whole snapshot.

        Returns:
            dict[str, Any]: The snapshot.
        """
        return {
            'generated': datetime.date.today().isoformat(),
            'scale': self.SCALE,
            'months': [str(month) for month in self.months],
            'main_sample': ['2005-01', str(self.months[-1])],
            'impact': dict(StudyRunner.UNIVERSE_IMPACT),
            'series': self.series(),
            'benchmarks': self.market(),
            'extensions': self.extensions(),
            'prose': self.prose(),
            'tables': self.tables(),
            'live': json.loads(
                (self.results / 'live' / 'live_tables.json').read_text()
            ),
        }

    def write(self, folder: Path) -> Path:
        """Writes the snapshot as compact JSON.

        Args:
            folder (Path): The site's data folder.

        Returns:
            Path: The file written.
        """
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'snapshot.json'
        path.write_text(json.dumps(self.build(), separators=(',', ':')))
        return path
