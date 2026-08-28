"""
T0 SPIKE — Gate 1 closer.

Answers all 8 open schema questions from SECTORS-HACKATHON-MASTER.md §16 in one
run, hard-capped at 40 credits (expected spend ~19-25).

Design notes:
  * SELF-BOOTSTRAPPING. We do not know any real mining slugs, so probes that
    need one derive it from P2's results. Never hardcode a slug.
  * SHAPE-AGNOSTIC. The pagination envelope is unverified. We LOG observed keys
    rather than asserting a structure.
  * FAIL-SOFT. Each probe is isolated; one failure never kills the run. A probe
    that errors still reports what it learned.
  * IDEMPOTENT. A second run is 100% cache hits and spends 0 credits.

Usage:
    STRATA_OFFLINE=1 python etl/spike.py     # dry run, proves it cannot spend
    python etl/spike.py                       # live, needs etl/.env
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import traceback
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

from clients import CreditExhausted, OfflineMiss, Sectors  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "schema-notes.md"

load_dotenv(ROOT / "etl" / ".env")

findings: list[dict[str, Any]] = []


# ── helpers ──────────────────────────────────────────────────────────────

def rows_of(payload: Any) -> list:
    """Extract row list from an unknown envelope without assuming its shape."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("results", "data", "companies", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        for v in payload.values():          # last resort: first list-valued key
            if isinstance(v, list):
                return v
    return []


def envelope(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "top_level_keys": sorted(payload.keys()),
            "pagination": payload.get("pagination"),
        }
    return {"top_level_keys": f"<{type(payload).__name__}>", "pagination": None}


def total_count(payload: Any) -> int | None:
    if isinstance(payload, dict) and isinstance(payload.get("pagination"), dict):
        return payload["pagination"].get("total_count")
    return None


def key_union(rows: list[dict]) -> list[str]:
    ks: set[str] = set()
    for r in rows[:200]:
        if isinstance(r, dict):
            ks |= set(r.keys())
    return sorted(ks)


def probe(name: str, question: str):
    """Decorator: isolate a probe, capture result or traceback into findings."""
    def wrap(fn):
        def run(client: Sectors, **kwargs) -> Any:
            print(f"\n── {name}: {question}")
            before = client.spent
            try:
                result = fn(client, **kwargs)
                findings.append({
                    "probe": name, "question": question, "ok": True,
                    "credits": client.spent - before, "result": result,
                })
                for k, v in result.items():
                    print(f"     {k}: {v}")
                return result
            except (OfflineMiss, CreditExhausted) as exc:
                print(f"     HALTED: {type(exc).__name__}: {exc}")
                findings.append({
                    "probe": name, "question": question, "ok": False,
                    "credits": client.spent - before, "error": f"{type(exc).__name__}: {exc}",
                })
                raise
            except Exception as exc:  # noqa: BLE001
                print(f"     FAILED: {type(exc).__name__}: {exc}")
                findings.append({
                    "probe": name, "question": question, "ok": False,
                    "credits": client.spent - before,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=3),
                })
                return None
        return run
    return wrap


# ── probes ───────────────────────────────────────────────────────────────

@probe("P1", "Does the API key work at all? (does the credit grant include API access?)")
def p1(c: Sectors):
    data = c.get("/v2/subsectors/")
    rows = rows_of(data)
    return {"authenticated": True, "subsector_count": len(rows), "sample": rows[:3]}


@probe("P2", "How many mining companies exist, how many carry a `symbol`, does limit exceed 100?")
def p2(c: Sectors):
    page100 = c.get("/v2/mining/companies/", {"limit": 100, "offset": 0})
    rows100 = rows_of(page100)
    page200 = c.get("/v2/mining/companies/", {"limit": 200, "offset": 0})
    rows200 = rows_of(page200)

    # Walk a bounded number of pages to count symbol-bearing companies.
    all_rows: list[dict] = []
    for row in c.paginate("/v2/mining/companies/", limit=100, max_pages=8):
        all_rows.append(row)

    with_symbol = [r for r in all_rows if r.get("symbol")]
    return {
        "rows_at_limit_100": len(rows100),
        "rows_at_limit_200": len(rows200),
        "limit_above_100_honoured": len(rows200) > len(rows100),
        "envelope": envelope(page100),
        "row_keys": key_union(rows100),
        "total_count": total_count(page100),
        "companies_scanned": len(all_rows),
        "companies_with_symbol": len(with_symbol),
        "distinct_symbols": sorted({r["symbol"] for r in with_symbol})[:60],
        "listed_company_slugs": [r["slug"] for r in with_symbol if r.get("slug")],
        "any_company_slugs": [r["slug"] for r in all_rows if r.get("slug")][:10],
        "company_type_breakdown": _tally(all_rows, "company_type"),
    }


