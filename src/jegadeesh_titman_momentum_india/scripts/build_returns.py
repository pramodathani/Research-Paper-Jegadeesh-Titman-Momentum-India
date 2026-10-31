"""Command-line program that builds adjusted daily returns from the database."""

import argparse
import os
from pathlib import Path

import pandas as pd
import psycopg

from jegadeesh_titman_momentum_india.data.timescale_store import (
    TimescaleStore,
)
from jegadeesh_titman_momentum_india.momentum.daily_return_builder import (
    DailyReturnBuilder,
)


class BuildReturnsApplication:
    """Reads raw prices and actions, builds returns, saves and stores them."""

    def run(self) -> None:
        """Runs the build.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--out-folder', default='data/derived')
        parser.add_argument('--skip-database', action='store_true')
        arguments = parser.parse_args()
        schema = TimescaleStore.SCHEMA
        connection = psycopg.connect(
            os.environ['RESEARCH_ANALYST_TIMESCALEDB_URL']
        )
        prices = pd.DataFrame(
            connection.execute(
                'SELECT date, symbol, series, isin, close, previous_close, '
                f'traded_value FROM {schema}.daily_prices_raw'
            ).fetchall(),
            columns=[
                'date',
                'symbol',
                'series',
                'isin',
                'close',
                'previous_close',
                'traded_value',
            ],
        )
        prices['date'] = pd.to_datetime(prices['date'])
        actions = pd.DataFrame(
            connection.execute(
                'SELECT ex_date, symbol, subject, face_value '
                f'FROM {schema}.corporate_actions'
            ).fetchall(),
            columns=['ex_date', 'symbol', 'subject', 'face_value'],
        )
        returns, flags = DailyReturnBuilder().build(prices, actions)
        folder = Path(arguments.out_folder)
        folder.mkdir(parents=True, exist_ok=True)
        returns.to_parquet(folder / 'daily_returns.parquet')
        flags.to_parquet(folder / 'return_flags.parquet')
        print(f'{len(returns)} daily returns, {len(flags)} flagged days')
        if arguments.skip_database:
            return
        store = TimescaleStore()
        store.create_tables()
        stored = returns[['date', 'symbol', 'ret']].dropna(subset=['ret'])
        for start in range(0, len(stored), 2_000_000):
            store.upsert(
                'daily_returns',
                stored.iloc[start : start + 2_000_000],
                ['symbol', 'date'],
            )
        store.upsert(
            'return_flags',
            flags[['date', 'symbol', 'kind', 'ret_raw']],
            ['symbol', 'kind', 'date'],
        )


if __name__ == '__main__':
    BuildReturnsApplication().run()
