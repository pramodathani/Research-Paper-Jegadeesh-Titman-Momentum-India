"""Command-line program that refreshes the whole study with the latest data.

Run it from the repository root, with the database address in the
environment. It downloads what NSE has published since the last run, loads
the database, rebuilds returns, the grid, every result file, the page's data
and the hand-off targets, and writes results/update_report.md. Pushing the
repository, republishing the page and reinstalling the hand-off package
still need the user's approval and are not done here.
"""

import argparse
import datetime
import subprocess
import sys
import time
from pathlib import Path

PACKAGE = 'jegadeesh_titman_momentum_india.scripts'

DOWNLOADS = (
    'bhavcopy',
    'fno',
    'index',
    'corporate_actions',
    'iima',
    'symbol_changes',
    'results_dates',
)
LOADS = ('bhavcopy', 'fno', 'index', 'corporate_actions', 'iima')


class UpdateStudyApplication:
    """Runs every refresh step in order and records how long each took."""

    def run(self) -> None:
        """Parses the arguments and runs the steps.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument(
            '--through-month',
            default=None,
            help='last month to use, YYYY-MM; default: the last complete month',
        )
        parser.add_argument(
            '--skip-download',
            action='store_true',
            help='use the files already in data/nse',
        )
        parser.add_argument(
            '--from-step',
            default=None,
            help='start at this step name, after a failure',
        )
        arguments = parser.parse_args()
        steps = self._steps(arguments)
        names = [name for name, _ in steps]
        if arguments.from_step:
            steps = steps[names.index(arguments.from_step) :]
        report = []
        for name, command in steps:
            started = time.time()
            print(f'== {name}', flush=True)
            result = subprocess.run(command, check=False)
            seconds = round(time.time() - started)
            report.append((name, result.returncode, seconds))
            if result.returncode:
                self._write(report)
                sys.exit(f'step {name} failed with exit status {result.returncode}')
        self._write(report)

    def _steps(self, arguments: argparse.Namespace) -> list[tuple[str, list]]:
        """Lists the steps in order.

        Args:
            arguments (argparse.Namespace): The parsed arguments.

        Returns:
            list[tuple[str, list]]: Each step's name and command.
        """
        python = sys.executable
        module = lambda name, *extra: [python, '-m', f'{PACKAGE}.{name}', *extra]
        steps = []
        if not arguments.skip_download:
            for source in DOWNLOADS:
                steps.append((f'download {source}', module('download_nse', source)))
        for source in LOADS:
            steps.append((f'load {source}', module('load_database', source)))
        build = module('build_returns')
        if arguments.through_month:
            build += ['--through-month', arguments.through_month]
        steps += [
            ('build returns', build),
            ('run grid', module('run_grid')),
            ('make results', module('make_results')),
            ('make table nine', module('make_table_nine')),
            ('make further results', module('make_further_results')),
            ('make live tables', module('make_live_tables')),
            ('make summary tables', module('make_summary_tables')),
            ('make charts', module('make_charts')),
            ('build snapshot', module('build_snapshot')),
            ('build brief page', module('build_brief_page')),
            ('store shared results', module('store_shared_results')),
            ('check page text', module('check_page_text')),
        ]
        return steps

    def _write(self, report: list[tuple[str, int, int]]) -> None:
        """Writes the update report.

        Args:
            report (list[tuple[str, int, int]]): Step, exit status, seconds.

        Returns:
            None.
        """
        lines = [
            f'# Update report, {datetime.datetime.now():%Y-%m-%d %H:%M}\n',
            '| Step | Exit status | Seconds |',
            '|---|---|---|',
        ]
        lines += [f'| {name} | {code} | {seconds} |' for name, code, seconds in report]
        lines.append(
            '\nNext, by hand: re-read the figures flagged by check_page_text, '
            'run the tests, commit, then ask for github_push, publish_site '
            'and install_into_trading_agent.'
        )
        Path('results').mkdir(exist_ok=True)
        Path('results/update_report.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    UpdateStudyApplication().run()