@probe("P3", "True license count; how dense is license_expiry_date?")
def p3(c: Sectors):
    page = c.get("/v2/mining/licenses/", {"limit": 100, "offset": 0, "order_by": "license_expiry_date"})
    rows = rows_of(page)
    expiring = c.get("/v2/mining/licenses/", {"limit": 100, "expiring_soon": "true"})
    exp_rows = rows_of(expiring)
    dated = [r for r in rows if r.get("license_expiry_date")]
    return {
        "envelope": envelope(page),
        "row_keys": key_union(rows),
        "rows_returned": len(rows),
        "with_expiry_date": len(dated),
        "expiry_date_density": round(len(dated) / len(rows), 3) if rows else None,
        "expiring_soon_rows": len(exp_rows),
        "cnc_values_observed": sorted({str(r.get("cnc")) for r in rows})[:10],
        "license_type_breakdown": _tally(rows, "license_type"),
        "sample": rows[:2],
    }


@probe("P4", "Do mining sites repeat across years? (decides whether A3 strip-ratio drift is possible)")
def p4(c: Sectors):
    rows: list[dict] = list(c.paginate("/v2/mining/sites/", {"order_by": "-year"}, limit=100, max_pages=3))
    by_slug: dict[str, set] = {}
    for r in rows:
        if r.get("slug"):
            by_slug.setdefault(r["slug"], set()).add(r.get("year"))

    multi = {k: sorted(v) for k, v in by_slug.items() if len(v) > 1}
    with_strip = [r for r in rows if r.get("strip_ratio") is not None]
    return {
        "rows_scanned": len(rows),
        "distinct_slugs": len(by_slug),
        "slugs_with_multiple_years": len(multi),
        "years_observed": sorted({r.get("year") for r in rows if r.get("year")}),
        "strip_ratio_density": round(len(with_strip) / len(rows), 3) if rows else None,
        "A3_VIABLE": len(multi) >= 10,
        "multi_year_examples": dict(list(multi.items())[:5]),
        "row_keys": key_union(rows),
    }


@probe("P3b", "Do licenses that matter (Coal/Nickel/Gold/Copper) carry company_slug?")
def p3b(c: Sectors):
    out = {}
    for commodity in ("Coal", "Nickel"):
        page = c.get("/v2/mining/licenses/", {"limit": 30, "commodity_type": commodity, "order_by": "-licensed_area_ha"})
        rows = rows_of(page)
        linked = [r for r in rows if r.get("company_slug")]
        out[commodity] = {
            "total_count": total_count(page),
            "rows": len(rows),
            "with_company_slug": len(linked),
            "slug_density": round(len(linked) / len(rows), 3) if rows else None,
            "example_slugs": sorted({r["company_slug"] for r in linked})[:8],
            "example_names": [r.get("company_name") for r in rows[:4]],
            "largest_area_ha": rows[0].get("licensed_area_ha") if rows else None,
        }
    any_linked = any(v["with_company_slug"] > 0 for v in out.values())
    return {"by_commodity": out, "LICENSE_JOIN_VIABLE": any_linked}


@probe("P4b", "Is strip_ratio populated for Coal, and do earlier years exist?")
def p4b(c: Sectors):
    out = {}
    for commodity in ("Coal", "Nickel", "Gold"):
        page = c.get("/v2/mining/sites/", {"limit": 30, "commodity_type": commodity, "order_by": "-year"})
        rows = rows_of(page)
        with_strip = [r for r in rows if r.get("strip_ratio") is not None]
        out[commodity] = {
            "total_count": total_count(page),
            "rows": len(rows),
            "years": sorted({r.get("year") for r in rows if r.get("year")}),
            "with_strip_ratio": len(with_strip),
            "with_production": sum(1 for r in rows if r.get("production_volume") is not None),
            "units": sorted({str(r.get("unit")) for r in rows})[:5],
            "with_company_slug": sum(1 for r in rows if r.get("company_slug")),
            "site_slugs": [r["slug"] for r in rows if r.get("slug")][:6],
            "company_slugs": sorted({r["company_slug"] for r in rows if r.get("company_slug")})[:6],
        }

    # Probe explicitly for an earlier year to see whether history exists at all.
    hist = c.get("/v2/mining/sites/", {"limit": 30, "commodity_type": "Coal", "year": 2023})
    hist_rows = rows_of(hist)
    out["coal_2023_probe"] = {
        "total_count": total_count(hist),
        "rows": len(hist_rows),
        "with_strip_ratio": sum(1 for r in hist_rows if r.get("strip_ratio") is not None),
    }

    strip_ok = any(v.get("with_strip_ratio", 0) > 0 for k, v in out.items() if k != "coal_2023_probe")
    multi_year = len(hist_rows) > 0
    return {
        "by_commodity": out,
        "STRIP_RATIO_AVAILABLE": strip_ok,
        "MULTI_YEAR_AVAILABLE": multi_year,
        "A3_VIABLE": strip_ok and multi_year,
    }


