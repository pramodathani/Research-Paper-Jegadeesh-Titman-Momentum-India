"""Reads NSE bhavcopy zip files in both formats into one table."""

import io
import zipfile
from pathlib import Path
from typing import ClassVar

import pandas as pd


class BhavcopyParser:
    """Turns an old-format or UDiFF bhavcopy into the study's columns.

    The output has the columns date, symbol, series, isin, open, high, low,
    close, previous_close, volume and traded_value, with prices as NSE
    printed them, unadjusted.
    """

    SERIES_KEPT = (
        'EQ',
        'BE',
        'BZ',
    )

    COLUMNS = (
        'date',
        'symbol',
        'series',
        'isin',
        'open',
        'high',
        'low',
        'close',
        'previous_close',
        'volume',
        'traded_value',
    )

    OLD_RENAMES: ClassVar[dict[str, str]] = {
        'SYMBOL': 'symbol',
        'SERIES': 'series',
        'OPEN': 'open',
        'HIGH': 'high',
        'LOW': 'low',
        'CLOSE': 'close',
        'PREVCLOSE': 'previous_close',
        'TOTTRDQTY': 'volume',
        'TOTTRDVAL': 'traded_value',
        'TIMESTAMP': 'date',
        'ISIN': 'isin',
    }

    UDIFF_RENAMES: ClassVar[dict[str, str]] = {
        'TradDt': 'date',
        'TckrSymb': 'symbol',
        'SctySrs': 'series',
        'ISIN': 'isin',
        'OpnPric': 'open',
        'HghPric': 'high',
        'LwPric': 'low',
        'ClsPric': 'close',
        'PrvsClsgPric': 'previous_close',
        'TtlTradgVol': 'volume',
        'TtlTrfVal': 'traded_value',
    }

    def parse_file(self, path: Path) -> pd.DataFrame:
        """Reads one zip file from disk.

        Args:
            path (Path): The bhavcopy zip.

        Returns:
            pd.DataFrame: The day's rows for the kept series.

        Raises:
            ValueError: The zip holds no csv file.
        """
        return self.parse_bytes(path.read_bytes())

    def parse_bytes(self, content: bytes) -> pd.DataFrame:
        """Reads the bytes of one zip file.

        Args:
            content (bytes): The zip file's bytes.

        Returns:
            pd.DataFrame: The day's rows for the kept series.

        Raises:
            ValueError: The zip holds no csv file.
        """
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = [n for n in archive.namelist() if n.endswith('.csv')]
            if not names:
                raise ValueError('the zip holds no csv file')
            with archive.open(names[0]) as handle:
                raw = pd.read_csv(handle, dtype=str, index_col=False)
        raw.columns = [name.strip() for name in raw.columns]
        return self.parse_table(raw)

    def parse_table(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Standardises a table read from either format.

        Args:
            raw (pd.DataFrame): The csv as strings.

        Returns:
            pd.DataFrame: The standardised rows for the kept series.
        """
        if 'TckrSymb' in raw.columns:
            raw = raw[raw['FinInstrmTp'] == 'STK']
            table = raw.rename(columns=self.UDIFF_RENAMES)
            table['date'] = pd.to_datetime(table['date'], format='%Y-%m-%d')
        else:
            table = raw.rename(columns=self.OLD_RENAMES)
            table['date'] = self._parse_old_dates(table['date'])
        if 'isin' not in table.columns:
            table['isin'] = None
        table['symbol'] = table['symbol'].str.strip()
        table['series'] = table['series'].str.strip()
        table = table[table['series'].isin(self.SERIES_KEPT)]
        for column in (
            'open',
            'high',
            'low',
            'close',
            'previous_close',
            'volume',
            'traded_value',
        ):
            table[column] = pd.to_numeric(table[column], errors='coerce')
        return table[list(self.COLUMNS)].reset_index(drop=True)

    def _parse_old_dates(self, dates: pd.Series) -> pd.Series:
        """Parses old-format dates, which NSE prints with 2 or 4 year digits.

        Args:
            dates (pd.Series): Strings such as 05-JUL-2024 or 13-Jul-20.

        Returns:
            pd.Series: The dates.
        """
        four_digit = pd.to_datetime(dates, format='%d-%b-%Y', errors='coerce')
        two_digit = pd.to_datetime(dates, format='%d-%b-%y', errors='coerce')
        return four_digit.fillna(two_digit)
