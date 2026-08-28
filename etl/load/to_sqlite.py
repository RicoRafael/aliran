from __future__ import annotations

import json
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "strata.sqlite"

SCHEMA = """
DROP TABLE IF EXISTS companies;
CREATE TABLE companies (
  slug TEXT PRIMARY KEY,
  name TEXT,
  symbol TEXT,
  company_type TEXT,
  key_operation TEXT,
  commodity_types TEXT
);

DROP TABLE IF EXISTS licenses;
CREATE TABLE licenses (
  wiup_code TEXT PRIMARY KEY,
  company_slug TEXT,
  company_name TEXT,
  license_number TEXT,
  license_type TEXT,
  activity TEXT,
  license_effective_date TEXT,
  license_expiry_date TEXT,
  licensed_area_ha REAL,
  cnc TEXT,
  generation TEXT,
  province TEXT,
  city TEXT,
  commodity_type TEXT
);
CREATE INDEX idx_lic_slug ON licenses(company_slug);
CREATE INDEX idx_lic_expiry ON licenses(license_expiry_date);

DROP TABLE IF EXISTS ownership_edges;
CREATE TABLE ownership_edges (
  parent_slug TEXT,
  parent_name TEXT,
  parent_symbol TEXT,
  child_slug TEXT,
  pct REAL,
  source TEXT
);
CREATE INDEX idx_own_child ON ownership_edges(child_slug);
CREATE INDEX idx_own_parent ON ownership_edges(parent_slug);

DROP TABLE IF EXISTS resolution;
CREATE TABLE resolution (
  company_slug TEXT PRIMARY KEY,
  symbol TEXT,
  method TEXT,
  confidence REAL,
  attributable_share REAL,
  hops INTEGER,
  detail TEXT
);
CREATE INDEX idx_res_symbol ON resolution(symbol);

DROP TABLE IF EXISTS meta;
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""

SCHEMA_T2 = """
DROP TABLE IF EXISTS performance;
CREATE TABLE performance (
  company_slug TEXT,
  year INTEGER,
  commodity_type TEXT,
  commodity_sub_type TEXT,
  unit TEXT,
  operation_status TEXT,
  production_volume REAL,
  sales_volume REAL,
  strip_ratio REAL,
  overburden_removal_volume REAL,
  reserves REAL,
  reserve_unit TEXT,
  resources REAL,
  resource_unit TEXT
);
CREATE INDEX idx_perf_slug ON performance(company_slug);
CREATE INDEX idx_perf_year ON performance(year);

DROP TABLE IF EXISTS sites;
CREATE TABLE sites (
  slug TEXT PRIMARY KEY,
  name TEXT,
  company_slug TEXT,
  company_name TEXT,
  commodity_type TEXT,
  year INTEGER,
  production_volume REAL,
  unit TEXT,
  strip_ratio REAL,
  reserves REAL,
  reserve_unit TEXT,
  province TEXT,
  city TEXT,
  latitude REAL,
  longitude REAL
);
CREATE INDEX idx_sites_slug ON sites(company_slug);

DROP TABLE IF EXISTS sales_destinations;
CREATE TABLE sales_destinations (
  company_slug TEXT,
  year INTEGER,
  country TEXT,
  revenue_usd REAL,
  pct_revenue REAL,
  volume REAL,
  pct_volume REAL,
  commodity_type TEXT,
  unit TEXT
);
CREATE INDEX idx_dest_slug ON sales_destinations(company_slug);

DROP TABLE IF EXISTS equity;
CREATE TABLE equity (
  symbol TEXT PRIMARY KEY,
  company_name TEXT,
  sector TEXT,
  sub_sector TEXT,
  market_cap REAL,
  market_cap_rank INTEGER,
  last_close_price REAL,
  listing_date TEXT,
  employee_num INTEGER
);

