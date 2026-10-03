# Gemini Execution Plan — Reddit Behavioral Replication V2 (US-Market Scope)

## Objective

Build the next research version around the trading process actually described by the Reddit source rather than treating it as one mathematical entry signal.

V2 must represent, as separate components:

1. persistent large positions in high-beta memory names;
2. active scalping and swing trading around those positions;
3. trend / impulse / pullback decisions;
4. stop-limit usage;
5. margin-financed capital deployment;
6. short-dated covered calls written during strength and repurchased during pullbacks;
7. U.S.-market execution only for this phase;
8. Level-2/order-book information as a separate data gate;
9. U.S.-listed 2x products where the source supports that behavior.

### Explicit V2 scope

Do not model direct KRX or Tokyo execution in V2.

Exclude:
- KRX SK hynix common stock;
- Tokyo Kioxia common stock 285A.

Use U.S.-market instruments only:
- SK Hynix ADR: SKHY;
- Kioxia ADR: KXIAY, only if usable historical U.S. data is available;
- verified U.S.-listed 2x products, subject to source-evidence classification and data validation.

KXIAY is a U.S. OTC ADR, not a Nasdaq-listed equivalent of SKHY. Kioxia stated on September 15, 2026 that details of a planned U.S. exchange ADS listing had not yet been decided. Therefore KXIAY is a U.S.-market access proxy for the Tokyo Kioxia behavior described by the source, not proof that the Reddit trader used KXIAY. The current ADR program is active and has a 1:10 ordinary-share-to-DR ratio.

The final V2 headline result must clearly distinguish observed source instruments from U.S.-market proxy instruments.

## 1. Research-integrity constraints

Do not tune parameters to reproduce the reported $550k, the reported ~1,300 trades, or a profitable July–September result.
Do not fabricate Level-2 data, option-chain data, or Asian-exchange data.
Do not silently substitute a KRX or Tokyo security into the U.S.-only experiment.
Do not call a deterministic proxy an observed Reddit rule.

Keep evidence labels: OBSERVED, DERIVED, HYPOTHESIS, ASSUMPTION, UNVERIFIED.

## 2. Read first

Read the existing AGENTS.md, source notes, strategy spec, decisions, Phase H/Phase I plans, parameter provenance, preserved baseline, fidelity reports, backtest engine, portfolio state, signal modules, options modules, execution modules, and all prior run manifests before editing.

Also re-check the primary Reddit post/comments because V2 depends on source details not present in OHLCV alone.

## 3. Phase A — Preserve existing evidence

Before code changes:
- preserve every Phase H and Phase I artifact;
- preserve the post-hoc parameter classification;
- preserve the July–September dataset and hashes;
- record current HEAD SHA;
- verify no API credentials are tracked.

The existing directional fidelity result remains POST_HOC_SPECIFIED / NOT_OOS_VALIDATED.
It must not be treated as the V2 benchmark.

## 4. Phase B — Build the V2 evidence matrix

Create docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md.

At minimum map these source observations:
- MU, SNDK, SKHY;
- 2x ETF exposure;
- scalping and swing trading;
- trend identification;
- large upward moves followed by retreats;
- stop-limit usage;
- short-dated covered calls during strength and repurchase on pullbacks;
- large persistent positions on margin;
- Level-2-based decision making;
- non-U.S. trading mentioned by the source, while explicitly marking that component out of scope for V2.

For each item record source evidence, evidence label, deterministic implication, data requirement, and validation status.

## 5. Phase C — Define the U.S.-market universe

Create docs/execution_plan/REDDIT_V2_US_UNIVERSE.md.

### Core observed U.S. equities
- MU
- SNDK
- SKHY

### Conditional U.S. ADR
- KXIAY

Use KXIAY only when the historical provider supplies usable U.S. trading data for the requested period. Classify it as OTC_ADR and as a DERIVED/HYPOTHESIS proxy for the source's Tokyo Kioxia activity.

### 2x candidate products

Inventory, but do not automatically treat as source-verified, the U.S.-listed 2x long products that existed during the sample. Current verification includes SKUU, SKHU, SKHL, MUU, and multiple 2x long SNDK products such as SNDG, SNDU, and SNXX.

For each candidate record ticker, issuer, underlying, leverage, long/short direction, inception/listing date, exchange, historical coverage, liquidity, provider availability, and source-evidence status.

