"""Tests of the bhavcopy parser on small made-up files."""

import io
import zipfile

from jegadeesh_titman_momentum_india.data.bhavcopy_parser import (
    BhavcopyParser,
)

OLD_FILE = (
    'SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,'
    'TIMESTAMP,\n'
    'AAA,EQ,10,12,9,11,11,10,1000,11000,2-JAN-1996,\n'
    'BBB,N1,10,12,9,11,11,10,1000,11000,2-JAN-1996,\n'
    'CCC,BE,5,6,4,5.5,5.5,5,200,1100,2-JAN-1996,\n'
)

UDIFF_FILE = (
    'TradDt,FinInstrmTp,TckrSymb,SctySrs,ISIN,OpnPric,HghPric,LwPric,'
    'ClsPric,PrvsClsgPric,TtlTradgVol,TtlTrfVal\n'
    '2026-10-30,STK,AAA,EQ,INE000A01010,100,110,90,105,100,50,5250\n'
    '2026-10-30,STK,SGBX,GB,IN0000000001,1,1,1,1,1,1,1\n'
    '2026-10-30,IDF,FUNDX,EQ,INF000A01010,1,1,1,1,1,1,1\n'
)


class TestBhavcopyParser:
    """Tests of BhavcopyParser."""

    @staticmethod
    def _zip(text: str) -> bytes:
        """Wraps text in a zip file in memory.

        Args:
            text (str): The csv text.

        Returns:
            bytes: The zip bytes.
        """
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('file.csv', text)
        return buffer.getvalue()

    def test_old_format_keeps_equity_series_only(self) -> None:
        """Only EQ, BE and BZ rows survive, with the date parsed.

        Returns:
            None.
        """
        table = BhavcopyParser().parse_bytes(self._zip(OLD_FILE))
        assert list(table['symbol']) == ['AAA', 'CCC']
        assert str(table['date'].iloc[0].date()) == '1996-01-02'
        assert table['previous_close'].iloc[0] == 10

    def test_udiff_keeps_stocks_only(self) -> None:
        """Bonds and fund rows are dropped and the ISIN is kept.

        Returns:
            None.
        """
        table = BhavcopyParser().parse_bytes(self._zip(UDIFF_FILE))
        assert list(table['symbol']) == ['AAA']
        assert table['isin'].iloc[0] == 'INE000A01010'
        assert table['traded_value'].iloc[0] == 5250

    def test_two_digit_year_dates(self) -> None:
        """A date printed as 13-Jul-20 is read as 13 July 2020.

        Returns:
            None.
        """
        text = OLD_FILE.replace('2-JAN-1996', '13-Jul-20')
        table = BhavcopyParser().parse_bytes(self._zip(text))
        assert str(table['date'].iloc[0].date()) == '2020-07-13'
