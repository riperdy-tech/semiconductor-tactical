# Reddit Strategy Fidelity — Execution Plan for Gemini

## Objective

Rework the research implementation so that the historical experiment more faithfully represents the trading behavior actually described in the primary Reddit post and its comments.

The current engine is considered **software-complete but strategy-fidelity-incomplete**.

The existing negative result must remain preserved as evidence of the **current mechanical pullback implementation**. It must not be deleted, overwritten, or retroactively relabeled as the Reddit trader's actual strategy.

The goal of this task is **not** to make the backtest profitable.

The goal is:

> Determine whether the currently implemented strategy is materially different from the behavior described by the source, and, where the source supports it, implement a deterministic research approximation that covers the observed components without optimizing to the reported $550k result.

---

# 1. Read first

Read all of the following before modifying code:

1. `AGENTS.md`
2. `docs/REDDIT_SOURCE_NOTES.md`
3. `docs/STRATEGY_SPEC.md`
4. `docs/BACKTEST_PROTOCOL.md`
5. `docs/DATA_CONTRACT.md`
6. `docs/DECISIONS.md`
7. `docs/execution_plan/OOS_PROVENANCE_RECONCILIATION.md`
8. `docs/USD_DATA_AUDIT.md`
9. `configs/historical_1m.yaml`
10. `src/tactical_engine/backtest/engine.py`
11. `src/tactical_engine/research/comparison.py`
12. `src/tactical_engine/signals/pullback.py`
13. `src/tactical_engine/signals/features.py`
14. options-related modules under `src/tactical_engine/options/`
15. execution/sizing/margin modules under `src/tactical_engine/execution/` and `src/tactical_engine/portfolio/`

Before changing anything, inspect the preserved first-run and post-audit artifacts.

---

# 2. Research-integrity rule

## Absolute prohibition

Do **not** tune the implementation to make it reproduce:

- the reported $550k profit;
- the reported $1.2M account value;
- the reported 1,300+ trade count;
- a visually attractive equity curve;
- a positive return on the current July–September sample.

Those are source observations, not optimization targets.

The implementation must remain falsifiable.

## Evidence labels

Every strategy rule must be labeled:

- `OBSERVED` — directly described by the Reddit post/comments;
- `DERIVED` — mechanical inference from observed behavior;
- `HYPOTHESIS` — plausible deterministic proxy for discretionary behavior;
- `ASSUMPTION` — value required because the source does not specify it;
- `UNVERIFIED` — cannot currently be checked with the available data.

Do not promote a hypothesis or assumption into an observed fact.

---

# 3. Phase A — Preserve the current experiment

Before changing strategy code:

1. Preserve the existing negative historical comparison.
2. Record:
   - run ID;
   - git SHA;
   - dataset ID;
   - aggregate dataset hash;
   - config hash;
   - exact configuration;
   - report path;
   - comparison JSON path.
3. Explicitly label the current implementation:

`CURRENT_MECHANICAL_PULLBACK_BASELINE`

4. Add a report/documentation note:

> This baseline is a deterministic mean-reversion implementation inspired by the source. It is not a faithful reconstruction of the full Reddit trading process.

5. Do not delete or rewrite historical artifacts.

### Required outcome

The negative result remains reproducible and independently identifiable from the new fidelity experiments.

---

# 4. Phase B — Build a source-evidence matrix

Create:

`docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`

For every source behavior, record:

| Component | Evidence | Label | Source location | Deterministic implication | Data required | Status |
|---|---|---|---|---|---|---|

At minimum evaluate these components:

### 4.1 Instruments

Source-described names:

- MU
- SNDK
- SKHY / Kioxia-related exposure
- 2× semiconductor ETF exposure

Record what is actually observed versus what is only inferred.

### 4.2 Directional underlying trading

Document evidence for:

- scalping;
- swing trading;
- frequent entries/exits;
- trend identification;
- pullback entries;
- active management rather than passive holding;
- stop-limit usage.

Do not invent an exact entry formula.

