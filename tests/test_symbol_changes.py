"""Tests of SymbolChanges."""

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.symbol_changes import (
    SymbolChanges,
)


def make_changes() -> SymbolChanges:
    """Builds TELCO to TATAMOTORS to TMPV and a reused symbol.

    Returns:
        SymbolChanges: The changes.
    """
    return SymbolChanges(
        pd.DataFrame(
            {
                'old_symbol': ['TELCO', 'TATAMOTORS', 'ZOMATO'],
                'new_symbol': ['TATAMOTORS', 'TMPV', 'ETERNAL'],
                'effective_date': ['2003-12-26', '2025-10-24', '2025-04-09'],
            }
        )
    )


class TestSymbolChanges:
    """Tests of SymbolChanges."""

    def test_chain_of_two_renames(self) -> None:
        """TELCO in 2002 becomes TMPV after both renames.

        Returns:
            None.
        """
        rows = pd.DataFrame(
            {
                'symbol': ['TELCO', 'TATAMOTORS', 'TMPV', 'ZOMATO'],
                'date': [
                    '2002-05-01',
                    '2010-01-04',
                    '2025-11-03',
                    '2024-01-02',
                ],
            }
        )
        renamed = make_changes().apply(rows, 'date')
        assert list(renamed['symbol']) == ['TMPV', 'TMPV', 'TMPV', 'ETERNAL']

    def test_rows_after_the_change_keep_their_symbol(self) -> None:
        """A symbol used again after its rename is left alone.

        Returns:
            None.
        """
        rows = pd.DataFrame(
            {
                'symbol': ['ZOMATO'],
                'date': ['2025-06-02'],
            }
        )
        renamed = make_changes().apply(rows, 'date')
        assert list(renamed['symbol']) == ['ZOMATO']
