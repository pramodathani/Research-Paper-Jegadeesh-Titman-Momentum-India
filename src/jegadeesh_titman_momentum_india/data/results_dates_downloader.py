"""Downloads NSE's quarterly financial results filings, one quarter at a time."""

import json
from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.data.nse_session import NseSession


class ResultsDatesDownloader:
    """Saves the financial results API's answer for each calendar quarter.

    Attributes:
        folder: Where the JSON files are saved.
        first_quarter: The first quarter, such as 2007Q1.
        last_quarter: The last quarter.
        session: The NSE session.
    """

    WARM_UP_URL = (
        'https://www.nseindia.com/companies-listing/'
        'corporate-filings-financial-results'
    )

    def __init__(
        self,
        folder: Path,
        first_quarter: str,
        last_quarter: str,
        session: NseSession | None = None,
    ) -> None:
        """Describes the download.

        Args:
            folder (Path): Where to save.
            first_quarter (str): First quarter, such as 2007Q1.
            last_quarter (str): Last quarter.
            session (NseSession | None): A session, or None to make one.

        Returns:
            None.
        """
        self.folder = folder
        self.first_quarter = pd.Period(first_quarter, freq='Q')
        self.last_quarter = pd.Period(last_quarter, freq='Q')
        self.session = session or NseSession(pause_seconds=1.0)

    def run(self) -> dict[str, int]:
        """Fetches every quarter whose file is missing.

        Returns:
            dict[str, int]: Rows saved for each quarter fetched.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session.get(self.WARM_UP_URL)
        saved = {}
        quarter = self.first_quarter
        while quarter <= self.last_quarter:
            target = self.folder / f'results_{quarter}.json'
            if not target.exists():
                rows = self._fetch(quarter)
                if rows is not None:
                    target.write_text(json.dumps(rows))
                    saved[str(quarter)] = len(rows)
            quarter += 1
        return saved

    def _fetch(self, quarter: pd.Period) -> list | None:
        """Fetches one quarter's filings.

        Args:
            quarter (pd.Period): The calendar quarter.

        Returns:
            list | None: The rows, or None if the request failed.
        """
        start = quarter.start_time.strftime('%d-%m-%Y')
        end = quarter.end_time.strftime('%d-%m-%Y')
        url = (
            'https://www.nseindia.com/api/corporates-financial-results'
            f'?index=equities&from_date={start}&to_date={end}'
            '&period=Quarterly'
        )
        response = self.session.get(url)
        if response is None or response.status_code != 200:
            return None
        try:
            return response.json()
        except ValueError:
            return None
