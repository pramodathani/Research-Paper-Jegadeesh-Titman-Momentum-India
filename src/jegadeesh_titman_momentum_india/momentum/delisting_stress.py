"""Charges a loss to shares that stop trading, for a worst-case check."""

import numpy as np
import pandas as pd


class DelistingStress:
    """Adds a terminal return the month after a share's last return.

    The engine drops a share that stops trading from its cohort without
    charging any loss. This class puts a chosen return, such as -100% or -30%,
    in the month after the last return, so the loss is charged to whoever
    holds the share. Some shares stop under one symbol and continue under
    another, so the stress overstates the damage.
    """

    def apply(
        self,
        monthly_returns: pd.DataFrame,
        terminal_return: float,
    ) -> pd.DataFrame:
        """Returns a copy of the table with terminal returns added.

        Args:
            monthly_returns (pd.DataFrame): Monthly returns, months by shares.
            terminal_return (float): The return charged, such as -1.0.

        Returns:
            pd.DataFrame: The table with one extra return per vanished share.
        """
        values = monthly_returns.to_numpy(dtype=float).copy()
        present = ~np.isnan(values)
        month_count = values.shape[0]
        last_position = np.where(
            present.any(axis=0),
            month_count - 1 - np.argmax(present[::-1], axis=0),
            -1,
        )
        for column, last in enumerate(last_position):
            if 0 <= last < month_count - 2:
                values[last + 1, column] = terminal_return
        return pd.DataFrame(
            values,
            index=monthly_returns.index,
            columns=monthly_returns.columns,
        )
