from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _common import load, log, save, total_count
from transform.normalise import site_location, site_reserves

COMMODITIES = ["Coal", "Nickel", "Gold", "Copper"]
MAX_DETAILS = 60


def run(client) -> dict:
    resolution = load("resolution")

    listing: list[dict] = []
    per_commodity: dict[str, dict] = {}
    for commodity in COMMODITIES:
        probe = client.get("/v2/mining/sites/", {"limit": 30, "commodity_type": commodity})
        expected = total_count(probe)
        rows = list(client.paginate("/v2/mining/sites/", {"commodity_type": commodity},
                                    limit=30, max_pages=6))
        per_commodity[commodity] = {"expected": expected, "fetched": len(rows)}
        log(f"{commodity:<8} sites expected={expected} fetched={len(rows)}")
        listing.extend(rows)

    by_slug = {r["slug"]: r for r in listing if r.get("slug")}
    sites = list(by_slug.values())

    resolved_sites = [s for s in sites if s.get("company_slug") in resolution]
    resolved_sites.sort(key=lambda s: -(float(s.get("production_volume") or 0)))
    log(f"{len(sites)} unique sites, {len(resolved_sites)} belong to a resolved company")

    targets = resolved_sites[:MAX_DETAILS]
    if len(resolved_sites) > MAX_DETAILS:
        log(f"capping details at {MAX_DETAILS}; {len(resolved_sites) - MAX_DETAILS} sites not detailed")

    details: dict[str, dict] = {}
    with_coords = with_reserves = 0
    for site in targets:
        slug = site["slug"]
        try:
            detail = client.get(f"/v2/mining/sites/{slug}/")
        except Exception:
            continue
        loc = site_location(detail)
        reserves, unit = site_reserves(detail)
        if loc.get("latitude") is not None:
            with_coords += 1
        if reserves is not None:
            with_reserves += 1
        details[slug] = {
            "slug": slug,
            "name": detail.get("name") if isinstance(detail, dict) else None,
            "company_slug": site.get("company_slug"),
            "company_name": site.get("company_name"),
            "commodity_type": site.get("commodity_type"),
            "year": site.get("year"),
            "production_volume": site.get("production_volume"),
            "unit": site.get("unit"),
            "strip_ratio": detail.get("strip_ratio") if isinstance(detail, dict) else None,
            "reserves": reserves,
            "reserve_unit": unit,
            **loc,
            "raw_resources_reserves": detail.get("resources_reserves") if isinstance(detail, dict) else None,
        }

    log(f"{len(details)} details fetched · {with_coords} with coordinates · {with_reserves} with reserves")

    save("sites", sites)
    save("site_details", details)
    return {
        "per_commodity": per_commodity,
        "unique_sites": len(sites),
        "sites_of_resolved_companies": len(resolved_sites),
        "details_fetched": len(details),
        "with_coordinates": with_coords,
        "with_reserves": with_reserves,
        "MAP_VIABLE": with_coords >= 20,
    }
