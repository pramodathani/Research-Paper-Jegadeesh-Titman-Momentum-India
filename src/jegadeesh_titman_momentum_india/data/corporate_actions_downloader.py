"""Downloads NSE's corporate actions list, one year at a time."""

import datetime
import json
from pathlib import Path

from jegadeesh_titman_momentum_india.data.nse_session import NseSession


class CorporateActionsDownloader:
    """Saves the corporate actions API's answer for each calendar year.

    Attributes:
        folder: Where the yearly JSON files are saved.
        first_year: The first year to fetch.
        last_year: The last year to fetch.
        session: The NSE session.
    """

    WARM_UP_URL = (
        'https://www.nseindia.com/companies-listing/corporate-filings-actions'
    )

    def __init__(
        self,
        folder: Path,
        first_year: int,
        last_year: int,
        session: NseSession | None = None,
    ) -> None:
        """Describes the download.

        Args:
            folder (Path): Where to save.
            first_year (int): First year.
            last_year (int): Last year.
            session (NseSession | None): A session, or None to make one.

        Returns:
            None.
        """
        self.folder = folder
        self.first_year = first_year
        self.last_year = last_year
        self.session = session or NseSession(pause_seconds=1.0)

    def run(self) -> dict[int, int]:
        """Fetches every year whose file is missing, and the current year.

        Returns:
            dict[int, int]: Rows saved for each year fetched in this run.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session.get(self.WARM_UP_URL)
        saved = {}
        current_year = datetime.date.today().year
        for year in range(self.first_year, self.last_year + 1):
            target = self.folder / f'corporate_actions_{year}.json'
            if target.exists() and year != current_year:
                continue
            rows = self._fetch_year(year)
            if rows is None:
                continue
            target.write_text(json.dumps(rows))
            saved[year] = len(rows)
        return saved

    def _fetch_year(self, year: int) -> list | None:
        """Fetches one year in half-year pieces to stay under any row cap.

        Args:
            year (int): The calendar year.

        Returns:
            list | None: The rows, or None if a request failed.
        """
        rows = []
        pieces = [
            (f'01-01-{year}', f'30-06-{year}'),
            (f'01-07-{year}', f'31-12-{year}'),
        ]
        for start, end in pieces:
            url = (
                'https://www.nseindia.com/api/corporates-corporateActions'
                f'?index=equities&from_date={start}&to_date={end}'
            )
            response = self.session.get(url)
            if response is None or response.status_code != 200:
                return None
            try:
                rows.extend(response.json())
            except ValueError:
                return None
        return rows
