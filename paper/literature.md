# The work around Jegadeesh and Titman (1993)

Gathered with the literature_scout subagent on 2026-10-31 and checked where possible. Items marked UNVERIFIED are known only from titles or search snippets; their findings must be read in full before they are cited as evidence.

## Follow-ups on US and international data

| Work | What it adds | Status |
|---|---|---|
| Jegadeesh, N., and Titman, S. (2001). Profitability of Momentum Strategies: An Evaluation of Alternative Explanations. *Journal of Finance* 56(2), 699-720. https://doi.org/10.1111/0022-1082.00342; NBER WP w7159 | Out-of-sample follow-up to the 1993 paper | Findings UNVERIFIED by us; working paper open |
| Lesmond, D., Schill, M., and Zhou, X. (2004). The Illusory Nature of Momentum Profits. *Journal of Financial Economics* 71(2), 349-380. SSRN 256926 | The main trading-cost critique | Findings UNVERIFIED by us |
| Daniel, K., and Moskowitz, T. (2016). Momentum Crashes. *Journal of Financial Economics* 122(2), 221-247. NBER WP w20439 | Momentum crashes in "panic" states, after market declines and when volatility is high; crashes are partly forecastable | Abstract verified; working paper open |
| Hou, K., Xue, C., and Zhang, L. (2020). Replicating Anomalies. *Review of Financial Studies* 33(5), 2019-2133. Open PDF at global-q.org | Many anomalies weaken once microcaps are controlled with NYSE breakpoints and value weights | Approach verified from snippet; momentum numbers not read |
| Rouwenhorst (1998), Korajczyk and Sadka (2004), Novy-Marx (2012), Asness, Moskowitz and Pedersen (2013) | International momentum, capacity, intermediate-horizon momentum, momentum across asset classes | Not yet searched; no citation given |

## India

| Work | What it found | Status |
|---|---|---|
| Sehgal, S., and Balakrishnan, I. (2002). Contrarian and Momentum Strategies in the Indian Capital Market. *Vikalpa* 27(1), 13-20. https://doi.org/10.1177/0256090920020103 | Short-term momentum in Indian stocks; long-term reversal once a one-year gap is left | Snippet only |
| Ansari, V. A., and Khan, S. (2012). Momentum Anomaly: Evidence from India. *Managerial Finance* 38(2), 206-223. https://doi.org/10.1108/03074351211193730 | Strong momentum in India (as reported by citing papers) | UNVERIFIED; paywalled |
| Maheshwari, S., and Dhankar, R. S. (2017). Momentum Anomaly: Evidence from the Indian Stock Market. *Journal of Advances in Management Research* 14(1), 3-22 | Short-run momentum strategies still persist and can earn profits | Snippet only; paywalled |
| Agarwalla, S. K., Jacob, J., and Varma, J. R. (2013). Four Factor Model in Indian Equities Market. IIMA W.P. 2013-09-05. SSRN 2334482; and (2017) Size, Value, and Momentum in Indian Equities, *Vikalpa* 42(4), 211-219 | Indian Fama-French and momentum factors | Open |
| IIMA data library, https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/ (read by us on 2026-10-31) | Release 2025-12 covers October 1993 to December 2025, BSE and NSE stocks from CMIE Prowess DX, total returns. **WML: 10.65% a year (annualised geometric) since 1 January 1994**; market premium 4.93%, SMB −3.71%, HML 6.61%. The new series drops stocks with market cap below 10% of the median and median price below ₹1 (26.8% of stocks in 2020-21), and recommends survivorship-bias-adjusted files for 1995-2000 | Verified; free monthly factor files. **Our benchmark for the Indian winners-minus-losers result** |
| NIFTY200 Momentum 30 index (NSE Indices factsheet and methodology) | Top 30 of the NIFTY 200 by a score of 50% 12-month and 50% 6-month volatility-adjusted return z-scores, with a rank buffer to cut turnover | From fund-house documents; weights, caps and rebalancing dates to be checked in the Adapt stage. **A tradable long-only momentum benchmark** |
| SEBI discussion paper on short selling and securities lending, https://www.sebi.gov.in/sebi_data/commondocs/rep40_p.pdf | Only covered short selling is allowed; stock lending (SLB) volumes are tiny and shorting is practical only through single-stock futures on the F&O list | To be checked against current SEBI circulars in the Adapt stage |

Leads not yet read: "Risk-Managed Momentum: An Evidence from Indian Stock Market" (2021, https://doi.org/10.1177/23197145211023001); "Taming momentum crashes through triple momentum investing" (*Journal of Public Affairs*, 2020, https://doi.org/10.1002/pa.2525); Devulapally and Tripurana (2023), arXiv 2302.13245, physical momentum on the NSE 500.

## What this means for the study

1. Indian studies from 2002 to 2017 and the IIMA factor library agree that medium-term momentum exists in Indian shares; the IIMA WML series gives an independent check on our long-short result.
2. Microcaps and penny stocks can create paper profits that cannot be captured (Lesmond et al.; Hou, Xue and Zhang). We should report a paper-faithful all-stocks universe and an investable one with size, price and liquidity filters.
3. Shorting in India is limited to F&O stocks through futures, so the long-short version is mainly a research result; the long-only winners portfolio is the one that can be traded, and the NIFTY200 Momentum 30 index is its natural benchmark.
4. Momentum crashes (Daniel and Moskowitz; Table VIII of the paper itself) mean drawdowns, especially around the March 2020 crash and rebound, deserve their own reporting.
