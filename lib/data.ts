import fs from "node:fs";
import path from "node:path";

const WEB = path.join(process.cwd(), "data", "web");

export type Flag = "red" | "amber" | "neutral" | "unknown";

export type Issuer = {
  symbol: string;
  ticker: string;
  company_name: string | null;
  sub_sector: string | null;
  market_cap: number | null;
  dominant_commodity: string | null;
  commodity_source: string | null;
  exposed_ha_24m: number | null;
  exposed_ha_12m: number | null;
  entity_count: number;
  license_count: number;
  licensed_ha_weighted: number | null;
  lci_12m: number | null;
  lci_24m: number | null;
  lci_36m: number | null;
  lci_flag: Flag;
  expired_share: number | null;
  rli_years: number | null;
  rli_flag: Flag;
  reserves: number | null;
  reserve_unit: string | null;
  production: number | null;
  strip_ratio_latest: number | null;
  strip_ratio_slope: number | null;
  strip_ratio_years: number | null;
  strip_flag: Flag;
  reserve_replacement_ratio: number | null;
  reserve_replacement_flag: Flag;
  reserve_replacement_outlier: boolean;
  hhi: number | null;
  hhi_top_country: string | null;
  hhi_max_share: number | null;
  hhi_flag: Flag;
  site_count: number;
};

export type License = {
  wiup_code: string;
  license_number: string | null;
  license_type: string | null;
  activity: string | null;
  commodity_type: string | null;
  province: string | null;
  city: string | null;
  company_name: string | null;
  company_slug: string | null;
  effective_date: string | null;
  expiry_date: string | null;
  months_to_expiry: number | null;
  area_ha: number | null;
  cnc: string | null;
  attributable_share: number | null;
  resolution_method: string;
  resolution_confidence: number;
};

export type PerformanceRow = {
  company_slug: string;
  year: number | null;
  commodity_type: string | null;
  commodity_sub_type: string | null;
  unit: string | null;
  production_volume: number | null;
  sales_volume: number | null;
  strip_ratio: number | null;
  reserves: number | null;
  reserve_unit: string | null;
};

export type IssuerDetail = {
  as_of: string;
  metrics: Issuer & {
    entities: string[];
    strip_ratio_points: [number, number][];
    reserve_replacement_entities: number;
    rli_entities_contributing: number;
    lci_counts: Record<string, number>;
    site_coords: SiteCoord[];
    performance_years: number[];
  };
  licenses: License[];
  performance: PerformanceRow[];
  sites: SiteCoord[];
};

export type SiteCoord = {
  slug: string;
  name: string | null;
  lat: number;
  lon: number;
  commodity: string | null;
  production: number | null;
  unit: string | null;
  reserves: number | null;
  reserve_unit: string | null;
  symbol?: string;
};

export type MapSite = SiteCoord & {
  ticker: string;
  company_name: string | null;
  site_months_to_expiry: number | null;
  issuer_months_to_expiry: number | null;
  lci_24m: number | null;
  lci_flag: Flag;
  owned_entities: number;
};

export type SitesFile = {
  as_of: string;
  count: number;
  bounds: { min_lat: number; max_lat: number; min_lon: number; max_lon: number } | null;
  sites: MapSite[];
};

export function getSites(): SitesFile {
  return (
    readJson<SitesFile>("sites.json") ?? {
      as_of: "",
      count: 0,
      bounds: null,
      sites: [],
    }
  );
}

export type Index = {
  as_of: string;
  generated_at: string;
  issuer_count: number;
  coverage: Record<string, number>;
  issuers: Issuer[];
};

function readJson<T>(rel: string): T | null {
  const file = path.join(WEB, rel);
  if (!fs.existsSync(file)) return null;
  return JSON.parse(fs.readFileSync(file, "utf-8")) as T;
}

export function getIndex(): Index {
  return (
    readJson<Index>("index.json") ?? {
      as_of: "",
      generated_at: "",
      issuer_count: 0,
      coverage: {},
      issuers: [],
    }
  );
}

export function getIssuer(ticker: string): IssuerDetail | null {
  return readJson<IssuerDetail>(path.join("issuers", `${ticker}.json`));
}

export function getTickers(): string[] {
  const dir = path.join(WEB, "issuers");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""));
}

export const fmtPct = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined ? "—" : `${(v * 100).toFixed(digits)}%`;

export const fmtNum = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined ? "—" : v.toLocaleString("en-US", { maximumFractionDigits: digits });

export const fmtIDR = (v: number | null | undefined) => {
  if (v === null || v === undefined) return "—";
  if (v >= 1e12) return `Rp ${(v / 1e12).toFixed(1)} T`;
  if (v >= 1e9) return `Rp ${(v / 1e9).toFixed(1)} B`;
  return `Rp ${v.toLocaleString("en-US")}`;
};
