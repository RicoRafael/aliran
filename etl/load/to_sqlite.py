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
