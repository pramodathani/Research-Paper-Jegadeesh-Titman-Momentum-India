"""Command-line program that writes the companion page's data snapshot."""

from pathlib import Path

import pandas as pd

import jegadeesh_titman_momentum_india
from jegadeesh_titman_momentum_india.momentum.site_snapshot import SiteSnapshot


class BuildSnapshotApplication:
    """Writes site/data/snapshot.json from the grid and results/."""

    def run(self) -> None:
        """Builds and writes the snapshot.

        Returns:
            None.
        """
        grid = pd.read_parquet('data/derived/grid.parquet')
        package = Path(jegadeesh_titman_momentum_india.__file__).parent
        snapshot = SiteSnapshot(grid, Path('results'))
        path = snapshot.write(package / 'site' / 'data')
        print(f'{path} {path.stat().st_size} bytes')


if __name__ == '__main__':
    BuildSnapshotApplication().run()
