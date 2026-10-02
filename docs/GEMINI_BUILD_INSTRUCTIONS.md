# Gemini Build Instructions

## Mission

You are implementing the repository described by these documents. Treat the documents as a software specification, not as suggestions.

Your job is to build a **research-grade deterministic backtesting engine** that tests whether the mechanics described by one Reddit trader can be approximated systematically.

Source post:
https://www.reddit.com/r/wallstreetbets/comments/1wtmanz/made_550k_in_90_days_cant_stop_wont_stop/

## Before touching code

Read, in order:

1. `README.md`
2. `AGENTS.md`
3. `docs/REDDIT_SOURCE_NOTES.md`
4. `docs/STRATEGY_SPEC.md`
5. `docs/BACKTEST_PROTOCOL.md`
6. `docs/DATA_CONTRACT.md`
7. `docs/ARCHITECTURE.md`
8. `docs/IMPLEMENTATION_PLAN.md`
9. `docs/EXPERIMENT_MATRIX.md`

Do not skip documents because the repository is small. The purpose of these documents is to prevent implementation drift.

## Critical instruction: do not invent facts

The Reddit post gives behavioral clues, not a complete algorithm.

Never write prose such as:

> "The strategy buys when RSI is below 30."

unless that rule is explicitly defined in the repository.

Instead write:

> "We introduce RSI < 30 as a hypothesis for approximating pullback entries."

Every unsupported parameter is a hypothesis or assumption.

## Critical instruction: implement in phases

Do NOT build everything at once.

### Phase 0

Create the package, config system, typed models, test fixtures, and run manifest.

### Phase 1

Implement equity-only backtesting first.

The first successful demonstration should be:

```bash
python -m tactical_engine ...
```

running on fixture data and producing deterministic trades + a report.

### Phase 2

Add robustness / walk-forward / parameter sweep tooling.

### Phase 3

Add realistic margin simulation.

### Phase 4

Add historical options and covered calls.

### Phase 5

Run the complete strategy comparison.

## Do not do these things

- Do not connect to a broker.
- Do not place live orders.
- Do not add credentials.
- Do not make a web UI.
- Do not add an LLM to the signal loop.
- Do not hard-code a data vendor into strategy code.
- Do not optimize until the fixture and historical baseline tests pass.
- Do not claim a profitable strategy from one backtest.
- Do not use the headline $550k as the optimization objective.

## Signal design requirement

Every signal function must be pure or close to pure:

```text
market information → features → signal intent
```

It should not know about brokerage fills, slippage, or account liquidation.

## Simulator requirement

Every simulated order must pass through the execution simulator.

Never directly modify cash/position state from the strategy.

## No-lookahead requirement

Write explicit tests proving:

- adding future bars does not alter past signals;
- option chains after a decision timestamp are inaccessible;
- corporate actions are not back-propagated improperly;
- next-bar fills are used by default.

## Options requirement

Do not implement covered calls using synthetic theoretical prices and then present them as historical evidence.

The correct behavior when option history is unavailable is:

```text
options experiment = UNVALIDATED
```

and the equity-only backtest should still run.

## Reporting requirement

Every report must show:

- strategy variant;
- data range;
- bar resolution;
- symbols;
- cost assumptions;
- slippage assumptions;
- leverage;
- margin assumptions;
- options assumptions;
- parameter values;
- sample count;
- P&L;
- drawdown;
- turnover;
- costs;
- margin utilization;
- tail losses;
- concentration;
- out-of-sample status.

## Coding style

Prefer:

- small modules;
- dataclasses / typed models;
- explicit configuration;
- pure calculations;
- deterministic fixtures;
- clear error messages;
- no magical globals.

## Definition of done for each phase

Before saying a phase is complete:

1. run pytest;
2. run lint/format checks;
3. run the documented example command;
4. inspect the generated report;
5. verify that the code still agrees with the strategy/spec documents;
6. update `docs/DECISIONS.md` for any design decision not already specified.

## Final deliverable

The completed repository should allow a new developer to clone it, install dependencies, load a documented data fixture/provider, run the experiment, and understand exactly where every performance number came from.
