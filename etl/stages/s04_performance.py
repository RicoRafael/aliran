from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import load, log, save
from transform.normalise import flatten_performance

MAX_SLUGS = 110
EXTRA_YEARS = 3
# Only the largest holders earn a multi-year pull. Sorting by year count instead
# buys three years of history for 200-hectare operators while the majors wait.
EXTRA_YEAR_SLUGS = 45


def _ranked_slugs() -> list[tuple[str, float]]:
    licenses = load("licenses")
    resolution = load("resolution")

    area: dict[str, float] = {}
    for lic in licenses:
        slug = lic.get("company_slug")
        if slug and slug in resolution:
            area[slug] = area.get(slug, 0.0) + float(lic.get("licensed_area_ha") or 0)

    for slug, res in resolution.items():
        if res.get("method") == "api_symbol":
            area.setdefault(slug, 0.0)

    return sorted(area.items(), key=lambda kv: -kv[1])


def run(client) -> dict:
    ranked = _ranked_slugs()[:MAX_SLUGS]
    log(f"probing performance for {len(ranked)} slugs (latest year first)")

    latest: dict[str, list[dict]] = {}
    available: dict[str, list[int]] = {}
    missing: list[str] = []

    for slug, _area in ranked:
        try:
            payload = client.get(f"/v2/mining/companies/performance/{slug}/")
        except Exception as exc:
            if "404" in str(exc):
                missing.append(slug)
                continue
            raise
        rows = flatten_performance(payload)
        if rows:
            latest[slug] = rows
            available[slug] = payload.get("available_years") or []

    log(f"{len(latest)} slugs have performance data, {len(missing)} returned 404")

    multi = {s: yrs for s, yrs in available.items() if len(yrs) >= 2}
    log(f"{len(multi)} slugs report multiple years")

    area_rank = {slug: area for slug, area in ranked}
    extra_targets = sorted(multi.items(), key=lambda kv: -area_rank.get(kv[0], 0.0))[:EXTRA_YEAR_SLUGS]
    log(f"multi-year pull for top {len(extra_targets)} by licensed area")

    history: dict[str, list[dict]] = {s: list(rows) for s, rows in latest.items()}
    fetched_years = 0

    for slug, years in extra_targets:
        newest = max(years)
        for year in sorted((y for y in years if y != newest), reverse=True)[:EXTRA_YEARS]:
            try:
                payload = client.get(f"/v2/mining/companies/performance/{slug}/", {"year": year})
            except Exception:
                continue
            rows = flatten_performance(payload)
            if rows:
                history[slug].extend(rows)
                fetched_years += 1

    with_strip = {s for s, rows in history.items() if any(r.get("strip_ratio") is not None for r in rows)}
    strip_series = {
        s for s, rows in history.items()
        if len({r["year"] for r in rows if r.get("strip_ratio") is not None}) >= 2
    }
    with_reserves = {s for s, rows in history.items() if any(r.get("reserves") is not None for r in rows)}
    with_production = {s for s, rows in history.items() if any(r.get("production_volume") is not None for r in rows)}

    log(f"extra year-pulls: {fetched_years}")
    log(f"strip_ratio present: {len(with_strip)} slugs; 2+ year series: {len(strip_series)}")
    log(f"reserves present: {len(with_reserves)}; production present: {len(with_production)}")

    save("performance", history)
    save("performance_available_years", available)

    return {
        "slugs_probed": len(ranked),
        "with_data": len(latest),
        "not_found": len(missing),
        "multi_year_slugs": len(multi),
        "extra_year_pulls": fetched_years,
        "with_strip_ratio": len(with_strip),
        "strip_ratio_series_2plus": len(strip_series),
        "with_reserves": len(with_reserves),
        "with_production": len(with_production),
        "A3_VIABLE": len(strip_series) >= 10,
    }
