"""Tests of the buy-and-hold portfolios."""

import numpy as np
import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.buy_and_hold import BuyAndHold


class TestBuyAndHold:
    """Tests of BuyAndHold."""

    def test_two_share_cohort_drifts_between_months(self) -> None:
        """A cohort of one +10% and one -10% share is not rebalanced.

        Returns:
            None.
        """
        months = pd.period_range('2010-01', periods=4, freq='M')
        returns = pd.DataFrame(
            {
                'A': [0.0, 0.10, 0.10, 0.10],
                'B': [0.0, -0.10, -0.10, -0.10],
            },
            index=months,
        )
        members = pd.DataFrame(
            {
                'A': [True, False, False, False],
                'B': [True, False, False, False],
            },
            index=months,
        )
        result = BuyAndHold(returns).portfolio_returns(members, 1)
        assert result.iloc[1] == pytest.approx(0.0)
        three = members.copy()
        three.iloc[:3] = True
        result = BuyAndHold(returns).portfolio_returns(three, 3)
        assert np.isnan(result.iloc[:3]).all()
        first = 1.03 / 1.01 - 1
        second = 1.01 / 1.00 - 1
        third = 0.0
        assert result.iloc[3] == pytest.approx((first + second + third) / 3)

    def test_empty_cohorts_make_no_return(self) -> None:
        """A strategy with no chosen shares has no returns.

        Returns:
            None.
        """
        months = pd.period_range('2010-01', periods=5, freq='M')
        returns = pd.DataFrame(0.01, index=months, columns=['A'])
        members = pd.DataFrame(False, index=months, columns=['A'])
        result = BuyAndHold(returns).portfolio_returns(members, 2)
        assert result.isna().all()
