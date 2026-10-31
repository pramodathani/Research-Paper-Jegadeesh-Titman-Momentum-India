"""Tests of the companion page's snapshot encoding."""

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.site_snapshot import SiteSnapshot


class TestSiteSnapshot:
    """Tests of SiteSnapshot."""

    def test_series_are_aligned_basis_points(self) -> None:
        """Returns become integers in basis points on the month grid.

        Returns:
            None.
        """
        grid = pd.DataFrame(
            {
                'month': pd.to_datetime(['2010-02-01', '2010-03-01']),
                'universe': 'U2',
                'skip': False,
                'formation_months': 6,
                'holding_months': 6,
                'leg': 'buy',
                'gross': [0.0142, -0.0031],
                'net': [0.0138, -0.0035],
                'turnover': [0.32, 0.30],
                'holding_count': 100,
            }
        )
        snapshot = SiteSnapshot(grid, None, '2010-01', '2010-03')
        series = snapshot.series()['U2|0|6|6|buy']
        assert series['g'] == [None, 142, -31]
        assert series['t'] == [None, 3200, 3000]

    def test_long_short_has_no_turnover(self) -> None:
        """The long-short leg leaves turnover to the page.

        Returns:
            None.
        """
        grid = pd.DataFrame(
            {
                'month': pd.to_datetime(['2010-01-01']),
                'universe': 'U1',
                'skip': True,
                'formation_months': 3,
                'holding_months': 3,
                'leg': 'long_short',
                'gross': [0.01],
                'net': [0.009],
                'turnover': [0.3],
                'holding_count': 100,
            }
        )
        snapshot = SiteSnapshot(grid, None, '2010-01', '2010-01')
        series = snapshot.series()['U1|1|3|3|long_short']
        assert 't' not in series
        assert series['n'] == [90]
