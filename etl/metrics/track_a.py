"""
Track A — physical asset to equity risk.

Pure functions over normalised dicts. No I/O, no network, no API shapes.
Every function tolerates missing data by returning None rather than raising:
government-scraped mining data has real gaps and the pipeline must survive them.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Iterable, Sequence

from .thresholds import (
    DAYS_PER_MONTH,
    HHI_AMBER,
    LCI_24M_AMBER,
    LCI_24M_RED,
    NON_CNC_RISK_WEIGHT,
    OWNERSHIP_MAX_DEPTH,
    RLI_AMBER,
    RLI_RED,
    SINGLE_COUNTRY_RED,
    SRD_AMBER,
    SRD_MIN_POINTS,
    SRD_RED,
)

# ══════════════════════════════════════════════════════════════════════════
#  A1 — Reserve Life Index
# ══════════════════════════════════════════════════════════════════════════


def reserve_life_index(reserves: float | None, annual_production: float | None) -> float | None:
    """
    Years of production remaining at the current extraction rate.

    Both arguments MUST already be in the same unit. Never mix units here —
    normalise upstream and assert on the `unit` field.
    """
    if reserves is None or annual_production is None:
        return None
    if annual_production <= 0 or reserves < 0:
        return None
    return reserves / annual_production


def rli_flag(rli: float | None) -> str:
    if rli is None:
        return "unknown"
    if rli < RLI_RED:
        return "red"
    if rli < RLI_AMBER:
        return "amber"
    return "neutral"


# ══════════════════════════════════════════════════════════════════════════
#  Ownership attribution
# ══════════════════════════════════════════════════════════════════════════


def attributable_share(
    edges: Iterable[dict[str, Any]],
    issuer: str,
    target: str,
    max_depth: int = OWNERSHIP_MAX_DEPTH,
) -> float:
    """
    Effective economic interest of `issuer` in `target`.

    edges: [{"parent": str, "child": str, "pct": float 0-100}, ...]

    Returns the product of ownership percentages along the DOMINANT control
    path (the strongest single chain), not the sum across all paths — summing
    would double-count a diamond structure.

    Returns 1.0 when issuer == target, 0.0 when unreachable within max_depth.
    """
    if issuer == target:
        return 1.0

    adj: dict[str, list[tuple[str, float]]] = {}
    for e in edges:
        pct = e.get("pct")
        if pct is None:
            continue
        adj.setdefault(e["parent"], []).append((e["child"], float(pct) / 100.0))

    best = 0.0

    def walk(node: str, share: float, depth: int, seen: frozenset[str]) -> None:
        nonlocal best
        if depth > max_depth or share <= best:
            return  # prune: this branch cannot beat the incumbent
        for child, frac in adj.get(node, []):
            if child in seen:
                continue  # cycle guard
            nxt = share * frac
            if child == target:
                best = max(best, nxt)
            else:
                walk(child, nxt, depth + 1, seen | {child})

    walk(issuer, 1.0, 1, frozenset({issuer}))
    return best


# ══════════════════════════════════════════════════════════════════════════
#  A2 — License Cliff Index  (the flagship signal)
# ══════════════════════════════════════════════════════════════════════════


def _parse_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    if not value:
        return None
    text = str(value)[:10]
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def _is_cnc(value: Any) -> bool:
    """
    Clear & Clean status.

    Spike P3 observed values 'CNC', 'CNC-1', 'CNC-8', 'CNC-27' — the suffix is a
    certificate batch, not a negation, so any CNC-prefixed value counts as clean.
    Null/empty stays unclean so unknown status still attracts the risk weight.
    """
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if not text or text in {"none", "null", "-"}:
        return False
    if text.startswith("cnc"):
        return True
    return text in {"clear and clean", "clear & clean", "true", "yes", "y", "1"}


def license_cliff_index(
    licenses: Sequence[dict[str, Any]],
    as_of: dt.date,
    shares: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Hectare-weighted share of an issuer's attributable licensed area expiring soon.

    licenses: [{"company_slug", "license_expiry_date", "licensed_area_ha", "cnc"}, ...]
    shares:   {company_slug: attributable_share 0-1}. Defaults to 1.0 (wholly owned).

    Buckets are CUMULATIVE: lci_24m includes everything in 0-12m.
    Expired licenses are reported separately, never folded into the buckets —
    an already-expired permit is a different (worse) fact than an expiring one.
    """
    shares = shares or {}
    b12 = b24 = b36 = expired = total = 0.0
    counts = {"0_12m": 0, "12_24m": 0, "24_36m": 0, "expired": 0, "no_date": 0, "total": 0}

    for lic in licenses:
        area = lic.get("licensed_area_ha")
        if area is None:
            continue
        share = shares.get(lic.get("company_slug", ""), 1.0)
        weight = float(area) * share
        if weight <= 0:
            continue
        if not _is_cnc(lic.get("cnc")):
            weight *= NON_CNC_RISK_WEIGHT

        total += weight
        counts["total"] += 1

        expiry = _parse_date(lic.get("license_expiry_date"))
        if expiry is None:
            counts["no_date"] += 1
            continue

        months = (expiry - as_of).days / DAYS_PER_MONTH
        if months < 0:
            expired += weight
            counts["expired"] += 1
        elif months <= 12:
            b12 += weight
            counts["0_12m"] += 1
        elif months <= 24:
            b24 += weight
            counts["12_24m"] += 1
        elif months <= 36:
            b36 += weight
            counts["24_36m"] += 1

    if total <= 0:
        return {
            "total_ha_weighted": 0.0, "lci_12m": None, "lci_24m": None,
            "lci_36m": None, "expired_share": None, "flag": "unknown", "counts": counts,
        }

    lci_24 = (b12 + b24) / total
    return {
        "total_ha_weighted": total,
        "lci_12m": b12 / total,
        "lci_24m": lci_24,
        "lci_36m": (b12 + b24 + b36) / total,
        "expired_share": expired / total,
        "flag": "red" if lci_24 >= LCI_24M_RED else "amber" if lci_24 >= LCI_24M_AMBER else "neutral",
        "counts": counts,
    }


