"""Downloads NSE's daily share bhavcopy files."""

import datetime

from jegadeesh_titman_momentum_india.data.dated_file_downloader import (
    DatedFileDownloader,
)


class BhavcopyDownloader(DatedFileDownloader):
    """Downloads the cash market bhavcopy in both of NSE's formats.

    Days up to 5 July 2024 use the old format, later days the UDiFF format.
    """

    LAST_OLD_FORMAT_DAY = datetime.date(2024, 7, 5)

    def url_for(self, day: datetime.date) -> str:
        """Gives the address of a day's bhavcopy.

        Args:
            day (datetime.date): The trading day.

        Returns:
            str: The address.
        """
        base = 'https://nsearchives.nseindia.com/content'
        if day > self.LAST_OLD_FORMAT_DAY:
            return (
                f'{base}/cm/BhavCopy_NSE_CM_0_0_0_'
                f'{day.strftime("%Y%m%d")}_F_0000.csv.zip'
            )
        month = day.strftime('%b').upper()
        return (
            f'{base}/historical/EQUITIES/{day.year}/{month}/'
            f'cm{day.strftime("%d")}{month}{day.year}bhav.csv.zip'
        )
