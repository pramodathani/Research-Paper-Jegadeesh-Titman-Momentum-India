"""Overlapping buy-and-hold portfolios, the paper's unreported variant."""

import numpy as np
import pandas as pd


class BuyAndHold:
    """Holds each month's cohort without rebalancing for K months.

    The paper says (p. 68) that portfolios held without monthly rebalancing
    earned very similar, slightly higher, returns. Each cohort buys equal
    amounts and lets them drift; the strategy holds K cohorts of equal value
    at the start of each month.

    Attributes:
        monthly_returns: Monthly returns, months by shares.
    """

    def __init__(self, monthly_returns: pd.DataFrame) -> None:
        """Keeps the returns.

        Args:
            monthly_returns (pd.DataFrame): Monthly returns; a missing return
                counts as zero, so the money stays in the share.

        Returns:
            None.
        """
        self.monthly_returns = monthly_returns
        self.values = monthly_returns.fillna(0.0).to_numpy(dtype=float)

    def portfolio_returns(
        self,
        members: pd.DataFrame,
        holding_months: int,
    ) -> pd.Series:
        """Gives the return of the K overlapping buy-and-hold cohorts.

        Args:
            members (pd.DataFrame): Bools, months by shares, True for the
                shares chosen at the end of each month.
            holding_months (int): K.

        Returns:
            pd.Series: Monthly returns, NaN until K cohorts exist.
        """
        selection = members.to_numpy(dtype=bool)
        count = len(selection)
        cohort_returns = np.full((count, count), np.nan)
        for formation in range(count):
            chosen = selection[formation]
            if not chosen.any():
                continue
            previous_value = 1.0
            growth = np.ones(chosen.sum())
            last = min(formation + holding_months, count - 1)
            for month in range(formation + 1, last + 1):
                growth = growth * (1.0 + self.values[month, chosen])
                value = float(growth.mean())
                cohort_returns[formation, month] = value / previous_value - 1.0
                previous_value = value
        result = np.full(count, np.nan)
        for month in range(holding_months, count):
            rows = cohort_returns[month - holding_months : month, month]
            if not np.isnan(rows).any():
                result[month] = rows.mean()
        return pd.Series(result, index=members.index)
