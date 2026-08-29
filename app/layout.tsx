import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import Disclaimer from "@/components/Disclaimer";
import Wordmark from "@/components/Wordmark";
import { getIndex } from "@/lib/data";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "STRATA — physical asset intelligence for IDX resource issuers",
  description:
    "Links IDX-listed resource companies, through their ownership trees, to the mining licences, reserves and production sites that back their valuation.",
  // Advisory only — compliant crawlers honour these, others ignore them.
  // The enforceable position is LICENSE section 5. See also public/robots.txt.
  other: {
    noai: "true",
    noimageai: "true",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const idx = getIndex();
  const red = idx.issuers.filter((i) => i.lci_flag === "red").length;

  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body style={{ fontFamily: "var(--font-sans), system-ui, sans-serif" }}>
        <header className="border-b" style={{ background: "var(--panel)" }}>
          <div className="mx-auto flex max-w-[1600px] items-center gap-6 px-5 py-2.5">
            <Link href="/" className="hover:opacity-80">
              <Wordmark />
            </Link>

            <nav className="flex gap-4 label">
              <Link href="/" className="hover:text-[var(--text)]">
                Screener
              </Link>
              <Link href="/map/" className="hover:text-[var(--text)]">
                Sites
              </Link>
            </nav>

            <div className="ml-auto flex items-center gap-5 label">
              <StatusItem k="Issuers" v={String(idx.issuer_count)} />
              <StatusItem k="High exposure" v={String(red)} tone="var(--sig-red)" />
              <StatusItem k="As of" v={idx.as_of || "—"} />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1600px] px-5 py-6">{children}</main>
        <Disclaimer />
      </body>
    </html>
  );
}

function StatusItem({ k, v, tone }: { k: string; v: string; tone?: string }) {
  return (
    <span className="hidden items-center gap-1.5 sm:flex">
      <span>{k}</span>
      <span className="mono text-[11px]" style={{ color: tone ?? "var(--text)" }}>
        {v}
      </span>
    </span>
  );
}