@probe("P5", "What shape and units does resources_reserves use?")
def p5(c: Sectors, slugs: list[str] | None = None):
    slugs = slugs or []
    out = {}
    for slug in slugs[:2]:
        detail = c.get(f"/v2/mining/sites/{slug}/")
        out[slug] = {
            "keys": sorted(detail.keys()) if isinstance(detail, dict) else None,
            "resources_reserves": detail.get("resources_reserves") if isinstance(detail, dict) else None,
            "unit": detail.get("unit") if isinstance(detail, dict) else None,
            "location": detail.get("location") if isinstance(detail, dict) else None,
        }
    return {"probed_slugs": list(out), "details": out}


@probe("P6", "Does the ownership tree carry `symbol`? (THE load-bearing join)")
def p6(c: Sectors, slugs: list[str] | None = None):
    slugs = slugs or []
    trees, symbols_found = {}, set()
    for slug in slugs[:3]:
        tree = c.get(f"/v2/mining/companies/ownership/{slug}/")
        if not isinstance(tree, dict):
            continue
        parents = tree.get("parents") or []
        subs = tree.get("subsidiaries") or []
        for node in list(parents) + list(subs):
            if isinstance(node, dict) and node.get("symbol"):
                symbols_found.add(node["symbol"])
        trees[slug] = {
            "parent_count": len(parents),
            "subsidiary_count": len(subs),
            "parents_with_symbol": sum(1 for n in parents if isinstance(n, dict) and n.get("symbol")),
            "subs_with_symbol": sum(1 for n in subs if isinstance(n, dict) and n.get("symbol")),
            "sample_parent": parents[0] if parents else None,
        }
    return {
        "trees": trees,
        "symbols_discovered_via_ownership": sorted(symbols_found),
        "JOIN_CONFIRMED": bool(symbols_found),
    }


@probe("P7", "How dense is idx_conglomerates_group_slug? (DECIDES TRACK B VIABILITY)")
def p7(c: Sectors):
    today = dt.date.today()
    page = c.get("/v2/filings/", {
        "limit": 100,
        "start": (today - dt.timedelta(days=365)).isoformat(),
        "end": today.isoformat(),
    })
    rows = rows_of(page)
    with_group = [r for r in rows if r.get("idx_conglomerates_group_slug")]
    groups: set[str] = set()
    for r in with_group:
        raw = r["idx_conglomerates_group_slug"]
        groups |= {raw} if isinstance(raw, str) else {str(g) for g in raw if g}

    return {
        "envelope": envelope(page),
        "row_keys": key_union(rows),
        "filings_scanned": len(rows),
        "filings_with_group": len(with_group),
        "group_density": round(len(with_group) / len(rows), 3) if rows else None,
        "distinct_groups": sorted(groups),
        "distinct_group_count": len(groups),
        "holder_type_breakdown": _tally(rows, "holder_type"),
        "TRACK_B_VIABLE": len(groups) >= 3 and len(with_group) >= 10,
    }


@probe("P8", "Does the screener return shareholders/executives? (saves ~50 credits if yes)")
def p8(c: Sectors):
    where = "sub_sector = 'coal' and market_cap > 1000000000000"
    plain = c.get("/v2/companies/", {"where": where, "limit": 5, "order_by": "-market_cap"})
    withvals = c.get("/v2/companies/", {
        "where": where, "limit": 5, "order_by": "-market_cap", "include_query_values": "true",
    })
    prows, wrows = rows_of(plain), rows_of(withvals)
    pk, wk = key_union(prows), key_union(wrows)
    extra = sorted(set(wk) - set(pk))
    ownership_fields = [k for k in wk if any(t in k for t in ("shareholder", "executive", "free_float"))]
    return {
        "plain_row_keys": pk,
        "extra_keys_from_include_query_values": extra,
        "ownership_fields_present": ownership_fields,
        "SAVES_COMPANY_REPORT_CREDITS": bool(ownership_fields),
        "symbols": [r.get("symbol") for r in prows],
        "sample": prows[:1],
    }


@probe("P9", "How far back does sales-destination data reach?")
def p9(c: Sectors, slugs: list[str] | None = None):
    slugs = slugs or []
    out = {}
    for slug in slugs[:2]:
        d = c.get(f"/v2/mining/sales-destination/{slug}/")
        if isinstance(d, dict):
            out[slug] = {
                "year": d.get("year"),
                "keys": sorted(d.keys()),
                "countries": sorted((d.get("data") or {}).keys()) if isinstance(d.get("data"), dict) else None,
            }
    return {"probed_slugs": list(out), "details": out}


def _tally(rows: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        v = r.get(field)
        if isinstance(v, list):
            for item in v:
                out[str(item)] = out.get(str(item), 0) + 1
        elif v is not None:
            out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1])[:12])


