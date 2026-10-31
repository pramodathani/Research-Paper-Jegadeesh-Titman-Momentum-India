"""Tests of the corporate action parser and security filter."""

import pytest

from jegadeesh_titman_momentum_india.momentum.action_parser import (
    ActionParser,
)
from jegadeesh_titman_momentum_india.momentum.security_filter import (
    SecurityFilter,
)


class TestActionParser:
    """Tests of ActionParser."""

    @pytest.mark.parametrize(
        ('subject', 'factor'),
        [
            ('Bonus 1:1', 0.5),
            ('Bonus 3:1', 0.25),
            ('Bonus 1:2', 2 / 3),
            ('Bonus 2:5', 5 / 7),
        ],
    )
    def test_bonus_factor(self, subject: str, factor: float) -> None:
        """A bonus of a new shares for b held leaves b / (a + b).

        Args:
            subject (str): The subject text.
            factor (float): The expected price factor.

        Returns:
            None.
        """
        parsed = ActionParser().parse(subject, '10')
        assert parsed.price_factor == pytest.approx(factor)

    @pytest.mark.parametrize(
        ('subject', 'factor'),
        [
            (
                (
                    'Face Value Split (Sub-Division) - From Rs 10/- Per Share '
                    'To Re 1/- Per Share'
                ),
                0.1,
            ),
            ('Face Value Split (Sub-Division) - From Rs 10/- To Rs 5/-', 0.5),
            ('FV Split Rs10/- to Rs2/-', 0.2),
            ('Face Value Consolidation From Re 1/- To Rs 10/-', 10.0),
        ],
    )
    def test_split_factor(self, subject: str, factor: float) -> None:
        """A split or consolidation scales the price by after over before.

        Args:
            subject (str): The subject text.
            factor (float): The expected price factor.

        Returns:
            None.
        """
        parsed = ActionParser().parse(subject, '10')
        assert parsed.price_factor == pytest.approx(factor)

    def test_dividend_in_rupees(self) -> None:
        """A rupee amount is read directly.

        Returns:
            None.
        """
        parsed = ActionParser().parse('Dividend - Rs 2.5 Per Share', '10')
        assert parsed.dividend == 2.5
        assert parsed.price_factor == 1.0

    def test_dividend_in_percent_of_face_value(self) -> None:
        """A percentage is applied to the face value.

        Returns:
            None.
        """
        parsed = ActionParser().parse('AGM/Dividend-20%', '10')
        assert parsed.dividend == pytest.approx(2.0)

    def test_dividend_re_one(self) -> None:
        """Re 1 means one rupee.

        Returns:
            None.
        """
        parsed = ActionParser().parse('Dividend - Re 1 Per Share', '2')
        assert parsed.dividend == 1.0

    def test_meetings_and_rights_do_not_change_price(self) -> None:
        """Meetings, rights and buybacks leave the price alone.

        Returns:
            None.
        """
        parser = ActionParser()
        for subject in (
            'Annual General Meeting',
            'Rights 1:4 @ Premium Rs 10/-',
            'Buy Back',
            'Demerger',
        ):
            parsed = parser.parse(subject, '10')
            assert parsed.price_factor == 1.0
            assert parsed.dividend == 0.0


class TestSecurityFilter:
    """Tests of SecurityFilter."""

    def test_funds_rights_and_shares(self) -> None:
        """Fund ISINs, rights symbols and ETFs are dropped.

        Returns:
            None.
        """
        security_filter = SecurityFilter()
        assert security_filter.is_company_share('RELIANCE', 'INE002A01018')
        assert not security_filter.is_company_share('GOLDBEES', 'INF204KB17I5')
        assert not security_filter.is_company_share('ABIN-RE1', None)
        assert not security_filter.is_company_share('NIFTYBEES', None)
        assert not security_filter.is_company_share('PARTLY', 'IN9002A01018')
        assert security_filter.is_company_share('INFY', None)
