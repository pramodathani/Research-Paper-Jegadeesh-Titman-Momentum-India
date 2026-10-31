# futures_portfolios.py

- Portfolio D (F&O long-short) ignores the futures basis and carry; the short leg earns the losers' stock return and pays futures costs.
- Portfolio C (hedged long-only) assumes the hedge is the full value of the portfolio, rolled monthly, and earns minus the index's total return plus the risk-free rate. The index total return is price plus a twelfth of the dividend yield.
