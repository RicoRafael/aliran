import SiteMap from "@/components/SiteMap";
import { getSites } from "@/lib/data";

export default function MapPage() {
  const { sites, as_of, count } = getSites();

  if (!count) {
    return (
      <div className="panel p-8 text-[12px] text-muted">
        No site coordinates yet. Run <span className="mono text-ink">etl/run_t2.py</span>.
      </div>
    );
  }

  const dated = sites.filter(
    (s) => (s.site_months_to_expiry ?? s.issuer_months_to_expiry) !== null,
  );
  const urgent = dated.filter(
    (s) => (s.site_months_to_expiry ?? s.issuer_months_to_expiry)! <= 24,
  );

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="mb-1 text-[20px] font-medium tracking-tight">Production sites</h1>
          <p className="max-w-3xl text-[12px] leading-relaxed text-muted">
            Mining sites placed geographically and attributed to a listed issuer. Colour is the
            soonest licence expiry for the operating company; circle size is annual production.
          </p>
        </div>
        <div className="flex gap-6">
          <Stat label="Sites" value={String(count)} />
          <Stat label="With dated licence" value={String(dated.length)} />
          <Stat
            label="Expiring ≤ 24mo"
            value={String(urgent.length)}
            tone="var(--sig-amber)"
          />
        </div>
      </div>

      <SiteMap sites={sites} />

      <p className="mt-3.5 max-w-4xl text-[11.5px] leading-relaxed text-muted">
        Coordinates come from the Sectors mining site detail endpoint, originally ESDM Minerba
        records. {count} of 143 known sites disclose them and belong to a resolved issuer. Sites
        without a dated licence are shown in grey rather than omitted &mdash; absence of a permit
        record is not evidence of an unencumbered site. Data as of{" "}
        <span className="mono text-ink">{as_of}</span>.
      </p>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="mono mt-0.5 text-[17px]" style={{ color: tone ?? "var(--text)" }}>
        {value}
      </div>
    </div>
  );
}
