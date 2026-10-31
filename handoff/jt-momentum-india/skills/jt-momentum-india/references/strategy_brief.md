# Strategy brief: 6-month momentum in India's 500 most traded shares (Jegadeesh and Titman, 1993)

This brief explains a long-only equity strategy so that a trader who has not read the paper can rebuild it. It comes from a study that recreated Jegadeesh and Titman's relative-strength strategies on NSE shares from 2005 to 2026, run under the study's own code and reviewed by an adversarial checker.

## Summary

Each month, rank the 500 most traded NSE shares on their return over the past six months, buy the top tenth (about 50 shares) in equal weights, and keep each month's purchase for six months. At any time the portfolio is six overlapping monthly cohorts of one sixth each, so about one sixth of it changes every month. In the backtest from January 2005 to October 2026 this earned 1.75% a month after Indian costs (Newey-West t-statistic 3.16), against 1.34% a month for the Indian market. The excess over the market is 0.40% a month (t 1.51, not significant) because the portfolio carries a market beta of 1.18; against the NIFTY 500 since March 2012 it earned 0.76% a month more (t 2.23), a compound 21.9% a year against 13.2%, with a worst drawdown of 40% against 29%. It is a long-only, delivery-only strategy that needs no shorting. Treat it as a return-seeking equity sleeve with more risk than the index, not as a market-neutral edge.

## Universe

- **Shares:** NSE company shares in the EQ, BE and BZ series. Exchange traded funds, rights entitlements and partly paid shares are removed. In UBI's master the symbols carry no type field, so the script removes symbols that end in -RE, end in BEES, contain ETF or start with LIQUID, GILT, NIFTY or SENSEX, and any symbol UBI lists in its funds segment. Add other fund symbols with the script's --exclude option.
- **Eligibility each month-end:** the share traded in the last five trading days and its last close is at least 10 rupees.
- **The 500:** of the eligible shares, the 500 with the highest median daily traded value (close times volume) over the previous 126 trading days, counting days without trading as zero. Median traded value in the study's data was between about 40 and 60 crore rupees a day for the average member of the top deciles.
- **Size:** 500 shares.
- **Suspect prices:** a share with a one-day move below -45% or above +100% anywhere in the last 12 months is left out, because it usually means a split or bonus that the price file has not adjusted. The script lists these.

## Signal

- **Score:** the share's price return over the last six months, from the close of the last trading day of the month six months earlier to the close of the last trading day of this month, using closes adjusted for splits and bonuses. Dividends are ignored; the study used total returns, and the difference in ranks is small.
- **No skip:** the study found that waiting a week after ranking raised returns slightly, but not enough to matter after costs, so the signal uses the last close of the month and trading happens at the next session.
- **Data needed:** about 13 months of daily closes and volumes for every NSE share, adjusted for splits and bonuses.

## Portfolio construction

- Cut the 500 into ten equal groups by the score. The top group is the winners, about 50 shares.
- Within a month's cohort, each winner gets an equal weight. The portfolio holds six cohorts, the last six month-ends, with one sixth of the money each, so a share chosen in several months has several parts and the largest holding is about 2% of the portfolio.
- Typical size: about 120 different shares (104 to 165 in the backtest); the largest single weight in the latest build was 2.06%.
- No sector or beta constraint was used in the study.

## Rebalancing

- **When:** once a month, on the first trading day after a month ends, once UBI holds the previous month's last prices. Backtested trading was at the close of the last day of the month; trading a day later gave the same result (1.74% a month after costs, t 3.13).
- **How:** build the new targets, drop the cohort chosen six months ago, add the cohort chosen at the month-end just finished, and trade the difference. The script prints the joiners, the leavers and the one-way turnover against last month's file.
- **Turnover:** about 16% of the portfolio is sold and 16% bought each month (two-way turnover 0.32), because one sixth of the cohorts is replaced.
- **A share that stops trading:** the script drops it from the cohort and shares its weight among the other members. In a halt or delisting the loss is not captured by this rule; the study's stress, charging -30% or -100% to every share in the month after its last trade, cut the return by 0.03% to 0.10% a month.

## Backtest results

Holding months January 2005 to October 2026, 262 months, top-500 universe, J = 6, K = 6, long only, after Indian delivery costs (STT 0.1% each side, stamp duty 0.015% on purchases, exchange and SEBI charges with GST, market impact 0.1% per side, zero brokerage). Market is the IIMA value-weighted Indian market total return.

