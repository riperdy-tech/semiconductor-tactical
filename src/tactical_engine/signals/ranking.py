from tactical_engine.data.models import SignalIntent


def rank_signals_by_strength(signals: list[SignalIntent], top_n: int = 2) -> list[SignalIntent]:
    active = [s for s in signals if s.action == "ENTER_LONG"]
    ranked = sorted(active, key=lambda s: s.strength, reverse=True)
    return ranked[:top_n]
