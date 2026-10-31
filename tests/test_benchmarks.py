"""Tests of the IIMA factors and index returns."""

import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.iima_factors import IimaFactors
from jegadeesh_titman_momentum_india.momentum.index_returns import (
    IndexReturns,
)


class TestIimaFactors:
    """Tests of IimaFactors."""

    def test_percent_to_decimal_and_market_return(self) -> None:
        """Percent values become decimals and market is mf plus rf.

        Returns:
            None.
        """
        table = pd.DataFrame(
            {
                'month': ['2010-01-01', '2010-02-01'],
                'smb': [1.0, 2.0],
                'hml': [0.0, 0.0],
                'wml': [3.0, 4.0],
                'mf': [2.0, -1.0],
                'rf': [0.5, 0.5],
            }
        )
        factors = IimaFactors(table)
        assert factors.factors['wml'].iloc[0] == pytest.approx(0.03)
        market = factors.market_return()
        assert market.iloc[1] == pytest.approx(-0.005)

    def test_risk_free_carries_last_value(self) -> None:
        """Months after the file ends repeat the last rate.

        Returns:
            None.
        """
        table = pd.DataFrame(
            {
                'month': ['2010-01-01'],
                'smb': [0.0],
                'hml': [0.0],
                'wml': [0.0],
                'mf': [0.0],
                'rf': [0.5],
            }
        )
        months = pd.period_range('2010-01', periods=3, freq='M')
        series = IimaFactors(table).risk_free(months)
        assert series.iloc[2] == pytest.approx(0.005)


class TestIndexReturns:
    """Tests of IndexReturns."""

    def test_chains_names_and_adds_dividend_yield(self) -> None:
        """Two names are joined and a twelfth of the yield is added.

        Returns:
            None.
        """
        rows = pd.DataFrame(
            {
                'date': ['2013-01-31', '2013-02-28', '2013-03-28'],
                'index_name': ['CNX 500', 'CNX 500', 'Nifty 500'],
                'close': [100.0, 110.0, 99.0],
                'div_yield': [1.2, 1.2, 1.2],
            }
        )
        monthly = IndexReturns().monthly(rows, ('CNX 500', 'Nifty 500'))
        assert monthly['price_return'].iloc[0] == pytest.approx(0.10)
        assert monthly['total_return'].iloc[0] == pytest.approx(0.101)
        assert monthly['price_return'].iloc[1] == pytest.approx(-0.10)
