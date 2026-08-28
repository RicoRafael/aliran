export default function Disclaimer() {
  return (
    <footer className="mt-16 border-t border-edge bg-panel/40 px-6 py-6 text-xs leading-relaxed text-muted">
      <p className="mb-2 font-medium uppercase tracking-wider text-[#a9b4c0]">
        Information and analysis tool — not investment advice
      </p>
      <p className="max-w-3xl">
        STRATA presents publicly available data from the Sectors Financial API and
        Indonesia&rsquo;s ESDM Minerba permit records. It does not provide investment advice
        or recommendations, and it does not execute trades of any kind.
      </p>
      <p className="mt-2 max-w-3xl">
        Mining permits are frequently renewed. A rising strip ratio can reflect growth
        investment rather than decline. Reserve figures are as reported by operators. A flag
        here means <em>a question worth asking</em>, not a prediction. Every figure carries an
        <span className="font-mono"> as_of </span> date — verify against primary sources
        before making any decision.
      </p>
    </footer>
  );
}
