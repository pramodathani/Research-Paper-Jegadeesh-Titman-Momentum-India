"""Downloads the IIMA Indian four-factor monthly file."""

from pathlib import Path

import requests


class IimaFactorsDownloader:
    """Saves the survivorship-bias-adjusted monthly factor file.

    Attributes:
        folder: Where the file is saved.
        url: The file's address, which changes with each release.
    """

    URL = (
        'https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/DATA/'
        '2025-12_FourFactors_and_Market_Returns_Monthly_'
        'SurvivorshipBiasAdjusted.csv'
    )

    def __init__(self, folder: Path, url: str | None = None) -> None:
        """Describes the download.

        Args:
            folder (Path): Where to save.
            url (str | None): The address, or None for the 2025-12 release.

        Returns:
            None.
        """
        self.folder = folder
        self.url = url or self.URL

    def run(self) -> Path:
        """Downloads the file.

        Returns:
            Path: The saved file.

        Raises:
            requests.HTTPError: The server refused.
        """
        self.folder.mkdir(parents=True, exist_ok=True)
        response = requests.get(self.url, timeout=60)
        response.raise_for_status()
        target = self.folder / self.url.rsplit('/', 1)[-1]
        target.write_bytes(response.content)
        return target
