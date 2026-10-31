"""Tests of the wide price tables and monthly returns."""

import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.monthly_returns import (
    MonthlyReturns,
)
from jegadeesh_titman_momentum_india.momentum.price_matrices import (
    PriceMatrices,
)


def make_daily() -> pd.DataFrame:
    """Builds six trading days over two months for two shares.

    Returns:
        pd.DataFrame: Long table with date, symbol, close, traded_value, ret.
    """
    rows = []
    dates = pd.to_datetime(
        [
            '2010-01-28',
            '2010-01-29',
            '2010-02-01',
            '2010-02-02',
            '2010-02-26',
            '2010-02-26',
        ]
    )
    dates = dates[:5]
    for date, ret in zip(dates, [0.0, 0.10, 0.10, -0.10, 0.05]):
        rows.append((date, 'AAA', 100.0, 5000.0, ret))
    for date, ret in zip(dates[:3], [0.0, 0.02, 0.02]):
        rows.append((date, 'BBB', 50.0, 100.0, ret))
    return pd.DataFrame(
        rows,
        columns=['date', 'symbol', 'close', 'traded_value', 'ret'],
    )


class TestPriceMatrices:
    """Tests of PriceMatrices and MonthlyReturns."""

    def test_month_end_dates(self) -> None:
        """The last trading day of each month is found.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily())
        dates = matrices.month_end_dates()
        assert [str(d.date()) for d in dates] == ['2010-01-29', '2010-02-26']

    def test_index_level_and_window_return(self) -> None:
        """A window return is the ratio of index levels.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily())
        start = pd.DatetimeIndex(['2010-01-29'])
        end = pd.DatetimeIndex(['2010-02-26'])
        window = matrices.window_returns(start, end)
        expected = 1.10 * 0.90 * 1.05 - 1.0
        assert window['AAA'].iloc[0] == pytest.approx(expected)

    def test_share_without_data_at_end_is_nan_after_stale_limit(self) -> None:
        """A share whose rows stop is carried 10 days then drops out.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily(), stale_days=1)
        start = pd.DatetimeIndex(['2010-01-29'])
        end = pd.DatetimeIndex(['2010-02-26'])
        window = matrices.window_returns(start, end)
        assert pd.isna(window['BBB'].iloc[0])

    def test_shifted_dates(self) -> None:
        """Going back two trading days lands on the right date.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily())
        shifted = matrices.shifted_dates(pd.DatetimeIndex(['2010-02-02']), 2)
        assert str(shifted[0].date()) == '2010-01-29'

    def test_monthly_returns_compound_daily_ones(self) -> None:
        """February compounds its three daily returns.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily())
        monthly = MonthlyReturns().build(matrices.returns)
        february = monthly.loc[pd.Period('2010-02'), 'AAA']
        assert february == pytest.approx(1.10 * 0.90 * 1.05 - 1.0)
        january = monthly.loc[pd.Period('2010-01'), 'BBB']
        assert january == pytest.approx(1.02 - 1.0)

    def test_month_without_rows_is_nan(self) -> None:
        """A share with no row in a month has no monthly return.

        Returns:
            None.
        """
        matrices = PriceMatrices(make_daily())
        monthly = MonthlyReturns().build(matrices.returns)
        assert pd.notna(monthly.loc[pd.Period('2010-02'), 'BBB'])
        frame = matrices.returns.copy()
        frame.loc[frame.index.month == 2, 'BBB'] = float('nan')
        monthly = MonthlyReturns().build(frame)
        assert pd.isna(monthly.loc[pd.Period('2010-02'), 'BBB'])
