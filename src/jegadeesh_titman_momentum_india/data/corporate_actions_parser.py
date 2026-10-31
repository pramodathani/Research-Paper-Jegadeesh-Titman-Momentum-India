"""Reads the corporate actions JSON files saved from NSE's API."""

import json
from pathlib import Path

import pandas as pd


class CorporateActionsParser:
    """Turns the yearly JSON files into one table of share actions."""

    SERIES_KEPT = (
        'EQ',
        'BE',
        'BZ',
    )

    def parse_folder(self, folder: Path) -> pd.DataFrame:
        """Reads every yearly file in a folder.

        Args:
            folder (Path): The folder with corporate_actions_YYYY.json files.

        Returns:
            pd.DataFrame: Columns ex_date, symbol, series, isin, subject,
                face_value.
        """
        rows = []
        for path in sorted(folder.glob('corporate_actions_*.json')):
            rows.extend(json.loads(path.read_text()))
        return self.parse_rows(rows)

    def parse_rows(self, rows: list[dict]) -> pd.DataFrame:
        """Standardises rows from the API.

        Args:
            rows (list[dict]): The API's rows.

        Returns:
            pd.DataFrame: Columns ex_date, symbol, series, isin, subject,
                face_value, for share series with a valid ex-date.
        """
        raw = pd.DataFrame(rows)
        if raw.empty:
            return pd.DataFrame(
                columns=[
                    'ex_date',
                    'symbol',
                    'series',
                    'isin',
                    'subject',
                    'face_value',
                ]
            )
        table = pd.DataFrame()
        table['ex_date'] = pd.to_datetime(
            raw['exDate'], format='%d-%b-%Y', errors='coerce'
        )
        table['symbol'] = raw['symbol'].str.strip()
        table['series'] = raw['series'].str.strip()
        table['isin'] = raw['isin']
        table['subject'] = raw['subject'].str.strip()
        table['face_value'] = raw['faceVal']
        table = table.dropna(subset=['ex_date', 'subject'])
        return table[table['series'].isin(self.SERIES_KEPT)]
