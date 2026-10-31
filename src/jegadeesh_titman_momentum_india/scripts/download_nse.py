"""Command-line program that downloads one NSE source into data/nse."""

import argparse
import datetime
from pathlib import Path

from jegadeesh_titman_momentum_india.data.bhavcopy_downloader import (
    BhavcopyDownloader,
)
from jegadeesh_titman_momentum_india.data.corporate_actions_downloader import (
    CorporateActionsDownloader,
)
from jegadeesh_titman_momentum_india.data.fno_bhavcopy_downloader import (
    FnoBhavcopyDownloader,
)
from jegadeesh_titman_momentum_india.data.iima_factors_downloader import (
    IimaFactorsDownloader,
)
from jegadeesh_titman_momentum_india.data.index_close_downloader import (
    IndexCloseDownloader,
)


class DownloadNseApplication:
    """Runs one downloader chosen on the command line."""

    SOURCES = (
        'bhavcopy',
        'fno',
        'index',
        'corporate_actions',
        'iima',
    )

    def run(self) -> None:
        """Parses the arguments and runs the chosen downloader.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('source', choices=self.SOURCES)
        parser.add_argument('--data-folder', default='data/nse')
        parser.add_argument('--first', default='1996-01-01')
        parser.add_argument('--last', default=datetime.date.today().isoformat())
        arguments = parser.parse_args()
        root = Path(arguments.data_folder)
        first = datetime.date.fromisoformat(arguments.first)
        last = datetime.date.fromisoformat(arguments.last)
        if arguments.source == 'bhavcopy':
            result = BhavcopyDownloader(root / 'bhavcopy', first, last).run()
        elif arguments.source == 'fno':
            result = FnoBhavcopyDownloader(root / 'fno', first, last).run()
        elif arguments.source == 'index':
            result = IndexCloseDownloader(root / 'index', first, last).run()
        elif arguments.source == 'corporate_actions':
            result = CorporateActionsDownloader(
                root / 'corporate_actions', first.year, last.year
            ).run()
        else:
            result = IimaFactorsDownloader(root / 'iima').run()
        print(result)


if __name__ == '__main__':
    DownloadNseApplication().run()
