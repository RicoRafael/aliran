"""Follow-up spike. Resolves the four unknowns P4b/P7/P8/P9 left open."""

from __future__ import annotations

import json
import pathlib
import sys
import traceback
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dotenv import load_dotenv

from clients import CreditExhausted, OfflineMiss, Sectors

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "schema-notes-round2.md"
load_dotenv(ROOT / "etl" / ".env")

findings: list[dict[str, Any]] = []


def rows_of(payload: Any) -> list:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("results", "data", "companies", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        for v in payload.values():
            if isinstance(v, list):
                return v
    return []


def total_count(payload: Any) -> int | None:
    if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict):
        return payload["pagination"].get("total_count")
    return None


def keys_of(rows: list) -> list[str]:
    ks: set[str] = set()
    for r in rows[:100]:
        if isinstance(r, dict):
            ks |= set(r.keys())
    return sorted(ks)


def run(name: str, question: str, fn, client: Sectors):
    print(f"\n── {name}: {question}")
    before = client.spent
    try:
        result = fn(client)
        findings.append({"probe": name, "question": question, "ok": True,
                         "credits": client.spent - before, "result": result})
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str)[:2600])
        return result
    except (OfflineMiss, CreditExhausted) as exc:
        print(f"     HALTED: {exc}")
        findings.append({"probe": name, "question": question, "ok": False,
                         "credits": client.spent - before, "error": str(exc)})
        raise
    except Exception as exc:
        print(f"     FAILED: {type(exc).__name__}: {exc}")
        findings.append({"probe": name, "question": question, "ok": False,
                         "credits": client.spent - before,
                         "error": f"{type(exc).__name__}: {exc}",
                         "traceback": traceback.format_exc(limit=2)})
        return None


def q1_screener(c: Sectors):
    out = {}
    for label, params in {
        "oil_gas_coal": {"where": "sub_sector = 'oil-gas-coal'", "order_by": "-market_cap", "limit": 30},
        "basic_materials": {"where": "sub_sector = 'basic-materials'", "order_by": "-market_cap", "limit": 30},
        "symbol_in_plain": {"where": "symbol in ['ADRO','PTBA','ANTM','INCO','MDKA']", "limit": 30},
        "symbol_in_suffixed": {"where": "symbol in ['ADRO.JK','PTBA.JK']", "limit": 30},
    }.items():
        page = c.get("/v2/companies/", params)
        rows = rows_of(page)
        out[label] = {
            "total_count": total_count(page),
            "rows": len(rows),
            "row_keys": keys_of(rows),
            "symbols": [r.get("symbol") for r in rows[:12]],
            "sample": rows[0] if rows else None,
        }
    working = [k for k, v in out.items() if v["rows"] > 0]
    return {"variants": out, "WORKING_FORMS": working}


def q2_site_history(c: Sectors):
    out = {}
    for commodity in ("Coal", "Nickel"):
        for year in (2021, 2022, 2023):
            page = c.get("/v2/mining/sites/", {"limit": 30, "commodity_type": commodity, "year": year})
            rows = rows_of(page)
            out[f"{commodity}_{year}"] = {
                "total_count": total_count(page),
                "rows": len(rows),
                "with_strip_ratio": sum(1 for r in rows if r.get("strip_ratio") is not None),
                "with_production": sum(1 for r in rows if r.get("production_volume") is not None),
                "with_company_slug": sum(1 for r in rows if r.get("company_slug")),
                "example_slugs": [r.get("slug") for r in rows[:4]],
            }
    strip_years = [k for k, v in out.items() if v["with_strip_ratio"] > 0]
    prod_years = [k for k, v in out.items() if v["with_production"] > 0]
    return {
        "by_year": out,
        "YEARS_WITH_STRIP_RATIO": strip_years,
        "YEARS_WITH_PRODUCTION": prod_years,
        "A3_VIABLE": len(strip_years) >= 2,
        "RLI_VIABLE": len(prod_years) >= 1,
    }


def q3_group_density(c: Sectors):
    scanned, with_group, with_investor = 0, 0, 0
    groups: set[str] = set()
    investors: set[str] = set()
    for row in c.paginate("/v2/filings/", {}, limit=30, max_pages=4):
        scanned += 1
        g = row.get("idx_conglomerates_group_slug")
        if g:
            with_group += 1
            groups |= {g} if isinstance(g, str) else {str(x) for x in g if x}
        inv = row.get("idx_investor_slug")
        if inv:
            with_investor += 1
            investors.add(str(inv))
    return {
        "filings_scanned": scanned,
        "with_group_slug": with_group,
        "group_density": round(with_group / scanned, 4) if scanned else None,
        "distinct_groups": sorted(groups),
        "with_investor_slug": with_investor,
        "investor_density": round(with_investor / scanned, 4) if scanned else None,
        "distinct_investors": sorted(investors)[:20],
        "TRACK_B_VIA_GROUPS": len(groups) >= 3,
        "TRACK_B_VIA_INVESTORS": len(investors) >= 10,
    }


def q4_company_depth(c: Sectors):
    out = {}
    for slug in ("pt-adaro-indonesia", "pt-bukit-asam-tbk", "pt-vale-indonesia"):
        entry = {}
        for label, path in {
            "performance": f"/v2/mining/companies/performance/{slug}/",
            "financials": f"/v2/mining/companies/financials/{slug}/",
            "sales_destination": f"/v2/mining/sales-destination/{slug}/",
        }.items():
            try:
                d = c.get(path)
                entry[label] = {
                    "keys": sorted(d.keys()) if isinstance(d, dict) else f"<{type(d).__name__}>",
                    "available_years": d.get("available_years") if isinstance(d, dict) else None,
                    "preview": json.dumps(d, default=str)[:700],
                }
            except Exception as exc:
                entry[label] = {"error": f"{type(exc).__name__}: {exc}"}
        out[slug] = entry
    return out


def main() -> int:
    print("STRATA spike round 2")
    try:
        client = Sectors()
    except RuntimeError as exc:
        print(f"SETUP ERROR: {exc}")
        return 2

    try:
        run("Q1", "Which screener filter form actually returns rows?", q1_screener, client)
        run("Q2", "Do earlier years carry strip_ratio and production_volume?", q2_site_history, client)
        run("Q3", "Group slug density over 120 filings; is idx_investor_slug a fallback?", q3_group_density, client)
        run("Q4", "How deep is per-company performance/financials/sales data?", q4_company_depth, client)
    except (OfflineMiss, CreditExhausted):
        print("\nHalted early; partial findings written.")
    finally:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            "# Schema Notes — Round 2 (`etl/spike2.py`)\n\n"
            f"Credits: **{client.spent}** · live calls {client.calls} · cache hits {client.cache_hits}\n\n"
            "```json\n"
            + json.dumps(findings, indent=2, ensure_ascii=False, default=str)[:150_000]
            + "\n```\n",
            encoding="utf-8",
        )
        print(f"\n→ wrote {REPORT.relative_to(ROOT)}")
        print(client.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
