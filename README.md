# High-Beta Tactical Research Engine

Research/backtesting repository for testing a systematic approximation of the trading behavior described in the Reddit post:

> https://www.reddit.com/r/wallstreetbets/comments/1wtmanz/made_550k_in_90_days_cant_stop_wont_stop/

The target behavior is **not copied as a claimed winning strategy**. It is decomposed into testable components:

1. high-beta semiconductor / adjacent-equity universe;
2. frequent short-horizon directional trades around pullbacks and rebounds;
3. short-dated covered-call harvesting during strength and repurchase on pullbacks;
4. optional leverage / margin simulation;
5. optional 2× semiconductor ETF exposure;
6. explicit risk, slippage, liquidity, and margin-call modeling.

The repository is deliberately separate from `rs2-local`. RS2 may provide an **optional regime input adapter**, but this engine must remain runnable without RS2.

## Non-negotiable research principles

- Deterministic signal generation. Do not put an LLM in the trading signal path.
- No look-ahead bias.
- No survivorship bias in the universe or corporate-action handling.
- No use of future option-chain information.
- Every simulated fill has a documented execution rule.
- Every result records data provenance, parameter values, code revision, and assumptions.
- The default mode is historical research / paper simulation. Live trading integration is out of scope until a separate, explicit specification exists.
- A backtest may report an attractive result, but the system must also report drawdown, tail loss, margin utilization, turnover, costs, and regime dependence.

## Repository truth hierarchy

1. `AGENTS.md` — implementation rules for coding agents.
2. `docs/STRATEGY_SPEC.md` — authoritative behavioral definition.
3. `docs/BACKTEST_PROTOCOL.md` — authoritative simulation rules.
4. `docs/DATA_CONTRACT.md` — authoritative data requirements.
5. `docs/ARCHITECTURE.md` — module boundaries.
6. `docs/DECISIONS.md` — dated decisions and changes.
7. Code and tests.

If documentation and code disagree, the implementation agent must stop, identify the conflict, and update both in the same change. Never silently reinterpret the strategy.

## First research question

> Does a deterministic strategy that approximates the Reddit trader's observable behavior retain positive expectancy after realistic transaction costs, slippage, option spreads, and margin financing across multiple market regimes — or was the reported result mainly regime/luck/capital dependent?

The first milestone is **not** live execution. It is a reproducible research report comparing three variants:

- `literal_clone`: closest feasible mechanical translation of the observed behavior;
- `risk_controlled`: same broad signals but with fixed risk budgets and no unconstrained averaging down;
- `regime_adapted`: risk-controlled strategy plus an optional market/sector regime filter.
