"""Wide tables of daily returns, a total return index, closes and turnover."""

import numpy as np
import pandas as pd


class PriceMatrices:
    """Holds daily data with one row per trading day and one column per share.

    Attributes:
        returns: Adjusted daily total returns, NaN where a share has none.
        index_level: A total return index starting at 1, carried forward over
            at most stale_days trading days without a row.
        close: Raw closes.
        traded_value: Rupees traded each day, NaN when the share did not trade.
        stale_days: How long an index level is carried forward.
    """

    def __init__(
        self,
        daily: pd.DataFrame,
        stale_days: int = 10,
    ) -> None:
        """Pivots a long table.

        Args:
            daily (pd.DataFrame): Columns date, symbol, close, traded_value
                and ret, one row per symbol and date.
            stale_days (int): Trading days an index level may be carried
                forward.

        Returns:
            None.
        """
        self.stale_days = stale_days
        self.returns = daily.pivot(
            index='date', columns='symbol', values='ret'
        ).astype('float32')
        self.close = daily.pivot(
            index='date', columns='symbol', values='close'
        ).astype('float32')
        self.traded_value = daily.pivot(
            index='date', columns='symbol', values='traded_value'
        ).astype('float32')
        self.returns = self.returns.sort_index()
        self.close = self.close.reindex(self.returns.index)
        self.traded_value = self.traded_value.reindex(self.returns.index)
        growth = np.log1p(self.returns.fillna(0.0).astype('float64'))
        level = np.exp(growth.cumsum())
        level = level.where(self.close.notna())
        self.index_level = level.ffill(limit=stale_days).astype('float32')

    def month_end_dates(self) -> pd.DatetimeIndex:
        """Gives the last trading day of every month.

        Returns:
            pd.DatetimeIndex: One date per month, in order.
        """
        dates = pd.Series(self.returns.index, index=self.returns.index)
        return pd.DatetimeIndex(
            dates.groupby(self.returns.index.to_period('M')).max().to_numpy()
        )

    def shifted_dates(
        self,
        dates: pd.DatetimeIndex,
        trading_days_back: int,
    ) -> pd.DatetimeIndex:
        """Moves each date back by a number of trading days.

        Args:
            dates (pd.DatetimeIndex): Trading days.
            trading_days_back (int): How many trading days to go back.

        Returns:
            pd.DatetimeIndex: The earlier trading days.
        """
        positions = self.returns.index.get_indexer(dates)
        shifted = np.maximum(positions - trading_days_back, 0)
        return self.returns.index[shifted]

    def window_returns(
        self,
        start_dates: pd.DatetimeIndex,
        end_dates: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        """Gives each share's return between pairs of dates.

        Args:
            start_dates (pd.DatetimeIndex): Window starts.
            end_dates (pd.DatetimeIndex): Window ends, same length.

        Returns:
            pd.DataFrame: One row per pair, indexed by the end date, NaN where
                a share lacks an index level at either date.
        """
        starts = self.index_level.loc[start_dates].to_numpy()
        ends = self.index_level.loc[end_dates].to_numpy()
        return pd.DataFrame(
            ends / starts - 1.0,
            index=end_dates,
            columns=self.index_level.columns,
        )
