---
name: jt-momentum-india
description: Use when building or rebalancing the monthly long-only momentum sleeve in Indian shares, which holds the winners among the 500 most traded NSE shares over the past six months in six overlapping monthly cohorts. Gives the strategy, the command that builds each month's target weights, suggested risk limits, the capital minimum and the backtest results.
---

# Jegadeesh and Titman momentum, long only, NSE top 500

## Strategy

Shares that have risen most over the past six months have tended to keep outperforming over the next six. Jegadeesh and Titman (1993) found this in US stocks; a study recreating it on NSE shares from 2005 to 2026 found it in India too, and this skill turns the part of it that a delivery-only Indian investor can hold.

- **Universe:** the 500 NSE company shares with the highest median daily traded value over the last 126 trading days, with a last close of at least 10 rupees. Funds and rights entitlements are removed.
- **Signal:** each share's price return over the last six months, month-end to month-end.
- **Portfolio:** at each month-end, rank the 500 on that return and take the top tenth, about 50 shares, in equal weights. Hold each month's choice for six months. The portfolio is therefore six overlapping cohorts of one sixth of the money each, about 120 different shares, with the largest weight about 2%.
- **Rebalance:** once a month, on the first trading day after a month ends, when UBI holds the last prices of that month. About 16% of the portfolio is sold and 16% bought each month.
- **Long only, delivery (CNC) only.** The paper's short leg cannot be held in Indian cash shares, so this skill does not use it.

The full explanation, with the formulas, risks and sources, is in `references/strategy_brief.md` (and the same as a page in `references/strategy_brief.html`). The paper is Jegadeesh and Titman (1993), *Journal of Finance* 48(1), 65-91. The study, its code and its results are at https://github.com/pramodathani/Research-Paper-Jegadeesh-Titman-Momentum-India, with an interactive page at https://tradingmachine.co.in/papers/jegadeesh-titman-momentum-india/.

This is a return-seeking equity strategy with more risk than the index, not a market-neutral edge: its beta against the Indian market was 1.18 and its alpha over 2005 to 2026 was not significantly different from zero.

## Monthly target command

```
python scripts/build_targets.py targets_2026-11.csv --previous targets_2026-10.csv --capital 2500000
```

- **Needs:** Python with pandas and numpy, and `tradingmachine` configured for UBI, which trading-agent's sandbox has. The script reads UBI's NSE equity master and the daily candles of every listed share in batches, adjusted for splits and bonuses, for about 15 months.
- **When:** on the first trading day after a month ends, after UBI holds that month's last prices. The script refuses to run if the data stops more than four days before the end of the last completed month, and says so. Run it for the month you are in, or use `--as-of YYYY-MM-DD` to rebuild a past month.
- **Writes:** the CSV named first, with columns `symbol,weight`, sorted from the largest weight, with weights adding up to 1.
- **Prints:** the month, the number of holdings, the largest weight, the size of each cohort, the shares left out for suspect price moves, the joiners and leavers against `--previous`, and the one-way turnover. With `--capital` it also prints how much of that capital whole shares can invest and how many targets round to zero shares.
- **Options:** `--prices-file` reads a parquet or CSV with columns `symbol,date,close,volume` instead of UBI, for testing; `--exclude SYMBOL ...` keeps shares out, which is how to remove an exchange traded fund the script's name patterns missed.
- **Time:** building the targets from a prices file of three million candles takes about two seconds; the fetch from UBI comes on top and was not timed, because UBI cannot be reached from the research sandbox where the script was written.
- **It never places, modifies or cancels orders.** Trading-agent's desks decide what to trade.

The first run should be checked by hand against the printed summary: around 100 to 140 holdings, a largest weight near 2%, six cohorts of about 45 to 50 shares, and a one-way turnover of 10% to 20% against last month's file. The script was tested to give exactly the study's weights on a made-up market. On real UBI candles it gave 118 holdings for October 2026, and 92% of its weight (109 of 118 shares) matched the study's own portfolio for that month, which is built from NSE data with dividends; the rest differs because of dividends and errors in UBI's adjustments.

