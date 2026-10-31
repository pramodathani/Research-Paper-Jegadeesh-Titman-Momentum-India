"""Downloads NSE's daily futures and options bhavcopy files."""

import datetime

from jegadeesh_titman_momentum_india.data.dated_file_downloader import (
    DatedFileDownloader,
)


class FnoBhavcopyDownloader(DatedFileDownloader):
    """Downloads the derivatives bhavcopy, which lists stock futures."""

    LAST_OLD_FORMAT_DAY = datetime.date(2024, 7, 5)

    def url_for(self, day: datetime.date) -> str:
        """Gives the address of a day's derivatives bhavcopy.

        Args:
            day (datetime.date): The trading day.

        Returns:
            str: The address.
        """
        base = 'https://nsearchives.nseindia.com/content'
        if day > self.LAST_OLD_FORMAT_DAY:
            return (
                f'{base}/fo/BhavCopy_NSE_FO_0_0_0_'
                f'{day.strftime("%Y%m%d")}_F_0000.csv.zip'
            )
        month = day.strftime('%b').upper()
        return (
            f'{base}/historical/DERIVATIVES/{day.year}/{month}/'
            f'fo{day.strftime("%d")}{month}{day.year}bhav.csv.zip'
        )
