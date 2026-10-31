"""Tells company shares from funds, rights entitlements and similar."""

import re


class SecurityFilter:
    """Decides whether an NSE equity-series symbol is an ordinary share.

    Funds are recognised by an ISIN starting INF, partly paid shares by IN9,
    and older or ISIN-less rows by name patterns.
    """

    NAME_PATTERN = re.compile(
        r'(-RE\d*$|-RE$|BEES$|ETF|^LIQUID|^GILT|IETF$|^NIFTY|^SENSEX)',
        re.IGNORECASE,
    )

    def is_company_share(self, symbol: str, isin: str | None) -> bool:
        """Says whether a row is an ordinary company share.

        Args:
            symbol (str): The NSE symbol.
            isin (str | None): The ISIN, or None when the file has none.

        Returns:
            bool: True for an ordinary share.
        """
        if isinstance(isin, str) and isin.startswith(('INF', 'IN9')):
            return False
        return self.NAME_PATTERN.search(symbol) is None
