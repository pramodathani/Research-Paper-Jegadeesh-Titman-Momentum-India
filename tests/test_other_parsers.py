"""Tests of the index, derivatives and corporate action parsers."""

import pandas as pd

from jegadeesh_titman_momentum_india.data.corporate_actions_parser import (
    CorporateActionsParser,
)
from jegadeesh_titman_momentum_india.data.fno_bhavcopy_parser import (
    FnoBhavcopyParser,
)
from jegadeesh_titman_momentum_india.data.index_close_parser import (
    IndexCloseParser,
)


class TestIndexCloseParser:
    """Tests of IndexCloseParser."""

    def test_dash_values_become_missing(self) -> None:
        """A dash in a ratio column becomes NaN and the close is kept.

        Returns:
            None.
        """
        text = (
            'Index Name,Index Date,Closing Index Value,P/E,P/B,Div Yield\n'
            'Nifty 500,01-10-2024,24271.3,27.9,4.22,1.04\n'
            'Nifty X,01-10-2024,100,-,-,-\n'
        )
        table = IndexCloseParser().parse_text(text)
        assert len(table) == 2
        assert table['div_yield'].iloc[0] == 1.04
        assert pd.isna(table['pe'].iloc[1])


class TestFnoBhavcopyParser:
    """Tests of FnoBhavcopyParser."""

    def test_nearest_expiry_stock_future_only(self) -> None:
        """Index futures are dropped and the nearer expiry is kept.

        Returns:
            None.
        """
        raw = pd.DataFrame(
            {
                'INSTRUMENT': ['FUTIDX', 'FUTSTK', 'FUTSTK', 'OPTSTK'],
                'SYMBOL': ['NIFTY', 'ACC', 'ACC', 'ACC'],
                'EXPIRY_DT': [
                    '27-Jan-2005',
                    '24-Feb-2005',
                    '27-Jan-2005',
                    '27-Jan-2005',
                ],
                'CLOSE': ['1', '2', '3', '4'],
                'SETTLE_PR': ['1', '2', '3', '4'],
                'OPEN_INT': ['1', '2', '3', '4'],
                'TIMESTAMP': ['3-JAN-2005'] * 4,
            }
        )
        table = FnoBhavcopyParser().parse_table(raw)
        assert list(table['symbol']) == ['ACC']
        assert table['close'].iloc[0] == 3


class TestCorporateActionsParser:
    """Tests of CorporateActionsParser."""

    def test_keeps_share_series_with_dates(self) -> None:
        """Bond rows and rows without an ex-date are dropped.

        Returns:
            None.
        """
        rows = [
            {
                'exDate': '02-Jan-2024',
                'symbol': 'ALLCARGO',
                'series': 'EQ',
                'isin': 'INE418H01029',
                'subject': 'Bonus 3:1',
                'faceVal': '2',
            },
            {
                'exDate': '01-Jan-2024',
                'symbol': '83GS2040',
                'series': 'GS',
                'isin': 'IN0020100031',
                'subject': 'Interest Payment',
                'faceVal': '100',
            },
            {
                'exDate': '-',
                'symbol': 'XYZ',
                'series': 'EQ',
                'isin': 'INE000000000',
                'subject': 'Agm',
                'faceVal': '10',
            },
        ]
        table = CorporateActionsParser().parse_rows(rows)
        assert list(table['symbol']) == ['ALLCARGO']
