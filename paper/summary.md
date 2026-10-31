# Jegadeesh and Titman (1993): structured summary

Jegadeesh, N., and Titman, S. (1993). Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency. *The Journal of Finance*, 48(1), 65-91.

Page numbers are the journal's printed pages (PDF page = journal page − 63; PDF page 1 is a JSTOR cover). Every table below was checked against the page image.

## 1. Question and hypothesis (pp. 65-68)

- Do strategies that buy stocks with high returns over the past 3-12 months and sell stocks with low returns earn abnormal returns over the following 3-12 months?
- This is set against short-horizon (1 week to 1 month) and long-horizon (3-5 year) reversals found by Jegadeesh (1990), Lehmann (1990) and De Bondt and Thaler (1985) (pp. 66-67).
- Main claim (abstract, p. 65): these "relative strength" strategies earn significant positive returns over 3- to 12-month holding periods. The profits are not due to systematic risk or to delayed reactions to common factors. They are consistent with delayed price reactions to firm-specific information. Part of the first year's abnormal return dissipates over the next two years.

## 2. Data (pp. 67-69, 87)

| Item | Paper |
|---|---|
| Source | CRSP daily returns file, July 1962 to December 1989; monthly returns compounded from daily returns (fn. 4, p. 69) |
| Universe | NYSE and AMEX stocks (p. 67); "All stocks with available returns data in the J months preceding the portfolio formation date are included" (p. 69). No price, size or share-type filter is stated. |
| Main sample | January 1965 to December 1989, 300 months (Table I caption, p. 70). 1965 is the first full year because 12/12 needs 23 months of lagged data (fn. 4). |
| Back-test samples | 1927-1940 and 1941-1964 (p. 85) |
| Market proxy | CRSP value-weighted index; risk-free rate is the 1-month Treasury bill (eq. 9, p. 77); equally weighted index used in unreported checks |
| Size and beta groups | S1, S2, S3: small, medium, large firms (breakpoints not stated). β1-β3: Scholes-Williams betas from the calendar year before formation (Table III caption, p. 78) |
| Earnings dates | COMPUSTAT quarterly industrial file (1990), 1980-1989; 429.2 announcements a month on average (p. 87) |

## 3. Method (p. 68)

1. At the beginning of each month t, rank all eligible stocks in ascending order of their return over the past J months, J ∈ {3, 6, 9, 12}.
2. Form ten equally weighted decile portfolios. The **buy** (winners) portfolio is the highest past-return decile and the **sell** (losers) portfolio is the lowest (Table I caption, p. 70). The body text on p. 68 has the labels the wrong way round ("The top decile portfolio is called the 'losers' decile"); the table captions and every result make clear winners = highest past return.
3. Hold for K months, K ∈ {3, 6, 9, 12}, with **overlapping portfolios**: in month t the strategy holds the cohorts formed in months t, t−1, …, t−K+1, each with weight 1/K. Each month it opens the new cohort and closes the one opened in month t−K, so 1/K of the portfolio is revised a month.
4. Portfolios are **rebalanced monthly to equal weights**. Buy-and-hold versions gave "very similar" (slightly higher) returns and are not reported.
5. The **zero-cost** portfolio is buy minus sell; its return is per dollar long (p. 69).
6. A second set of 16 strategies **skips one week** between formation and holding to avoid bid-ask bounce, price pressure and short-horizon reversal (p. 68). In total 32 strategies.
7. Statistics: t-statistics on average monthly returns; the method is not stated for Table I (presumably plain time-series t). Newey-West (autocorrelation-consistent) standard errors are used for cumulative event-time returns (Tables VII and VIII) and the lead-lag regression (p. 75). Bonferroni bound for 32 tests: a t of 4.28 has probability < 0.0006 (p. 69, fn. 5).
8. Risk adjustment: CAPM alpha from r_p − r_f = α_p + β_p (r_m − r_f) + e (eq. 9, p. 77).

## 4. Results to reproduce

### Table I, Returns of relative strength portfolios, 1965-1989 (p. 70)

Average monthly returns, t-statistics in parentheses. Panel A: no skip. Panel B: one-week skip.

