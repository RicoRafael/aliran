from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import load, log, save, total_count

SUBSECTORS = ["oil-gas-coal", "basic-materials"]


def _resolved_tickers() -> list[str]:
    resolution = load("resolution")
    licenses = load("licenses")
    licensed = {l.get("company_slug") for l in licenses if l.get("company_slug")}
    tickers = {
        r["symbol"] for slug, r in resolution.items()
        if slug in licensed and r.get("confidence", 0) >= 0.85
    }
    return sorted(tickers)


def run(client) -> dict:
    universe: dict[str, dict] = {}
    for sub in SUBSECTORS:
        probe = client.get("/v2/companies/", {"where": f"sub_sector = '{sub}'", "limit": 30})
        expected = total_count(probe)
        rows = list(client.paginate("/v2/companies/", {"where": f"sub_sector = '{sub}'",
                                                       "order_by": "-market_cap"},
                                    limit=30, max_pages=5))
        log(f"{sub:<18} expected={expected} fetched={len(rows)}")
        for r in rows:
            if r.get("symbol"):
                universe[r["symbol"]] = {**r, "sub_sector": sub}

    tickers = _resolved_tickers()
    log(f"fetching overview for {len(tickers)} resolved tickers")

    overview: dict[str, dict] = {}
    failures: list[str] = []
    for symbol in tickers:
        try:
            rep = client.get(f"/v2/company/report/{symbol}/", {"sections": "overview"}, cost=1)
        except Exception as exc:
            failures.append(f"{symbol}: {type(exc).__name__}")
            continue
        if not isinstance(rep, dict):
            continue
        ov = rep.get("overview") or {}
        overview[symbol] = {
            "symbol": rep.get("symbol") or symbol,
            "company_name": rep.get("company_name"),
            "sector": ov.get("sector"),
            "sub_sector": ov.get("sub_sector"),
            "market_cap": ov.get("market_cap"),
            "market_cap_rank": ov.get("market_cap_rank"),
            "last_close_price": ov.get("last_close_price"),
            "listing_date": ov.get("listing_date"),
            "employee_num": ov.get("employee_num"),
            "indices": ov.get("indices"),
            "raw_overview_keys": sorted(ov.keys()),
        }

    with_mcap = sum(1 for v in overview.values() if v.get("market_cap"))
    log(f"{len(overview)} overviews fetched, {with_mcap} carry market_cap")
    if failures:
        log(f"{len(failures)} failures: {failures[:5]}")

    save("equity_universe", universe)
    save("equity_overview", overview)
    return {
        "subsector_universe": len(universe),
        "tickers_requested": len(tickers),
        "overviews_fetched": len(overview),
        "with_market_cap": with_mcap,
        "failures": failures,
    }
