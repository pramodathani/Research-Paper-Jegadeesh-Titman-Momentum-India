"""Scholes-Williams betas from daily returns with gaps."""

import numpy as np
import pandas as pd


class ScholesWilliamsBeta:
    """Estimates betas that allow for thin trading, as the paper does.

    The beta is the sum of the slopes on the market's return a day earlier,
    the same day and a day later, divided by one plus twice the market's
    first-order autocorrelation.

    Attributes:
        minimum_days: The fewest days of data a share needs.
    """

    def __init__(self, minimum_days: int = 100) -> None:
        """Sets the data requirement.

        Args:
            minimum_days (int): Fewest paired days a share needs.

        Returns:
            None.
        """
        self.minimum_days = minimum_days

    def betas(
        self,
        stock_returns: pd.DataFrame,
        market_returns: pd.Series,
    ) -> pd.Series:
        """Estimates each share's beta over a window.

        Args:
            stock_returns (pd.DataFrame): Daily returns, one row per day, one
                column per share, NaN where a share has none.
            market_returns (pd.Series): The market's daily returns with the
                same days.

        Returns:
            pd.Series: Betas by share, NaN with too little data.
        """
        values = stock_returns.to_numpy(dtype=float)
        market = market_returns.to_numpy(dtype=float)
        slopes = [
            self._slope(values, np.roll(market, shift), shift)
            for shift in (1, 0, -1)
        ]
        valid_pairs = ~np.isnan(market[1:]) & ~np.isnan(market[:-1])
        first = market[1:][valid_pairs]
        second = market[:-1][valid_pairs]
        if len(first) < 3 or first.std() == 0 or second.std() == 0:
            return pd.Series(np.nan, index=stock_returns.columns)
        autocorrelation = float(np.corrcoef(first, second)[0, 1])
        beta = (slopes[0] + slopes[1] + slopes[2]) / (
            1.0 + 2.0 * autocorrelation
        )
        return pd.Series(beta, index=stock_returns.columns)

    def _slope(
        self,
        values: np.ndarray,
        shifted_market: np.ndarray,
        shift: int,
    ) -> np.ndarray:
        """Regresses each share on a shifted market series.

        Args:
            values (np.ndarray): Daily returns, days by shares.
            shifted_market (np.ndarray): The market series rolled by shift.
            shift (int): The roll; the days wrapped around are ignored.

        Returns:
            np.ndarray: The slope of each share, NaN with too little data.
        """
        market = shifted_market.copy()
        if shift == 1:
            market[0] = np.nan
        elif shift == -1:
            market[-1] = np.nan
        valid = ~np.isnan(values) & ~np.isnan(market)[:, None]
        count = valid.sum(axis=0)
        safe_count = np.where(count > 1, count, np.nan)
        filled_values = np.where(valid, values, 0.0)
        filled_market = np.where(valid, market[:, None], 0.0)
        mean_value = filled_values.sum(axis=0) / safe_count
        mean_market = filled_market.sum(axis=0) / safe_count
        value_dev = np.where(valid, values - mean_value, 0.0)
        market_dev = np.where(valid, market[:, None] - mean_market, 0.0)
        covariance = (value_dev * market_dev).sum(axis=0)
        variance = (market_dev * market_dev).sum(axis=0)
        slope = covariance / np.where(variance > 0, variance, np.nan)
        return np.where(count >= self.minimum_days, slope, np.nan)
