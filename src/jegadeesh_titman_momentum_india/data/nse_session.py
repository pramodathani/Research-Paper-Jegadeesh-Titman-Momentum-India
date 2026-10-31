"""A polite HTTP session for NSE's public archives."""

import time
from typing import ClassVar

import requests


class NseSession:
    """Fetches files from NSE with browser headers and a pause between calls.

    Attributes:
        pause_seconds: Seconds to wait before every request.
        session: The underlying requests session.
    """

    HEADERS: ClassVar[dict[str, str]] = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/130.0 Safari/537.36'
        ),
        'Accept': '*/*',
        'Referer': 'https://www.nseindia.com/',
    }

    def __init__(self, pause_seconds: float = 0.3) -> None:
        """Creates the session.

        Args:
            pause_seconds (float): Seconds to wait before every request.

        Returns:
            None.
        """
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get(self, url: str, attempts: int = 4) -> requests.Response | None:
        """Fetches one address, retrying on network errors.

        Args:
            url (str): The address.
            attempts (int): How many times to try before giving up.

        Returns:
            requests.Response | None: The response, or None if every attempt
                raised a network error.
        """
        for attempt in range(attempts):
            time.sleep(self.pause_seconds)
            try:
                return self.session.get(url, timeout=60)
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
        return None
