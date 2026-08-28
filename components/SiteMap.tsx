"use client";

import { Map as MapLibreMap, Marker, NavigationControl } from "maplibre-gl";
import type { StyleSpecification } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
import type { MapSite } from "@/lib/data";

const URGENCY = [
  { max: 12, color: "#e5484d", label: "≤ 12 months" },
  { max: 24, color: "#f5a524", label: "12–24 months" },
  { max: 36, color: "#d8b31a", label: "24–36 months" },
  { max: Infinity, color: "#46a758", label: "> 36 months" },
];
const NO_DATA = { color: "#5a646f", label: "no dated licence" };

function urgencyColor(months: number | null) {
  if (months === null || months === undefined) return NO_DATA.color;
  return URGENCY.find((u) => months <= u.max)!.color;
}

function radius(production: number | null) {
  if (!production || production <= 0) return 6;
  return Math.min(26, 6 + Math.sqrt(production) * 2.4);
}

const STYLE: StyleSpecification = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: ["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors © CARTO",
    },
  },
  layers: [
    { id: "bg", type: "background", paint: { "background-color": "#0b0d10" } },
    { id: "carto", type: "raster", source: "carto", paint: { "raster-opacity": 0.8 } },
  ],
};

export default function SiteMap({ sites }: { sites: MapSite[] }) {
  const container = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<MapSite | null>(null);
  const [tilesFailed, setTilesFailed] = useState(false);

  useEffect(() => {
    if (!container.current) return;

    const map = new MapLibreMap({
      container: container.current,
      style: STYLE,
      center: [117.5, -2.2],
      zoom: 4.1,
      // customAttribution is explicit rather than relying on the source spec:
      // OSM and CARTO both require visible attribution, and source-level
      // attribution was not being collected by the control.
      attributionControl: {
        compact: false,
        customAttribution:
          '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap</a> contributors · <a href="https://carto.com/attributions" target="_blank" rel="noreferrer">© CARTO</a>',
      },
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.on("error", (e) => {
      if (String(e?.error?.message ?? "").toLowerCase().includes("tile")) setTilesFailed(true);
    });

    const markers: Marker[] = [];
    for (const site of sites) {
      if (site.lat === null || site.lon === null) continue;
      const months = site.site_months_to_expiry ?? site.issuer_months_to_expiry ?? null;
      const size = radius(site.production);

      const el = document.createElement("button");
      el.type = "button";
      el.setAttribute("aria-label", `${site.name ?? site.slug} — ${site.ticker}`);
      Object.assign(el.style, {
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "50%",
        background: urgencyColor(months),
        border: "1.5px solid rgba(255,255,255,0.55)",
        opacity: "0.85",
        cursor: "pointer",
        padding: "0",
      });
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        setSelected(site);
      });

      markers.push(new Marker({ element: el }).setLngLat([site.lon, site.lat]).addTo(map));
    }

    return () => {
      markers.forEach((m) => m.remove());
      map.remove();
    };
  }, [sites]);

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
      <div className="relative">
        <div
          ref={container}
          className="h-[70vh] min-h-[420px] w-full overflow-hidden rounded border border-edge"
        />
        {tilesFailed && (
          <p className="absolute bottom-3 left-3 rounded bg-panel/90 px-3 py-1.5 text-xs text-muted">
            Basemap tiles unavailable — site positions are still accurate.
          </p>
        )}
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
          <span className="uppercase tracking-wider">Soonest licence expiry</span>
          {URGENCY.map((u) => (
            <span key={u.label} className="flex items-center gap-1.5">
              <i
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: u.color }}
              />
              {u.label}
            </span>
          ))}
          <span className="flex items-center gap-1.5">
            <i
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ background: NO_DATA.color }}
            />
            {NO_DATA.label}
          </span>
          <span>Circle size &prop; annual production</span>
        </div>
      </div>

      <aside className="rounded border border-edge bg-panel p-4">
        {selected ? (
          <div>
            <div className="mb-1 text-xs uppercase tracking-wider text-muted">
              {selected.commodity ?? "—"}
            </div>
            <h3 className="text-base font-medium">{selected.name ?? selected.slug}</h3>
            <a
              href={`/issuer/${selected.ticker}/`}
              className="text-sm text-[#7bb0ff] hover:underline"
            >
              {selected.ticker} — {selected.company_name ?? ""}
            </a>
            <dl className="mt-4 space-y-2 text-xs">
              <Row
                label="Annual production"
                value={
                  selected.production === null
                    ? "not reported"
                    : `${selected.production.toLocaleString()} ${selected.unit ?? ""}`
                }
              />
              <Row
                label="Reserves"
                value={
                  selected.reserves === null
                    ? "not reported"
                    : `${selected.reserves.toLocaleString()} ${selected.reserve_unit ?? ""}`
                }
              />
              <Row
                label="Soonest licence expiry"
                value={
                  selected.site_months_to_expiry === null
                    ? selected.issuer_months_to_expiry === null
                      ? "no dated licence"
                      : `${selected.issuer_months_to_expiry} mo (issuer-level)`
                    : `${selected.site_months_to_expiry} months`
                }
              />
              <Row
                label="Coordinates"
                value={`${selected.lat.toFixed(4)}, ${selected.lon.toFixed(4)}`}
              />
            </dl>
            {selected.production !== null &&
              selected.reserves !== null &&
              selected.unit !== selected.reserve_unit && (
                <p className="mt-3 border-t border-edge pt-3 text-[0.6875rem] leading-relaxed text-muted">
                  Production is reported in{" "}
                  <span className="font-mono">{selected.unit}</span> and reserves in{" "}
                  <span className="font-mono">{selected.reserve_unit}</span> — contained metal
                  versus ore tonnage. They are not divisible, so no reserve life is shown for
                  this site.
                </p>
              )}
          </div>
        ) : (
          <p className="text-sm text-muted">
            {sites.length} production sites with disclosed coordinates. Click a circle for site
            detail and a link to the issuer dossier.
          </p>
        )}
      </aside>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-mono">{value}</dd>
    </div>
  );
}
