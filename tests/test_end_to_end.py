"""One test that runs the whole study on a made-up market."""

import numpy as np
import pandas as pd

from jegadeesh_titman_momentum_india.momentum.daily_return_builder import (
    DailyReturnBuilder,
)
from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner


def make_market() -> pd.DataFrame:
    """Makes 40 shares over 48 months in which past winners keep winning.

    Each share has a fixed daily drift between -0.1% and +0.1% and noise, so
    ranking on past returns picks the highest drift shares.

    Returns:
        pd.DataFrame: Raw bhavcopy-style rows.
    """
    rng = np.random.default_rng(7)
    dates = pd.bdate_range('2008-01-01', periods=48 * 21)
    rows = []
    for number in range(40):
        drift = (number - 20) / 20 * 0.001
        price = 100.0
        for date in dates:
            previous = price
            price = price * (1.0 + drift + rng.normal(0.0, 0.01))
            rows.append(
                (
                    date,
                    f'SH{number:02d}',
                    'EQ',
                    None,
                    price,
                    previous,
                    5.0e7,
                )
            )
    return pd.DataFrame(
        rows,
        columns=[
            'date',
            'symbol',
            'series',
            'isin',
            'close',
            'previous_close',
            'traded_value',
        ],
    )


class TestEndToEnd:
    """The whole pipeline from raw prices to strategy returns."""

    def test_winners_beat_losers_and_costs_reduce_returns(self) -> None:
        """Buy-minus-sell is positive, net is below gross, and a copy matches.

        Returns:
            None.
        """
        empty_actions = pd.DataFrame(
            columns=['ex_date', 'symbol', 'subject', 'face_value']
        )
        returns, flags = DailyReturnBuilder().build(
            make_market(), empty_actions
        )
        assert flags.empty
        runner = StudyRunner(returns)
        top_200 = runner.universes['U3']
        assert not (top_200 & ~runner.universes['U2']).any().any()
        assert (top_200.sum(axis=1) <= 200).all()
        grid = runner.grid(
            formation_choices=(3, 6),
            holding_choices=(3, 6),
            universes=('U1', 'U2'),
        )
        spread = grid[
            (grid['leg'] == 'long_short')
            & (grid['universe'] == 'U1')
            & ~grid['skip']
            & (grid['formation_months'] == 6)
            & (grid['holding_months'] == 6)
        ]
        assert spread['gross'].notna().sum() > 20
        assert spread['gross'].mean() > 0.0
        assert (spread['net'].dropna() < spread['gross'].dropna()).all()
        again = StudyRunner(returns).grid(
            formation_choices=(3, 6),
            holding_choices=(3, 6),
            universes=('U1', 'U2'),
        )
        pd.testing.assert_frame_equal(grid, again)