| J | Portfolio | A: K=3 | K=6 | K=9 | K=12 | B: K=3 | K=6 | K=9 | K=12 |
|---|---|---|---|---|---|---|---|---|---|
| 3 | Sell | 0.0108 (2.16) | 0.0091 (1.87) | 0.0092 (1.92) | 0.0087 (1.87) | 0.0083 (1.67) | 0.0079 (1.64) | 0.0084 (1.77) | 0.0083 (1.79) |
| 3 | Buy | 0.0140 (3.57) | 0.0149 (3.78) | 0.0152 (3.83) | 0.0156 (3.89) | 0.0156 (3.95) | 0.0158 (3.98) | 0.0158 (3.96) | 0.0160 (3.98) |
| 3 | Buy-sell | 0.0032 (1.10) | 0.0058 (2.29) | 0.0061 (2.69) | 0.0069 (3.53) | 0.0073 (2.61) | 0.0078 (3.16) | 0.0074 (3.36) | 0.0077 (4.00) |
| 6 | Sell | 0.0087 (1.67) | 0.0079 (1.56) | 0.0072 (1.48) | 0.0080 (1.66) | 0.0066 (1.28) | 0.0068 (1.35) | 0.0067 (1.38) | 0.0076 (1.58) |
| 6 | Buy | 0.0171 (4.28) | 0.0174 (4.33) | 0.0174 (4.31) | 0.0166 (4.13) | 0.0179 (4.47) | 0.0178 (4.41) | 0.0175 (4.32) | 0.0166 (4.13) |
| 6 | Buy-sell | 0.0084 (2.44) | 0.0095 (3.07) | 0.0102 (3.76) | 0.0086 (3.36) | 0.0114 (3.37) | 0.0110 (3.61) | 0.0108 (4.01) | 0.0090 (3.54) |
| 9 | Sell | 0.0077 (1.47) | 0.0065 (1.29) | 0.0071 (1.43) | 0.0082 (1.66) | 0.0058 (1.13) | 0.0058 (1.15) | 0.0066 (1.34) | 0.0078 (1.59) |
| 9 | Buy | 0.0186 (4.56) | 0.0186 (4.53) | 0.0176 (4.30) | 0.0164 (4.03) | 0.0193 (4.72) | 0.0188 (4.56) | 0.0176 (4.30) | 0.0164 (4.04) |
| 9 | Buy-sell | 0.0109 (3.03) | 0.0121 (3.78) | 0.0105 (3.47) | 0.0082 (2.89) | 0.0135 (3.85) | 0.0130 (4.09) | 0.0109 (3.67) | 0.0085 (3.04) |
| 12 | Sell | 0.0060 (1.17) | 0.0065 (1.29) | 0.0075 (1.48) | 0.0087 (1.74) | 0.0048 (0.93) | 0.0058 (1.15) | 0.0070 (1.40) | 0.0085 (1.71) |
| 12 | Buy | 0.0192 (4.63) | 0.0179 (4.36) | 0.0168 (4.10) | 0.0155 (3.81) | 0.0196 (4.73) | 0.0179 (4.36) | 0.0167 (4.09) | 0.0154 (3.79) |
| 12 | Buy-sell | 0.0131 (3.74) | 0.0114 (3.40) | 0.0093 (2.95) | 0.0068 (2.25) | 0.0149 (4.28) | 0.0121 (3.65) | 0.0096 (3.09) | 0.0069 (2.31) |

All 32 buy-sell returns are positive; all are significant except 3/3 in Panel A. The best is 12/3: 1.31% a month (A), 1.49% (B). J = 6 earns about 1% a month for every K. The one-week skip raises returns slightly (p. 69). The paper then studies **6/6 without the skip** in detail (p. 69).

### Table II, Betas and size of the 6/6 decile portfolios (p. 73)

| | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P10−P1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Beta (VW index) | 1.36 | 1.19 | 1.14 | 1.11 | 1.09 | 1.08 | 1.09 | 1.12 | 1.17 | 1.28 | −0.08 |
| Average market cap | 208.24 | 480.07 | 545.31 | 618.85 | 692.89 | 702.51 | 738.09 | 758.87 | 680.18 | 495.13 | — |

Both extreme deciles hold smaller, higher-beta stocks; the zero-cost portfolio's beta is slightly negative. Units of market cap are not stated.

### Section III: sources of profit (pp. 71-75)

