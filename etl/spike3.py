"""Confirms multi-year depth on companies/performance — the endpoint A1/A3 depend on."""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dotenv import load_dotenv

from clients import CreditExhausted, Sectors

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "etl" / ".env")

TARGETS = ["pt-adaro-indonesia", "pt-bukit-asam-tbk"]
YEARS = [2020, 2022, 2023]


def series(client: Sectors, slug: str) -> dict:
    out = {}
    for year in YEARS:
        try:
            d = client.get(f"/v2/mining/companies/performance/{slug}/", {"year": year})
        except CreditExhausted:
            raise
        except Exception as exc:
            out[year] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        rows = d.get("data") or []
        picked = []
        for r in rows:
            st = r.get("commodity_stats") or {}
            rr = st.get("resources_reserves") or {}
            picked.append({
                "commodity": r.get("commodity_type"),
                "sub_type": r.get("commodity_sub_type"),
                "unit": st.get("unit"),
                "production_volume": st.get("production_volume"),
                "sales_volume": st.get("sales_volume"),
                "strip_ratio": st.get("strip_ratio"),
                "overburden": st.get("overburden_removal_volume"),
                "total_reserves_Mt": rr.get("total_reserves_Mt"),
                "total_resources_Mt": rr.get("total_resources_Mt"),
            })
        out[year] = picked
    return out


def main() -> int:
    client = Sectors(tranche_cap=int(pathlib.os.environ.get("STRATA_TRANCHE_CAP", 60)))
    report = {}
    try:
        for slug in TARGETS:
            report[slug] = series(client, slug)
            print(f"\n{'=' * 66}\n{slug}")
            for year, rows in report[slug].items():
                if isinstance(rows, dict):
                    print(f"  {year}: {rows}")
                    continue
                for r in rows:
                    print(f"  {year}  {r['commodity']:<8} prod={r['production_volume']} "
                          f"strip={r['strip_ratio']} reserves={r['total_reserves_Mt']} unit={r['unit']}")
    except CreditExhausted as exc:
        print(f"HALTED: {exc}")
    finally:
        path = ROOT / "docs" / "schema-notes-round3.md"
        path.write_text(
            "# Schema Notes — Round 3: multi-year company performance\n\n"
            f"Credits: **{client.spent}** · live calls {client.calls} · cache hits {client.cache_hits}\n\n"
            "```json\n" + json.dumps(report, indent=2, default=str)[:60_000] + "\n```\n",
            encoding="utf-8",
        )
        print(f"\n→ wrote {path.relative_to(ROOT)}")
        print(client.summary())

    strip_years = {
        slug: [y for y, rows in yrs.items()
               if isinstance(rows, list) and any(r.get("strip_ratio") is not None for r in rows)]
        for slug, yrs in report.items()
    }
    print("\nYEARS WITH strip_ratio:", strip_years)
    print("A3_VIABLE:", any(len(v) >= 2 for v in strip_years.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
