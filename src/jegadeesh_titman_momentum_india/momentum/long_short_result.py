"""Combines a winners leg and a losers leg into a zero-cost portfolio."""

import pandas as pd
from data_and_analytics.backtesting.backtest_result import BacktestResult


class LongShortResult:
    """Winners minus losers, before and after costs.

    The short leg is treated as a paper portfolio: it earns the opposite of
    the losers' return and pays the same delivery costs on its turnover as a
    long leg would, and no borrowing fee is charged because the engine has
    none.

    Attributes:
        buy: The winners' result.
        sell: The losers' result.
    """

    def __init__(self, buy: BacktestResult, sell: BacktestResult) -> None:
        """Keeps both legs.

        Args:
            buy (BacktestResult): The winners' result.
            sell (BacktestResult): The losers' result.

        Returns:
            None.
        """
        self.buy = buy
        self.sell = sell

    def gross(self) -> pd.Series:
        """Gives winners minus losers before costs.

        Returns:
            pd.Series: Monthly returns.
        """
        return self.buy.gross_returns - self.sell.gross_returns

    def net(self) -> pd.Series:
        """Gives winners minus losers after costs on both legs.

        Returns:
            pd.Series: Monthly returns.
        """
        return self.buy.net_returns - (
            self.sell.gross_returns + self.sell.costs
        )

    def turnover(self) -> pd.Series:
        """Gives the average of the two legs' turnover.

        Returns:
            pd.Series: Turnover as a fraction of one leg's value.
        """
        return (self.buy.turnover() + self.sell.turnover()) / 2.0