- Profit decomposes into cross-sectional dispersion of expected returns, serial covariance of the factor, and serial covariance of firm-specific returns (eq. 3).
- Serial covariance of 6-month EW index returns is −0.0028 (p. 73), so factor autocorrelation is not the source. Average serial covariance of market-model residuals is +0.0012 (p. 74).
- A weighted relative strength strategy (weights proportional to return minus the EW index) earns 4.5% semiannually per dollar long (t = 2.99), correlation 0.95 with the decile strategy (p. 71).
- Lead-lag regression of 6/6 profits on squared lagged market return: θ = −2.29 (Newey-West t = −1.74), so lead-lag effects do not explain the profits (p. 75).

### Table III, 6/6 deciles within size and beta groups (pp. 78-79)

Panel A, average monthly raw returns (t):

| | All | S1 (small) | S2 | S3 (large) | β1 (low) | β2 | β3 (high) |
|---|---|---|---|---|---|---|---|
| P1 (losers) | 0.0079 (1.56) | 0.0083 (1.35) | 0.0047 (0.99) | 0.0082 (2.22) | 0.0129 (2.92) | 0.0097 (2.01) | 0.0052 (0.95) |
| P10 (winners) | 0.0174 (4.33) | 0.0182 (3.99) | 0.0173 (4.11) | 0.0157 (4.41) | 0.0191 (5.17) | 0.0176 (4.53) | 0.0160 (3.50) |
| P10−P1 | 0.0095 (3.07) | 0.0099 (2.77) | 0.0126 (4.57) | 0.0075 (3.03) | 0.0062 (2.05) | 0.0079 (2.64) | 0.0108 (3.35) |

Panel B, CAPM alphas against the CRSP VW index (t):

| | All | S1 | S2 | S3 | β1 | β2 | β3 |
|---|---|---|---|---|---|---|---|
| P1 | −0.0030 (−0.89) | −0.0029 (−0.60) | −0.0062 (−2.11) | −0.0020 (−1.17) | 0.0031 (0.94) | −0.0009 (−0.28) | −0.0062 (−1.71) |
| P10 | 0.0070 (3.24) | 0.0077 (2.56) | 0.0067 (2.91) | 0.0056 (3.50) | 0.0094 (4.10) | 0.0074 (3.47) | 0.0048 (2.02) |
| P10−P1 | 0.0100 (3.23) | 0.0106 (2.97) | 0.0129 (4.69) | 0.0076 (3.08) | 0.0063 (2.09) | 0.0083 (2.76) | 0.0111 (3.42) |

Returns rise almost monotonically from P1 to P10 in every group. Against the VW index the abnormal return comes from the **winners**: P10's alpha is significant and P1's is not (p. 77). Against the EW index both legs are significant and P10−P1 alpha is 0.0115 (t = 3.84). The full P1-P10 rows are on pp. 78-79.

### Transaction costs (p. 77)

Turnover is 84.8% semiannually (fn. 12: buy side 86.6%, sell side 83.1%). After a 0.5% one-way cost the risk-adjusted return is **9.29% a year**, still significant, and significant in each size group.

### Table IV, 6/6 P10−P1 by calendar month (p. 80)

| Month | All | S1 | S2 | S3 |
|---|---|---|---|---|
| Jan | −0.0686 (−3.52) | −0.0797 (−3.36) | −0.0347 (−2.14) | −0.0161 (−1.28) |
| Feb | 0.0063 (0.85) | 0.0089 (0.81) | 0.0149 (2.44) | 0.0099 (1.35) |
| Mar | 0.0105 (1.37) | 0.0196 (2.08) | 0.0103 (1.49) | 0.0108 (1.49) |
| Apr | 0.0333 (7.39) | 0.0323 (5.35) | 0.0368 (7.29) | 0.0215 (4.91) |
| May | 0.0102 (1.32) | 0.0046 (0.56) | 0.0091 (1.18) | 0.0079 (1.19) |
| Jun | 0.0238 (3.86) | 0.0237 (3.50) | 0.0231 (3.23) | 0.0185 (2.59) |
| Jul | 0.0075 (0.96) | 0.0112 (1.44) | 0.0084 (0.96) | 0.0035 (0.41) |
| Aug | 0.0027 (0.35) | 0.0079 (0.97) | −0.0011 (−0.14) | −0.0058 (−0.71) |
| Sep | 0.0116 (1.10) | 0.0126 (1.20) | 0.0137 (1.27) | 0.0053 (0.60) |
| Oct | 0.0137 (1.30) | 0.0160 (1.40) | 0.0151 (1.44) | 0.0025 (0.22) |
| Nov | 0.0372 (5.31) | 0.0352 (5.01) | 0.0331 (4.12) | 0.0248 (2.78) |
| Dec | 0.0264 (2.61) | 0.0265 (2.13) | 0.0224 (2.86) | 0.0070 (0.99) |
| Feb-Dec | 0.0166 (6.67) | 0.0181 (6.47) | 0.0169 (6.83) | 0.0096 (4.00) |
| F, all months equal (p) | 7.90 (0.00) | 7.14 (0.00) | 4.11 (0.00) | 1.81 (0.51) |
| F, Feb-Dec equal (p) | 2.04 (0.03) | 1.23 (0.27) | 1.91 (0.04) | 1.28 (0.24) |

