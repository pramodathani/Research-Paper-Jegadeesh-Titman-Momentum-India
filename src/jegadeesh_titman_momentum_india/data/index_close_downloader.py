"""Downloads NSE's daily file of every index's close."""

import datetime

from jegadeesh_titman_momentum_india.data.dated_file_downloader import (
    DatedFileDownloader,
)


class IndexCloseDownloader(DatedFileDownloader):
    """Downloads ind_close_all, which holds closes and dividend yields."""

    def url_for(self, day: datetime.date) -> str:
        """Gives the address of a day's index file.

        Args:
            day (datetime.date): The trading day.

        Returns:
            str: The address.
        """
        return (
            'https://nsearchives.nseindia.com/content/indices/'
            f'ind_close_all_{day.strftime("%d%m%Y")}.csv'
        )
