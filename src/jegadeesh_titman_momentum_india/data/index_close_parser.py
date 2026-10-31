"""Reads NSE's daily index close files."""

import io
from pathlib import Path

import pandas as pd


class IndexCloseParser:
    """Turns ind_close_all csv text into date, index name, close and ratios."""

    def parse_file(self, path: Path) -> pd.DataFrame:
        """Reads one file from disk.

        Args:
            path (Path): The ind_close_all csv.

        Returns:
            pd.DataFrame: Columns date, index_name, close, pe, pb, div_yield.
        """
        return self.parse_text(path.read_text(errors='replace'))

    def parse_text(self, text: str) -> pd.DataFrame:
        """Reads the text of one file.

        Args:
            text (str): The csv text.

        Returns:
            pd.DataFrame: Columns date, index_name, close, pe, pb, div_yield.
        """
        raw = pd.read_csv(io.StringIO(text), dtype=str, index_col=False)
        raw.columns = [name.strip() for name in raw.columns]
        table = pd.DataFrame()
        dates = raw['Index Date'].str.strip().str.replace('/', '-')
        table['date'] = pd.to_datetime(dates, format='%d-%m-%Y')
        table['index_name'] = raw['Index Name'].str.strip()
        table['close'] = pd.to_numeric(
            raw['Closing Index Value'], errors='coerce'
        )
        table['pe'] = pd.to_numeric(raw.get('P/E'), errors='coerce')
        table['pb'] = pd.to_numeric(raw.get('P/B'), errors='coerce')
        table['div_yield'] = pd.to_numeric(
            raw.get('Div Yield'), errors='coerce'
        )
        return table.dropna(subset=['close'])