The strategy loses about 7% each January; the January loss shrinks with firm size. April is positive in 24 of 25 years (pp. 79-81). Footnote 15: reversing the positions in January only would earn close to 25% a year abnormal.

### Table V, Share of months with a positive 6/6 P10−P1 return (p. 81)

All stocks: January 0.24, April 0.96, November 0.84, February-December 0.71, all months 0.67. S1 0.66, S2 0.68, S3 0.60 over all months.

### Table VI, 6/6 P10−P1 by five-year subperiod (p. 82)

| Sample | Months | 1965-69 | 1970-74 | 1975-79 | 1980-84 | 1985-89 |
|---|---|---|---|---|---|---|
| All | All | 0.0123 (1.94) | 0.0109 (1.23) | −0.0044 (−0.51) | 0.0127 (2.67) | 0.0162 (3.42) |
| All | Jan | −0.0524 (−1.28) | −0.1070 (−2.54) | −0.1017 (−1.31) | −0.0253 (−1.38) | −0.0569 (−2.76) |
| All | Feb-Dec | 0.0182 (3.36) | 0.0217 (2.88) | 0.0044 (0.78) | 0.0161 (3.44) | 0.0229 (6.09) |
| S1 | All | 0.0082 (1.14) | 0.0128 (1.63) | −0.0064 (−0.58) | 0.0153 (2.61) | 0.0197 (2.89) |
| S2 | All | 0.0177 (3.08) | 0.0115 (1.57) | 0.0018 (0.24) | 0.0172 (3.38) | 0.0146 (3.40) |
| S3 | All | 0.0129 (2.71) | 0.0115 (1.62) | 0.0018 (0.35) | 0.0076 (1.41) | 0.0035 (0.73) |

Only 1975-79 is negative overall, driven by small-firm Januaries; February-December returns are positive in every subperiod and size group. (The January and February-December rows for S1-S3 are on p. 82.)

### Table VII, 6-month winners minus losers in event time, 1965-1989 (p. 84)

Average monthly return in month t after formation, and cumulative return (Newey-West t):

| t | Monthly | Cumulative | t | Monthly | Cumulative | t | Monthly | Cumulative |
|---|---|---|---|---|---|---|---|---|
| 1 | −0.0025 (−0.59) | −0.0025 (−0.59) | 13 | −0.0036 (−1.12) | 0.0915 (3.35) | 25 | −0.0035 (−1.36) | 0.0521 (1.41) |
| 2 | 0.0124 (3.29) | 0.0099 (1.37) | 14 | −0.0039 (−1.34) | 0.0876 (3.07) | 26 | −0.0030 (−1.14) | 0.0492 (1.22) |
| 3 | 0.0116 (3.18) | 0.0216 (2.20) | 15 | −0.0034 (−1.21) | 0.0842 (2.89) | 27 | −0.0024 (−0.98) | 0.0467 (1.10) |
| 4 | 0.0110 (3.19) | 0.0326 (2.67) | 16 | −0.0038 (−1.41) | 0.0804 (2.76) | 28 | −0.0032 (−1.33) | 0.0435 (0.98) |
| 5 | 0.0093 (2.82) | 0.0419 (2.79) | 17 | −0.0047 (−1.74) | 0.0757 (2.70) | 29 | −0.0032 (−1.38) | 0.0403 (0.87) |
| 6 | 0.0091 (2.94) | 0.0510 (2.92) | 18 | −0.0056 (−2.19) | 0.0701 (2.68) | 30 | −0.0030 (−1.31) | 0.0373 (0.77) |
| 7 | 0.0134 (4.98) | 0.0644 (3.32) | 19 | −0.0026 (−1.14) | 0.0675 (2.75) | 31 | −0.0001 (−0.06) | 0.0372 (0.74) |
| 8 | 0.0115 (4.16) | 0.0759 (3.60) | 20 | −0.0032 (−1.35) | 0.0642 (2.73) | 32 | 0.0008 (0.41) | 0.0380 (0.73) |
| 9 | 0.0085 (3.07) | 0.0844 (3.73) | 21 | −0.0032 (−1.32) | 0.0611 (2.55) | 33 | 0.0013 (0.62) | 0.0394 (0.73) |
| 10 | 0.0048 (1.69) | 0.0892 (3.74) | 22 | −0.0034 (−1.39) | 0.0577 (2.21) | 34 | 0.0008 (0.36) | 0.0402 (0.71) |
| 11 | 0.0045 (1.55) | 0.0938 (3.77) | 23 | −0.0011 (−0.45) | 0.0566 (1.93) | 35 | 0.0010 (0.45) | 0.0412 (0.71) |
| 12 | 0.0013 (0.43) | 0.0951 (3.67) | 24 | −0.0010 (−0.40) | 0.0556 (1.69) | 36 | −0.0005 (−0.24) | 0.0406 (0.67) |

