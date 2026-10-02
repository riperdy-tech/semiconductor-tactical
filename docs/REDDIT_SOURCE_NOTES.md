# Reddit Source Notes

## Primary source

- URL: https://www.reddit.com/r/wallstreetbets/comments/1wtmanz/made_550k_in_90_days_cant_stop_wont_stop/
- Post date: 2026-09-29
- Accessed for research: 2026-10-02

## Directly observable claims from the post/comments

The author says that they:

- made about **$550k over 90 days**;
- executed **1,300+ trades**;
- traded **SNDK, MU, and SKHY**, describing the activity as scalping and swing trading;
- began using **short-dated covered calls during strength and buying them back on pullbacks**;
- used **stop limits** and traded frequently because the names can move substantially;
- held large positions in MU/SNDK/SKHY plus **2× ETFs**, using margin;
- also traded SKHY/Kioxia-related exposure outside U.S. regular hours;
- said they had experienced losses and avoided margin calls;
- described the process as watching charts, identifying trends, and deciding when to enter/exit.

The author also replied that the $1.2m figure they discussed was net liquidation value after margin debt and said they had withdrawn $220k in cash. These are self-reported comments, not broker-verified statements.

## What is NOT specified well enough to copy literally

The source does not provide a complete deterministic rule set for:

- entry trigger;
- exact pullback threshold;
- exact profit target;
- exact stop distance;
- position sizing formula;
- maximum leverage;
- precise covered-call strike selection;
- exact DTE at call sale;
- exact option delta target;
- exact repurchase trigger;
- treatment around earnings;
- exact universe of 2× ETFs;
- exact execution costs;
- exact historical account equity curve.

Therefore the repository must not pretend that a single "Reddit strategy" has been recovered. Instead, we test a **family of plausible mechanical approximations**.

## Interpretation rules

`OBSERVED`: what the author says.

`DERIVED`: e.g. high turnover + high-beta names + frequent exits implies capital recycling is a major component of the reported P&L.

`HYPOTHESIS`: e.g. buying a statistically extreme pullback inside a still-positive sector trend is a plausible approximation of the author's discretionary chart reading.

`ASSUMPTION`: any exact threshold we have to choose for the first backtest.

## Important warning about the headline result

The $550k result is an observed self-report, not evidence that the strategy has a persistent edge. The historical period may have been unusually favorable for the selected securities, and capital, margin availability, leverage, turnover, skill, timing, and survivorship may all contribute.

The project's job is to falsify easy explanations before declaring an edge.
