"""Regression tests that tie the page's precomputed tables to the main results."""

import json
from pathlib import Path

import pandas as pd
import pytest

RESULTS = Path(__file__).resolve().parent.parent / 'results'


@pytest.mark.skipif(
    not (RESULTS / 'live' / 'live_tables.json').exists(),
    reason='live tables not built',
)
class TestLiveTables:
    """The 6/6 precomputed tables equal the earlier fixed tables."""

    @pytest.fixture(scope='class')
    def live(self) -> dict:
        """Reads the precomputed tables.

        Returns:
            dict: The contents of live_tables.json.
        """
        return json.loads((RESULTS / 'live' / 'live_tables.json').read_text())

    @pytest.mark.parametrize('universe', ['U1', 'U2'])
    def test_deciles_match_table_two(self, live: dict, universe: str) -> None:
        """The live decile rows equal results/table2_deciles.

        Args:
            live (dict): The precomputed tables.
            universe (str): U1 or U2.

        Returns:
            None.
        """
        fixed = pd.read_csv(RESULTS / f'table2_deciles_{universe}.csv')
        rows = live[f'{universe}|0|6|6']['joint']['All']['deciles']
        for row, (_, expected) in zip(rows, fixed.iterrows()):
            assert row[0] == str(expected['decile'])
            assert row[1] == pytest.approx(expected['mean'], abs=1e-5)
            assert row[2] == pytest.approx(expected['t_statistic'], abs=1e-3)

    @pytest.mark.parametrize('universe', ['U1', 'U2'])
    def test_event_time_matches_table_seven(
        self, live: dict, universe: str
    ) -> None:
        """The live cumulative spread equals results/table7_event_time.

        Args:
            live (dict): The precomputed tables.
            universe (str): U1 or U2.

        Returns:
            None.
        """
        fixed = pd.read_csv(RESULTS / f'table7_event_time_{universe}.csv')
        got = live['event'][f'{universe}|0|6']['cumulative']
        assert len(got) == 36
        for value, expected in zip(got, fixed['cumulative']):
            assert value == pytest.approx(expected, abs=1e-5)

    def test_every_specification_is_present(self, live: dict) -> None:
        """Each of the 64 specifications has all three tables.

        Args:
            live (dict): The precomputed tables.

        Returns:
            None.
        """
        keys = [key for key in live if key != 'event']
        assert len(keys) == 64
        for key in keys:
            assert set(live[key]) == {'section3', 'hold', 'joint'}
            assert 'All' in live[key]['joint']
