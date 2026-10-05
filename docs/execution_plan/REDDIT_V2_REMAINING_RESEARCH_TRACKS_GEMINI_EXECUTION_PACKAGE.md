# Gemini Master Execution Package — Remaining Reddit V2 Research Tracks

**Status:** ACTIVE RESEARCH PACKAGE  
**Tracks:** Phase M / Phase N / Phase O  
**Precondition:** Phase M.1.4 accepted; engineering/audit layer frozen  
**Historical control:** `24a9e783`  
**First prospective run:** `bb0887e4`  
**Latest structural gate:** `d047369f`

## 0. Purpose

This package coordinates the remaining Reddit V2 research work.

The three tracks are:

- **Phase M:** Frozen prospective OOS validation
- **Phase N / V2-D:** Historical covered-call reconstruction
- **Phase O / V2-F:** Genuine Level-2 information-set ablation

The goal is not to maximize backtest returns.

The goal is to determine, with preserved provenance and explicit evidence gates, which source-described behaviors can actually explain the Reddit trader's reported performance.

The existing detailed packages remain authoritative for implementation specifics:

- `docs/execution_plan/REDDIT_V2_PHASE_M_PROSPECTIVE_CONTINUATION_EXECUTION_PLAN.md`
- `docs/execution_plan/REDDIT_V2_PHASE_M_STRUCTURAL_OOS_DATA_ACQUISITION_VALIDATION_PLAN.md`
- `docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md`
- `docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md`
- `docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md`

This document is the **operational master sequence** for Gemini.

---

# 1. Global research freeze

The accepted historical V2 result remains immutable:

- Run `24a9e783`
- V2-A: **+6.48%**
- V2-B: **+7.93%**
- V2-C: **+7.93%**
- tactical contribution: **+$1,446.69**
- peak historical V2-C debt: **$0.00**

The first prospective observation remains immutable:

- Run `bb0887e4`
- 2 complete sessions
- V2-A: **+1.21%**
- V2-B: **+0.92%**
- V2-C: **+0.92%**
- tactical contribution: **-$290.98**
- classification: `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`
- interpretation: **NEUTRAL / INCONCLUSIVE**

Never overwrite either run.

Global statuses remain:

`FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`

`TRUE_LEVEL2_REPLICATION = UNVALIDATED`

`HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED`

`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`

`PRISTINE_OOS = UNAVAILABLE` until a sufficient genuinely unseen chronological period has been evaluated.

---

# 2. Immediate operating mode

The repository is currently in a **research accumulation / data-validation state**.

### Phase M

The structural continuation gate has not reached the performance threshold.

The latest accepted structural result is:

`PHASE_M_STRUCTURAL_OOS_INSUFFICIENT_SAMPLE`

Do not run V2-A/B/C until the preregistered **20 complete regular U.S. sessions** after the accepted prospective endpoint are available and structurally validated.

Prior accepted endpoint:

`2026-10-02T19:59:00Z`

Every continuation bar must satisfy:

`timestamp > 2026-10-02T19:59:00Z`

### Phase N

Phase N may proceed **now** with:

- data-source research;
- authentic option-chain acquisition;
- schema/provenance validation;
- contract-lifecycle implementation;
- deterministic event/replay tests;
- freeze-spec creation.

Do not expose headline V2-D performance until the option policy and data gate are frozen.

### Phase O

Phase O may proceed **now** with:

- genuine MBO/MBP data acquisition;
- data-license/source validation;
- order-book replay;
- feature implementation;
- point-in-time tests;
- frozen feature/threshold registry;
- ablation-engine tests.

Do not expose headline V2-F performance until the Level-2 policy and data gate are frozen.

### Key rule

**M performance may be blocked while N/O engineering and data validation proceed in parallel.**

Do not let the M delay cause premature tuning or premature performance execution in N/O.

---

# 3. Cross-track contamination rules

These rules apply to all three tracks.

## Forbidden

Never:

- tune a parameter after viewing the corresponding performance result;
- use Phase M performance to select N parameters;
- use Phase M performance to select O parameters;
- use N performance to select O parameters;
- use O performance to select N parameters;
- shift the common OOS window because a result is favorable/unfavorable;
- remove unfavorable days, symbols, contracts, or events;
- modify costs after seeing results;
- modify execution semantics after seeing results;
- combine M/N/O P&L into a single synthetic headline result.

## Allowed

Before performance exposure, it is allowed to:

- acquire data;
- validate metadata;
- measure structural coverage;
- build deterministic parsers;
- build replay engines;
- add no-lookahead tests;
- add accounting tests;
- validate hashes/provenance;
- freeze written specifications.

