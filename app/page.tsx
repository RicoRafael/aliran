import Link from "next/link";
import Flag, { FlagCell } from "@/components/Flag";
import { fmtIDR, fmtNum, fmtPct, getIndex } from "@/lib/data";

export default function Screener() {
  const idx = getIndex();

  if (!idx.issuers.length) {
    return (
      <div className="rounded border border-edge bg-panel p-8 text-sm text-muted">
        No data yet. Run <span className="font-mono text-white">python etl/run_t1.py</span> then{" "}
        <span className="font-mono text-white">python etl/run_t2.py</span> to build{" "}
        <span className="font-mono">data/web/</span>.
      </div>
    );
  }

  const red = idx.issuers.filter((i) => i.lci_flag === "red").length;
  const amber = idx.issuers.filter((i) => i.lci_flag === "amber").length;
  const totalHa = idx.issuers.reduce((s, i) => s + (i.licensed_ha_weighted ?? 0), 0);

  return (
    <div>
      <div className="mb-6">
        <h1 className="mb-1 text-xl font-semibold tracking-tight">Licence exposure screener</h1>
        <p className="max-w-3xl text-sm text-muted">
          Every IDX-listed resource issuer STRATA could link to at least one mining licence
          through its ownership tree. Sorted by 24-month licence cliff — the share of
          attributable licensed hectares whose permit expires within two years.
        </p>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Issuers covered" value={String(idx.issuer_count)} />
        <Stat label="High exposure" value={String(red)} tone="red" />
        <Stat label="Watch" value={String(amber)} tone="amber" />
        <Stat label="Attributable hectares" value={fmtNum(totalHa, 0)} />
      </div>

      <div className="overflow-x-auto rounded border border-edge">
        <table className="data">
          <thead>
            <tr>
              <th>Issuer</th>
              <th>Commodity</th>
              <th className="num">Cliff 24m</th>
              <th className="num">Exposed ha</th>
              <th className="num">Cliff 12m</th>
              <th className="num">Reserve life</th>
              <th className="num">Strip</th>
              <th className="num">Replacement</th>
              <th className="num">Attrib. ha</th>
              <th className="num">Entities</th>
              <th className="num">Licences</th>
            </tr>
          </thead>
          <tbody>
            {idx.issuers.map((i) => (
              <tr key={i.symbol}>
                <td>
                  <Link href={`/issuer/${i.ticker}/`} className="font-medium hover:underline">
                    {i.ticker}
                  </Link>
                  <span className="ml-2 text-xs text-muted">{i.company_name ?? ""}</span>
                </td>
                <td className="text-xs text-muted">{i.dominant_commodity ?? "—"}</td>
                <td className="num">
                  <FlagCell flag={i.lci_flag}>{fmtPct(i.lci_24m)}</FlagCell>
                </td>
                <td className="num">{fmtNum(i.exposed_ha_24m, 0)}</td>
                <td className="num text-muted">{fmtPct(i.lci_12m)}</td>
                <td className="num">
                  <FlagCell flag={i.rli_flag}>
                    {i.rli_years === null ? "—" : `${fmtNum(i.rli_years, 1)} yr`}
                  </FlagCell>
                </td>
                <td className="num">
                  <FlagCell flag={i.strip_flag}>{fmtNum(i.strip_ratio_latest, 2)}</FlagCell>
                </td>
                <td className="num text-muted">{fmtNum(i.reserve_replacement_ratio, 2)}</td>
                <td className="num">{fmtNum(i.licensed_ha_weighted, 0)}</td>
                <td className="num text-muted">{i.entity_count}</td>
                <td className="num text-muted">{i.license_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted">
        <span>
          Data as of <span className="font-mono text-white">{idx.as_of}</span>
        </span>
        <span>
          Generated <span className="font-mono">{idx.generated_at}</span>
        </span>
        <span className="flex items-center gap-2">
          <Flag flag="red" /> cliff ≥ 20%
          <Flag flag="amber" /> ≥ 10%
        </span>
      </div>

      <div className="mt-4 max-w-3xl space-y-2 text-xs leading-relaxed text-muted">
        <p>
          Coverage is partial and reported rather than smoothed over. Licences held by
          companies whose listed parent the API does not disclose are excluded rather than
          guessed at — see <span className="font-mono">etl/overrides/entity_map.yaml</span> for
          the known gaps, led by pt-berau-coal at 78,004&nbsp;ha.
        </p>
        <p>
          Per-metric coverage across {idx.issuer_count} issuers:{" "}
          {Object.entries(idx.coverage)
            .map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`)
            .join(" · ")}
          . Reserve life and replacement need production and reserves reported by the same
          entity in the same year, so they cover fewer issuers than the licence cliff.
          Destination concentration is present for only two issuers and is shown on the
          issuer page rather than here.
        </p>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "red" | "amber";
}) {
  const color = tone === "red" ? "flag-red" : tone === "amber" ? "flag-amber" : "";
  return (
    <div className="rounded border border-edge bg-panel px-4 py-3">
      <div className="text-[0.6875rem] uppercase tracking-wider text-muted">{label}</div>
      <div className={`mt-1 font-mono text-xl ${color}`}>{value}</div>
    </div>
  );
}
