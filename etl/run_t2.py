"""T2 pipeline: performance -> sites -> equity -> destinations -> metrics -> SQLite."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "stages"))

from dotenv import load_dotenv

from clients import CreditExhausted, RateLimited, Sectors
from load.to_json import export
from load.to_sqlite import build_t2
from stages import s04_performance, s05_sites, s06_equity, s07_sales_dest
from stages._common import load, save
from transform.compute_metrics import compute

load_dotenv(ROOT / "etl" / ".env")

import os

TRANCHE_CAP = int(os.environ.get("STRATA_TRANCHE_CAP", 280))
AS_OF = dt.date.today()


def _safe_load(name, default):
    try:
        return load(name)
    except FileNotFoundError:
        return default


def main() -> int:
    client = Sectors(tranche_cap=TRANCHE_CAP)
    print(f"T2 pipeline · cap {TRANCHE_CAP} credits · as_of {AS_OF}\n")
    report: dict = {}

    stages = [
        ("04 performance", s04_performance),
        ("05 sites", s05_sites),
        ("06 equity", s06_equity),
        ("07 sales destinations", s07_sales_dest),
    ]
    for label, module in stages:
        print(f"[{label}]")
        try:
            report[label] = module.run(client)
        except (CreditExhausted, RateLimited) as exc:
            print(f"    HALTED: {exc}")
            report[label] = {"halted": str(exc)}
            break
        except Exception as exc:
            print(f"    FAILED: {type(exc).__name__}: {exc}")
            report[label] = {"error": f"{type(exc).__name__}: {exc}"}
        print(f"    spent so far: {client.spent}\n")

    resolution = load("resolution")
    licenses = load("licenses")
    performance = _safe_load("performance", {})
    site_details = _safe_load("site_details", {})
    equity = _safe_load("equity_overview", {})
    sales = _safe_load("sales_destinations", {})

    print("[08 metrics]")
    metrics = compute(resolution, licenses, performance, site_details, equity, sales, AS_OF)
    save("metrics_issuer", metrics)
    print(f"    computed metrics for {len(metrics)} tickers")

    have = lambda f: sum(1 for m in metrics if m.get(f) is not None)
    coverage = {
        "lci_24m": have("lci_24m"),
        "rli_years": have("rli_years"),
        "strip_ratio_slope": have("strip_ratio_slope"),
        "reserve_replacement_ratio": have("reserve_replacement_ratio"),
        "hhi": have("hhi"),
        "market_cap": have("market_cap"),
        "site_coords": sum(1 for m in metrics if m.get("site_coords")),
    }
    report["metric_coverage"] = coverage
    print("    coverage across tickers:")
    for k, v in coverage.items():
        print(f"      {k:<28} {v}/{len(metrics)}")

    print("\n    LEAGUE TABLE — sorted by 24-month licence cliff")
    ranked = sorted(
        (m for m in metrics if m.get("lci_24m") is not None),
        key=lambda m: -m["lci_24m"],
    )
    print(f"      {'SYM':<10} {'LCI24':>7} {'RLIyr':>7} {'STRIP':>6} {'SLOPE':>7} "
          f"{'RRR':>6} {'HHI':>5} {'HA':>10}  FLAGS")
    for m in ranked[:20]:
        fmt = lambda v, p=2: f"{v:.{p}f}" if isinstance(v, (int, float)) else "  -  "
        flags = ",".join(f for f in (m["lci_flag"], m["rli_flag"], m["strip_flag"], m["hhi_flag"])
                         if f in ("red", "amber"))
        print(f"      {m['symbol']:<10} {m['lci_24m']:>6.1%} {fmt(m['rli_years'],1):>7} "
              f"{fmt(m['strip_ratio_latest']):>6} {fmt(m['strip_ratio_slope'],3):>7} "
              f"{fmt(m['reserve_replacement_ratio']):>6} {fmt(m['hhi']):>5} "
              f"{(m['licensed_ha_weighted'] or 0):>10,.0f}  {flags}")

    print("\n[09 load sqlite]")
    db = build_t2(performance, site_details, sales, equity, metrics)
    print(f"    wrote {db.relative_to(ROOT)} ({db.stat().st_size / 1024:.0f} KB)")

    print("\n[10 export web json]")
    exported = export(metrics, licenses, resolution, performance, AS_OF, coverage)
    report["web_export"] = exported
    for k, v in exported.items():
        print(f"    {k:<24} {v}")

    out = ROOT / "docs" / "t2-report.md"
    out.write_text(
        "# T2 Pipeline Report\n\n"
        f"Credits: **{client.spent}** of {TRANCHE_CAP} cap · live calls {client.calls} "
        f"· cache hits {client.cache_hits} · throttled {client.throttled}\n\n"
        f"Tickers with metrics: **{len(metrics)}**\n\n"
        "```json\n" + json.dumps(report, indent=2, default=str)[:150_000] + "\n```\n",
        encoding="utf-8",
    )
    print(f"    wrote {out.relative_to(ROOT)}")
    print(f"\n{client.summary()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
