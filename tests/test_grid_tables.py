"""Tests of GridTables on a tiny made-up grid."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.grid_tables import GridTables


def make_grid() -> pd.DataFrame:
    """Builds 24 months of one strategy's returns.

    Returns:
        pd.DataFrame: Grid rows for U1, no skip, J=6, K=6, long-short.
    """
    months = pd.date_range('2010-01-01', periods=24, freq='MS')
    gross = np.where(months.month == 1, -0.05, 0.02)
    return pd.DataFrame(
        {
            'month': months,
            'universe': 'U1',
            'skip': False,
            'formation_months': 6,
            'holding_months': 6,
            'leg': 'long_short',
            'gross': gross,
            'net': gross - 0.005,
            'turnover': 0.3,
            'holding_count': 100,
        }
    )


class TestGridTables:
    """Tests of GridTables."""

    @staticmethod
    def _tables() -> GridTables:
        """Builds the tables object with a flat market.

        Returns:
            GridTables: The object.
        """
        months = pd.period_range('2010-01', periods=24, freq='M')
        rng = np.random.default_rng(3)
        market = pd.Series(rng.normal(0.01, 0.02, 24), index=months)
        return GridTables(make_grid(), market, pd.Series(0.005, index=months))

    def test_table_one_means_and_costs(self) -> None:
        """Gross and net means differ by the cost and the count is right.

        Returns:
            None.
        """
        table = self._tables().table_one('2010-01', '2011-12')
        row = table.iloc[0]
        assert row['months'] == 24
        expected_mean = (2 * -0.05 + 22 * 0.02) / 24
        assert row['gross_mean'] == pytest.approx(expected_mean)
        assert row['net_mean'] == pytest.approx(expected_mean - 0.005)
        assert row['turnover_monthly'] == pytest.approx(0.3)

    def test_calendar_table_finds_january_loss(self) -> None:
        """January is negative and the other months positive.

        Returns:
            None.
        """
        keys = ('U1', False, 6, 6, 'long_short')
        table = self._tables().calendar_table(keys, '2010-01', '2011-12')
        assert table.loc[1, 'mean'] == pytest.approx(-0.05)
        assert table.loc[2, 'mean'] == pytest.approx(0.02)

    def test_subperiods_split_january(self) -> None:
        """Each subperiod reports January and February to December apart.

        Returns:
            None.
        """
        keys = ('U1', False, 6, 6, 'long_short')
        table = self._tables().subperiods(
            keys, [('2010-01', '2010-12'), ('2011-01', '2011-12')]
        )
        january = table[table['months'] == 'January']
        assert list(january['count']) == [1, 1]
        rest = table[table['months'] == 'February to December']
        assert rest['mean'].iloc[0] == pytest.approx(0.02)
