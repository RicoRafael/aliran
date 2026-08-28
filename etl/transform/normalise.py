from __future__ import annotations

from typing import Any

RESERVE_KEYS = [
    ("total_reserves_Mt", "Mt"),
    ("total_reserves_wmt", "wmt"),
    ("total_reserves_dmt", "dmt"),
    ("total_reserves_koz", "koz"),
    ("total_reserves_kt", "kt"),
    ("Ni_reserves_Kt", "Kt_Ni"),
]

RESOURCE_KEYS = [
    ("total_resources_Mt", "Mt"),
    ("total_resources_wmt", "wmt"),
    ("total_resources_dmt", "dmt"),
    ("total_resources_koz", "koz"),
    ("Ni_resources_Kt", "Kt_Ni"),
]


def _first(mapping: dict, candidates: list[tuple[str, str]]) -> tuple[float | None, str | None]:
    for key, unit in candidates:
        value = mapping.get(key)
        if value is not None:
            try:
                return float(value), unit
            except (TypeError, ValueError):
                continue
    return None, None


def flatten_performance(payload: Any) -> list[dict]:
    """
    One row per (year, commodity, sub_type).

    Units differ by commodity — coal in Mt, nickel in wmt/dmt/ton, gold in koz —
    so unit is carried on every row and never assumed. Downstream code must
    compare units before dividing or summing.
    """
    if not isinstance(payload, dict):
        return []
    year = payload.get("year")
    rows = []
    for entry in payload.get("data") or []:
        stats = entry.get("commodity_stats") or {}
        rr = stats.get("resources_reserves") or {}
        reserves, reserve_unit = _first(rr, RESERVE_KEYS)
        resources, resource_unit = _first(rr, RESOURCE_KEYS)
        rows.append({
            "year": entry.get("year") or year,
            "commodity_type": entry.get("commodity_type"),
            "commodity_sub_type": entry.get("commodity_sub_type"),
            "unit": stats.get("unit"),
            "operation_status": stats.get("mining_operation_status"),
            "production_volume": stats.get("production_volume"),
            "sales_volume": stats.get("sales_volume"),
            "strip_ratio": stats.get("strip_ratio"),
            "overburden_removal_volume": stats.get("overburden_removal_volume"),
            "reserves": reserves,
            "reserve_unit": reserve_unit,
            "resources": resources,
            "resource_unit": resource_unit,
            "measurement_year": rr.get("measurement_year"),
        })
    return rows


def units_comparable(production_unit: str | None, reserve_unit: str | None) -> bool:
    if not production_unit or not reserve_unit:
        return False
    return production_unit.strip().lower() == reserve_unit.strip().lower()


def site_location(detail: Any) -> dict:
    loc = (detail or {}).get("location") or {} if isinstance(detail, dict) else {}
    return {
        "province": loc.get("province"),
        "city": loc.get("city"),
        "latitude": loc.get("latitude"),
        "longitude": loc.get("longitude"),
    }


def site_reserves(detail: Any) -> tuple[float | None, str | None]:
    if not isinstance(detail, dict):
        return None, None
    rr = detail.get("resources_reserves")
    if not isinstance(rr, dict):
        return None, None
    return _first(rr, RESERVE_KEYS)
