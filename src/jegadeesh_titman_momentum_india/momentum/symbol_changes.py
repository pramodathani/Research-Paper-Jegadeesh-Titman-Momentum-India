"""Joins a share's history across NSE symbol changes."""

import pandas as pd


class SymbolChanges:
    """Renames old symbols to the symbol the share trades under last.

    Each change says that from its effective date the share's old symbol is
    replaced by a new one. Rows of the old symbol before that date are
    renamed, following later changes of the new symbol too, so a share
    renamed twice ends up under its final symbol. A symbol reused later by
    another company keeps its rows after the change date.

    Attributes:
        changes: Columns old_symbol, new_symbol and effective_date.
    """

    def __init__(self, changes: pd.DataFrame) -> None:
        """Keeps the changes, sorted by date.

        Args:
            changes (pd.DataFrame): Columns old_symbol, new_symbol and
                effective_date.

        Returns:
            None.
        """
        table = changes.dropna(subset=['old_symbol', 'new_symbol']).copy()
        table['old_symbol'] = table['old_symbol'].str.strip()
        table['new_symbol'] = table['new_symbol'].str.strip()
        table['effective_date'] = pd.to_datetime(table['effective_date'])
        table = table[table['old_symbol'] != table['new_symbol']]
        self.changes = table.sort_values('effective_date').reset_index(
            drop=True
        )

    @classmethod
    def from_nse_file(cls, path: str) -> SymbolChanges:
        """Reads NSE's symbolchange.csv.

        Args:
            path (str): The file.

        Returns:
            SymbolChanges: The changes.
        """
        raw = pd.read_csv(path, dtype=str, encoding='latin-1')
        raw.columns = [name.strip() for name in raw.columns]
        table = pd.DataFrame(
            {
                'old_symbol': raw['OLD SYMBOL'],
                'new_symbol': raw['NEW SYMBOL'],
                'effective_date': pd.to_datetime(
                    raw['EFFECTIVE DATE'].str.strip(),
                    format='%d-%b-%Y',
                    errors='coerce',
                ),
            }
        )
        return cls(table.dropna(subset=['effective_date']))

    def final_symbol(self, symbol: str, after: pd.Timestamp) -> str:
        """Follows renames of a symbol that take effect after a date.

        Args:
            symbol (str): The symbol on that date.
            after (pd.Timestamp): The date.

        Returns:
            str: The symbol the share ends up with.
        """
        current = symbol
        moment = after
        for _ in range(20):
            later = self.changes[
                (self.changes['old_symbol'] == current)
                & (self.changes['effective_date'] > moment)
            ]
            if later.empty:
                return current
            first = later.iloc[0]
            current = first['new_symbol']
            moment = first['effective_date']
        return current

    def apply(self, table: pd.DataFrame, date_column: str) -> pd.DataFrame:
        """Renames the symbol column of a table.

        Args:
            table (pd.DataFrame): Rows with a symbol and a date column.
            date_column (str): The date column's name.

        Returns:
            pd.DataFrame: A copy with old symbols replaced.
        """
        result = table.copy()
        affected = set(self.changes['old_symbol'])
        candidates = result[result['symbol'].isin(affected)]
        symbols = candidates['symbol']
        dates = pd.to_datetime(candidates[date_column])
        renamed = symbols.copy()
        for symbol in affected:
            rows = symbols == symbol
            if not rows.any():
                continue
            own = self.changes[self.changes['old_symbol'] == symbol]
            previous = pd.Timestamp.min
            for change in own.itertuples(index=False):
                segment = (
                    rows & (dates >= previous) & (dates < change.effective_date)
                )
                if segment.any():
                    target = self.final_symbol(
                        change.new_symbol, change.effective_date
                    )
                    renamed[segment] = target
                previous = change.effective_date
        result.loc[candidates.index, 'symbol'] = renamed
        return result