### 4.3 Strength → covered-call overlay

The source specifically describes:

- short-dated covered calls entered during strength;
- buying them back during pullbacks;
- assignment/strike considerations.

Separate this from the equity signal.

Do not treat covered calls as an optional generic income strategy. This experiment exists because the source describes them as part of the trading process.

### 4.4 Leverage / margin / capital rotation

Document:

- large positions;
- 2× ETF exposure;
- use of margin;
- margin-risk behavior;
- capital rotation among symbols.

Exact leverage must remain `ASSUMPTION` unless explicitly documented by the source.

### 4.5 Extended-hours / non-RTH activity

The source describes trading related to SKHY/Kioxia exposure outside U.S. regular trading hours.

Mark this as a separate data requirement.

Do not silently treat a RTH-only dataset as a full implementation of this behavior.

### 4.6 Trade frequency

The source reports approximately 1,300+ trades over the reported period.

Treat this only as a **descriptive plausibility check**, not as a calibration target.

---

# 5. Phase C — Audit the current implementation against the evidence matrix

Create:

`docs/execution_plan/REDDIT_STRATEGY_FIDELITY_GAP_AUDIT.md`

For each current behavior, answer:

1. What does the engine currently do?
2. What does the source actually describe?
3. Is the current rule observed, derived, hypothesized, assumed, or unsupported?
4. Does the mismatch materially affect P&L?
5. Can the current dataset support a better implementation?
6. What is the minimum change required?

The audit must explicitly identify the following current behavior:

- entry uses a short-term z-score pullback threshold;
- relative-volume filtering;
- optional benchmark regime filter;
- ATR stop/target;
- maximum hold period;
- 1-minute RTH-only data;
- covered calls disabled in the historical config;
- current leverage/layering rules;
- current market-order execution model.

The audit must state clearly:

> The current z-score/ATR strategy is a **HYPOTHESIS/ASSUMPTION mechanical proxy**, not an observed source rule.

---

# 6. Phase D — Redesign the strategy representation before tuning anything

Do not immediately replace the current signal formula.

First introduce a strategy composition that can represent the source's separate P&L components.

Required conceptual layers:

### Layer 1 — Directional Equity

A deterministic approximation of the source's active MU/SNDK/SKHY trading.

Must support:

- entry;
- exit;
- stop-limit behavior where data permits;
- position scaling;
- maximum layers;
- capital rotation;
- long-only behavior unless evidence supports otherwise.

Exact thresholds remain configuration parameters tagged as `HYPOTHESIS` or `ASSUMPTION`.

### Layer 2 — Covered Calls

A separate overlay tied to actual underlying ownership.

Must support:

- sale during an explicitly defined strength condition;
- short-dated DTE range;
- configurable strike/moneyness;
- repurchase on pullback;
- assignment;
- underlying-share linkage;
- premium and realized option P&L attribution.

Do not use theoretical prices as executable historical fills.

If historical option-chain data is unavailable:

`OPTIONS_REPLICATION_STATUS = UNVALIDATED`

and do not put synthetic options P&L into the headline result.

### Layer 3 — Capital / Margin

Represent:

- margin financing;
- gross exposure;
- buying-power constraint;
- maintenance requirement;
- forced liquidation;
- interest;
- capital rotation.

Do not hard-code an assumed 3× leverage simply because it might resemble the source. Test documented and explicitly labeled leverage assumptions as separate experiments.

### Layer 4 — Session / Extended Hours

Treat non-RTH activity as a distinct execution/data mode.

Do not fabricate bars.

If reliable historical extended-hours data is unavailable:

`EXTENDED_HOURS_REPLICATION_STATUS = UNVALIDATED`

and report what fraction of the described behavior is not represented.

---

# 7. Phase E — Fix the strategy semantics before performance evaluation

The new implementation must distinguish:

## Observed behavior

Examples:

- active trading of high-beta semiconductor names;
- scalping/swinging;
- trend/pullback decision-making;
- stop-limit use;
- covered calls during strength;
- call repurchase during pullbacks;
- margin;
- 2× ETF exposure;
- some non-RTH trading.

