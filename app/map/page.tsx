import SiteMap from "@/components/SiteMap";
import { getSites } from "@/lib/data";

export default function MapPage() {
  const { sites, as_of, count } = getSites();

  if (!count) {
    return (
      <div className="rounded border border-edge bg-panel p-8 text-sm text-muted">
        No site coordinates yet. Run <span className="font-mono text-white">etl/run_t2.py</span>.
      </div>
    );
  }

  const dated = sites.filter(
    (s) => (s.site_months_to_expiry ?? s.issuer_months_to_expiry) !== null,
  );
  const urgent = dated.filter(
    (s) => (s.site_months_to_expiry ?? s.issuer_months_to_expiry)! <= 24,
  );
  const provinces = new Set(sites.map((s) => s.slug.split("-")[0]));

  return (
    <div>
      <div className="mb-6">
        <h1 className="mb-1 text-xl font-semibold tracking-tight">Production sites</h1>
        <p className="max-w-3xl text-sm text-muted">
          Every mining site STRATA could place geographically and attribute to a listed
          issuer. Colour is the soonest licence expiry for that site&rsquo;s operating company;
          circle size is annual production. {urgent.length} of {dated.length} dated sites sit
          under a permit expiring within 24 months.
        </p>
      </div>

      <SiteMap sites={sites} />

      <p className="mt-4 max-w-3xl text-xs leading-relaxed text-muted">
        Coordinates come from the Sectors mining site detail endpoint, originally ESDM Minerba
        records. {count} of 143 known sites disclose them and belong to a resolved issuer.
        Sites without a dated licence are shown in grey rather than omitted — absence of a
        permit record is not evidence of an unencumbered site. Data as of{" "}
        <span className="font-mono text-white">{as_of}</span>.
      </p>
    </div>
  );
}
