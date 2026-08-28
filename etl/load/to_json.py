"""Web-ready JSON export.

The Next.js build reads these instead of the SQLite file so the web layer has no
native-module dependency. SQLite remains the analysis surface.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
WEB = ROOT / "data" / "web"

FLAG_ORDER = {"red": 0, "amber": 1, "neutral": 2, "unknown": 3}


def _bounds(sites: list[dict]) -> dict | None:
    lats = [s["lat"] for s in sites if s.get("lat") is not None]
    lons = [s["lon"] for s in sites if s.get("lon") is not None]
    if not lats or not lons:
        return None
    return {"min_lat": min(lats), "max_lat": max(lats), "min_lon": min(lons), "max_lon": max(lons)}


def _license_rows(licenses: list[dict], resolution: dict, as_of: dt.date) -> dict[str, list[dict]]:
    by_ticker: dict[str, list[dict]] = defaultdict(list)
    for lic in licenses:
        slug = lic.get("company_slug")
        res = resolution.get(slug) if slug else None
        if not res or res.get("confidence", 0) < 0.85:
            continue
        expiry = lic.get("license_expiry_date")
        months = None
        if expiry:
            try:
                months = round((dt.date.fromisoformat(expiry[:10]) - as_of).days / 30.4375, 1)
            except ValueError:
                months = None
        by_ticker[res["symbol"]].append({
            "wiup_code": lic.get("wiup_code"),
            "license_number": lic.get("license_number"),
            "license_type": lic.get("license_type"),
            "activity": lic.get("activity"),
            "commodity_type": lic.get("commodity_type"),
            "province": lic.get("province"),
            "city": lic.get("city"),
            "company_name": lic.get("company_name"),
            "company_slug": slug,
            "effective_date": lic.get("license_effective_date"),
            "expiry_date": expiry,
            "months_to_expiry": months,
            "area_ha": lic.get("licensed_area_ha"),
            "cnc": lic.get("cnc"),
            "attributable_share": res.get("attributable_share"),
            "resolution_method": res.get("method"),
            "resolution_confidence": res.get("confidence"),
        })
    for rows in by_ticker.values():
        rows.sort(key=lambda r: (r["expiry_date"] or "9999", -(r["area_ha"] or 0)))
    return by_ticker


def export(metrics: list[dict], licenses: list[dict], resolution: dict,
           performance: dict, as_of: dt.date, coverage: dict) -> dict:
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "issuers").mkdir(exist_ok=True)

    lic_by_ticker = _license_rows(licenses, resolution, as_of)

    index = []
    for m in metrics:
        ha = m.get("licensed_ha_weighted") or 0
        index.append({
            "symbol": m["symbol"],
            "ticker": m["symbol"].replace(".JK", ""),
            "company_name": m.get("company_name"),
            "sub_sector": m.get("sub_sector"),
            "market_cap": m.get("market_cap"),
            "dominant_commodity": m.get("dominant_commodity"),
            "commodity_source": m.get("commodity_source"),
            # Materiality, not just proportion: a 37% cliff on 2,766 ha matters
            # far less than a 32% cliff on 112,963 ha.
            "exposed_ha_24m": (m.get("lci_24m") or 0) * ha if m.get("lci_24m") is not None else None,
            "exposed_ha_12m": (m.get("lci_12m") or 0) * ha if m.get("lci_12m") is not None else None,
            "entity_count": m.get("entity_count"),
            "license_count": m.get("license_count"),
            "licensed_ha_weighted": m.get("licensed_ha_weighted"),
            "lci_12m": m.get("lci_12m"),
            "lci_24m": m.get("lci_24m"),
            "lci_36m": m.get("lci_36m"),
            "lci_flag": m.get("lci_flag"),
            "expired_share": m.get("expired_share"),
            "rli_years": m.get("rli_years"),
            "rli_flag": m.get("rli_flag"),
            "reserves": m.get("reserves"),
            "reserve_unit": m.get("reserve_unit"),
            "production": m.get("production"),
            "strip_ratio_latest": m.get("strip_ratio_latest"),
            "strip_ratio_slope": m.get("strip_ratio_slope"),
            "strip_flag": m.get("strip_flag"),
            "reserve_replacement_ratio": m.get("reserve_replacement_ratio"),
            "hhi": m.get("hhi"),
            "hhi_top_country": m.get("hhi_top_country"),
            "hhi_max_share": m.get("hhi_max_share"),
            "hhi_flag": m.get("hhi_flag"),
            "site_count": len(m.get("site_coords") or []),
        })

    index.sort(key=lambda r: (
        FLAG_ORDER.get(r["lci_flag"], 3),
        -(r["lci_24m"] or 0),
        -(r["licensed_ha_weighted"] or 0),
    ))

    (WEB / "index.json").write_text(
        json.dumps({
            "as_of": as_of.isoformat(),
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "issuer_count": len(index),
            "coverage": coverage,
            "issuers": index,
        }, indent=1, default=str),
        encoding="utf-8",
    )

    for m in metrics:
        symbol = m["symbol"]
        slugs = set(m.get("entities") or [])
        perf = [
            {**r, "company_slug": slug}
            for slug in slugs for r in performance.get(slug, [])
        ]
        perf.sort(key=lambda r: (r.get("year") or 0))
        payload = {
            "as_of": as_of.isoformat(),
            "metrics": m,
            "licenses": lic_by_ticker.get(symbol, []),
            "performance": perf,
            "sites": m.get("site_coords") or [],
        }
        (WEB / "issuers" / f"{symbol.replace('.JK', '')}.json").write_text(
            json.dumps(payload, indent=1, default=str), encoding="utf-8")

    all_sites = []
    for m in metrics:
        symbol = m["symbol"]
        ticker = symbol.replace(".JK", "")
        owned = {e for e in (m.get("entities") or [])}
        future = [
            l for l in lic_by_ticker.get(symbol, [])
            if l["months_to_expiry"] is not None and l["months_to_expiry"] >= 0
        ]
        soonest = min((l["months_to_expiry"] for l in future), default=None)

        for s in m.get("site_coords") or []:
            site_licences = [l for l in future if l["company_slug"] == s.get("company_slug")]
            site_soonest = min((l["months_to_expiry"] for l in site_licences), default=None)
            all_sites.append({
                **s,
                "symbol": symbol,
                "ticker": ticker,
                "company_name": m.get("company_name"),
                "site_months_to_expiry": site_soonest,
                "issuer_months_to_expiry": soonest,
                "lci_24m": m.get("lci_24m"),
                "lci_flag": m.get("lci_flag"),
                "owned_entities": len(owned),
            })

    (WEB / "sites.json").write_text(
        json.dumps({
            "as_of": as_of.isoformat(),
            "count": len(all_sites),
            "bounds": _bounds(all_sites),
            "sites": all_sites,
        }, indent=1, default=str),
        encoding="utf-8",
    )

    return {
        "index_issuers": len(index),
        "issuer_files": len(metrics),
        "sites": len(all_sites),
        "licenses_attributed": sum(len(v) for v in lic_by_ticker.values()),
    }
