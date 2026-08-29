# Data provenance and terms

## Where the data comes from

Every figure in STRATA originates from the **[Sectors Financial API v2](https://docs.sectors.app)**. There is no second source. Remove it and this product is an empty shell.

Sectors in turn sources the mining records from Indonesia's **ESDM Minerba** portal — the government registry of mining licences (IUP/IUPK/PKP2B), production sites and reserves — and the equity records from **IDX**.

## Why data is committed to this repository

`data/` and `fixtures/raw/` are committed for one reason: **so a reviewer can clone this repository and run the entire product without an API key and without spending a single credit.**

That reproducibility is a deliberate design goal. A judge should be able to verify that the numbers on screen come from real API responses rather than from a fixture hand-written to make a demo look good.

| Path | What it is |
|---|---|
| `data/web/*.json` | Computed metrics the site renders. Build input. |
| `data/strata.sqlite` | Normalised entity graph. Analysis surface for ad-hoc SQL. |
| `fixtures/raw/*.json` | Verbatim API responses, cached on first fetch. The offline replay path. |
| `docs/credit-ledger.jsonl` | Every billed API call: endpoint, timestamp, status, cost. |

## Terms

**This data is not licensed for redistribution or reuse.**

It was retrieved using API credits granted for Sectors Hackathon 2026. It remains subject to the terms of the Sectors Financial API and of the underlying government and exchange sources. Those terms take precedence over this repository's LICENSE.

Including it here for build reproducibility is **not** a grant of any right to:

- redistribute it, in whole or in part
- use it in another product or service
- use it as training data for machine learning models
- commercially exploit it in any form

If you want this data, get it from Sectors directly: https://sectors.app

## Freshness

Every figure carries an `as_of` date, shown in the interface and stored in each JSON export. Mining licence and reserve records change infrequently — quarterly at most — but the snapshot here is exactly that: a snapshot. It is not live, and it is not maintained.

## Regenerating it

```bash
pip install -r etl/requirements.txt
cp etl/.env.example etl/.env     # your own Sectors API key
python etl/run_t1.py
python etl/run_t2.py
```

A full cold build costs roughly 450–500 credits. Cached responses cost nothing, so re-runs are free. The client refuses any call that would breach its tranche cap.

## A note on accuracy

Linking a government-registered licence holder to an exchange-listed ticker is genuinely ambiguous in places. Every resolved link carries a confidence score and the method that produced it, both surfaced in the interface. Where the product could not resolve a link, it says so rather than guessing — 43 licence-holding companies remain unattributed, led by pt-berau-coal at 78,004 hectares.

Reserve and production figures are **as reported by operators**. They are not independently verified, and mining companies restate them.
