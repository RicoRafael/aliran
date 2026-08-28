from __future__ import annotations

from _common import log, save, total_count

# Ordered by -licensed_area_ha, so page 1 holds the largest concessions.
# Capping pages therefore drops only small licenses, and the cap protects the
# ownership stage downstream from being starved of credits.
PAGE_CAPS = {"Coal": 32, "Nickel": 14, "Gold": 12, "Copper": 8}


def run(client) -> dict:
    all_rows: list[dict] = []
    summary: dict[str, dict] = {}

    for commodity, page_cap in PAGE_CAPS.items():
        probe = client.get("/v2/mining/licenses/", {"limit": 30, "commodity_type": commodity})
        expected = total_count(probe)

        rows = list(client.paginate(
            "/v2/mining/licenses/",
            {"commodity_type": commodity, "order_by": "-licensed_area_ha"},
            limit=30,
            max_pages=page_cap,
        ))
        linked = [r for r in rows if r.get("company_slug")]
        area = sum(float(r.get("licensed_area_ha") or 0) for r in rows)

        summary[commodity] = {
            "expected_total": expected,
            "fetched": len(rows),
            "with_company_slug": len(linked),
            "slug_density": round(len(linked) / len(rows), 3) if rows else None,
            "distinct_slugs": len({r["company_slug"] for r in linked}),
            "total_area_ha": round(area, 1),
        }
        capped = expected is not None and len(rows) < expected
        summary[commodity]["page_capped"] = capped
        log(f"{commodity:<8} expected={expected} fetched={len(rows)} "
            f"linked={len(linked)} slugs={summary[commodity]['distinct_slugs']} "
            f"area={area:,.0f} ha" + ("  [CAPPED]" if capped else ""))

        for r in rows:
            r["_commodity_query"] = commodity
        all_rows.extend(rows)

    by_code = {r["wiup_code"]: r for r in all_rows if r.get("wiup_code")}
    licenses = list(by_code.values())
    log(f"total unique licenses: {len(licenses)}")

    save("licenses", licenses)
    return {"by_commodity": summary, "unique_licenses": len(licenses)}
