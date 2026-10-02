from datetime import datetime
from tactical_engine.options.contracts import OptionQuote


class OptionChainProvider:
    def get_chain(self, underlying: str, timestamp: datetime) -> list[OptionQuote]:
        raise NotImplementedError


class HistoricalOptionChainProvider(OptionChainProvider):
    def __init__(self, quotes: list[OptionQuote] | None = None):
        self._quotes = quotes or []

    def add_quotes(self, quotes: list[OptionQuote]) -> None:
        self._quotes.extend(quotes)

    def get_chain(self, underlying: str, timestamp: datetime) -> list[OptionQuote]:
        return [
            q for q in self._quotes
            if q.underlying == underlying and q.timestamp == timestamp
        ]
