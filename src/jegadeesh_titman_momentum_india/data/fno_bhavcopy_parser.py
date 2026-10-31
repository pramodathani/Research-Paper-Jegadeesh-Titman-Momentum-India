"""Reads NSE derivatives bhavcopy files into stock futures rows."""

import io
import zipfile
from pathlib import Path

import pandas as pd


class FnoBhavcopyParser:
    """Keeps the nearest-expiry stock future of each share for each day."""

    def parse_file(self, path: Path) -> pd.DataFrame:
        """Reads one zip file from disk.

        Args:
            path (Path): The derivatives bhavcopy zip.

        Returns:
            pd.DataFrame: Columns date, symbol, expiry, close, settle,
                open_interest, one row per share.
        """
        with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as archive:
            names = [n for n in archive.namelist() if n.endswith('.csv')]
            with archive.open(names[0]) as handle:
                raw = pd.read_csv(handle, dtype=str, index_col=False)
        raw.columns = [name.strip() for name in raw.columns]
        return self.parse_table(raw)

    def parse_table(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Standardises a table in either format.

        Args:
            raw (pd.DataFrame): The csv as strings.

        Returns:
            pd.DataFrame: Columns date, symbol, expiry, close, settle,
                open_interest, one row per share.
        """
        table = pd.DataFrame()
        if 'TckrSymb' in raw.columns:
            raw = raw[raw['FinInstrmTp'] == 'STF']
            table['date'] = pd.to_datetime(raw['TradDt'], format='%Y-%m-%d')
            table['symbol'] = raw['TckrSymb'].str.strip()
            table['expiry'] = pd.to_datetime(raw['XpryDt'], format='%Y-%m-%d')
            table['close'] = pd.to_numeric(raw['ClsPric'], errors='coerce')
            table['settle'] = pd.to_numeric(raw['SttlmPric'], errors='coerce')
            table['open_interest'] = pd.to_numeric(
                raw['OpnIntrst'], errors='coerce'
            )
        else:
            raw = raw[raw['INSTRUMENT'] == 'FUTSTK']
            table['date'] = pd.to_datetime(raw['TIMESTAMP'], format='%d-%b-%Y')
            table['symbol'] = raw['SYMBOL'].str.strip()
            table['expiry'] = pd.to_datetime(
                raw['EXPIRY_DT'], format='%d-%b-%Y'
            )
            table['close'] = pd.to_numeric(raw['CLOSE'], errors='coerce')
            table['settle'] = pd.to_numeric(raw['SETTLE_PR'], errors='coerce')
            table['open_interest'] = pd.to_numeric(
                raw['OPEN_INT'], errors='coerce'
            )
        table = table.sort_values(['symbol', 'expiry'])
        return table.drop_duplicates(subset=['symbol'], keep='first')