| | Strategy | Market (IIMA) |
|---|---|---|
| Average return a month, before costs | 1.82% (Newey-West t 3.28) | |
| Average return a month, after costs | 1.75% (t 3.16) | 1.34% |
| Compound annual return, after costs | 18.2% | 14.7% (252 months) |
| Excess over the market a month | 0.40% (t 1.51) | |
| Alpha a month (CAPM, risk-free subtracted) | 0.25% (t 1.07) | |
| Beta | 1.18 | 1 |
| Volatility a year | 28.4% | |
| Sharpe ratio (risk-free subtracted) | 0.52 | |
| Worst drawdown | -74.2% (2008) | -61.9% |
| Costs a month | 0.07% of the portfolio | |
| Turnover a month, two-way | 0.32 of the portfolio | |

Since March 2012, 176 months, against the NIFTY 500 (price return plus a twelfth of its dividend yield): strategy 21.9% a year, index 13.2%; excess 0.76% a month (t 2.23); alpha 0.63% a month (t 2.06); worst drawdown -40.4% against -28.8%.

By period, average return a month before costs: 2005 to 2009 1.99% (t 1.33), 2010 to 2014 1.39% (t 1.72), 2015 to 2019 1.07% (t 1.18), 2020 to 2026 2.56% (t 3.15). The portfolio lost money in eight calendar years: 2008 (-71%), 2011 (-25%), 2013 (-8%), 2016 (-11%), 2018 (-21%), 2019 (-1%), 2022 (-1%) and 2025 (-5%).

Robustness for the top-500 winners: brokerage of 0.03% a side, 1.74% a month after costs; trading one day later, 1.74%; -100% charged to every share after it stops trading, 1.65%; top 200 instead of top 500, 1.53% (t 2.82).

## Risks and caveats

- **Deep drawdowns.** The portfolio lost 74.2% from December 2007 to February 2009 (the market lost 61.9%), and 40.4% from April 2018 to March 2020 (the NIFTY 500 lost 28.8%). It has a beta of 1.18 and a volatility of 28% a year, about 1.3 times the market's. In 2009, when beaten-down shares rebounded, it gained 62% against the market's 94%. In the study's long-short version that rebound cost 49% in a single month; the long-only version avoids that loss but lags in a rebound.
- **The edge over the market is small.** After subtracting the risk-free rate and market beta, the monthly alpha is 0.25% (t 1.07) over 2005 to 2026. Most of the extra return is the cost of carrying more market risk. Against the NIFTY 500 since 2012 it is clearer (0.63%, t 2.06).
- **Period dependence.** The first half of the sample is statistically weak; returns were strongest in 2020 to 2026.
- **Not market neutral.** A version hedged with NIFTY 50 futures earned 1.05% a month after costs from 2012 with a worst drawdown of 32% (t 2.65), but it needs futures margin and rolls.
- **Data caveats.** Prices before 2006 were repaired from price jumps; UBI's adjustment factors are wrong for some shares (gap 32), which is why the script drops shares with suspect moves. UBI's price series ignores dividends. UBI holds only shares listed today, so a live run is never affected by delisted shares but the script cannot protect against a halted share.
- **Costs assumed.** Brokerage zero and market impact of 0.1% a side. Depository charges (about 15 rupees plus GST per share sold) and the bid-ask spread of thinner shares are not modelled.
- **How many variants.** The study ran 192 strategy series and about 150 more checks. The 6/6 strategy was chosen as the lead in advance because it is the paper's main strategy; shorter holding periods such as 12/3 look better in the backtest but were not chosen, to avoid selecting the best cell.
- **Whole shares.** With 118 targets, 10 lakh rupees invests only 87.5% in whole shares; 25 lakh invests 94.5% (see the capital minimum in SKILL.md).

## Sources

- Jegadeesh, N., and Titman, S. (1993). Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency. *Journal of Finance*, 48(1), 65-91. https://doi.org/10.1111/j.1540-6261.1993.tb04702.x
- The study: https://github.com/pramodathani/Research-Paper-Jegadeesh-Titman-Momentum-India and its companion page https://tradingmachine.co.in/papers/jegadeesh-titman-momentum-india/
- Data: NSE daily price files (bhavcopies), corporate actions and index files from NSE's public archives; the Indian four-factor library of Agarwalla, Jacob and Varma (IIM Ahmedabad) for the market return and risk-free rate; UBI through tradingmachine for the live script.
