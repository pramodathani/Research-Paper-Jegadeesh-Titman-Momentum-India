"""Tests that the hand-off script builds the same weights as the study."""

import datetime
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from data_and_analytics.backtesting.overlapping_cohorts import (
    OverlappingCohorts,
)

from jegadeesh_titman_momentum_india.momentum.study_runner import StudyRunner

SCRIPT = (
    Path(__file__).parent.parent
    / 'handoff'
    / 'jt-momentum-india'
    / 'skills'
    / 'jt-momentum-india'
    / 'scripts'
    / 'build_targets.py'
)


def load_script():
    """Imports the hand-off script as a module.

    Returns:
        module: The loaded module.
    """
    specification = importlib.util.spec_from_file_location(
        'build_targets', SCRIPT
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def make_market() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Builds 60 shares over 36 months with distinct drifts and volumes.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Prices for the script, with symbol,
            date, close and volume, and returns for the study runner, with
            date, symbol, close, traded_value and ret.
    """
    rng = np.random.default_rng(11)
    dates = pd.bdate_range('2008-01-01', '2010-12-31')
    price_rows = []
    return_rows = []
    for number in range(60):
        drift = (number - 30) / 30 * 0.001
        price = 100.0 + number
        volume = 1.0e5 * (1 + number % 7)
        for position, date in enumerate(dates):
            move = 0.0
            if position > 0:
                move = drift + rng.normal(0.0, 0.01)
                price = price * (1.0 + move)
            symbol = f'SH{number:02d}'
            price_rows.append((symbol, date, price, volume))
            return_rows.append(
                (
                    date,
                    symbol,
                    price,
                    volume * price,
                    move if position > 0 else np.nan,
                )
            )
    prices = pd.DataFrame(
        price_rows, columns=['symbol', 'date', 'close', 'volume']
    )
    returns = pd.DataFrame(
        return_rows,
        columns=['date', 'symbol', 'close', 'traded_value', 'ret'],
    )
    return prices, returns


class TestBuildTargets:
    """Tests of the hand-off script."""

    def test_weights_match_the_study_runner(self) -> None:
        """The script's targets equal the engine's weights for the next month.

        Returns:
            None.
        """
        module = load_script()
        prices, returns = make_market()
        as_of = datetime.date(2011, 1, 3)
        builder = module.MomentumTargets(prices, universe_size=500)
        weights, _ = builder.targets(as_of)
        runner = StudyRunner(returns)
        deciles = runner.deciles('U2', 6, False)
        members = deciles == 10
        months = runner.months
        cutoff = months.get_loc(pd.Period('2010-12', freq='M'))
        members = members.iloc[: cutoff + 1]
        cohorts = OverlappingCohorts(members, 6)
        expected = cohorts.next_period_weights(
            runner.monthly_returns.iloc[: cutoff + 1]
        )
        expected = expected.sort_index()
        compared = weights.reindex(expected.index.union(weights.index)).fillna(
            0.0
        )
        wanted = expected.reindex(compared.index).fillna(0.0)
        assert compared.sum() == pytest.approx(1.0)
        assert compared.to_numpy() == pytest.approx(wanted.to_numpy(), abs=1e-9)
        assert len(weights) > 6

    def test_stops_when_the_data_ends_early(self) -> None:
        """Building for January with data that stops mid-December fails.

        Returns:
            None.
        """
        module = load_script()
        prices, _ = make_market()
        cut = prices[prices['date'] <= '2010-12-10']
        builder = module.MomentumTargets(cut)
        with pytest.raises(ValueError, match='wait for the last prices'):
            builder.targets(datetime.date(2011, 1, 3))

    def test_excluded_symbols_are_never_held(self) -> None:
        """An excluded share has no weight and the rest still sum to one.

        Returns:
            None.
        """
        module = load_script()
        prices, _ = make_market()
        builder = module.MomentumTargets(prices)
        plain, _ = builder.targets(datetime.date(2011, 1, 3))
        top = plain.index[0]
        weights, _ = builder.targets(datetime.date(2011, 1, 3), {top})
        assert top not in weights.index
        assert weights.sum() == pytest.approx(1.0)

    def test_suspect_split_is_flagged(self) -> None:
        """A share whose price halves overnight is listed as suspect.

        Returns:
            None.
        """
        module = load_script()
        prices, _ = make_market()
        mask = (prices['symbol'] == 'SH05') & (prices['date'] > '2010-06-15')
        prices.loc[mask, 'close'] = prices.loc[mask, 'close'] * 0.4
        builder = module.MomentumTargets(prices)
        assert 'SH05' in builder.suspect_symbols(pd.Timestamp('2010-01-01'))
