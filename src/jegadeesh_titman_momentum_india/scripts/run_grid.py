"""Command-line program that runs the grid of strategies."""

import argparse
from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.data.timescale_store import (
    TimescaleStore,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner


class RunGridApplication:
    """Runs StudyRunner on the saved daily returns and stores the outputs."""

    def run(self) -> None:
        """Parses arguments, runs the grid, saves and stores it.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--daily',
            default='data/derived/daily_returns.parquet',
        )
        parser.add_argument('--out', default='data/derived/grid.parquet')
        parser.add_argument('--brokerage', type=float, default=0.0)
        parser.add_argument('--skip-database', action='store_true')
        arguments = parser.parse_args()
        daily = pd.read_parquet(arguments.daily)
        daily['date'] = pd.to_datetime(daily['date'])
        runner = StudyRunner(daily, brokerage=arguments.brokerage)
        result = runner.save_grid(Path(arguments.out))
        print(result.shape)
        if arguments.skip_database:
            return
        self._store(runner, result)

    def _store(self, runner: StudyRunner, result: pd.DataFrame) -> None:
        """Writes monthly returns, universes and the grid to the database.

        Args:
            runner (StudyRunner): The runner with its tables.
            result (pd.DataFrame): The grid.

        Returns:
            None.
        """
        store = TimescaleStore()
        store.create_tables()
        for table in (
            'monthly_returns',
            'universe_membership',
            'strategy_returns_detail',
        ):
            store.clear(table)
        monthly = runner.monthly_returns.copy()
        monthly.index = monthly.index.to_timestamp()
        monthly.index.name = 'month'
        long_returns = monthly.stack().rename('ret').reset_index()
        long_returns.columns = ['month', 'symbol', 'ret']
        for start in range(0, len(long_returns), 1_000_000):
            store.upsert(
                'monthly_returns',
                long_returns.iloc[start : start + 1_000_000],
                ['symbol', 'month'],
            )
        for name, table in runner.universes.items():
            members = table.copy()
            members.index = members.index.to_timestamp()
            members.index.name = 'month'
            stacked = members.stack()
            stacked = stacked[stacked].reset_index()
            stacked.columns = ['month', 'symbol', 'member']
            stacked['universe'] = name
            store.upsert(
                'universe_membership',
                stacked[['month', 'universe', 'symbol']],
                ['universe', 'symbol', 'month'],
            )
        detail = result.dropna(subset=['gross']).copy()
        store.upsert(
            'strategy_returns_detail',
            detail[
                [
                    'month',
                    'universe',
                    'skip',
                    'formation_months',
                    'holding_months',
                    'leg',
                    'gross',
                    'net',
                    'turnover',
                    'holding_count',
                ]
            ],
            [
                'universe',
                'skip',
                'formation_months',
                'holding_months',
                'leg',
                'month',
            ],
        )


if __name__ == '__main__':
    RunGridApplication().run()