## Mechanical proxy

Examples:

- a deterministic trend-state predicate;
- a deterministic pullback predicate;
- a deterministic strength predicate;
- a fixed stop-limit model;
- a fixed DTE/moneyness band;
- a fixed allocation/risk model.

The code and reports must show which is which.

Do not call a proxy "the Reddit rule."

---

# 8. Phase F — Execution semantics audit

Review `docs/BACKTEST_PROTOCOL.md` and verify that the fidelity implementation obeys:

- no look-ahead;
- signal-at-close cannot fill at unknown same-bar close;
- next eligible bar/trade semantics;
- conservative intrabar stop/target ordering when sequence is unknowable;
- pending order behavior;
- realistic slippage;
- financing;
- assignment;
- forced liquidation.

For stop-limit behavior, document:

- trigger price;
- limit price;
- fill eligibility;
- cancellation/expiry behavior;
- what happens when the market gaps through the limit.

Do not silently convert a source-described stop-limit into an unlimited market order.

---

# 9. Phase G — Data sufficiency gate

Before claiming the new strategy is fully replicated, verify data availability for:

### Required for equity RTH research

- MU
- SNDK
- SKHY
- relevant ETF
- benchmarks

### Required for extended-hours research

Reliable historical non-RTH data for the relevant instruments.

### Required for covered-call research

Historical option chains containing, at minimum:

- contract;
- timestamp;
- bid;
- ask;
- strike;
- expiry;
- underlying;
- enough observations to reconstruct entry and repurchase.

### Required outcome

For each component report:

- `VALIDATED`
- `PARTIALLY_VALIDATED`
- `UNVALIDATED`

Never fill missing historical information with synthetic market data and call it replication.

---

# 10. Phase H — Build the fidelity experiment matrix

Do not collapse everything into one headline strategy.

Run separate experiments:

### Experiment 1 — Current baseline

`CURRENT_MECHANICAL_PULLBACK_BASELINE`

Purpose: preserve the existing result.

### Experiment 2 — Directional fidelity

Equity-only implementation using the new evidence-backed deterministic proxy.

Purpose: determine whether the underlying trading behavior itself can produce positive expectancy.

### Experiment 3 — Directional + margin

Same strategy with explicit financing and leverage assumptions.

Purpose: determine whether reported performance characteristics could arise from leverage rather than signal edge.

### Experiment 4 — Directional + covered calls

Add only validated historical option data.

Purpose: quantify option premium contribution separately from directional P&L.

### Experiment 5 — Full validated composite

Combine:

- directional equity;
- covered calls;
- margin;
- supported session coverage.

Only run this if every required data component is validated.

### Experiment 6 — Component ablations

Report:

- equity only;
- equity + margin;
- equity + covered calls;
- equity + supported extended hours;
- full composite.

This is critical for identifying where any observed P&L comes from.

---

# 11. Phase I — Descriptive plausibility diagnostics

Before looking at profitability, report:

- trades/day;
- trades/symbol/day;
- median hold;
- distribution of hold times;
- entries/exits by symbol;
- gross exposure;
- net exposure;
- number of concurrent positions;
- leverage utilization;
- margin utilization;
- covered-call frequency;
- call DTE at entry;
- call moneyness at entry;
- call repurchase latency;
- assignment count;
- RTH vs extended-hours activity;
- percentage of P&L from each component.

Compare these against source descriptions only as **descriptive plausibility checks**.

Do not tune parameters until trade frequency resembles the source.

In particular:

> The reported trade count must never become a fitting objective.

---

# 12. Phase J — Falsification tests

Run the existing research/falsification suite against the new implementation.

At minimum:

1. realistic transaction-cost sensitivity;
2. leverage sensitivity;
3. ticker leave-one-out;
4. strongest-day exclusion;
5. strategy-return bootstrap;
6. benchmark-return bootstrap;
7. parameter perturbation;
8. component ablations;
9. chronological train/validation/test analysis;
10. future pristine OOS when data permits.

