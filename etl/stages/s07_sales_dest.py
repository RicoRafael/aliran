from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import load, log, save

MAX_SLUGS = 40


def run(client) -> dict:
    performance = load("performance")
    resolution = load("resolution")

    producers = [
        slug for slug, rows in performance.items()
        if slug in resolution and any(r.get("production_volume") or r.get("sales_volume") for r in rows)
    ]
    log(f"{len(producers)} producing slugs; capping at {MAX_SLUGS}")

    dest: dict[str, dict] = {}
    not_found = 0
    for slug in producers[:MAX_SLUGS]:
        try:
            payload = client.get(f"/v2/mining/sales-destination/{slug}/")
        except Exception as exc:
            if "404" in str(exc):
                not_found += 1
                continue
            raise
        if not isinstance(payload, dict):
            continue
        body = payload.get("data")
        if not isinstance(body, dict) or not body:
            continue
        dest[slug] = {
            "year": payload.get("year"),
            "countries": {
                country: {
                    "revenue_usd": v.get("revenue_usd"),
                    "pct_revenue": v.get("percentage_of_total_revenue"),
                    "volume": v.get("volume"),
                    "pct_volume": v.get("percentage_of_sales_volume"),
                    "commodity_type": v.get("commodity_type"),
                    "unit": v.get("unit"),
                }
                for country, v in body.items() if isinstance(v, dict)
            },
        }

    with_revenue = sum(1 for d in dest.values()
                       if any(c["pct_revenue"] is not None for c in d["countries"].values()))
    with_volume = sum(1 for d in dest.values()
                      if any(c["pct_volume"] is not None for c in d["countries"].values()))

    log(f"{len(dest)} slugs with destination data ({not_found} 404s)")
    log(f"revenue-share populated: {with_revenue} · volume-share populated: {with_volume}")

    save("sales_destinations", dest)
    return {
        "producers": len(producers),
        "fetched": len(dest),
        "not_found": not_found,
        "with_revenue_share": with_revenue,
        "with_volume_share": with_volume,
        "HHI_BASIS": "pct_volume" if with_volume >= with_revenue else "pct_revenue",
    }
