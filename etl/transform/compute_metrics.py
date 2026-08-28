from __future__ import annotations

import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metrics.thresholds import RRR_AMBER, RRR_GREEN, RRR_OUTLIER_ABS
from metrics.track_a import (
    destination_hhi,
    license_cliff_index,
    reserve_life_index,
    rli_flag,
    srd_flag,
    strip_ratio_drift,
)
from transform.normalise import units_comparable


def rrr_flag(ratio: float | None) -> str:
    """Flag the replacement ratio itself — an outlier is not a grade."""
    if ratio is None:
        return "unknown"
    if abs(ratio - 1.0) > RRR_OUTLIER_ABS:
        return "unknown"
    if ratio >= RRR_GREEN:
        return "neutral"
    if ratio >= RRR_AMBER:
        return "amber"
    return "red"


def rrr_is_outlier(ratio: float | None) -> bool:
    return ratio is not None and abs(ratio - 1.0) > RRR_OUTLIER_ABS

MIN_CONFIDENCE = 0.85


def _slugs_by_ticker(resolution: dict) -> dict[str, list[tuple[str, float]]]:
    out: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for slug, res in resolution.items():
        if res.get("confidence", 0) < MIN_CONFIDENCE:
            continue
        out[res["symbol"]].append((slug, float(res.get("attributable_share") or 1.0)))
    return out


def _entity_basis(rows: list[dict]) -> dict[tuple, dict]:
    """
    Per-entity, per-(commodity, unit) reserves and production from the SAME year.

    Reserves and production must come from one entity and one reporting year, or
    the ratio is meaningless. Aggregating across entities first — which an earlier
    version did — produced reserve lives of 500+ years for multi-entity issuers,
    because the numerator and denominator described different companies.
    """
    by_key_year: dict[tuple, dict[int, dict]] = defaultdict(dict)
    for r in rows:
        year = r.get("year")
        if year is None:
            continue
        key = (r.get("commodity_type"), r.get("unit"))
        slot = by_key_year[key].setdefault(int(year), {"reserves": None, "production": None,
                                                       "unit_mismatch": False})
        if r.get("reserves") is not None:
            if units_comparable(r.get("unit"), r.get("reserve_unit")):
                slot["reserves"] = float(r["reserves"])
            else:
                slot["unit_mismatch"] = True
        if r.get("production_volume") is not None:
            slot["production"] = float(r["production_volume"])

    out: dict[tuple, dict] = {}
    for key, years in by_key_year.items():
        paired = [y for y, v in years.items() if v["reserves"] is not None and v["production"]]
        reserves_years = [y for y, v in years.items() if v["reserves"] is not None]
        prod_years = [y for y, v in years.items() if v["production"] is not None]

        latest_paired = max(paired) if paired else None
        out[key] = {
            "commodity": key[0],
            "unit": key[1],
            "paired_year": latest_paired,
            "reserves": years[latest_paired]["reserves"] if latest_paired else None,
            "production": years[latest_paired]["production"] if latest_paired else None,
            "reserves_latest": years[max(reserves_years)]["reserves"] if reserves_years else None,
            "reserves_latest_year": max(reserves_years) if reserves_years else None,
            "reserves_earliest": years[min(reserves_years)]["reserves"] if reserves_years else None,
            "reserves_earliest_year": min(reserves_years) if reserves_years else None,
            "production_by_year": {y: years[y]["production"] for y in prod_years},
            "unit_mismatch": any(v["unit_mismatch"] for v in years.values()),
        }
    return out


def _entity_rrr(basis: dict) -> float | None:
    """Reserve replacement for ONE entity and one commodity/unit pair."""
    first, last = basis.get("reserves_earliest_year"), basis.get("reserves_latest_year")
    if first is None or last is None or first == last:
        return None
    produced = sum(v for y, v in (basis.get("production_by_year") or {}).items()
                   if v is not None and first < y <= last)
    if produced <= 0:
        return None
    delta = (basis.get("reserves_latest") or 0) - (basis.get("reserves_earliest") or 0)
    return (delta + produced) / produced