The negative baseline and all new experiments must remain separately identifiable.

---

# 13. Parameter discipline

Do not search for the most profitable parameters on the full sample.

For any parameter that cannot be observed directly from the source:

- define a small, predeclared candidate set;
- document why the set exists;
- select using train only;
- validate on validation;
- do not use the post-hoc September segment as tuning data;
- preserve the methodology once frozen.

No parameter may be selected because it improves the reported Reddit-period return.

---

# 14. Required documentation updates

After implementation, update:

### `docs/REDDIT_SOURCE_NOTES.md`

Add the evidence discovered during the source audit.

### `docs/STRATEGY_SPEC.md`

Separate:

- observed source behavior;
- deterministic proxy rules;
- assumptions;
- unsupported behavior.

Do not rewrite history to pretend the original implementation was faithful.

### `docs/DECISIONS.md`

Add a dated decision documenting:

- why the current z-score/ATR baseline is not considered a full source reconstruction;
- what source behaviors were added;
- what remains unvalidated because of data limitations.

### New documents

Create:

- `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`
- `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_GAP_AUDIT.md`
- `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_RESULTS_PROTOCOL.md`

---

# 15. Testing requirements

Every implementation slice must include tests for:

- no-lookahead;
- signal timing;
- stop-limit execution;
- pending-order behavior;
- position layering;
- covered-call ownership requirement;
- covered-call repurchase;
- assignment;
- margin financing;
- forced liquidation;
- component P&L attribution;
- deterministic repeatability.

Run:

```
.\\run.ps1 test
.\\run.ps1 doctor
.\\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed
.\\.venv\\Scripts\\python.exe -m ruff check .
```

Then run only the explicitly documented historical experiment commands.

---

# 16. Reporting requirements

Every new experiment must output:

1. human-readable Markdown;
2. machine-readable JSON;
3. exact config;
4. config hash;
5. git SHA;
6. dataset ID;
7. aggregate dataset hash;
8. component validation status;
9. evidence labels for strategy rules;
10. sample dates;
11. all major P&L components;
12. costs;
13. leverage/margin;
14. options attribution where applicable;
15. OOS scope classification.

The headline report must show the current baseline separately from the fidelity implementation.

---

# 17. Acceptance criteria

This task is complete only when all of the following are true:

- [ ] Current negative baseline is preserved unchanged.
- [ ] The source evidence matrix exists.
- [ ] Every new strategy rule has an evidence label.
- [ ] The current z-score/ATR implementation is explicitly identified as a mechanical hypothesis, not observed Reddit behavior.
- [ ] Directional equity trading is represented independently from covered calls.
- [ ] Covered-call behavior is represented independently and requires real option data for validation.
- [ ] Extended-hours behavior is explicitly represented as validated or unvalidated.
- [ ] Margin/leverage behavior is explicitly represented.
- [ ] Execution semantics are documented and tested.
- [ ] Descriptive plausibility diagnostics are reported.
- [ ] No parameter was tuned to the reported $550k outcome.
- [ ] No parameter was tuned to force the reported trade count.
- [ ] No parameter was tuned to make the July–September sample profitable.
- [ ] Existing provenance/OOS controls remain intact.
- [ ] pytest passes.
- [ ] ruff passes.
- [ ] no credentials are committed.

---

# 18. Stop condition

When the acceptance criteria pass:

**STOP SOFTWARE CHANGES.**

Do not continue iterating because the result is negative.

Do not continue iterating because the result is positive.

Do not select a new rule because it improves the chart.

The next step is research interpretation:

1. compare the current mechanical baseline with the evidence-backed fidelity implementation;
2. identify which components drive P&L;
3. assess whether any positive result survives costs and chronological OOS testing;
4. state clearly which source behaviors remain unvalidated.

A profitable result is not success by itself, and an unprofitable result is not failure by itself.

The research question is whether the observed source behavior can be represented faithfully enough to test its claimed economics without silently inventing rules.
