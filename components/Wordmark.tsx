export default function Wordmark({ size = 16 }: { size?: number }) {
  return (
    <span className="flex items-center gap-2">
      <svg
        width={size}
        height={size}
        viewBox="0 0 16 16"
        aria-hidden="true"
        className="shrink-0"
      >
        <rect x="0" y="3" width="16" height="2" fill="var(--text)" />
        <rect x="0" y="7" width="12" height="2" fill="var(--muted)" />
        <rect x="0" y="11" width="7" height="2" fill="var(--dim)" />
      </svg>
      <span
        className="font-medium"
        style={{ letterSpacing: "0.14em", fontSize: "14px" }}
      >
        STRATA
      </span>
    </span>
  );
}