DROP TABLE IF EXISTS metrics_issuer;
CREATE TABLE metrics_issuer (
  symbol TEXT PRIMARY KEY,
  company_name TEXT,
  sub_sector TEXT,
  market_cap REAL,
  entity_count INTEGER,
  license_count INTEGER,
  licensed_ha_weighted REAL,
  lci_12m REAL,
  lci_24m REAL,
  lci_36m REAL,
  expired_share REAL,
  lci_flag TEXT,
  rli_years REAL,
  rli_flag TEXT,
  dominant_commodity TEXT,
  reserves REAL,
  reserve_unit TEXT,
  production REAL,
  strip_ratio_latest REAL,
  strip_ratio_slope REAL,
  strip_flag TEXT,
  reserve_replacement_ratio REAL,
  hhi REAL,
  hhi_top_country TEXT,
  hhi_max_share REAL,
  hhi_flag TEXT,
  hhi_basis TEXT,
  market_cap_per_reserve_unit REAL,
  performance_years TEXT,
  detail TEXT
);
"""


def build_t2(performance: dict, site_details: dict, sales: dict,
             equity: dict, metrics: list[dict]) -> pathlib.Path:
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA_T2)

    con.executemany(
        "INSERT INTO performance VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(slug, r.get("year"), r.get("commodity_type"), r.get("commodity_sub_type"),
          r.get("unit"), r.get("operation_status"), r.get("production_volume"),
          r.get("sales_volume"), r.get("strip_ratio"), r.get("overburden_removal_volume"),
          r.get("reserves"), r.get("reserve_unit"), r.get("resources"), r.get("resource_unit"))
         for slug, rows in performance.items() for r in rows],
    )

    con.executemany(
        "INSERT OR REPLACE INTO sites VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(s.get("slug"), s.get("name"), s.get("company_slug"), s.get("company_name"),
          s.get("commodity_type"), s.get("year"), s.get("production_volume"), s.get("unit"),
          s.get("strip_ratio"), s.get("reserves"), s.get("reserve_unit"),
          s.get("province"), s.get("city"), s.get("latitude"), s.get("longitude"))
         for s in site_details.values()],
    )

    con.executemany(
        "INSERT INTO sales_destinations VALUES (?,?,?,?,?,?,?,?,?)",
        [(slug, entry.get("year"), country, c.get("revenue_usd"), c.get("pct_revenue"),
          c.get("volume"), c.get("pct_volume"), c.get("commodity_type"), c.get("unit"))
         for slug, entry in sales.items() for country, c in entry.get("countries", {}).items()],
    )

    con.executemany(
        "INSERT OR REPLACE INTO equity VALUES (?,?,?,?,?,?,?,?,?)",
        [(v.get("symbol"), v.get("company_name"), v.get("sector"), v.get("sub_sector"),
          v.get("market_cap"), v.get("market_cap_rank"), v.get("last_close_price"),
          v.get("listing_date"), v.get("employee_num")) for v in equity.values()],
    )

    con.executemany(
        "INSERT OR REPLACE INTO metrics_issuer VALUES "
        "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(m["symbol"], m.get("company_name"), m.get("sub_sector"), m.get("market_cap"),
          m.get("entity_count"), m.get("license_count"), m.get("licensed_ha_weighted"),
          m.get("lci_12m"), m.get("lci_24m"), m.get("lci_36m"), m.get("expired_share"),
          m.get("lci_flag"), m.get("rli_years"), m.get("rli_flag"),
          m.get("dominant_commodity"), m.get("reserves"), m.get("reserve_unit"),
          m.get("production"), m.get("strip_ratio_latest"), m.get("strip_ratio_slope"),
          m.get("strip_flag"), m.get("reserve_replacement_ratio"), m.get("hhi"),
          m.get("hhi_top_country"), m.get("hhi_max_share"), m.get("hhi_flag"),
          m.get("hhi_basis"), m.get("market_cap_per_reserve_unit"),
          json.dumps(m.get("performance_years") or []), json.dumps(m, default=str))
         for m in metrics],
    )

    con.commit()
    con.close()
    return DB


def build(companies: list[dict], licenses: list[dict], edges: list[dict],
          resolution: dict[str, dict], meta: dict) -> pathlib.Path:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)

    con.executemany(
        "INSERT OR REPLACE INTO companies VALUES (?,?,?,?,?,?)",
        [(c.get("slug"), c.get("name"), c.get("symbol"), c.get("company_type"),
          c.get("key_operation"), json.dumps(c.get("commodity_type") or []))
         for c in companies if c.get("slug")],
    )

    con.executemany(
        "INSERT OR REPLACE INTO licenses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(l.get("wiup_code"), l.get("company_slug"), l.get("company_name"),
          l.get("license_number"), l.get("license_type"), l.get("activity"),
          l.get("license_effective_date"), l.get("license_expiry_date"),
          l.get("licensed_area_ha"), l.get("cnc"), l.get("generation"),
          l.get("province"), l.get("city"), l.get("commodity_type"))
         for l in licenses if l.get("wiup_code")],
    )

    con.executemany(
        "INSERT INTO ownership_edges VALUES (?,?,?,?,?,?)",
        [(e.get("parent_slug"), e.get("parent_name"), e.get("parent_symbol"),
          e.get("child_slug"), e.get("pct"), e.get("source")) for e in edges],
    )

    con.executemany(
        "INSERT OR REPLACE INTO resolution VALUES (?,?,?,?,?,?,?)",
        [(slug, r["symbol"], r["method"], r["confidence"],
          r.get("attributable_share"), r.get("hops"), json.dumps(r, default=str))
         for slug, r in resolution.items()],
    )

    con.executemany(
        "INSERT OR REPLACE INTO meta VALUES (?,?)",
        [(k, json.dumps(v, default=str)) for k, v in meta.items()],
    )

    con.commit()
    con.close()
    return DB
