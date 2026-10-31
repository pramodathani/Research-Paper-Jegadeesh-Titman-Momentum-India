"""The price effect of one corporate action."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedAction:
    """What a corporate action does to a share's price.

    Attributes:
        price_factor: The ex-date price divided by the price before it, due to
            the action alone: 0.5 for a 1:1 bonus, 0.1 for a 10 to 1 split,
            1.0 when the action does not change the price.
        dividend: Cash dividend in rupees per share, 0.0 if none.
    """

    price_factor: float = 1.0
    dividend: float = 0.0
