"""Tests of the daily return builder on made-up prices."""

import pandas as pd
import pytest

from jegadeesh_titman_momentum_india.momentum.daily_return_builder import (
    DailyReturnBuilder,
)


def make_prices(rows: list[tuple]) -> pd.DataFrame:
    """Builds a price table.

    Args:
        rows (list[tuple]): Tuples of date, symbol, series, isin, close and
            previous close.

    Returns:
        pd.DataFrame: The table with traded_value of 1000.
    """
    table = pd.DataFrame(
        rows,
        columns=[
            'date',
            'symbol',
            'series',
            'isin',
            'close',
            'previous_close',
        ],
    )
    table['date'] = pd.to_datetime(table['date'])
    table['traded_value'] = 1000.0
    return table


def make_actions(rows: list[tuple]) -> pd.DataFrame:
    """Builds an action table.

    Args:
        rows (list[tuple]): Tuples of ex-date, symbol, subject and face value.

    Returns:
        pd.DataFrame: The table.
    """
    return pd.DataFrame(
        rows,
        columns=['ex_date', 'symbol', 'subject', 'face_value'],
    )


class TestDailyReturnBuilder:
    """Tests of DailyReturnBuilder."""

    def test_plain_return(self) -> None:
        """Without actions the return is close over previous close.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-04', 'AAA', 'EQ', None, 110.0, 100.0)])
        returns, flags = DailyReturnBuilder().build(prices, make_actions([]))
        assert returns['ret'].iloc[0] == pytest.approx(0.10)
        assert flags.empty

    def test_bonus_is_not_a_loss(self) -> None:
        """A 1:1 bonus halves the price but the return is the true one.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-05', 'AAA', 'EQ', None, 51.0, 100.0)])
        actions = make_actions([('2010-01-05', 'AAA', 'Bonus 1:1', '10')])
        returns, _ = DailyReturnBuilder().build(prices, actions)
        assert returns['ret'].iloc[0] == pytest.approx(0.02)

    def test_split_and_dividend_together(self) -> None:
        """A 10 to 1 split on the same day as a rupee dividend.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-05', 'AAA', 'EQ', None, 10.5, 100.0)])
        actions = make_actions(
            [
                (
                    '2010-01-05',
                    'AAA',
                    'Face Value Split (Sub-Division) - From Rs 10/- To Re 1/-',
                    '10',
                ),
                ('2010-01-05', 'AAA', 'Dividend - Rs 0.5 Per Share', '10'),
            ]
        )
        returns, _ = DailyReturnBuilder().build(prices, actions)
        assert returns['ret'].iloc[0] == pytest.approx(1.10 - 1.0)

    def test_dividend_alone(self) -> None:
        """A dividend adds to the return.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-05', 'AAA', 'EQ', None, 98.0, 100.0)])
        actions = make_actions(
            [('2010-01-05', 'AAA', 'Dividend - Rs 3 Per Share', '10')]
        )
        returns, _ = DailyReturnBuilder().build(prices, actions)
        assert returns['ret'].iloc[0] == pytest.approx(0.01)

    def test_action_on_a_holiday_moves_to_next_trading_day(self) -> None:
        """An ex-date with no trading applies on the next trading day.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-06', 'AAA', 'EQ', None, 51.0, 100.0)])
        actions = make_actions([('2010-01-05', 'AAA', 'Bonus 1:1', '10')])
        returns, _ = DailyReturnBuilder().build(prices, actions)
        assert returns['ret'].iloc[0] == pytest.approx(0.02)

    def test_missed_split_is_inferred(self) -> None:
        """A halving with no listed action is read as a missed 1:1 bonus.

        Returns:
            None.
        """
        prices = make_prices([('2004-03-01', 'AAA', 'EQ', None, 51.0, 100.0)])
        returns, flags = DailyReturnBuilder().build(prices, make_actions([]))
        assert returns['ret'].iloc[0] == pytest.approx(0.02)
        assert list(flags['kind']) == ['inferred_action']

    def test_implausible_move_is_zeroed_and_flagged(self) -> None:
        """A move matching no ratio is set to zero.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-05', 'AAA', 'EQ', None, 270.0, 100.0)])
        returns, flags = DailyReturnBuilder().build(prices, make_actions([]))
        assert returns['ret'].iloc[0] == 0.0
        assert list(flags['kind']) == ['zeroed']

    def test_eq_preferred_and_funds_dropped(self) -> None:
        """EQ beats BE on the same day and fund ISINs are removed.

        Returns:
            None.
        """
        prices = make_prices(
            [
                ('2010-01-04', 'AAA', 'BE', None, 90.0, 100.0),
                ('2010-01-04', 'AAA', 'EQ', None, 110.0, 100.0),
                ('2010-01-04', 'FUND', 'EQ', 'INF000A01010', 10.0, 10.0),
            ]
        )
        returns, _ = DailyReturnBuilder().build(prices, make_actions([]))
        assert list(returns['symbol']) == ['AAA']
        assert returns['ret'].iloc[0] == pytest.approx(0.10)

    def test_zero_previous_close_gives_no_return(self) -> None:
        """A missing base price gives NaN, not infinity.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-04', 'AAA', 'EQ', None, 10.0, 0.0)])
        returns, _ = DailyReturnBuilder().build(prices, make_actions([]))
        assert pd.isna(returns['ret'].iloc[0])

    def test_penny_stock_tick_jump_is_not_a_split(self) -> None:
        """A real doubling of a share priced under 5 is kept.

        Returns:
            None.
        """
        prices = make_prices([('2010-01-05', 'AAA', 'EQ', None, 0.2, 0.1)])
        returns, flags = DailyReturnBuilder().build(prices, make_actions([]))
        assert returns['ret'].iloc[0] == pytest.approx(1.0)
        assert flags.empty
