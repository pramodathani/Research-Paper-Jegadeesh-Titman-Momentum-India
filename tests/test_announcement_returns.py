"""Tests of AnnouncementReturns."""

import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.announcement_returns import (
    AnnouncementReturns,
)


def make_daily() -> pd.DataFrame:
    """Builds five trading days of returns for one share.

    Returns:
        pd.DataFrame: Wide daily returns.
    """
    dates = pd.bdate_range('2015-03-09', periods=5)
    return pd.DataFrame({'AAA': [0.01, 0.02, 0.03, 0.04, 0.05]}, index=dates)


class TestAnnouncementReturns:
    """Tests of AnnouncementReturns."""

    def test_filing_before_close_uses_same_day(self) -> None:
        """A filing at 14:00 on day 3 makes day 3 day zero.

        Returns:
            None.
        """
        filings = pd.DataFrame(
            {
                'symbol': ['AAA'],
                'broadcast': [pd.Timestamp('2015-03-11 14:00')],
            }
        )
        table = AnnouncementReturns().returns(filings, make_daily())
        assert table['day_zero'].iloc[0] == pd.Timestamp('2015-03-11')
        assert table['ret3'].iloc[0] == pytest.approx(1.01 * 1.02 * 1.03 - 1)

    def test_filing_after_close_moves_to_next_day(self) -> None:
        """A filing at 17:21 counts for the next trading day.

        Returns:
            None.
        """
        filings = pd.DataFrame(
            {
                'symbol': ['AAA'],
                'broadcast': [pd.Timestamp('2015-03-11 17:21')],
            }
        )
        table = AnnouncementReturns().returns(filings, make_daily())
        assert table['day_zero'].iloc[0] == pd.Timestamp('2015-03-12')
        assert table['ret3'].iloc[0] == pytest.approx(1.02 * 1.03 * 1.04 - 1)

    def test_weekend_filing_uses_next_trading_day(self) -> None:
        """A Saturday filing counts for Monday.

        Returns:
            None.
        """
        dates = pd.bdate_range('2015-03-04', periods=6)
        daily = pd.DataFrame(
            {'AAA': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06]}, index=dates
        )
        filings = pd.DataFrame(
            {
                'symbol': ['AAA'],
                'broadcast': [pd.Timestamp('2015-03-07 11:00')],
            }
        )
        table = AnnouncementReturns().returns(filings, daily)
        assert table['day_zero'].iloc[0] == pd.Timestamp('2015-03-09')
        assert table['ret3'].iloc[0] == pytest.approx(1.02 * 1.03 * 1.04 - 1)

    def test_too_early_filing_is_dropped(self) -> None:
        """A filing without two earlier trading days is left out.

        Returns:
            None.
        """
        filings = pd.DataFrame(
            {
                'symbol': ['AAA'],
                'broadcast': [pd.Timestamp('2015-03-09 10:00')],
            }
        )
        table = AnnouncementReturns().returns(filings, make_daily())
        assert table.empty