If a genuine implementation defect is found after performance exposure:

1. preserve the affected run;
2. document the defect;
3. repair it independently of performance;
4. create a new execution commit;
5. run a new run ID;
6. never overwrite the failed artifact.

---

# 4. Phase M — frozen prospective OOS

## M objective

Determine whether the frozen V2 directional/core/margin hypothesis generalizes to genuinely unseen U.S.-market data.

## M performance gate

Do not execute another performance run until:

- at least **20 complete regular U.S. trading sessions** exist after the accepted `bb0887e4` endpoint;
- MU, SNDK, and SKHY all satisfy structural coverage;
- chronology is strictly forward;
- no overlap or contamination exists;
- frozen configuration/fingerprint remains unchanged;
- provenance is complete.

## M data work allowed now

Run only the structural package when new completed chronology becomes available:

`docs/execution_plan/REDDIT_V2_PHASE_M_STRUCTURAL_OOS_DATA_ACQUISITION_VALIDATION_PLAN.md`

Required structural fields:

- source/dataset identity;
- complete-session count;
- RTH coverage;
- missing bars;
- duplicates;
- chronology;
- per-symbol hashes;
- aggregate hash;
- frozen config hash;
- validation commit SHA.

When fewer than 20 sessions exist:

**STOP — NO PERFORMANCE RUN.**

When 20+ sessions exist:

Classify:

`PHASE_M_STRUCTURAL_OOS_PERFORMANCE_GATE_READY`

and **STOP**.

Do not automatically launch V2-A/B/C.

## M eventual performance execution

After the gate is separately satisfied, execute exactly once:

- V2-A;
- V2-B;
- V2-C.

Use the explicit continuation lineage:

- prior run: `bb0887e4`;
- prior endpoint: `2026-10-02T19:59:00Z`;
- new run ID;
- validated new chronological window.

Required primary comparisons:

- V2-B minus V2-A = tactical value-add;
- V2-C minus V2-B = margin value-add.

Required interpretation:

- SUPPORTIVE;
- NEUTRAL / INCONCLUSIVE;
- CONTRADICTORY;
- INVALID.

Never call the Reddit strategy fully validated from M alone.

---

# 5. Phase N — V2-D covered-call reconstruction

## N objective

Determine whether the covered-call behavior described by the Reddit source can add material economic value to the frozen V2-C process.

Primary comparison:

**V2-C control vs V2-D treatment**

Only the covered-call layer changes.

## N data gate

Require authentic point-in-time historical option quotes with:

- timestamp;
- bid;
- ask;
- contract identity;
- strike;
- expiry;
- call/put;
- underlying;
- multiplier;
- quote condition;
- synchronized underlying price;
- corporate-action policy.

Synthetic Black-Scholes prices are forbidden for the headline result.

Midpoint execution is only a sensitivity diagnostic.

If authentic intraday option data is unavailable:

**HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED**

Do not fabricate V2-D performance.

## N frozen hypothesis

The existing package defines the first default policy:

- target DTE: **5 days**
- target OTM delta: **0.20**
- sell maximum fully covered contracts
- buy back at first occurrence of:
  - 50% premium decay, OR
  - 2% underlying decline
- otherwise hold through expiry/assignment

These are explicitly:

**HYPOTHESIS / ASSUMPTION**

not observed facts.

Freeze the policy before headline performance is viewed.

## N required accounting

At every timestamp:

`short-call shares <= eligible long shares`

Maintain separate attribution for:

- underlying P&L;
- option premium;
- buyback cost;
- assignment;
- expiry;
- fees;
- financing.

Primary incremental quantity:

`V2-D economics - V2-C economics`

## N execution rule

Preferred validation period:

Use the same genuinely unseen period used by Phase M **when authentic option data covers that exact period**.

Do not change to a more favorable period.

If option data cannot cover the common M window:

- report the data limitation;
- do not silently substitute another performance period;
- a separately labeled historical sensitivity experiment may be conducted only under an explicitly frozen scope.

## N status outcomes

Use:

- `GATED_UNVALIDATED`
- `VALIDATED_PARTIAL`
- `VALIDATED`

Do not call V2-D full Reddit replication.

---

# 6. Phase O — genuine Level-2 ablation

## O objective

Determine whether genuine order-book information adds decision value to the already-frozen V2 sequence.

Primary design:

**V2_OHLCV_BASELINE vs V2_LEVEL2_MICROSTRUCTURE**

The only intended experimental difference is the decision information available to the tactical layer.

## O data gate

Require genuine:

