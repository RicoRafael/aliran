import type { Metadata } from "next";
import Link from "next/link";
import Disclaimer from "@/components/Disclaimer";
import "./globals.css";

export const metadata: Metadata = {
  title: "STRATA — physical asset intelligence for IDX resource issuers",
  description:
    "Links IDX-listed resource companies, through their ownership trees, to the mining licenses, reserves and production sites that back their valuation.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-edge px-6 py-4">
          <div className="mx-auto flex max-w-7xl items-baseline justify-between">
            <div className="flex items-baseline gap-4">
              <Link href="/" className="text-lg font-semibold tracking-tight">
                STRATA
              </Link>
              <span className="hidden text-xs text-muted sm:inline">
                The balance sheet tells you what a mining company earned. This tells you how
                long it can keep earning it.
              </span>
            </div>
            <nav className="flex gap-4 text-xs uppercase tracking-wider text-muted">
              <Link href="/" className="hover:text-white">
                Screener
              </Link>
              <Link href="/map/" className="hover:text-white">
                Sites
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        <Disclaimer />
      </body>
    </html>
  );
}
