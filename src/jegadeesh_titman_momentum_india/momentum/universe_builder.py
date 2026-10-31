"""Decides which shares are eligible at each formation date."""

import numpy as np
import pandas as pd

from jegadeesh_titman_momentum_india.momentum.price_matrices import (
    PriceMatrices,
)


class UniverseBuilder:
    """Builds the all-shares universe U1 and the top-500 universe U2.

    U1 holds every share with a close in the last recent_days trading days.
    U2 keeps the top_count of those by median daily traded value over the
    last liquidity_days trading days, counting days without trading as zero,
    among shares whose last close is at least minimum_price.

    Attributes:
        matrices: The wide price tables.
        top_count: How many shares U2 holds.
        minimum_price: The lowest last close allowed in U2.
        liquidity_days: Trading days in the traded value window.
        recent_days: Trading days in which a share must have traded for U1.
    """

    def __init__(
        self,
        matrices: PriceMatrices,
        top_count: int = 500,
        minimum_price: float = 10.0,
        liquidity_days: int = 126,
        recent_days: int = 5,
    ) -> None:
        """Sets the rules.

        Args:
            matrices (PriceMatrices): The wide price tables.
            top_count (int): Size of U2.
            minimum_price (float): Lowest last close in U2.
            liquidity_days (int): Days in the traded value window.
            recent_days (int): Days in which a share must have a close.

        Returns:
            None.
        """
        self.matrices = matrices
        self.top_count = top_count
        self.minimum_price = minimum_price
        self.liquidity_days = liquidity_days
        self.recent_days = recent_days

    def build(
        self,
        formation_dates: pd.DatetimeIndex,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Builds both universes at each formation date.

        Args:
            formation_dates (pd.DatetimeIndex): Trading days.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: U1 and U2 as bool tables, one
                row per formation date and one column per share.
        """
        calendar = self.matrices.close.index
        columns = self.matrices.close.columns
        u1_rows = np.zeros((len(formation_dates), len(columns)), dtype=bool)
        u2_rows = np.zeros_like(u1_rows)
        for row, date in enumerate(formation_dates):
            position = calendar.get_loc(date)
            first = max(position - self.recent_days + 1, 0)
            recent = self.matrices.close.iloc[first : position + 1]
            traded = recent.notna().any(axis=0).to_numpy()
            last_close = recent.ffill().iloc[-1].to_numpy(dtype=float)
            u1_rows[row] = traded
            window_start = max(position - self.liquidity_days + 1, 0)
            window = self.matrices.traded_value.iloc[
                window_start : position + 1
            ]
            median_value = (
                window.fillna(0.0).median(axis=0).to_numpy(dtype=float)
            )
            allowed = traded & (last_close >= self.minimum_price)
            score = np.where(allowed, median_value, -1.0)
            top = np.argsort(-score)[: self.top_count]
            top = top[score[top] >= 0.0]
            u2_rows[row, top] = True
        u1 = pd.DataFrame(u1_rows, index=formation_dates, columns=columns)
        u2 = pd.DataFrame(u2_rows, index=formation_dates, columns=columns)
        return u1, u2
