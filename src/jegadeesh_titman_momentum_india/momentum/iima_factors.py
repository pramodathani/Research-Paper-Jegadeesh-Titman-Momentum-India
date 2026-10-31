"""The IIMA monthly factor returns as decimal monthly returns."""

import pandas as pd


class IimaFactors:
    """Reads the IIMA four-factor file.

    Attributes:
        factors: Decimal monthly returns indexed by month period, with columns
            smb, hml, wml, mf (market premium) and rf (risk-free rate).
    """

    def __init__(self, table: pd.DataFrame) -> None:
        """Converts a table of percent returns to decimals.

        Args:
            table (pd.DataFrame): Columns month (a date) and smb, hml, wml, mf
                and rf in percent.

        Returns:
            None.
        """
        factors = table.copy()
        factors.index = pd.PeriodIndex(pd.to_datetime(factors['month']), 'M')
        factors = factors[['smb', 'hml', 'wml', 'mf', 'rf']].astype(float)
        self.factors = factors / 100.0

    def market_return(self) -> pd.Series:
        """Gives the market's total return: premium plus risk-free rate.

        Returns:
            pd.Series: Monthly returns.
        """
        return self.factors['mf'] + self.factors['rf']

    def risk_free(self, months: pd.PeriodIndex) -> pd.Series:
        """Gives the risk-free rate for each month, carrying the last value on.

        Args:
            months (pd.PeriodIndex): The months wanted.

        Returns:
            pd.Series: The monthly risk-free rate; months after the file ends
                repeat its last value.
        """
        series = self.factors['rf'].reindex(months)
        return series.ffill()