# ── report ───────────────────────────────────────────────────────────────

def write_report(client: Sectors) -> None:
    lines = [
        "# Schema Notes — generated by `etl/spike.py`",
        "",
        f"Run: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}  ",
        f"Credits: **{client.spent}** billed · live calls {client.calls} · cache hits {client.cache_hits}",
        "",
        "> Auto-generated. Do not hand-edit — re-run the spike instead.",
        "> This file is the record that closes **Gate 1** (MASTER.md §10).",
        "",
        "## Verdicts",
        "",
        "| Probe | Question | OK | Credits |",
        "|---|---|---|---|",
    ]
    for f in findings:
        q = f["question"].replace("|", "\\|")
        lines.append(f"| {f['probe']} | {q} | {'✅' if f['ok'] else '❌'} | {f['credits']} |")

    # Headline decisions the plan branches on.
    def look(probe_name: str, key: str):
        for f in findings:
            if f["probe"] == probe_name and f.get("ok") and isinstance(f.get("result"), dict):
                return f["result"].get(key)
        return None

    lines += [
        "",
        "## Gate decisions",
        "",
        f"- **API access works:** `{look('P1', 'authenticated')}`",
        f"- **Ownership `symbol` join confirmed (P6):** `{look('P6', 'JOIN_CONFIRMED')}`",
        f"- **License→company join viable (P3b):** `{look('P3b', 'LICENSE_JOIN_VIABLE')}`",
        f"- **strip_ratio populated anywhere (P4b):** `{look('P4b', 'STRIP_RATIO_AVAILABLE')}`",
        f"- **Multi-year site history (P4b):** `{look('P4b', 'MULTI_YEAR_AVAILABLE')}`",
        f"- **A3 strip-ratio drift viable (P4b):** `{look('P4b', 'A3_VIABLE')}`",
        f"- **Track B viable (P7):** `{look('P7', 'TRACK_B_VIABLE')}`",
        f"- **Screener supplies ownership fields (P8):** `{look('P8', 'SAVES_COMPANY_REPORT_CREDITS')}`",
        "",
        "### Gate 2 pre-read",
        "",
        f"- Mining companies scanned: `{look('P2', 'companies_scanned')}`",
        f"- With a non-null `symbol`: `{look('P2', 'companies_with_symbol')}`",
        f"- Extra symbols via ownership trees: `{look('P6', 'symbols_discovered_via_ownership')}`",
        "",
        "Gate 2 (6 Sep) needs **≥25** tickers resolving to ≥1 license. "
        "Under 15 → cut Track B per MASTER.md §10.",
        "",
        "## Raw findings",
        "",
        "```json",
        json.dumps(findings, indent=2, ensure_ascii=False, default=str)[:120_000],
        "```",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n→ wrote {REPORT.relative_to(ROOT)}")


def main() -> int:
    cap = int(os.environ.get("STRATA_TRANCHE_CAP", 40))
    print(f"STRATA T0 spike · tranche cap {cap} credits · offline={os.environ.get('STRATA_OFFLINE', '0')}")

    try:
        client = Sectors(tranche_cap=cap)
    except RuntimeError as exc:
        print(f"\nSETUP ERROR: {exc}")
        return 2

    try:
        p1(client)
        r2 = p2(client)
        p3(client)
        r3b = p3b(client)
        p4(client)
        r4b = p4b(client)

        # Self-bootstrap downstream probes from whatever real slugs we found.
        # Prefer LISTED companies — those are the ones the product is about.
        company_slugs: list[str] = []
        site_slugs: list[str] = []

        if r2:
            company_slugs += r2.get("listed_company_slugs") or []
            company_slugs += r2.get("any_company_slugs") or []
        if r3b:
            for v in (r3b.get("by_commodity") or {}).values():
                company_slugs += v.get("example_slugs") or []
        if r4b:
            for k, v in (r4b.get("by_commodity") or {}).items():
                if k == "coal_2023_probe":
                    continue
                site_slugs += v.get("site_slugs") or []
                company_slugs += v.get("company_slugs") or []

        company_slugs = list(dict.fromkeys(s for s in company_slugs if s))
        site_slugs = list(dict.fromkeys(s for s in site_slugs if s))
        print(f"\n     bootstrapped {len(company_slugs)} company slugs, {len(site_slugs)} site slugs")

        p5(client, slugs=site_slugs)
        p6(client, slugs=company_slugs)
        p7(client)
        p8(client)
        p9(client, slugs=company_slugs)

    except (OfflineMiss, CreditExhausted):
        print("\nRun halted early — partial findings still written.")
    finally:
        write_report(client)
        print(f"\n{client.summary()}")

    failed = [f["probe"] for f in findings if not f["ok"]]
    if failed:
        print(f"Probes needing attention: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
