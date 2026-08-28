import type { Flag as FlagType } from "@/lib/data";

const LABEL: Record<FlagType, string> = {
  red: "high",
  amber: "watch",
  neutral: "clear",
  unknown: "n/a",
};

export default function Flag({ flag }: { flag: FlagType }) {
  return <span className={`chip flag-${flag}`}>{LABEL[flag] ?? flag}</span>;
}

export function FlagCell({
  flag,
  children,
}: {
  flag: FlagType;
  children: React.ReactNode;
}) {
  return <span className={`flag-${flag}`}>{children}</span>;
}
