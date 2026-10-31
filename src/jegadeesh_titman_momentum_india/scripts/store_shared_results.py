"""Command-line program that writes monthly strategy returns to the shared table."""

import os

import pandas as pd
import psycopg

PROJECT = 'jegadeesh-and-titman-research-analyst'
UNIVERSE_NAMES = {
    'U1': 'nse-all-shares',
    'U2': 'nse-top500-traded-value',
}
LEG_NAMES = {
    'buy': 'winners-long-only',
    'long_short': 'winners-minus-losers',
}


class StoreSharedResultsApplication:
    """Upserts the no-skip strategies and portfolios C and D into results.strategy_returns."""

    def run(self) -> None:
        """Builds the rows and writes them.

        Returns:
            None.
        """
        grid = pd.read_parquet('data/derived/grid.parquet')
        market = pd.read_csv('results/market_monthly.csv', index_col=0)
        market.index = pd.PeriodIndex(market.index, freq='M').to_timestamp()
        benchmark = market['market_return']
        rows = []
        chosen = grid[
            ~grid['skip']
            & grid['leg'].isin(LEG_NAMES)
            & (grid['month'] >= '2005-01-01')
        ].dropna(subset=['gross'])
        for row in chosen.itertuples(index=False):
            rows.append(
                (
                    row.month.date(),
                    PROJECT,
                    (
                        f'J{row.formation_months}-K{row.holding_months}-'
                        f'{LEG_NAMES[row.leg]}'
                    ),
                    UNIVERSE_NAMES[row.universe],
                    float(row.gross),
                    float(row.net),
                    self._benchmark(benchmark, row.month),
                )
            )
        extensions = pd.read_csv(
            'results/portfolios_c_d_monthly.csv', index_col=0
        )
        extensions.index = pd.PeriodIndex(
            extensions.index, freq='M'
        ).to_timestamp()
        pairs = {
            'C-top500-winners-hedged-nifty-futures-J6-K6': (
                'C top-500 winners hedged with NIFTY futures J6 K6',
                'nse-top500-traded-value',
            ),
            'D-fno-winners-minus-losers-stock-futures-J6-K6': (
                'D F&O long-short J6 K6',
                'nse-fno-shares',
            ),
        }
        for strategy, (prefix, universe) in pairs.items():
            gross = extensions[f'{prefix} gross'].dropna()
            net = extensions[f'{prefix} net']
            for month, value in gross.items():
                rows.append(
                    (
                        month.date(),
                        PROJECT,
                        strategy,
                        universe,
                        float(value),
                        float(net.loc[month]),
                        self._benchmark(benchmark, month),
                    )
                )
        self._write(rows)
        print(f'{len(rows)} rows written')

    def _benchmark(
        self, benchmark: pd.Series, month: pd.Timestamp
    ) -> float | None:
        """Gives the market's return for a month if known.

        Args:
            benchmark (pd.Series): The market's monthly return.
            month (pd.Timestamp): The month's first day.

        Returns:
            float | None: The return, or None when unknown.
        """
        value = benchmark.get(month)
        if value is None or pd.isna(value):
            return None
        return float(value)

    def _write(self, rows: list[tuple]) -> None:
        """Upserts the rows.

        Args:
            rows (list[tuple]): month, project, strategy, universe, gross,
                net and benchmark.

        Returns:
            None.
        """
        with psycopg.connect(
            os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL']
        ) as connection:
            connection.execute('CREATE SCHEMA IF NOT EXISTS results')
            connection.execute(
                'CREATE TABLE IF NOT EXISTS results.strategy_returns ('
                'month date NOT NULL, project text NOT NULL, '
                'strategy text NOT NULL, universe text NOT NULL, '
                'return_before_costs double precision, '
                'return_after_costs double precision, '
                'benchmark_return double precision, '
                'updated_at timestamptz NOT NULL DEFAULT now(), '
                'PRIMARY KEY (project, strategy, universe, month))'
            )
            connection.execute(
                "SELECT create_hypertable('results.strategy_returns', "
                "by_range('month'), if_not_exists => TRUE)"
            )
            with connection.cursor() as cursor:
                cursor.executemany(
                    'INSERT INTO results.strategy_returns (month, project, '
                    'strategy, universe, return_before_costs, '
                    'return_after_costs, benchmark_return) VALUES '
                    '(%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (project, '
                    'strategy, universe, month) DO UPDATE SET '
                    'return_before_costs = EXCLUDED.return_before_costs, '
                    'return_after_costs = EXCLUDED.return_after_costs, '
                    'benchmark_return = EXCLUDED.benchmark_return, '
                    'updated_at = now()',
                    rows,
                )


if __name__ == '__main__':
    StoreSharedResultsApplication().run()