The exact product used by the Reddit trader must be SOURCE-IDENTIFIED before being labeled observed. Otherwise classify it as CANDIDATE_PROXY.

Do not include the generic USD semiconductor ETF in the source-replication headline merely because it is a 2x semiconductor product.

## 6. Phase D — Replace the single-signal model

V2 must represent a portfolio process.

### Layer 1 — Persistent core holdings

Support long-lived MU, SNDK, SKHY, and verified 2x-product inventory independently from tactical trades.

Track quantity, average cost, realized/unrealized P&L, margin debt, available shares for covered calls, and tactical inventory separately.

Do not invent exact allocation percentages; those remain UNVERIFIED/ASSUMPTION.

### Layer 2 — Tactical trading around core

Support add, reload, partial reduction, full reduction, re-entry, multiple simultaneous symbols, and capital rotation.

A tactical exit must not automatically liquidate the persistent core position.

### Layer 3 — Covered-call overlay

Attach covered calls to actual owned shares.

Required state machine:
strength -> sell short-dated call -> underlying pulls back -> buy back call -> retain/redeploy shares.

Track shares, contracts, strike, expiry, DTE, bid/ask, sale, buyback, assignment, delivered shares, realized option P&L, and capped-upside attribution.

Historical option quotes remain a hard validation gate.

### Layer 4 — Margin/capital

Margin must operate at account level across persistent holdings and tactical exposure.

Track margin debt, buying power, financing, maintenance, forced liquidation, and available tactical capacity.

Do not reset the account to flat cash after each tactical trade.

### Layer 5 — Information inputs

Keep OHLCV, Level-2/order book, options, and session data as separate information layers.

Do not represent Level-2 as generic OHLCV features.

## 7. Phase E — Define the directional behavior

Create docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md.

The deterministic proxy should follow the observed process:

trend/regime -> strong directional impulse -> retreat/pullback -> stabilization/reclaim -> tactical add/reload -> rebound -> partial/full reduction.

The source's approximately 2% move example is an observed economic reference, not a hard-coded take-profit.

Do not recycle the post-hoc 0.5%–3%, 0.35 stabilization, 1.5 ATR stop, or 2.5 ATR target values as though they were source facts.

V2 must use a new pre-registered parameter set or a deliberately small parameter family that is frozen before any V2 performance evaluation.

Do not use the July–September sample to choose those parameters.

## 8. Phase F — Level-2 data gate

Create docs/execution_plan/REDDIT_V2_LEVEL2_DATA_GATE.md.

The source explicitly says the trader looks at Level 2 and makes a call. Therefore TRUE_LEVEL2_REPLICATION is UNVALIDATED unless genuine historical order-book/depth data is acquired.

Do not synthesize Level-2 from OHLCV.

An optional OHLCV/trade-proxy may be implemented, but it must be labeled HYPOTHESIS and reported separately from true Level-2 replication.

## 9. Phase G — Stop-limit execution

Keep the tested stop-limit engine.

Classify:
- OBSERVED: trader used stop-limit orders;
- HYPOTHESIS: stop-limit as a specific directional entry mechanism.

Support trigger, limit, gap-through non-fill, and pending-order behavior.

Do not assume every source stop-limit was an entry.

## 10. Phase H — Covered-call data gate

Do not use theoretical option prices.

Required chain fields include timestamp, underlying, contract, strike, expiry, bid, ask, volume, and open interest where available.

Do not put option P&L into a headline result unless the historical chain is validated.

Exact DTE/moneyness/strike choice remains an assumption and must be pre-registered before V2 evaluation.

## 11. Phase I — U.S.-only session scope

Include U.S. RTH and U.S. pre/post-market only where verified data exists.

Exclude direct KRX and Tokyo execution.

Set DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2.

Do not fabricate overnight returns from foreign venues.

The source's direct Korea/Japan execution can become a separate V3 project.

## 12. Phase J — Optional U.S.-market information linkage

Do not import KRX/Tokyo prices merely as hidden signals.

Default V2 information set is U.S.-market data only.

U.S.-traded SKHY and KXIAY may be used as U.S.-market instruments where validated.

## 13. Phase K — Account-level portfolio reconstruction

Create docs/execution_plan/REDDIT_V2_PORTFOLIO_MODEL.md.

Represent:
- persistent core holdings;
- tactical sleeve;
- covered calls;
- margin;
- cash;
- optional profit withdrawals as a separate accounting scenario.

