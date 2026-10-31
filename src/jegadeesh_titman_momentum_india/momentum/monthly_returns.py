"""Compounds daily returns into calendar-month returns."""

import numpy as np
import pandas as pd


class MonthlyReturns:
    """Builds monthly holding returns from daily ones."""

    def build(self, daily_returns: pd.DataFrame) -> pd.DataFrame:
        """Compounds each month's daily returns.

        A share that traded in a month but not on every day keeps the return
        of the days it traded; one with no return in the month gets NaN.

        Args:
            daily_returns (pd.DataFrame): Daily returns, one row per trading
                day, one column per share.

        Returns:
            pd.DataFrame: Monthly returns indexed by month period.
        """
        growth = np.log1p(daily_returns.astype('float64'))
        months = growth.index.to_period('M')
        summed = growth.groupby(months).sum(min_count=1)
        return np.expm1(summed)
