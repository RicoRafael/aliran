# STRATA

**The balance sheet tells you what a mining company earned. STRATA tells you how long it can keep earning it.**

Sectors Hackathon 2026 · Track 03 — Market Intelligence

---

## The problem

A large share of Indonesia's stock market is resource companies. Their value depends on physical facts that never appear in a financial statement: how much ore is left, how long the government permit runs, whether extraction is getting more expensive, and who buys the output.

That data is public — it sits in Indonesia's ESDM Minerba permit records. But it is registered to **unlisted subsidiaries**, not the listed parent whose shares you can buy. So an analyst can quote a coal issuer's P/E to two decimals and not know that the mine behind 40% of its revenue holds a permit expiring in eleven months.

**Not missing data. Disconnected data.**

## What STRATA does

Joins mining permits, corporate ownership chains, and listed equities — so you can look up a ticker and see the physical reality underneath it.

The join works because the Sectors ownership endpoint returns the **IDX ticker** on subsidiary records. An unlisted subsidiary's expiring permit can therefore be traced, through a percentage-weighted ownership chain, back to the listed parent whose share price depends on it.

## What it tells you

| Question | Metric |
|---|---|
| How long does this company legally have? | **License Cliff Index** — attributable licensed hectares expiring within 0–36 months |
| Is its cost base structurally deteriorating? | **Strip Ratio Drift** — a physical signal that reaches reported COGS 2–4 quarters later |
| How long until the ore runs out? | **Reserve Life Index** — reserves ÷ current production rate |
| Who could stop buying? | **Destination concentration** — revenue HHI by export country |
| What does this conglomerate own in the ground? | **Group Physical Backing** — market-cap-weighted roll-up across a group's listed holdings |

## Who it's for

Equity analysts pricing resource issuers, fund managers checking for permit risk hiding as diversification, and journalists who need a sourceable lead with a government document behind every number.

## Running it

**Offline, zero API credits** — recommended for review:

```bash
npm install
npm run build
npm start
```

Then open http://localhost:3000. The pages are statically generated at build time from the committed JSON in `data/web/`, so there is no database, no native module and no API key involved — nothing is fetched at runtime.

`data/strata.sqlite` is also committed, but it is the analysis surface for ad-hoc SQL rather than the site's data source.

**Refreshing the data** — requires a Sectors API key:

```bash
pip install -r etl/requirements.txt
cp etl/.env.example etl/.env    # paste your key into etl/.env
python etl/run_t1.py            # universe, licences, ownership, entity resolution
python etl/run_t2.py            # performance, sites, equity, metrics, exports
```

`etl/spike.py` is the schema probe that established the API's real shapes; it is kept for the record and is not part of the pipeline.

Every response is cached to `fixtures/raw/` on first fetch, so re-runs cost **zero** credits. The client refuses any call that would exceed its tranche cap, and logs every billed call to `docs/credit-ledger.jsonl`.

**Tests** — no network:

```bash
python -m pytest etl/tests -v
```

## Data and honesty

All data comes from the [Sectors Financial API v2](https://docs.sectors.app). Remove it and this product is an empty shell.

Linking a government-registered company to an exchange ticker is genuinely ambiguous in places, so **every resolved link carries a confidence score and a method label**, both shown in the UI:

| Method | Confidence |
|---|---|
| `symbol` returned by the API | 1.00 |
| `symbol` on an ownership-tree node | 0.95 |
| Normalised exact name match | 0.85 |
| Token-set fuzzy match ≥92 | 0.60 |
| Hand-reviewed override | 1.00 |

Hand-reviewed mappings in `etl/overrides/entity_map.yaml` are committed on purpose — where we resolved something manually, you can check it. `docs/credit-ledger.jsonl` logs every billed API call. `docs/thresholds.md` explains every flag boundary, including the judgement calls.

---

## Disclaimer

STRATA is an **information and analysis tool**. It does not provide investment advice or recommendations, and it does not execute trades.

Permits are frequently renewed; rising costs can reflect growth investment rather than decay. A flag here means *a question worth asking*, not a prediction. All figures carry an `as_of` date — verify against primary sources before making any decision.
