"""Turns NSE's free-text corporate action subjects into price effects."""

import re

from jegadeesh_titman_momentum_india.momentum.parsed_action import (
    ParsedAction,
)


class ActionParser:
    """Reads bonuses, splits, consolidations and dividends from a subject."""

    BONUS = re.compile(r'bonus\D*(\d+)\s*:\s*(\d+)')
    FACE_VALUE_CHANGE = re.compile(
        r'\b(?:rs|re)(?![a-z])\.?\s*(\d+(?:\.\d+)?)\D{0,40}?to\s*'
        r'(?:rs|re)(?![a-z])\.?\s*(\d+(?:\.\d+)?)'
    )
    RUPEES = re.compile(r'\b(?:rs|re)(?![a-z])\.?\s*(\d+(?:\.\d+)?)')
    PERCENT = re.compile(r'(\d+(?:\.\d+)?)\s*%')

    def parse(self, subject: str, face_value: str | None) -> ParsedAction:
        """Reads one action.

        Args:
            subject (str): NSE's subject text, such as Bonus 1:1.
            face_value (str | None): The share's face value as text.

        Returns:
            ParsedAction: The price factor and cash dividend; an action that
                does not change the price gives the defaults.
        """
        text = ' '.join(subject.lower().split())
        if 'bonus' in text:
            match = self.BONUS.search(text)
            if match:
                new_shares = float(match.group(1))
                old_shares = float(match.group(2))
                if old_shares > 0 and new_shares > 0:
                    factor = old_shares / (new_shares + old_shares)
                    return ParsedAction(price_factor=factor)
            return ParsedAction()
        is_split = 'split' in text or 'sub-division' in text
        if is_split or 'consolidation' in text:
            match = self.FACE_VALUE_CHANGE.search(text)
            if match:
                before = float(match.group(1))
                after = float(match.group(2))
                if before > 0 and after > 0:
                    return ParsedAction(price_factor=after / before)
            return ParsedAction()
        if 'div' in text:
            return ParsedAction(dividend=self._dividend(text, face_value))
        return ParsedAction()

    def _dividend(self, text: str, face_value: str | None) -> float:
        """Reads a dividend in rupees per share.

        Args:
            text (str): The lower-case subject.
            face_value (str | None): The face value as text.

        Returns:
            float: Rupees per share, 0.0 if no amount is found.
        """
        rupees = [float(value) for value in self.RUPEES.findall(text)]
        if rupees:
            return sum(rupees)
        percents = [float(value) for value in self.PERCENT.findall(text)]
        if percents and face_value:
            try:
                face = float(face_value)
            except ValueError:
                return 0.0
            return sum(percents) / 100.0 * face
        return 0.0
