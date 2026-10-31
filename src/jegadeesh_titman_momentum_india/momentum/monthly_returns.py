"""Compounds daily returns into calendar-month returns."""

import numpy as np
import pandas as pd


class MonthlyReturns:
    """Builds monthly holding returns from daily ones."""

    def build(
        self,
        daily_returns: pd.DataFrame,
        delay_days: int = 0,
    ) -> pd.DataFrame:
        """Compounds each month's daily returns.

        A share that traded in a month but not on every day keeps the return
        of the days it traded; one with no return in the month gets NaN.

        With delay_days above zero, each month starts and ends that many
        trading days later, as if every trade were made after the formation
        close instead of at it.

        Args:
            daily_returns (pd.DataFrame): Daily returns, one row per trading
                day, one column per share.
            delay_days (int): Trading days by which each month is shifted.

        Returns:
            pd.DataFrame: Monthly returns indexed by month period.
        """
        growth = np.log1p(daily_returns.astype('float64'))
        dates = pd.Series(growth.index, index=growth.index)
        if delay_days > 0:
            dates = dates.shift(delay_days).fillna(dates.iloc[0])
        months = pd.DatetimeIndex(dates).to_period('M')
        summed = growth.groupby(months).sum(min_count=1)
        return np.expm1(summed)
