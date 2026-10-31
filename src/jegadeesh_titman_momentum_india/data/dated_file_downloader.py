"""Downloads one NSE file per trading day, resuming where it stopped."""

import datetime
from pathlib import Path

from jegadeesh_titman_momentum_india.data.nse_session import NseSession


class DatedFileDownloader:
    """Saves one zip or csv per weekday exactly as NSE served it.

    A day that returns 404 is usually a holiday and is written to
    not_available.txt so that a rerun skips it. A day that returns any other
    failure is left alone and tried again on the next run.

    Attributes:
        folder: Where files and not_available.txt are saved.
        first_day: The first day to try.
        last_day: The last day to try.
        session: The NSE session.
    """

    def __init__(
        self,
        folder: Path,
        first_day: datetime.date,
        last_day: datetime.date,
        session: NseSession | None = None,
    ) -> None:
        """Describes the download.

        Args:
            folder (Path): Where to save.
            first_day (datetime.date): First day to try.
            last_day (datetime.date): Last day to try.
            session (NseSession | None): A session, or None to make one.

        Returns:
            None.
        """
        self.folder = folder
        self.first_day = first_day
        self.last_day = last_day
        self.session = session or NseSession()

    def url_for(self, day: datetime.date) -> str:
        """Gives the address of a day's file.

        Args:
            day (datetime.date): The trading day.

        Returns:
            str: The address.

        Raises:
            NotImplementedError: A subclass must define it.
        """
        raise NotImplementedError

    def file_name_for(self, day: datetime.date) -> str:
        """Gives the name a day's file is saved under.

        Args:
            day (datetime.date): The trading day.

        Returns:
            str: The file name.
        """
        return self.url_for(day).rsplit('/', 1)[-1]

    def run(self) -> dict[str, int]:
        """Downloads every missing day.

        Returns:
            dict[str, int]: Counts of files saved, already present, missing
                at NSE and failed.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        missing_path = self.folder / 'not_available.txt'
        missing_days = set()
        if missing_path.exists():
            missing_days = set(missing_path.read_text().split())
        counts = {'saved': 0, 'present': 0, 'not_available': 0, 'failed': 0}
        day = self.first_day
        while day <= self.last_day:
            if day.weekday() < 5:
                self._fetch_day(day, missing_days, missing_path, counts)
            day += datetime.timedelta(days=1)
        return counts

    def _fetch_day(
        self,
        day: datetime.date,
        missing_days: set[str],
        missing_path: Path,
        counts: dict[str, int],
    ) -> None:
        """Fetches one day unless it is already known.

        Args:
            day (datetime.date): The day.
            missing_days (set[str]): Days known to have no file.
            missing_path (Path): The not_available.txt file.
            counts (dict[str, int]): The running counts, updated here.

        Returns:
            None.
        """
        key = day.isoformat()
        target = self.folder / self.file_name_for(day)
        if target.exists():
            counts['present'] += 1
            return
        if key in missing_days:
            counts['not_available'] += 1
            return
        response = self.session.get(self.url_for(day))
        if response is None or response.status_code not in (200, 404):
            counts['failed'] += 1
            return
        if response.status_code == 404 or len(response.content) < 200:
            with missing_path.open('a') as handle:
                handle.write(key + '\n')
            missing_days.add(key)
            counts['not_available'] += 1
            return
        target.write_bytes(response.content)
        counts['saved'] += 1