Month 1 is slightly negative (short-term reversal), months 2-9 strongly positive, the cumulative return peaks at 9.51% after 12 months, and more than half of it is lost by month 36. The event-time beta of P10−P1 rises from −0.20 to 0.02 against the VW index (p. 84). Footnote 17: the whole negative return after the first year occurs in Januaries.

### Table VIII, Back-test before 1965 (pp. 86-87)

- 1927-1940: month 1 is −4.95% (t = −3.72); cumulative return reaches −40.81% by month 36 (t = −2.01). The paper blames very high loser betas and market mean reversion: in July 1932 the 6/6 strategy lost 40% and in August 1932 lost 68% as the market rebounded (p. 85). This is the **momentum crash** pattern.
- 1941-1964: similar to 1965-89; cumulative 5.83% at month 12 (t = 3.40), dissipating almost entirely by month 24 (0.50%).

### Table IX, Earnings announcement returns, 1980-1989 (p. 88)

Three-day (days −2 to 0) announcement return of winners minus losers: positive and significant in months 1-6 (0.55% to 0.90%), negative in months 11-18 (about −0.7% on average, e.g. −0.97%, t = −5.75, in month 16), near zero later. Announcement returns account for about 25% of the zero-cost return over the first six months (p. 88).

## 5. Conclusions (pp. 89-90)

- Buying past winners and selling past losers earned significant abnormal returns in 1965-1989; the 6/6 strategy earned a compounded excess return of **12.01% a year**.
- The profits are not explained by systematic risk or lead-lag effects; they are consistent with delayed reaction to firm-specific information.
- Half of the first year's excess return dissipates over the following two years, and earnings-announcement returns show the same rise and fall, so neither simple underreaction nor overreaction fits. Positive-feedback trading (De Long et al. 1990), or underreaction to short-term and overreaction to long-term news, are offered as explanations the paper cannot tell apart.

## 6. Points that matter for the Indian replication

1. **Universe rule:** a stock only needs J months of returns before formation. There is no price, size or liquidity filter, so microcaps dominate the extreme deciles (Table II shows P1 and P10 are the smallest).
2. **Delistings:** the paper does not say how delisting returns are handled.
3. **Weighting:** equal weights rebalanced monthly within each cohort; cohorts weighted 1/K.
4. **Skip-a-week:** defined only loosely; our data are daily, so a 5-trading-day skip can be built exactly.
5. **t-statistics:** plain t for Table I; Newey-West for cumulative returns. ResearchRules require Newey-West throughout, so our t-statistics will be somewhat lower than plain ones.
6. **Costs:** the paper's only cost test is a flat 0.5% one way on a risk-adjusted return; we will use full Indian costs.
7. **Short side:** the paper assumes free shorting of any stock. Table III Panel B suggests most of the alpha is on the long side, which favours a long-only Indian version.
8. **Seasonality:** January matters in the US because of tax-loss selling; the Indian financial year ends in March, so we should test March/April instead of (or as well as) January.
9. **Main exhibits to reproduce:** Table I (both panels, 32 strategies), Table III (deciles, size groups, CAPM alpha), Table IV and V (calendar months), Table VI (subperiods), Table VII (36-month event time), plus the turnover and after-cost result. Table VIII (pre-1965) has no Indian counterpart in our data; Table IX needs earnings dates and is optional.
