import Link from "next/link";
import { notFound } from "next/navigation";
import Flag, { FlagCell } from "@/components/Flag";
import { fmtIDR, fmtNum, fmtPct, getIssuer, getTickers } from "@/lib/data";

export function generateStaticParams() {
  return getTickers().map((ticker) => ({ ticker }));
}

export default async function IssuerPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const data = getIssuer(ticker);
  if (!data) notFound();

  const m = data.metrics;
  const licenses = data.licenses;
  const sym = m.ticker ?? m.symbol?.replace(".JK", "") ?? ticker.toUpperCase();

  const buckets = [
    { label: "Expired", key: "expired", tone: "flag-red" },
    { label: "0–12 mo", key: "0_12m", tone: "flag-red" },
    { label: "12–24 mo", key: "12_24m", tone: "flag-amber" },
    { label: "24–36 mo", key: "24_36m", tone: "flag-neutral" },
  ];
  const counts = m.lci_counts ?? {};
  const maxCount = Math.max(1, ...buckets.map((b) => counts[b.key] ?? 0));

  const soon = licenses
    .filter((l) => l.months_to_expiry !== null && l.months_to_expiry >= 0)
    .slice(0, 25);

  const perfByYear = new Map<number, typeof data.performance>();
  for (const row of data.performance) {
    if (row.year === null) continue;
    const list = perfByYear.get(row.year) ?? [];
    list.push(row);
    perfByYear.set(row.year, list);
  }

  return (
    <div>
      <Link href="/" className="label hover:text-ink">
        ← Screener
      </Link>

      <div className="mb-5 mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1 border-b pb-3">
        <h1 className="mono text-[26px] font-medium leading-none tracking-tight">{sym}</h1>
        <span className="text-[13px] text-muted">{m.company_name ?? m.symbol}</span>
        <span className="label">{m.sub_sector ?? ""}</span>
        <span className="ml-auto flex items-baseline gap-2">
          <span className="label">Market cap</span>
          <span className="mono text-[14px]">{fmtIDR(m.market_cap)}</span>
        </span>
      </div>

      <div className="mb-7 grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-5">
        <Card
          label="Licence cliff 24m"
          value={fmtPct(m.lci_24m)}
          flag={m.lci_flag}
          note={`${fmtPct(m.lci_12m)} within 12 mo`}
        />
        <Card
          label="Reserve life"
          value={m.rli_years === null ? "—" : `${fmtNum(m.rli_years, 1)} yr`}
          flag={m.rli_flag}
          note={
            m.reserves
              ? `${fmtNum(m.reserves, 0)} ${m.reserve_unit ?? ""} reserves`
              : "reserves unavailable"
          }
        />
        {/* Level is uncoloured on purpose: strip ratio depends on geology and is
            not comparable between mines. The trend is the signal, so only the
            delta beneath carries colour. */}
        <div className="panel px-3 py-2.5">
          <span className="label">Strip ratio</span>
          <div className="mono mt-1.5 text-[22px] leading-none">
            {fmtNum(m.strip_ratio_latest, 2)}
          </div>
          <div className="mt-1.5 text-[10.5px] leading-snug">
            {m.strip_ratio_slope === null ? (
              <span className="text-muted">no multi-year series</span>
            ) : (
              <FlagCell flag={m.strip_flag}>
                {m.strip_ratio_slope > 0 ? "▲" : m.strip_ratio_slope < 0 ? "▼" : ""}
                {fmtNum(Math.abs(m.strip_ratio_slope), 3)} /yr over{" "}
                {m.strip_ratio_years ?? 0} yrs
              </FlagCell>
            )}
          </div>
        </div>
        <Card
          label="Reserve replacement"
          value={
            m.reserve_replacement_ratio === null
              ? "—"
              : `${fmtNum(m.reserve_replacement_ratio, 2)}${m.reserve_replacement_outlier ? "*" : ""}`
          }
          flag={m.reserve_replacement_outlier ? "unknown" : m.reserve_replacement_flag}
          note={
            m.reserve_replacement_outlier
              ? "* magnitude indicates a reserve restatement, not a replacement rate"
              : "1.0 = replaced what it mined"
          }
        />
        <Card
          label="Buyer concentration"
          value={fmtNum(m.hhi, 2)}
          flag={m.hhi_flag}
          note={
            m.hhi_top_country
              ? `${m.hhi_top_country} ${fmtPct(m.hhi_max_share)}`
              : "destination data unavailable"
          }
        />
      </div>

      <Section title="Licence expiry profile">
        <div className="panel p-4">
          <div className="space-y-3">
            {buckets.map((b) => {
              const n = counts[b.key] ?? 0;
              return (
                <div key={b.key} className="flex items-center gap-3">
                  <span className="w-20 shrink-0 text-xs text-muted">{b.label}</span>
                  <div className="h-5 flex-1 rounded bg-[#1a1f26]">
                    <div
                      className={`h-5 rounded ${b.tone}`}
                      style={{
                        width: `${(n / maxCount) * 100}%`,
                        background: "currentColor",
                        opacity: n ? 0.85 : 0,
                      }}
                    />
                  </div>
                  <span className="w-16 shrink-0 text-right font-mono text-xs">
                    {n} lic.
                  </span>
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-xs text-muted">
            {fmtNum(m.licensed_ha_weighted, 0)} attributable hectares across{" "}
            {m.entity_count} {m.entity_count === 1 ? "entity" : "entities"} and{" "}
            {m.license_count} licences. Hectares are weighted by ownership share and
            up-weighted 1.5× where Clear &amp; Clean status is absent.
          </p>
        </div>
      </Section>

      <Section title={`Licences by expiry — soonest first (${soon.length} of ${licenses.length})`}>
        <div className="panel overflow-x-auto">
          <table className="data">
            <thead>
              <tr>
                <th>Expiry</th>
                <th className="num">Months</th>
                <th className="num">Area ha</th>
                <th>Type</th>
                <th>Activity</th>
                <th>CnC</th>
                <th>Commodity</th>
                <th>Province</th>
                <th>Holder</th>
                <th className="num">Share</th>
                <th>Attributed via</th>
                <th>WIUP code</th>
              </tr>
            </thead>
            <tbody>
              {soon.map((l) => (
                <tr key={l.wiup_code}>
                  <td className="font-mono text-xs">{l.expiry_date ?? "—"}</td>
                  <td className="num">
                    <span
                      className={
                        (l.months_to_expiry ?? 99) <= 12
                          ? "flag-red"
                          : (l.months_to_expiry ?? 99) <= 24
                            ? "flag-amber"
                            : "text-muted"
                      }
                    >
                      {fmtNum(l.months_to_expiry, 0)}
                    </span>
                  </td>
                  <td className="num">{fmtNum(l.area_ha, 0)}</td>
                  <td className="text-xs">{l.license_type ?? "—"}</td>
                  <td className="text-xs text-muted">{l.activity ?? "—"}</td>
                  <td className="text-xs">
                    {l.cnc ? (
                      <span className="text-muted">{l.cnc}</span>
                    ) : (
                      <span className="flag-amber">none</span>
                    )}
                  </td>
                  <td className="text-xs text-muted">{l.commodity_type ?? "—"}</td>
                  <td className="text-xs text-muted">{l.province ?? "—"}</td>
                  <td className="text-xs text-muted">{l.company_name ?? "—"}</td>
                  <td className="num text-xs">{fmtPct(l.attributable_share, 0)}</td>
                  <td className="text-xs">
                    <span
                      className={`chip ${
                        l.resolution_confidence >= 0.95
                          ? "flag-neutral"
                          : l.resolution_confidence >= 0.85
                            ? "flag-amber"
                            : "flag-red"
                      }`}
                    >
                      {l.resolution_method.replace(/_/g, " ")} {l.resolution_confidence.toFixed(2)}
                    </span>
                  </td>
                  <td className="text-xs">
                    <span className="font-mono text-muted">{l.wiup_code}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-muted">
          WIUP code is the government permit identifier — the lookup key in Indonesia&rsquo;s
          ESDM Minerba records. Share is the ownership-weighted attribution to {sym}, and
          &ldquo;attributed via&rdquo; shows how that link was established, with its confidence
          score — an API-supplied ticker is certain, an ownership-tree link near-certain, a name
          match weaker.
        </p>
      </Section>

      {perfByYear.size > 0 && (
        <Section title="Production history">
          <div className="panel overflow-x-auto">
            <table className="data">
              <thead>
                <tr>
                  <th>Year</th>
                  <th>Entity</th>
                  <th>Commodity</th>
                  <th className="num">Production</th>
                  <th className="num">Sales</th>
                  <th className="num">Strip ratio</th>
                  <th className="num">Reserves</th>
                  <th>Unit</th>
                </tr>
              </thead>
              <tbody>
                {[...perfByYear.entries()]
                  .sort((a, b) => b[0] - a[0])
                  .flatMap(([year, rows]) =>
                    rows.map((r, n) => (
                      <tr key={`${year}-${r.company_slug}-${n}`}>
                        <td className="font-mono text-xs">{year}</td>
                        <td className="text-xs text-muted">{r.company_slug}</td>
                        <td className="text-xs text-muted">
                          {r.commodity_sub_type ?? r.commodity_type ?? "—"}
                        </td>
                        <td className="num">{fmtNum(r.production_volume, 2)}</td>
                        <td className="num text-muted">{fmtNum(r.sales_volume, 2)}</td>
                        <td className="num">{fmtNum(r.strip_ratio, 2)}</td>
                        <td className="num text-muted">{fmtNum(r.reserves, 1)}</td>
                        <td className="text-xs text-muted">{r.unit ?? "—"}</td>
                      </tr>
                    )),
                  )}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {data.sites.length > 0 && (
        <Section title={`Production sites (${data.sites.length})`}>
          <div className="panel overflow-x-auto">
            <table className="data">
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Commodity</th>
                  <th className="num">Production</th>
                  <th className="num">Reserves</th>
                  <th className="num">Lat</th>
                  <th className="num">Lon</th>
                </tr>
              </thead>
              <tbody>
                {data.sites.map((s) => (
                  <tr key={s.slug}>
                    <td className="text-xs">{s.name ?? s.slug}</td>
                    <td className="text-xs text-muted">{s.commodity ?? "—"}</td>
                    <td className="num">
                      {fmtNum(s.production, 2)}{" "}
                      <span className="text-muted">{s.unit ?? ""}</span>
                    </td>
                    <td className="num text-muted">
                      {fmtNum(s.reserves, 1)} {s.reserve_unit ?? ""}
                    </td>
                    <td className="num font-mono text-xs text-muted">{fmtNum(s.lat, 4)}</td>
                    <td className="num font-mono text-xs text-muted">{fmtNum(s.lon, 4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      <Section title="Attribution chain">
        <div className="panel p-4 text-[11.5px]">
          <p className="mb-3 text-muted">
            {sym} is linked to the following licence-holding entities. Confidence
            reflects how the link was established — an API-supplied ticker is certain, an
            ownership-tree link is near-certain, a name match is weaker.
          </p>
          <ul className="grid gap-1 sm:grid-cols-2">
            {(m.entities ?? []).map((slug) => (
              <li key={slug} className="mono text-[11px] text-muted">
                {slug}
              </li>
            ))}
          </ul>
        </div>
      </Section>

      <p className="mt-6 text-xs text-muted">
        Data as of <span className="font-mono">{data.as_of}</span>. Source: Sectors Financial
        API v2 (IDX equities, ESDM Minerba permit and production records).
      </p>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-7">
      <h2 className="rule label mb-2.5">{title}</h2>
      {children}
    </section>
  );
}

function Card({
  label,
  value,
  flag,
  note,
}: {
  label: string;
  value: string;
  flag: "red" | "amber" | "neutral" | "unknown";
  note?: string;
}) {
  return (
    <div className="panel px-3 py-2.5">
      <div className="flex items-start justify-between gap-2">
        <span className="label">{label}</span>
        {flag !== "unknown" && <Flag flag={flag} />}
      </div>
      <div className="mono mt-1.5 text-[22px] leading-none">
        <FlagCell flag={flag}>{value}</FlagCell>
      </div>
      {note && <div className="mt-1.5 text-[10.5px] leading-snug text-muted">{note}</div>}
    </div>
  );
}