# ══════════════════════════════════════════════════════════════════════════
#  A3 — Strip Ratio Drift
# ══════════════════════════════════════════════════════════════════════════


def strip_ratio_drift(points: Sequence[tuple[float, float]]) -> float | None:
    """
    OLS slope of strip_ratio against year. Hand-rolled to keep tests dependency-free.

    points: [(year, strip_ratio), ...]. Returns None below SRD_MIN_POINTS or
    when every x is identical (zero variance -> undefined slope).
    """
    clean = [(float(x), float(y)) for x, y in points if x is not None and y is not None]
    if len(clean) < SRD_MIN_POINTS:
        return None

    n = len(clean)
    mx = sum(x for x, _ in clean) / n
    my = sum(y for _, y in clean) / n
    sxx = sum((x - mx) ** 2 for x, _ in clean)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in clean)
    return sxy / sxx


def srd_flag(slope: float | None) -> str:
    if slope is None:
        return "unknown"
    if slope >= SRD_RED:
        return "red"
    if slope >= SRD_AMBER:
        return "amber"
    return "neutral"


# ══════════════════════════════════════════════════════════════════════════
#  A4 — Destination Concentration
# ══════════════════════════════════════════════════════════════════════════


def destination_hhi(revenue_by_country: dict[str, float]) -> dict[str, Any]:
    """
    Herfindahl-Hirschman index on revenue share by destination country.
    1.0 = single buyer, 0.25 = four equal buyers.
    """
    positive = {k: float(v) for k, v in (revenue_by_country or {}).items() if v and float(v) > 0}
    total = sum(positive.values())
    if total <= 0:
        return {"hhi": None, "max_share": None, "top_country": None, "flag": "unknown"}

    shares = {k: v / total for k, v in positive.items()}
    hhi = sum(s * s for s in shares.values())
    top_country, max_share = max(shares.items(), key=lambda kv: kv[1])

    if max_share >= SINGLE_COUNTRY_RED:
        flag = "red"
    elif hhi >= HHI_AMBER:
        flag = "amber"
    else:
        flag = "neutral"
    return {"hhi": hhi, "max_share": max_share, "top_country": top_country, "flag": flag}


# ══════════════════════════════════════════════════════════════════════════
#  A5 / A6
# ══════════════════════════════════════════════════════════════════════════


def ev_per_tonne(
    market_cap: float | None,
    total_debt: float | None,
    cash: float | None,
    attributable_reserves: float | None,
) -> float | None:
    """Enterprise value per tonne of attributable reserve. Compare to peers, never absolutely."""
    if market_cap is None or attributable_reserves is None or attributable_reserves <= 0:
        return None
    ev = float(market_cap) + float(total_debt or 0) - float(cash or 0)
    return ev / attributable_reserves


def realized_price_spread(
    revenue_usd: float | None,
    sales_volume: float | None,
    benchmark_price: float | None,
) -> float | None:
    """
    Implied realised price vs. benchmark, as a decimal (-0.15 = a 15% discount).
    A widening persistent discount points at quality, contract or logistics problems.
    """
    if not all(v is not None for v in (revenue_usd, sales_volume, benchmark_price)):
        return None
    if sales_volume <= 0 or benchmark_price <= 0:
        return None
    return (float(revenue_usd) / float(sales_volume)) / float(benchmark_price) - 1.0
