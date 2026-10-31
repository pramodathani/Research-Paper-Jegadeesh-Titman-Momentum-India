# Review of JT momentum India (backtest_reviewer, 2026-10-31)
Written in scratch_review/ because the analyst's task allowed writes only there or /tmp.
## Check 1 look-ahead / code
- Reproduced grid U2 6/6 LS gross 1.5434%, net 1.4031% exactly with own OverlappingCohorts+Backtest run.
- Weights sum to 1 every held month 2005-01..2026-10, unpriced weight 0.
- Hand recompute 2015-03 winners gross 3.4811% = engine.
- Universe/liquidity/ranking use data up to formation close (inclusive); holding month = next calendar month. Cohorts p-K..p-1. OK.
- Membership conditions on having a return in holding month: 0.27% of member-months (210 of 76,630 winners, 213 of 78,076 losers) dropped.
## Check 2 survivorship: bhavcopies keep delisted shares; robustness_checks.csv -100% stress: U2 6/6 LS 1.541% (vs 1.543), U1 rises to 1.99% (losers delist more). Reasonable.
## Check 3 data: RELIANCE 2024-10-28 +0.49%, INFY 2014-12-02 -2.2%, HDFCBANK 2019-09-19 +0.66% correct. Dividends included (COALINDIA 2023 total 77.5% vs price 67.3%).
Flags 990 zeroed + 646 inferred, concentrated pre-2006 (2001: 363). In held U2 6/6 months: winners 28 inferred + 29 zeroed; losers 14 + 5.
Errors found: UNITECH 2008-10-24 real crash 61.6->31.0 (-49.7%) inferred as 1:2 split -> +0.6%; YESBANK 2020-03-06 real -56% zeroed. Both in losers; both bias against momentum.
Held stock-months >100%: winners 17 of 33,079, losers 52 of 34,007; none >200%.
## Check 4/6: see fragility.csv. Double impact: U2 net 1.403->1.337; U1 net 1.470->1.270 (t 3.01).
## Check 5: 64 LS cells, 49 gross NW t>3.16 (Bonferroni 64). 6/6 pre-specified (plan line 128).
## Tests: 70 passed.
## Verdict: sound with caveats. Main caveats: short leg not tradable as costed; size/liquidity fragility (top200 1.13%, t 2.5); 2005-2009 weak (0.90%, t 0.64) and first half t 2.14; a few real crashes neutralised by the split inference/zeroing (bias against momentum).
