"""Command-line program that runs the grid of strategies."""

import argparse
from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner


class RunGridApplication:
    """Runs StudyRunner on the saved daily returns."""

    def run(self) -> None:
        """Parses arguments, runs the grid and prints a summary.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--daily', default='data/derived/daily_returns.parquet'
        )
        parser.add_argument('--out', default='data/derived/grid.parquet')
        parser.add_argument('--brokerage', type=float, default=0.0)
        arguments = parser.parse_args()
        daily = pd.read_parquet(arguments.daily)
        daily['date'] = pd.to_datetime(daily['date'])
        runner = StudyRunner(daily, brokerage=arguments.brokerage)
        result = runner.save_grid(Path(arguments.out))
        print(result.shape)


if __name__ == '__main__':
    RunGridApplication().run()
