"""Point-in-time historical option chain providers.

The provider never looks forward. For an as-of timestamp it returns the latest
available quote for each contract whose timestamp is <= the requested time and
whose age is within the caller's explicit freshness limit.
"""

from datetime import datetime

from tactical_engine.options.contracts import OptionQuote


class OptionChainProvider:
    def get_chain(
        self,
        underlying: str,
        timestamp: datetime,
        *,
        max_age_seconds: float | None = 60.0,
    ) -> list[OptionQuote]:
        raise NotImplementedError

    def get_quote(
        self,
        symbol: str,
        timestamp: datetime,
        *,
        max_age_seconds: float | None = 60.0,
    ) -> OptionQuote | None:
        raise NotImplementedError


class HistoricalOptionChainProvider(OptionChainProvider):
    def __init__(self, quotes: list[OptionQuote] | None = None):
        self._quotes: list[OptionQuote] = []
        self._seen_keys: set[tuple[str, str, datetime]] = set()
        self.add_quotes(quotes or [])

    def add_quotes(self, quotes: list[OptionQuote]) -> None:
        for quote in quotes:
            if quote.timestamp.tzinfo is None:
                raise ValueError("Historical option quotes must use timezone-aware timestamps")
            key = (quote.underlying, quote.symbol, quote.timestamp)
            if key in self._seen_keys:
                raise ValueError(
                    f"Duplicate historical option quote for {quote.symbol} at {quote.timestamp.isoformat()}"
                )
            self._seen_keys.add(key)
            self._quotes.append(quote)

        self._quotes.sort(key=lambda q: (q.underlying, q.symbol, q.timestamp))

    @staticmethod
    def _fresh_enough(
        quote: OptionQuote,
        timestamp: datetime,
        max_age_seconds: float | None,
    ) -> bool:
        if quote.timestamp > timestamp:
            return False
        if max_age_seconds is None:
            return True
        age = (timestamp - quote.timestamp).total_seconds()
        return 0.0 <= age <= max_age_seconds

    def get_quote(
        self,
        symbol: str,
        timestamp: datetime,
        *,
        max_age_seconds: float | None = 60.0,
    ) -> OptionQuote | None:
        candidates = [
            q
            for q in self._quotes
            if q.symbol == symbol and self._fresh_enough(q, timestamp, max_age_seconds)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda q: q.timestamp)

    def get_chain(
        self,
        underlying: str,
        timestamp: datetime,
        *,
        max_age_seconds: float | None = 60.0,
    ) -> list[OptionQuote]:
        latest_by_contract: dict[str, OptionQuote] = {}
        for quote in self._quotes:
            if quote.underlying != underlying:
                continue
            if not self._fresh_enough(quote, timestamp, max_age_seconds):
                continue
            current = latest_by_contract.get(quote.symbol)
            if current is None or quote.timestamp > current.timestamp:
                latest_by_contract[quote.symbol] = quote

        return [latest_by_contract[symbol] for symbol in sorted(latest_by_contract)]
