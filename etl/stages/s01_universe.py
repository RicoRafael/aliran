from __future__ import annotations

from _common import log, rows_of, save, total_count


def run(client) -> dict:
    probe = client.get("/v2/mining/companies/", {"limit": 30, "offset": 0})
    expected = total_count(probe)
    log(f"total mining companies reported: {expected}")

    rows = list(client.paginate("/v2/mining/companies/", limit=30, max_pages=16))
    by_slug = {r["slug"]: r for r in rows if r.get("slug")}
    companies = list(by_slug.values())

    listed = [c for c in companies if c.get("symbol")]
    unlisted = [c for c in companies if not c.get("symbol")]

    types: dict[str, int] = {}
    for c in companies:
        types[c.get("company_type") or "unknown"] = types.get(c.get("company_type") or "unknown", 0) + 1

    log(f"fetched {len(companies)} unique companies ({len(listed)} listed, {len(unlisted)} unlisted)")
    log(f"types: {types}")
    log(f"listed symbols: {sorted(c['symbol'] for c in listed)}")

    save("companies", companies)
    return {
        "expected_total": expected,
        "fetched": len(companies),
        "listed": len(listed),
        "unlisted": len(unlisted),
        "listed_symbols": sorted(c["symbol"] for c in listed),
        "company_types": types,
    }
