# site/app.js

- The snapshot stores gross and net monthly returns of every strategy at the default costs, plus each leg's monthly turnover. When the reader changes market impact or brokerage, the page adjusts net returns by turnover times the change (brokerage times 1.18 for GST). Impact and brokerage are linear in traded value in the engine's DeliveryCosts, so this matches the engine: all shares at 0.6% impact shows 1.16% (t 2.77) on the page against 1.16% (t 2.78) from the engine.
- The long-short's turnover is the sum of the two legs' turnover, computed in the page to keep the snapshot under 1 MB.
- Newey-West t follows statsmodels' HAC on a constant: Bartlett weights, automatic lag floor(4(T/100)^(2/9)), and the n/(n-1) small-sample factor. Encoding returns in basis points moves some t-statistics by 0.01.
- Colours follow the user's request for Google colours (blue #4285f4, red #ea4335, yellow #fbbc05, green #34a853), not the skill's default blue and orange. Positive numbers stay black; only negatives are red.
- The URL hash holds the state, such as #j12-k3-skip1-all-ls-gross, and only lists impact, brokerage, fee and sample when they differ from the defaults.
