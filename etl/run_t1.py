"""T1 pipeline: universe -> licenses -> ownership -> resolution -> SQLite -> Gate 2."""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "stages"))

from dotenv import load_dotenv

from clients import CreditExhausted, RateLimited, Sectors
from load.to_sqlite import build
from stages import s01_universe, s02_licenses, s03_ownership
from stages._common import load, save
from transform.entity_resolution import gate2_report, resolve

load_dotenv(ROOT / "etl" / ".env")

TRANCHE_CAP = 360


def main() -> int:
    client = Sectors(tranche_cap=TRANCHE_CAP)
    print(f"T1 pipeline · cap {TRANCHE_CAP} credits\n")
    report: dict = {}

    try:
        print("[01] universe")
        report["s01"] = s01_universe.run(client)
        print(f"     spent so far: {client.spent}\n")

        print("[02] licenses")
        report["s02"] = s02_licenses.run(client)
        print(f"     spent so far: {client.spent}\n")

        print("[03] ownership")
        report["s03"] = s03_ownership.run(client)
        print(f"     spent so far: {client.spent}\n")
    except CreditExhausted as exc:
        print(f"\nCREDIT CAP HIT: {exc}")
        report["halted"] = str(exc)
    except RateLimited as exc:
        print(f"\nRATE LIMITED: {exc}")
        report["halted"] = str(exc)

    companies = load("companies")
    licenses = load("licenses")
    try:
        edges = load("ownership_edges")
    except FileNotFoundError:
        edges = []

    print("[04] entity resolution")
    resolution = resolve(companies, edges)
    save("resolution", resolution)
    print(f"     resolved {len(resolution)} of {len(companies)} company slugs")

    print("\n[05] gate 2 measurement")
    gate2 = gate2_report(resolution, licenses)
    report["gate2"] = gate2

    print(f"     license-holding slugs   : {gate2['license_holding_slugs']}")
    print(f"     of those resolved       : {gate2['resolved_slugs']}")
    print(f"     DISTINCT TICKERS        : {gate2['tickers_resolved']}")
    print(f"     resolution methods      : {gate2['resolution_methods']}")
    print("\n     top tickers by attributable licensed hectares:")
    for e in gate2["per_ticker"][:15]:
        print(f"       {e['symbol']:<10} {e['attributable_ha']:>12,.0f} ha  "
              f"({e['license_slug_count']} entities, {','.join(e['methods'])})")
    if gate2["unresolved_top_by_area"]:
        print("\n     largest UNRESOLVED license holders (coverage gap):")
        for slug, area in gate2["unresolved_top_by_area"][:8]:
            print(f"       {slug:<48} {area:>12,.0f} ha")

    n = gate2["tickers_resolved"]
    verdict = "PASS - full T2 scope" if n >= 25 else \
              "PASS WITH CAVEAT - note coverage in README/video" if n >= 15 else \
              "FAIL - rethink before spending T2"
    print(f"\n     GATE 2 VERDICT: {n} tickers -> {verdict}")
    report["gate2_verdict"] = verdict

    print("\n[06] load sqlite")
    meta = {
        "tranche": "T1",
        "credits_spent": client.spent,
        "gate2_tickers": n,
        "gate2_verdict": verdict,
        "stage_report": report,
    }
    db = build(companies, licenses, edges, resolution, meta)
    print(f"     wrote {db.relative_to(ROOT)} ({db.stat().st_size / 1024:.0f} KB)")

    out = ROOT / "docs" / "t1-report.md"
    out.write_text(
        "# T1 Pipeline Report\n\n"
        f"Credits: **{client.spent}** of {TRANCHE_CAP} tranche cap · "
        f"live calls {client.calls} · cache hits {client.cache_hits}\n\n"
        f"## Gate 2: {n} tickers resolved — {verdict}\n\n"
        "```json\n" + json.dumps(report, indent=2, default=str)[:150_000] + "\n```\n",
        encoding="utf-8",
    )
    print(f"     wrote {out.relative_to(ROOT)}")
    print(f"\n{client.summary()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
