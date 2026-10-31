"""Command-line program that loads downloaded data into TimescaleDB."""

import argparse
from pathlib import Path

import pandas as pd

from jegadeesh_titman_momentum_india.data.bhavcopy_parser import (
    BhavcopyParser,
)
from jegadeesh_titman_momentum_india.data.corporate_actions_parser import (
    CorporateActionsParser,
)
from jegadeesh_titman_momentum_india.data.fno_bhavcopy_parser import (
    FnoBhavcopyParser,
)
from jegadeesh_titman_momentum_india.data.index_close_parser import (
    IndexCloseParser,
)
from jegadeesh_titman_momentum_india.data.timescale_store import (
    TimescaleStore,
)


class LoadDatabaseApplication:
    """Loads one downloaded source into the study's TimescaleDB schema."""

    SOURCES = (
        'bhavcopy',
        'fno',
        'index',
        'corporate_actions',
        'iima',
        'ubi',
    )

    CHUNK_FILES = 100

    def run(self) -> None:
        """Parses the arguments and loads the chosen source.

        Returns:
            None.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('source', choices=self.SOURCES)
        parser.add_argument('--data-folder', default='data')
        arguments = parser.parse_args()
        root = Path(arguments.data_folder)
        store = TimescaleStore()
        store.create_tables()
        loaders = {
            'bhavcopy': self._load_bhavcopy,
            'fno': self._load_fno,
            'index': self._load_index,
            'corporate_actions': self._load_corporate_actions,
            'iima': self._load_iima,
            'ubi': self._load_ubi,
        }
        rows = loaders[arguments.source](store, root)
        print(f'{arguments.source}: {rows} rows sent')

    def _load_bhavcopy(self, store: TimescaleStore, root: Path) -> int:
        """Loads every bhavcopy file in chunks.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        parser = BhavcopyParser()
        files = sorted((root / 'nse' / 'bhavcopy').glob('*.zip'))
        total = 0
        for start in range(0, len(files), self.CHUNK_FILES):
            frames = [
                parser.parse_file(path)
                for path in files[start : start + self.CHUNK_FILES]
            ]
            total += store.upsert(
                'daily_prices_raw',
                pd.concat(frames),
                ['symbol', 'series', 'date'],
            )
        return total

    def _load_fno(self, store: TimescaleStore, root: Path) -> int:
        """Loads every derivatives bhavcopy in chunks.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        parser = FnoBhavcopyParser()
        files = sorted((root / 'nse' / 'fno').glob('*.zip'))
        total = 0
        for start in range(0, len(files), self.CHUNK_FILES):
            frames = [
                parser.parse_file(path)
                for path in files[start : start + self.CHUNK_FILES]
            ]
            total += store.upsert(
                'fno_stock_futures_daily',
                pd.concat(frames),
                ['symbol', 'expiry', 'date'],
            )
        return total

    def _load_index(self, store: TimescaleStore, root: Path) -> int:
        """Loads every index close file.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        parser = IndexCloseParser()
        files = sorted((root / 'nse' / 'index').glob('ind_close_all_*.csv'))
        total = 0
        for start in range(0, len(files), self.CHUNK_FILES):
            frames = [
                parser.parse_file(path)
                for path in files[start : start + self.CHUNK_FILES]
            ]
            total += store.upsert(
                'index_daily',
                pd.concat(frames),
                ['index_name', 'date'],
            )
        return total

    def _load_corporate_actions(self, store: TimescaleStore, root: Path) -> int:
        """Loads the corporate actions.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        table = CorporateActionsParser().parse_folder(
            root / 'nse' / 'corporate_actions'
        )
        return store.upsert(
            'corporate_actions',
            table,
            ['symbol', 'series', 'subject', 'ex_date'],
        )

    def _load_iima(self, store: TimescaleStore, root: Path) -> int:
        """Loads the IIMA monthly factors.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        path = next((root / 'nse' / 'iima').glob('*.csv'))
        raw = pd.read_csv(path, na_values=['NA'])
        table = pd.DataFrame()
        table['month'] = pd.to_datetime(raw['Date'] + '-01')
        for name in ('SMB', 'HML', 'WML', 'MF', 'RF'):
            table[name.lower()] = raw[name]
        return store.upsert('iima_factors_monthly', table, ['month'])

    def _load_ubi(self, store: TimescaleStore, root: Path) -> int:
        """Loads UBI's daily candles.

        Args:
            store (TimescaleStore): The store.
            root (Path): The data folder.

        Returns:
            int: Rows sent.
        """
        path = root / 'ubi' / 'prices_nse_equities_day_adjusted.parquet'
        raw = pd.read_parquet(path)
        table = raw[
            [
                'date',
                'symbol',
                'instrument_id',
                'open',
                'high',
                'low',
                'close',
                'volume',
                'price_factor',
            ]
        ]
        total = 0
        symbols = table['symbol'].unique()
        for start in range(0, len(symbols), 200):
            chunk = table[table['symbol'].isin(symbols[start : start + 200])]
            total += store.upsert('ubi_daily_prices', chunk, ['symbol', 'date'])
        return total


if __name__ == '__main__':
    LoadDatabaseApplication().run()
