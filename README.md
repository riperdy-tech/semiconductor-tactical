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

## Start here — one command

On Windows, from the repository root:

```powershell
.\run.ps1
```

Or double-click:

```
run.bat
```

The default runner:

1. creates `.venv` if needed;
2. installs/upgrades the project dependencies;
3. runs the full pytest suite;
4. runs the fixture backtest;
5. runs the fixture robustness experiment;
6. runs the fixture strategy comparison;
7. stops immediately on any failure.

Useful modes:

```powershell
.\run.ps1 doctor
.\run.ps1 test
.\run.ps1 backtest
.\run.ps1 research
.\run.ps1 comparison
.\run.ps1 full
```

`doctor` checks the Python environment and pytest collection. `test` runs only tests.

### Important: current commands are fixture validation

The current CLI research commands use `generate_synthetic_bars()`.

That means:

- a passing run proves the software can execute reproducibly;
- it does **not** prove that the trading strategy works;
- it is **not** a historical backtest of MU/SNDK/SKHY/AMD;
- it must not be used as evidence for the original Reddit-strategy research question.

Historical market-data ingestion is a separate required milestone. See `docs/AUDIT_20261002.md`.

## Automatic testing

GitHub Actions runs on every push and pull request across Windows and Ubuntu with Python 3.11 and 3.12.

The CI job performs:

- full pytest;
- fixture backtest smoke test;
- fixture robustness smoke test;
- fixture comparison smoke test;
- working-tree cleanliness check.

So the normal workflow is no longer "run four commands and hope." Push the repo; GitHub tests it automatically.

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
8. `docs/AUDIT_20261002.md` — current implementation audit.

If documentation and code disagree, the implementation agent must stop, identify the conflict, and update both in the same change. Never silently reinterpret the strategy.

## First research question

> Does a deterministic strategy that approximates the Reddit trader's observable behavior retain positive expectancy after realistic transaction costs, slippage, option spreads, and margin financing across multiple market regimes — or was the reported result mainly regime/luck/capital dependent?

The first milestone is **not** live execution. It is a reproducible research report comparing three variants:

- `literal_clone`: closest feasible mechanical translation of the observed behavior;
- `risk_controlled`: same broad signals but with fixed risk budgets and no unconstrained averaging down;
- `regime_adapted`: risk-controlled strategy plus an optional market/sector regime filter.

## Current implementation status

The repository currently has the core package/test scaffold and synthetic fixture runner.

The following items remain research blockers and are documented in `docs/AUDIT_20261002.md`:

- real historical equity-data ingestion;
- genuine leverage enforcement;
- genuine layered-entry behavior;
- actual 2× ETF integration;
- sector/regime inputs rather than per-symbol trend substitution;
- real use of relative-volume and event filters;
- historical options data and realistic covered-call repurchase/assignment accounting;
- consistent cost/P&L accounting tests.