## Risk limits

These are suggestions for the user to put into trading-agent's TradingRules.md; the study did not impose them.

- **Per share:** at most 3% of the portfolio. The script's largest weight is about 2.1%, when a share is chosen in all six cohorts.
- **Per sector:** at most 25%. The study had no sector data and imposed no limit, so check sector weights by hand the first few months.
- **Holdings:** expect 100 to 140. Treat fewer than 60 or more than 200 as a data fault and stop.
- **Order size:** at most 2% of a share's median daily traded value.
- **Turnover:** at most 40% two-way in a month; the backtest average is 32%.
- **Leverage and derivatives:** none; delivery only, no margin.
- **Drawdown:** the portfolio lost 74% from December 2007 to February 2009 and 40% from April 2018 to March 2020. Suggest a review with the user at 25% below the portfolio's previous peak, and no new monthly buying at 45% below it until the user decides.
- **Hedge option:** selling NIFTY 50 futures against the portfolio cut the worst drawdown to 32% in the study, for a lower return (1.05% a month after costs against 1.75%) and with margin needs; it is the user's choice.

## Capital minimum

About 118 to 125 shares are held, and the smallest weight is about 0.35% of the portfolio (one sixth of a cohort of 48 shares). Whole shares then decide the minimum:

- **₹10 lakh:** the smallest position is about ₹3,500, and 10 of 118 targets round to zero shares because their price is too high, so 87.5% of the money is invested. This is the lowest workable capital, with about 12% left in cash.
- **₹25 lakh:** the smallest position is about ₹8,700, 2 of 124 targets round to zero, and 94.5% is invested. This is the suggested starting capital.
- **Costs that do not scale:** depository charges on every share sold, about ₹15 plus GST, come to about 20 sales a month, around ₹350, or 0.04% of ₹10 lakh a month; the study's cost model does not include them.

Below ₹10 lakh the whole-share rounding and the fixed charges make the portfolio different from the one backtested.

## Backtest summary

Top-500 universe, J = 6, K = 6, long only, after Indian delivery costs (STT, stamp duty, exchange and SEBI charges, GST, market impact of 0.1% per side, zero brokerage). Holding months January 2005 to October 2026, 262 months.

| | Strategy | Benchmark |
|---|---|---|
| Average return a month, after costs | 1.75% (Newey-West t 3.16) | IIMA market 1.34% |
| Compound annual return | 18.2% | 14.7% (252 months to December 2025) |
| Excess return a month | 0.40% (t 1.51) | |
| Volatility a year | 28.4% | |
| Sharpe ratio, risk-free subtracted | 0.52 | |
| Worst drawdown | -74.2% | -61.9% |
| Turnover a month, two-way | 0.32 | |
| Costs a month | 0.07% | |

Since March 2012 against the NIFTY 500 (price return plus a twelfth of its dividend yield), 176 months: 21.9% a year against 13.2%, excess 0.76% a month (t 2.23), alpha 0.63% a month (t 2.06), worst drawdown -40.4% against -28.8%. More tables are in `references/backtest_summary.md`.

**Review:** the backtest was checked by an adversarial reviewer on 31 October 2026, who found no look-ahead or coding error and reproduced the results exactly. Problems it found, such as real crashes mistaken for splits, were fixed before these numbers were produced.

**Main caveats:**
- The excess return over the market is not statistically significant over the whole sample, because the portfolio carries more market risk.
- The first half of the sample is weak statistically (2005 to 2015, t about 1.8 after costs).
- The study ran 192 strategy series and about 150 more checks; the 6/6 strategy was chosen in advance, and better-looking cells such as 12/3 were not used.
- Backtest prices include dividends and delisted shares; UBI's do not, so live rankings use price returns and a small set of data errors in UBI's adjustments is handled by dropping shares with suspect moves.
- Brokerage was assumed zero and depository charges are not modelled.
