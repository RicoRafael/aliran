"""
Sectors Financial API v2 client — cache-first, credit-metered.

Three guarantees:
  1. A response already on disk costs 0 credits. Dev iteration is free.
  2. No call can exceed the active tranche cap. CreditExhausted is raised first.
  3. Every billed call is appended to docs/credit-ledger.jsonl — committed
     evidence of real, metered API usage for the judges.

Billing rules (docs changelog 2026-07-31):
  2xx and 404 bill the endpoint's stated cost.
  400, 401/403, 429 and 5xx are FREE — retry 429/503 freely with backoff.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import time
from typing import Any, Iterator

import requests

BASE = "https://api.sectors.app"
ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "fixtures" / "raw"
LEDGER = ROOT / "docs" / "credit-ledger.jsonl"

# Endpoints whose cost is NOT a flat 1 credit. Read MASTER.md §8 "credit traps".
#   /v2/company/report/      → 1 PER SECTION  (default all 8 = 8 credits)
#   /v2/subsector/report/    → 1 PER SECTION  (default all 6 = 6 credits)
#   /v2/companies/top-changes/ → 1 per classification × period (default = 10)
#   /v2/financials/quarterly/  → 1 PER QUARTER returned
#   /v2/companies/?q=        → 3 (natural language); ?where= → 1
# Always pass `cost=` explicitly for these. The default of 1 will under-count.
DEFAULT_COST = 1


class CreditExhausted(RuntimeError):
    """Raised instead of spending past the tranche cap."""


class OfflineMiss(RuntimeError):
    """STRATA_OFFLINE=1 and the response is not in the cache."""


class Sectors:
    def __init__(
        self,
        api_key: str | None = None,
        tranche_cap: int | None = None,
        offline: bool | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("SECTORS_API_KEY", "")
        self.cap = int(tranche_cap if tranche_cap is not None else os.environ.get("STRATA_TRANCHE_CAP", 40))
        self.offline = bool(int(os.environ.get("STRATA_OFFLINE", 0)) if offline is None else offline)
        self.spent = 0
        self.calls = 0
        self.cache_hits = 0

        if not self.offline and not self.api_key:
            raise RuntimeError(
                "SECTORS_API_KEY is not set. Copy etl/.env.example to etl/.env "
                "and paste your key there (never into chat or a commit)."
            )

    # ── internals ────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(path: str, params: dict[str, Any]) -> str:
        canon = f"{path}?{json.dumps(sorted(params.items()), sort_keys=True)}"
        return hashlib.sha256(canon.encode()).hexdigest()[:24]

    def _log(self, path: str, params: dict, status: int | str, billed: int) -> None:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                        "path": path,
                        "params": params,
                        "status": status,
                        "billed": billed,
                        "cumulative": self.spent,
                    }
                )
                + "\n"
            )

    # ── public ───────────────────────────────────────────────────────────

    def get(self, path: str, params: dict[str, Any] | None = None, cost: int = DEFAULT_COST) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        blob = CACHE_DIR / f"{self._cache_key(path, params)}.json"

        if blob.exists():
            self.cache_hits += 1
            return json.loads(blob.read_text(encoding="utf-8"))

        if self.offline:
            raise OfflineMiss(f"STRATA_OFFLINE=1 and no cached response for {path} {params}")

        if self.spent + cost > self.cap:
            raise CreditExhausted(
                f"tranche cap {self.cap} would be exceeded by {path} "
                f"(cost {cost}, spent {self.spent}). Raise STRATA_TRANCHE_CAP deliberately."
            )

        resp = None
        for attempt in range(5):
            resp = requests.get(
                f"{BASE}{path}",
                headers={"Authorization": self.api_key},  # raw key, no Bearer
                params=params,
                timeout=30,
            )
            # 429 and 503 are free by policy — back off without burning credits.
            if resp.status_code in (429, 503):
                self._log(path, params, resp.status_code, 0)
                time.sleep(2**attempt)
                continue
            break

        assert resp is not None
        billed = cost if (resp.status_code < 300 or resp.status_code == 404) else 0
        self.spent += billed
        self.calls += 1
        self._log(path, params, resp.status_code, billed)

        resp.raise_for_status()
        data = resp.json()

        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.35)  # docs are explicit: sleep(0.3) is not optional
        return data

    # Spike P2/P3 measured the server cap: limit is clamped to 30 regardless of
    # what you ask for. Requesting more just wastes the round trip.
    MAX_LIMIT = 30

    def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int = MAX_LIMIT,
        max_pages: int = 40,
        cost_per_page: int = 1,
    ) -> Iterator[dict]:
        """
        Yield rows across pages. Stops on a short page, an empty page, or max_pages.

        max_pages is a credit guard, not a convenience — an unbounded loop over
        /v2/mining/licenses/ could drain a whole tranche. Always keep it tight.
        """
        offset = 0
        for _ in range(max_pages):
            page = self.get(path, {**(params or {}), "limit": limit, "offset": offset}, cost=cost_per_page)
            rows = page.get("results") if isinstance(page, dict) else page
            if not rows:
                return
            yield from rows
            if len(rows) < limit:
                return
            offset += limit

    def summary(self) -> str:
        return (
            f"credits spent={self.spent}/{self.cap} · live calls={self.calls} "
            f"· cache hits={self.cache_hits} · ledger={LEDGER.relative_to(ROOT)}"
        )
