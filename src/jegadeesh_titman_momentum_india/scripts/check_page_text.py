"""Command-line program that checks the page's prose against the latest results.

The tables and the dates on the page fill themselves from the snapshot. The
sentences in sections 4.2 to 4.7 quote numbers typed by hand, so after a
refresh this program recomputes the ones it can and lists any that no longer
appear on the page, and names the rest to re-read.
"""

from pathlib import Path

import pandas as pd

import jegadeesh_titman_momentum_india


class CheckPageTextApplication:
    """Compares numbers quoted in the page's prose with the results files."""

    MANUAL = (
        'Section 4.2: the count of positive cells after costs, the turnover '
        'figures and the 3/3 example.',
        'Section 4.3: the range of the spread across size and beta groups.',
        'Section 4.4: the strongest and weakest calendar months.',
        'Section 4.6: portfolio B (winners only) mean, beta and alphas, and '
        'the number of shares with stock futures.',
        'Section 4.7: the number of series tried and the Bonferroni counts.',
        'Abstract: the top-200 and futures-universe spreads, the 2009 '
        'drawdown and the hedged portfolio.',
        'Section 3: the number of symbol changes and the date of the first '
        'reliable corporate-action records.',
        'Section 4.8 text: the January and Section III sentences.',
    )

    def run(self) -> None:
        """Runs the checks and prints what to fix.

        Returns:
            None.
        """
        package = Path(jegadeesh_titman_momentum_india.__file__).parent
        page = (package / 'site' / 'index.html').read_text()
        results = Path('results')
        portfolios = pd.read_csv(results / 'portfolios_c_d.csv')
        hedged = portfolios[
            portfolios['portfolio'].str.startswith('C top-500')
            & portfolios['portfolio'].str.endswith('J6 K6 net')
        ].iloc[0]
        event = pd.read_csv(results / 'table7_event_time_U2.csv')
        event_all = pd.read_csv(results / 'table7_event_time_U1.csv')
        checks = {
            'hedged portfolio, mean a month after costs': (
                f"{hedged['mean'] * 100:.2f}%"
            ),
            'hedged portfolio, worst drawdown': (
                f"{abs(hedged['maximum_drawdown']) * 100:.0f}%"
            ),
            'top 500, cumulative spread after 36 months': (
                f"{event.loc[event['month_after'] == 36, 'cumulative'].iloc[0] * 100:.1f}%"
            ),
            'all shares, cumulative spread after 12 months': (
                f"{event_all.loc[event_all['month_after'] == 12, 'cumulative'].iloc[0] * 100:.1f}%"
            ),
        }
        stale = 0
        for label, text in checks.items():
            found = text in page
            stale += not found
            print(f"{'ok     ' if found else 'STALE  '}{label}: {text}")
        print('\nRe-read by hand:')
        for line in self.MANUAL:
            print(f'  - {line}')
        if stale:
            print(f'\n{stale} quoted figures changed; edit site/index.html.')


if __name__ == '__main__':
    CheckPageTextApplication().run()