def _strip_points(rows_by_slug: dict[str, list[dict]], slugs: list[tuple[str, float]]) -> list[tuple[float, float]]:
    per_year: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for slug, _share in slugs:
        for r in rows_by_slug.get(slug, []):
            if r.get("strip_ratio") is None or r.get("year") is None:
                continue
            weight = float(r.get("production_volume") or 1.0)
            per_year[int(r["year"])].append((float(r["strip_ratio"]), weight))
    points = []
    for year, pairs in sorted(per_year.items()):
        total_w = sum(w for _, w in pairs)
        if total_w <= 0:
            continue
        points.append((float(year), sum(v * w for v, w in pairs) / total_w))
    return points


def _aggregate_reserve_metrics(
    rows_by_slug: dict[str, list[dict]], slugs: list[tuple[str, float]]
) -> dict:
    """
    Attributable reserves and production, restricted to entity/commodity pairs
    that report BOTH in the same year. RRR is production-weighted across entities
    with a valid multi-year series.
    """
    dominant_unit: dict[tuple, dict] = defaultdict(
        lambda: {"reserves": 0.0, "production": 0.0, "entities": 0, "unit_mismatch": False}
    )
    rrr_pairs: list[tuple[float, float]] = []

    for slug, share in slugs:
        for key, basis in _entity_basis(rows_by_slug.get(slug, [])).items():
            if basis["reserves"] is not None and basis["production"]:
                bucket = dominant_unit[key]
                bucket["reserves"] += basis["reserves"] * share
                bucket["production"] += basis["production"] * share
                bucket["entities"] += 1
                bucket["unit_mismatch"] |= basis["unit_mismatch"]

            ratio = _entity_rrr(basis)
            if ratio is not None:
                weight = sum(v for v in (basis.get("production_by_year") or {}).values() if v)
                rrr_pairs.append((ratio, (weight or 1.0) * share))

    dominant = None
    if dominant_unit:
        key, bucket = max(dominant_unit.items(), key=lambda kv: kv[1]["reserves"])
        dominant = {
            "commodity": key[0],
            "unit": key[1],
            "reserves": bucket["reserves"],
            "production": bucket["production"],
            "entities_contributing": bucket["entities"],
            "unit_mismatch": bucket["unit_mismatch"],
        }

    rrr = None
    if rrr_pairs:
        total_w = sum(w for _, w in rrr_pairs)
        if total_w > 0:
            rrr = sum(v * w for v, w in rrr_pairs) / total_w

    return {
        "dominant": dominant,
        "rrr": rrr,
        "rrr_entity_count": len(rrr_pairs),
    }


def _hhi_for(slugs: list[tuple[str, float]], sales: dict) -> dict:
    volume: dict[str, float] = defaultdict(float)
    revenue: dict[str, float] = defaultdict(float)
    for slug, _share in slugs:
        entry = sales.get(slug)
        if not entry:
            continue
        for country, c in entry.get("countries", {}).items():
            if c.get("pct_volume") is not None:
                volume[country] += float(c["pct_volume"])
            if c.get("pct_revenue") is not None:
                revenue[country] += float(c["pct_revenue"])
    if volume:
        return {**destination_hhi(dict(volume)), "basis": "sales_volume"}
    if revenue:
        return {**destination_hhi(dict(revenue)), "basis": "revenue"}
    return {"hhi": None, "max_share": None, "top_country": None, "flag": "unknown", "basis": None}