Do not use withdrawals to enhance reported strategy return.

## 14. Phase L — Instrument manifest

Create a machine-readable V2 instrument manifest.

Every instrument must include:
- ticker;
- issuer;
- instrument type;
- underlying;
- leverage;
- exchange/venue;
- inception/listing date;
- source-evidence status;
- data-provider status;
- first valid bar;
- coverage;
- liquidity notes.

Keep SOURCE_IDENTIFIED and CANDIDATE_PROXY separate.

## 15. Phase M — V2 experiment matrix

After the V2 specification is frozen, define:

V2-A: core portfolio only.
V2-B: core plus tactical trading.
V2-C: core plus tactical plus margin.
V2-D: core plus tactical plus validated covered calls.
V2-E: full validated U.S.-market composite.
V2-F: information-set ablations, including OHLCV-only versus validated microstructure/options inputs.

Do not call V2-E a full Reddit replication unless all required components are validated.

## 16. Phase N — Pre-registration

Create docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md.

For every V2 parameter record value/candidate set, evidence label, rationale, commit SHA, timestamp, and whether the July–September performance had already been observed.

Any parameter entered after the July–September result is automatically POST_HOC_SPECIFIED for that historical sample.

Do not rerun parameter searches against the contaminated sample.

## 17. Phase O — OOS

July–September remains post-hoc.

PRISTINE_OOS remains UNAVAILABLE until genuinely unseen chronological data exists after the V2 specification is frozen.

Do not relabel September as pristine.

## 18. Phase P — Data gates

Required for headline V2 research:
- verified U.S. intraday data for core equities;
- verified U.S. intraday data for selected leveraged products;
- verified U.S. extended-hours data if included;
- validated historical option chains for covered-call P&L.

Strongly preferred:
- genuine historical Level-2/order-book data.

Not required for V2:
- KRX common stock;
- Tokyo common stock.

## 19. Phase Q — Tests

Add tests for:
- persistent core holdings;
- tactical add/reduce/re-entry;
- partial exits;
- covered-call ownership and state transitions;
- margin against persistent positions;
- stop-limit execution;
- U.S.-only instrument classification;
- KXIAY OTC classification;
- KRX/Tokyo exclusion;
- source-evidence labels;
- parameter registry;
- pre-registration metadata;
- no-lookahead;
- P&L component attribution.

Run the canonical test, doctor, doctor-data, and ruff commands.

## 20. Required documentation

Create:
- docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md
- docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
- docs/execution_plan/REDDIT_V2_US_UNIVERSE.md
- docs/execution_plan/REDDIT_V2_LEVEL2_DATA_GATE.md
- docs/execution_plan/REDDIT_V2_PORTFOLIO_MODEL.md
- docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
- docs/execution_plan/REDDIT_V2_RESULTS_PROTOCOL.md

Update the source notes, strategy spec, and decisions.

## 21. Acceptance criteria

- direct KRX and Tokyo execution excluded from V2;
- SKHY used as the U.S. SK hynix instrument;
- KXIAY only as a clearly labeled U.S.-market ADR proxy when data is sufficient;
- KXIAY never described as Nasdaq-listed;
- exact source ETFs separated from candidate proxy ETFs;
- persistent core holdings represented independently from tactical trades;
- tactical add/reduce/re-entry supported;
- covered calls attached to owned shares;
- account-level margin supported;
- Level-2 explicitly gated;
- no fabricated Level-2 features;
- stop-limit entry remains a hypothesis;
- V2 parameters pre-registered;
- July–September not used for V2 parameter selection;
- no optimization to profitability or trade count;
- all rules evidence-labeled;
- data gaps explicit;
- tests pass;
- ruff passes;
- prior artifacts untouched.

## 22. Mandatory stop condition

After the V2 specification, instrument manifest, parameter registry, data gates, tests, and documentation pass:

STOP SOFTWARE CHANGES.

Do not tune toward $550k, ~1,300 trades, or positive P&L.

The next action is a separately approved V2 research execution using the frozen specification and, ideally, a genuinely unseen future chronological period.

## Final research question

How much of the Reddit trader's reported behavior and claimed economics can be reproduced using only U.S.-market instruments and data once persistent holdings, tactical trading, margin, covered calls, and the Level-2 information limitation are represented explicitly?