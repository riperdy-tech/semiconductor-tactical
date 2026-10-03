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

- `OBSERVED`: directly described by the Reddit post/comments.
- `DERIVED`: necessary mechanical or structural inference from observed facts.
- `HYPOTHESIS`: plausible deterministic proxy chosen to approximate discretionary chart reading.
- `ASSUMPTION`: parameter or threshold chosen because the source is silent.
- `UNVERIFIED`: information or claim that cannot currently be checked with primary data.

## Phase H Fidelity Audit Findings

See full matrix in `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md` and gap audit in `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_GAP_AUDIT.md`.

1. **Current Baseline is a Hypothesis Proxy:** The initial z-score pullback and tight ATR exit implementation is designated `CURRENT_MECHANICAL_PULLBACK_BASELINE`. It is an engineering hypothesis, not the observed Reddit rule.
2. **Component Decoupling:** Directional equity trading, covered-call writing, margin financing, and extended-hours trading must be evaluated independently.
3. **Data Sufficiency Status:**
   - Equity RTH: `VALIDATED` (1m OHLCV for MU, SNDK, SKHY, USD, SMH, SPY).
   - Margin Financing: `VALIDATED` (mechanics validated; specific leverage is `ASSUMPTION`).
   - Covered Calls: `UNVALIDATED` (historical option chains absent; Black-Scholes substitution prohibited).
   - Extended Hours: `UNVALIDATED` (dataset strictly RTH 09:30-16:00 ET; non-RTH SKHY/Kioxia trading absent).
4. **Descriptive Plausibility Diagnostics:** The reported ~1,300+ trade count over ~90 calendar days (~20.6 trades/day across portfolio) serves as a reality check on holding duration (multi-hour to multi-day swing positions vs. 2-minute tick stop-outs), NOT as an optimization objective.

## Important warning about the headline result

The $550k result is an observed self-report, not evidence that the strategy has a persistent edge. The historical period may have been unusually favorable for the selected securities, and capital, margin availability, leverage, turnover, skill, timing, and survivorship may all contribute.

The project's job is to falsify easy explanations before declaring an edge.

## Phase J Behavioral Replication V2 Findings & Scope Boundaries

See full evidence matrix in `docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md` and directional behavior spec in `docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md`.

1. **Portfolio Process vs Single Signal:** The trader's actual activity was a multi-layer process: persistent long inventory in high-beta memory names -> active scalps/reloads around core on margin -> short-dated covered calls sold on surges and repurchased on pullbacks. Tactical reductions never liquidate core holdings.
2. **U.S.-Market Only Scope:** Direct Asian execution (KRX SK hynix `000660`, Tokyo Kioxia `285A`) is explicitly out of scope for V2 (`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`).
3. **Instrument Clarifications:**
   - `SKHY`: Primary U.S. vehicle for SK hynix memory exposure (`SOURCE_IDENTIFIED`).
   - `KXIAY`: Active U.S. OTC ADR (1:10 ratio) evaluated as a proxy for Tokyo Kioxia activity. Never describe as Nasdaq-listed. Kioxia officially stated on Sep 15, 2026 that U.S. exchange listing details remain undecided.
   - 2x Leveraged ETFs: Candidates (`SKUU`, `SKHU`, `SKHL`, `MUU`, `SNDG`, `SNDU`, `SNXX`) inventoried as `CANDIDATE_PROXY`.
   - Generic `USD` ETF: Strictly quarantined from headline source-replication results.
4. **Level-2 Data Gate:** Gated as `TRUE_LEVEL2_REPLICATION = UNVALIDATED`. Synthetic order book features from OHLCV are prohibited.
5. **Pre-Registration:** Phase H parameters (`0.5%–3%`, `0.35 stabilization`, tight ATRs) remain quarantined as `POST_HOC_SPECIFIED`. V2 pre-registers a bounded candidate family prior to any simulation.


