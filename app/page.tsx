import Link from "next/link";
import { FlagCell } from "@/components/Flag";
import { fmtFixed, fmtNum, fmtPct, getIndex } from "@/lib/data";

export default function Screener() {
  const idx = getIndex();

  if (!idx.issuers.length) {
    return (
      <div className="panel p-8 text-sm text-muted">
        No data yet. Run <span className="mono text-ink">python etl/run_t1.py</span> then{" "}
        <span className="mono text-ink">python etl/run_t2.py</span>.
      </div>
    );
  }

  const red = idx.issuers.filter((i) => i.lci_flag === "red").length;
  const amber = idx.issuers.filter((i) => i.lci_flag === "amber").length;
  const totalHa = idx.issuers.reduce((s, i) => s + (i.licensed_ha_weighted ?? 0), 0);
  const exposedHa = idx.issuers.reduce((s, i) => s + (i.exposed_ha_24m ?? 0), 0);

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="mb-1 text-[20px] font-medium tracking-tight">Licence exposure</h1>
          <p className="max-w-3xl text-[12px] leading-relaxed text-muted">
            IDX-listed resource issuers linked to mining licences through their ownership
            trees. Grouped by 24-month licence-cliff severity, then ranked by the hectares
            actually exposed.
          </p>
        </div>
        <div className="flex gap-6">
          <Stat label="Issuers" value={String(idx.issuer_count)} />
          <Stat label="High" value={String(red)} tone="var(--sig-red)" />
          <Stat label="Watch" value={String(amber)} tone="var(--sig-amber)" />
          <Stat label="Attributable ha" value={fmtNum(totalHa, 0)} />
          <Stat label="Exposed ≤24mo" value={fmtNum(exposedHa, 0)} tone="var(--sig-amber)" />
        </div>
      </div>

      <div className="panel max-h-[68vh] overflow-auto">
        <table className="data">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Company</th>
              <th>Commodity</th>
              <th className="num">Cliff 24m</th>
              <th className="num">Exposed ha</th>
              <th className="num">Cliff 12m</th>
              <th className="num">Res. life</th>
              <th className="num">Strip</th>
              <th className="num">Strip Δ/yr</th>
              <th className="num">Replacement</th>
              <th className="num">Attrib. ha</th>
              <th className="num">Ent.</th>
              <th className="num">Lic.</th>
            </tr>
          </thead>
          <tbody>
            {idx.issuers.map((i) => (
              <tr key={i.symbol}>
                <td>
                  <Link href={`/issuer/${i.ticker}/`} className="mono hover:underline">
                    {i.ticker}
                  </Link>
                </td>
                <td className="max-w-[240px] truncate text-muted">{i.company_name ?? "—"}</td>
                <td className="text-muted">{i.dominant_commodity ?? "—"}</td>
                <td className="num">
                  <FlagCell flag={i.lci_flag}>{fmtPct(i.lci_24m)}</FlagCell>
                </td>
                <td className="num">{fmtNum(i.exposed_ha_24m, 0)}</td>
                <td className="num text-muted">{fmtPct(i.lci_12m)}</td>
                <td className="num">
                  <FlagCell flag={i.rli_flag}>{fmtFixed(i.rli_years, 1)}</FlagCell>
                </td>
                <td className="num text-ink">{fmtFixed(i.strip_ratio_latest, 2)}</td>
                <td className="num">
                  {i.strip_ratio_slope === null ? (
                    <span className="text-dim">—</span>
                  ) : (
                    <FlagCell flag={i.strip_flag}>
                      {i.strip_ratio_slope > 0 ? "▲" : i.strip_ratio_slope < 0 ? "▼" : " "}
                      {fmtFixed(Math.abs(i.strip_ratio_slope), 2)}
                    </FlagCell>
                  )}
                </td>
                <td className="num">
                  {i.reserve_replacement_ratio === null ? (
                    <span className="text-dim">—</span>
                  ) : i.reserve_replacement_outlier ? (
                    <span
                      className="text-dim"
                      title="Magnitude indicates a reserve restatement, not a replacement rate"
                    >
                      {fmtFixed(i.reserve_replacement_ratio, 2)}*
                    </span>
                  ) : (
                    <FlagCell flag={i.reserve_replacement_flag}>
                      {fmtFixed(i.reserve_replacement_ratio, 2)}
                    </FlagCell>
                  )}
                </td>
                <td className="num">{fmtNum(i.licensed_ha_weighted, 0)}</td>
                <td className="num text-dim">{i.entity_count}</td>
                <td className="num text-dim">{i.license_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-[10.5px] text-muted">
        <span className="flex items-center gap-1.5">
          <i className="inline-block h-2 w-2" style={{ background: "var(--sig-red)" }} />
          cliff ≥ 20%
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block h-2 w-2" style={{ background: "var(--sig-amber)" }} />
          10–20%
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block h-2 w-2" style={{ background: "var(--sig-green)" }} />
          &lt; 10%
        </span>
        <span className="flex items-center gap-1.5">
          <i className="inline-block h-2 w-2" style={{ background: "var(--sig-dim)" }} />
          no data — not the same as clear
        </span>
        <span>
          Strip level is uncoloured: it depends on geology and is not comparable between
          mines. Only the trend is flagged.
        </span>
        <span>* restatement, not a replacement rate</span>
        <span className="mono">generated {idx.generated_at}</span>
      </div>

      <div className="mt-4 max-w-4xl space-y-2 text-[11.5px] leading-relaxed text-muted">
        <p>
          Coverage is partial and reported rather than smoothed over. Licences held by
          companies whose listed parent the API does not disclose are excluded rather than
          guessed at — see <span className="mono">etl/overrides/entity_map.yaml</span>, led by
          pt-berau-coal at 78,004&nbsp;ha.
        </p>
        <p>
          Per-metric coverage across {idx.issuer_count} issuers:{" "}
          <span className="mono">
            {Object.entries(idx.coverage)
              .map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`)
              .join("  ·  ")}
          </span>
          . Reserve life and replacement require production and reserves reported by the same
          entity in the same year, so they cover fewer issuers than the licence cliff.
        </p>
      </div>
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
