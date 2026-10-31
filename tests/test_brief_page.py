"""Tests of the brief's web page builder."""

import pandas as pd

from jegadeesh_titman_momentum_india.momentum.brief_page import BriefPage


class TestBriefPage:
    """Tests of BriefPage."""

    def test_page_is_self_contained_with_chart(self) -> None:
        """The page has a doctype, a table, an inline chart and no scripts.

        Returns:
            None.
        """
        text = (
            '# Strategy brief: test\n\n## Summary\n\nOne.\n\n'
            '## Backtest results\n\n| a | b |\n|---|---|\n| 1 | 2 |\n'
        )
        months = pd.period_range('2010-01', periods=48, freq='M')
        strategy = pd.Series(0.02, index=months)
        market = pd.Series(0.01, index=months)
        page = BriefPage().render(text, strategy, market)
        assert page.startswith('<!doctype html>')
        assert '<table>' in page
        assert '<svg' in page
        assert '<script' not in page
        assert page.index('<svg') > page.index('Backtest results')
