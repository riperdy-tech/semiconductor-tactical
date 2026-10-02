# Architecture

## Design principle

The engine should be a deterministic pipeline with explicit state transitions. Avoid a giant backtest class.

```text
raw data
  ↓
validation / normalization
  ↓
feature engine
  ↓
signal engine
  ↓
portfolio / sizing
  ↓
execution simulator
  ├── equity fills
  └── option fills / assignment
  ↓
accounting / margin
  ↓
metrics
  ↓
experiment runner
  ↓
JSON + Markdown report
```

## Package layout

```text
src/tactical_engine/
    data/
        models.py
        providers.py
        validation.py
        corporate_actions.py
    signals/
        features.py
        pullback.py
        exits.py
        ranking.py
    portfolio/
        sizing.py
        constraints.py
        margin.py
    execution/
        fills.py
        slippage.py
        simulator.py
    options/
        contracts.py
        covered_calls.py
        assignment.py
    backtest/
        engine.py
        state.py
        manifest.py
    reports/
        metrics.py
        renderer.py
        attribution.py
```

## Boundary: RS2

Optional integration belongs under an adapter such as:

```text
src/tactical_engine/signals/rs2_regime_adapter.py
```

The adapter must accept a normalized regime object. It must not import internal RS2 modules directly. This keeps the tactical repo independently testable and prevents a broken RS2 environment from breaking the core engine.

## Boundary: strategy vs simulator

A strategy asks:

> Given the information available now, what order intent should exist?

The simulator decides:

> Given that intent, market data, liquidity, costs, and account state, what actually fills?

Never put fill assumptions inside signal functions.

## Boundary: research vs production

Historical research is the only first-phase execution mode. Live brokerage integration is a future project.
