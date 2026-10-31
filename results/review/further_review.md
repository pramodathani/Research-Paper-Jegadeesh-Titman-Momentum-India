# Review of the further results (Section III, joint tests, buy-and-hold, event-time betas, January reversal)

Reviewed 2026-10-31 by backtest_reviewer. No source files were changed. Scratch scripts are in /tmp/rv/.
Tests: `pytest -q` gives 94 passed.

## Verdict: sound with caveats
The formulas are correct. The U1 decomposition is not a coding bug: one uninvestable share (SELMC) dominates it, so it should not be published as it stands.

## Findings (most serious first)

1. **The U1 decomposition is driven by one share, SELMC.** SELMC's monthly returns were +188%, +185%, +164%, +165%, +178% and +107% from 2021-11 to 2022-04. That gives a single 6-month period return of 328.8 (+32,880%) in offset 4. Its beta is 318 and its residual serial covariance is 686.
   - With all shares: beta variance 8.53, factor 0.0605, idiosyncratic 0.0493, dispersion -0.0997.
   - Betas trimmed at the 1st and 99th percentiles: beta variance 0.257.
   - SELMC dropped: total 0.0106, dispersion 0.0101, factor 0.0044, idiosyncratic -0.0039, beta variance 0.65.
   - SELMC, EQUIPPP, ORCHPHARMA and JITFINFRA dropped: dispersion 0.0113, factor 0.0021, idiosyncratic -0.0024, beta variance 0.31.
   - The data look genuine rather than broken. Most daily moves were circuit steps of about +5% (largest +9.9%, about -2% steps in May 2022), and the close went from ₹4.95 on 2021-10-28 to ₹1,881. But traded value was only ₹49.50 on 2021-10-28, so the move could not have been traded, and the ±50%/+100% daily screen (gap 6) never catches it.
   - SELMC also takes up to 62% of the WRSS long side (2022-04). The WRSS mean barely moves without it: 0.0684 → 0.0708 per 6 months.
   - U2 has no such outlier (largest 6-month return 13.0) and is sensible: beta variance 0.30, factor 0.00002, idiosyncratic 0.0021, dispersion 0.0050.
   - **Action:** report U2 as the main decomposition. For U1, either apply a liquidity floor (U1 admits shares trading ₹50 a day) or winsorise the 6-month period returns before estimating betas and residuals. Report the SELMC-excluded figures as a sensitivity. Capping monthly returns at the 99.9th percentile is not enough (dispersion -0.0028).

2. **The decomposition estimator is fragile by construction** (profit_sources.py:152-240).
   - The dispersion term is the remainder (total − factor − idiosyncratic), so all estimation noise lands in it.
   - The "total" uses only shares present in both consecutive periods. The beta and residual terms use any share with 10 or more non-overlapping periods. These are different share sets.
   - The first period of each offset is not masked by eligibility (line 167, `np.ones`). This lets in 34-43 ineligible shares per offset, which enter both the equally weighted index and the regressions.
   - **Action:** mask row 0 with eligibility at the start of its period, use one share set for all three terms, and add a test with one extreme share.

3. **The January reversal is computed correctly** (make_further_results.py:376).
   - The returns are flipped in January only: `series.where(month != 1, -series)`.
   - I recomputed the CAGR as (Π(1+r))^(12/262) − 1. U1 6/6 gives normal 0.18477 and reversed 0.14630; U2 6/6 gives 0.15223 and 0.09161. All match the CSV.
   - The mean check also holds: normal mean − reversed mean = 2 × 22 × 0.016395 / 262 = 0.002753, which equals 0.016355 − 0.013602.
   - The finding is that the Indian January spread is positive (U1 +1.6%, U2 +2.7%), so the reversal loses in 16-18 of 22 Januaries. This is a market difference from the US, not a bug.
   - Caveat: compounding a zero-cost spread as if it were a fully invested return is a presentation choice. The means and alphas are the cleaner comparison.

4. **The lead-lag regression matches the paper's specification (p. 75)** (profit_sources.py:263-292).
   - The regressor is the demeaned value-weighted (IIMA mf+rf, decimals) return over the 6 months ending at the formation month, i.e. the ranking window t−6..t−1. There is no look-ahead.
   - The dependent variable is the 6-month holding return of that formation month. The standard errors are HAC with 6 lags.
   - Results: θ = −0.84 (t −1.97) for WRSS and −1.14 (t −1.89) for deciles in U1. The paper reports −2.29 (t −1.74) for deciles and −1.77 (t −3.56) for WRSS.
   - It uses 252 rather than 256 months because the IIMA file ends 2025-12, so formation months from 2026-01 are dropped silently.
   - The halves are demeaned with the full-sample mean. This is minor.
   - **Action:** state the 2025-12 end in the CSV or README.

5. **The WRSS is correct** (lines 69-98). Weights are past return minus the eligible equally weighted average, scaled to one rupee long, as in the paper's "per dollar long". The holding window is months t+1..t+6, and ranking uses data up to t. Mean 6.8% semiannual (Newey-West t 3.34); correlation with the decile strategy 0.93 (paper: 4.5%, t 2.99, correlation 0.95).

6. **The Hotelling and GRS tests are correct** (joint_tests.py).
   - Hotelling uses F = (n−p)/(p(n−1))·T² with p = 9 and df (9, n−9). On simulated data it gives the same F as a different contrast basis (1.0920 both ways), as it should.
   - GRS uses (T−N−1)/N · α'Σ⁻¹α/(1+μ²/σ²) with maximum-likelihood Σ and σ². This is algebraically identical to GRS (1989) with the unbiased Σ.
   - Both run on 2005-01..2025-12 because the market series ends there; the risk-free rate is forward-filled after that.

7. **Buy-and-hold is correct** (buy_and_hold.py). Cohorts formed at m−K..m−1 are averaged in month m, and each cohort drifts from equal weights. It is slightly above rebalanced in all 32 cells (U1 6/6: 1.79% vs 1.64%), which matches the paper's p. 68 remark. Missing returns count as zero, so delisting proceeds stay in the share.

8. **Event-time betas are correct** (event_time_returns.py:80-103). I recomputed the lag-1 beta by hand at −0.2379, matching the CSV, with 251 months. The t-statistics are plain OLS, which is fine because each lag's series does not overlap.
   - Minor: in `winners_minus_losers`, a lag with a missing spread adds 0 to the running cumulative (`nan_to_num`, line 131).

9. **The flat-cost test is correct.** Leg turnover is bought plus sold (backtest_result.py:61), so `0.005*(buy+sell)` charges 0.5% per rupee traded per rupee of one leg. The 6/6 one-way turnover is about 1.00 per 6 months, which is plausible.
