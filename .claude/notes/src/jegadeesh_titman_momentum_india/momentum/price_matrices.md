# price_matrices.py

- The total return index is carried forward at most 10 trading days, so a suspended share keeps its level briefly but drops out of ranking windows once it has stopped trading. An earlier version let the level survive for ever after a delisting; a test now catches that.
- Monthly returns come from daily returns (not month-end prices), so a share that traded for part of its last month keeps that partial return, as the paper's compounded daily CRSP returns did.
- float32 keeps the 7,600 days by 5,700 shares tables near 170 MB each.
