export default function Disclaimer() {
  return (
    <footer className="mt-12 border-t px-5 py-5" style={{ background: "var(--panel)" }}>
      <div className="mx-auto max-w-[1600px]">
        <p className="label mb-2">Information and analysis tool — not investment advice</p>
        <p className="max-w-4xl text-[11.5px] leading-relaxed" style={{ color: "var(--muted)" }}>
          STRATA presents publicly available data from the Sectors Financial API and
          Indonesia&rsquo;s ESDM Minerba permit records. It does not provide investment advice or
          recommendations, and it does not execute trades of any kind. Mining permits are
          frequently renewed. A rising strip ratio can reflect growth investment rather than
          decline. Reserve figures are as reported by operators. A flag here means{" "}
          <em>a question worth asking</em>, not a prediction. Every figure carries an{" "}
          <span className="mono">as_of</span> date — verify against primary sources before
          making any decision.
        </p>
      </div>
    </footer>
  );
}
