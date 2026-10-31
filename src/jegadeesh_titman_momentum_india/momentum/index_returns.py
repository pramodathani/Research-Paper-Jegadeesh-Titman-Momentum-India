"""Monthly index returns from NSE's daily index files."""

import pandas as pd


class IndexReturns:
    """Builds monthly price and approximate total returns for an index.

    The total return adds a twelfth of the month-end dividend yield to the
    price return, because no total return history can be downloaded.
    """

    def monthly(
        self,
        index_daily: pd.DataFrame,
        names: tuple[str, ...],
    ) -> pd.DataFrame:
        """Chains an index under its successive names.

        Args:
            index_daily (pd.DataFrame): Columns date, index_name, close and
                div_yield, as in the index_daily table; yields in percent.
            names (tuple[str, ...]): The names the index has had, oldest
                first.

        Returns:
            pd.DataFrame: Columns price_return and total_return indexed by
                month period, from the second month on.
        """
        rows = index_daily[index_daily['index_name'].isin(names)].copy()
        rows['date'] = pd.to_datetime(rows['date'])
        rows = rows.sort_values('date').drop_duplicates('date', keep='last')
        rows['month'] = rows['date'].dt.to_period('M')
        month_end = rows.groupby('month').last()
        price_return = month_end['close'].pct_change()
        yield_part = month_end['div_yield'].fillna(0.0) / 100.0 / 12.0
        return pd.DataFrame(
            {
                'price_return': price_return,
                'total_return': price_return + yield_part,
            }
        ).dropna()