def compute(
    resolution: dict,
    licenses: list[dict],
    performance: dict,
    site_details: dict,
    equity: dict,
    sales: dict,
    as_of: dt.date,
) -> list[dict]:
    by_ticker = _slugs_by_ticker(resolution)
    lic_by_slug: dict[str, list[dict]] = defaultdict(list)
    for lic in licenses:
        if lic.get("company_slug"):
            lic_by_slug[lic["company_slug"]].append(lic)

    sites_by_slug: dict[str, list[dict]] = defaultdict(list)
    for site in site_details.values():
        if site.get("company_slug"):
            sites_by_slug[site["company_slug"]].append(site)

    out = []
    for ticker, slugs in by_ticker.items():
        slug_names = [s for s, _ in slugs]
        shares = {s: sh for s, sh in slugs}

        ticker_licenses = [l for s in slug_names for l in lic_by_slug.get(s, [])]
        lci = license_cliff_index(ticker_licenses, as_of, shares)

        licence_commodity = None
        if ticker_licenses:
            area_by_commodity: dict[str, float] = defaultdict(float)
            for l in ticker_licenses:
                if l.get("commodity_type"):
                    area_by_commodity[l["commodity_type"]] += float(l.get("licensed_area_ha") or 0)
            if area_by_commodity:
                licence_commodity = max(area_by_commodity.items(), key=lambda kv: kv[1])[0]

        perf_rows = [r for s in slug_names for r in performance.get(s, [])]
        agg = _aggregate_reserve_metrics(performance, slugs)
        dominant = agg["dominant"]
        rli = reserve_life_index(dominant["reserves"], dominant["production"]) if dominant else None

        strip_points = _strip_points(performance, slugs)
        slope = strip_ratio_drift(strip_points)
        hhi = _hhi_for(slugs, sales)

        eq = equity.get(ticker) or {}
        mcap = eq.get("market_cap")
        mcap_per_tonne = None
        if mcap and dominant and dominant.get("reserves"):
            mcap_per_tonne = float(mcap) / float(dominant["reserves"])

        coords = [
            {"slug": s["slug"], "name": s.get("name"), "lat": s.get("latitude"), "lon": s.get("longitude"),
             "commodity": s.get("commodity_type"), "production": s.get("production_volume"),
             "unit": s.get("unit"), "reserves": s.get("reserves"), "reserve_unit": s.get("reserve_unit")}
            for slug in slug_names for s in sites_by_slug.get(slug, [])
            if s.get("latitude") is not None
        ]

        out.append({
            "symbol": ticker,
            "company_name": eq.get("company_name"),
            "sub_sector": eq.get("sub_sector"),
            "market_cap": mcap,
            "market_cap_rank": eq.get("market_cap_rank"),
            "entity_count": len(slug_names),
            "entities": slug_names,
            "license_count": len(ticker_licenses),
            "lci_12m": lci["lci_12m"],
            "lci_24m": lci["lci_24m"],
            "lci_36m": lci["lci_36m"],
            "expired_share": lci["expired_share"],
            "licensed_ha_weighted": lci["total_ha_weighted"],
            "lci_flag": lci["flag"],
            "lci_counts": lci["counts"],
            "rli_years": rli,
            "rli_flag": rli_flag(rli),
            "dominant_commodity": (dominant["commodity"] if dominant else None) or licence_commodity,
            "commodity_source": "production" if dominant and dominant.get("commodity") else (
                "licence_area" if licence_commodity else None
            ),
            "reserves": dominant["reserves"] if dominant else None,
            "reserve_unit": dominant["unit"] if dominant else None,
            "production": dominant["production"] if dominant else None,
            "unit_mismatch": dominant["unit_mismatch"] if dominant else False,
            "rli_entities_contributing": dominant["entities_contributing"] if dominant else 0,
            # Level and slope are separate facts. Strip-ratio level is not
            # comparable between mines (it depends on geology), so only the
            # slope carries a flag — the level is rendered without colour.
            "strip_ratio_latest": strip_points[-1][1] if strip_points else None,
            "strip_ratio_points": strip_points,
            "strip_ratio_years": len(strip_points),
            "strip_ratio_slope": slope,
            "strip_flag": srd_flag(slope),
            "reserve_replacement_ratio": agg["rrr"],
            "reserve_replacement_flag": rrr_flag(agg["rrr"]),
            "reserve_replacement_outlier": rrr_is_outlier(agg["rrr"]),
            "reserve_replacement_entities": agg["rrr_entity_count"],
            "hhi": hhi.get("hhi"),
            "hhi_top_country": hhi.get("top_country"),
            "hhi_max_share": hhi.get("max_share"),
            "hhi_flag": hhi.get("flag"),
            "hhi_basis": hhi.get("basis"),
            "market_cap_per_reserve_unit": mcap_per_tonne,
            "site_coords": coords,
            "performance_years": sorted({r["year"] for r in perf_rows if r.get("year")}),
        })

    # A ticker with neither a licence nor a production record has nothing to show.
    # Carrying it into the screener pads the coverage numbers with empty rows.
    out = [r for r in out if r["license_count"] > 0 or r["performance_years"]]
    out.sort(key=lambda r: -(r["licensed_ha_weighted"] or 0))
    return out