- MBO or MBP order-book data;
- timestamp precision adequate for decision replay;
- venue identity;
- event/message type;
- sequence/order identity where available;
- side;
- price;
- size;
- add/cancel/replace/execute lifecycle;
- depth coverage;
- RTH coverage;
- provenance and hashes.

Forbidden:

- synthetic Level-2 from OHLCV;
- candle-derived walls;
- volume-derived queue estimates;
- silent gap filling.

If only venue-specific data exists, identify it explicitly. Never label venue-specific depth as consolidated Level 2.

## O frozen feature family

At minimum expose:

- best bid/ask;
- spread;
- top-1 imbalance;
- top-5 imbalance;
- top-5 bid/ask depth;
- bid/ask wall size;
- wall persistence;
- bid/ask depletion;
- bid/ask replenishment;
- event intensity;
- trade-to-depth ratio.

Initial frozen hypothesis includes:

`top-5 imbalance >= +0.20`

and:

`spread <= 2 ticks`

plus pre-registered persistence and replenishment definitions.

Those parameters are:

**HYPOTHESIS**

not observed source facts.

Freeze them before headline OOS performance.

## O replay requirement

The replay engine must reconstruct the book deterministically from raw events and provide a point-in-time snapshot.

No future event may affect an earlier decision.

Required no-lookahead tests must demonstrate this.

## O primary ablation

Control and treatment must keep identical:

- universe;
- core allocation;
- V2 impulse;
- pullback;
- stabilization;
- exits;
- margin;
- costs;
- execution mechanics.

Only decision information may differ.

Primary quantity:

**treatment incremental P&L vs OHLCV control**

Also report:

- signal acceptance/rejection;
- trade frequency;
- drawdown;
- turnover;
- exposure;
- microstructure feature coverage.

## O status outcomes

At minimum distinguish:

- `UNVALIDATED`
- `DATA_VALIDATED`
- `ABLATION_VALIDATED`

Do not call V2-F full Reddit replication.

---

# 7. Required N/O implementation order

For each N and O:

### Step A — data acquisition

Acquire the best authentic data source available.

### Step B — structural validation

Validate coverage, chronology, quote/event integrity, provenance, and hashes.

### Step C — freeze specification

Commit:

- research specification;
- parameter registry;
- data manifest schema;
- deterministic replay rules;
- configuration fingerprint.

### Step D — deterministic tests

Run:

- parsing tests;
- lifecycle tests;
- accounting tests;
- no-lookahead tests;
- provenance tests;
- missing-data tests.

### Step E — data gate

Only after the authentic-data gate passes may headline performance become eligible.

### Step F — common-period check

Attempt to align the performance window with Phase M.

If unavailable, STOP and report the limitation rather than silently changing the sample.

### Step G — one performance run

Only after all gates pass.

Then preserve:

- JSON;
- Markdown;
- manifest;
- preservation note;
- execution SHA;
- artifact-content SHA;
- provenance-finalization SHA.

Then:

**STOP SOFTWARE CHANGES.**

---

# 8. Recommended parallelization now

Gemini should work in this order:

**Track M:** wait for new complete sessions; perform only structural scans.

**Track N:** begin authentic historical option-data acquisition and lifecycle implementation now.

**Track O:** begin authentic historical Level-2 acquisition and deterministic order-book replay now.

These activities can proceed in parallel because none requires seeing the other track's performance.

Do not wait for M merely to begin N/O data engineering.

---

# 9. Live trading separation

Any real-money live trading implementation is a **separate production track**.

Do not:

- use live P&L to tune M/N/O;
- substitute live fills for historical evidence;
- alter research parameters based on live behavior;
- mix live artifacts into historical/OOS reports.

The live pilot, when implemented, must have its own:

- run namespace;
- broker adapter;
- risk controls;
- fill journal;
- account reconciliation;
- kill switch;
- deployment/version record.

This package does not authorize a live performance claim.

---

# 10. Final synthesis gate

Do not create a single "Reddit strategy return."

After M, N, and O are independently preserved, produce a synthesis that answers separately:

1. Does frozen directional V2 generalize?
2. Does margin add measurable value?
3. Do covered calls add measurable value?
4. Does genuine Level-2 information add measurable value?
5. Which source behaviors remain unsupported?
6. How much of the reported Reddit outcome is plausibly attributable to each tested component?

The correct scientific result may be:

- some components help;
- some components do not;
- some components remain unvalidated.

That is a valid result.

## 11. Final global stop

After each track is complete:

**STOP SOFTWARE CHANGES.**

After all three are complete:

**STOP SOFTWARE CHANGES.**

The next activity is synthesis/falsification analysis.

Never optimize after seeing the combined result.
