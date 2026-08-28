# Flag thresholds and why they are what they are

**Source of truth: [`etl/metrics/thresholds.py`](../etl/metrics/thresholds.py).** This document explains the values; it does not define them. If the two disagree, the code is right and this file is stale.

All thresholds are provisional until the Gate-1 spike measures real distributions. Record every change here with a date and a reason.

---

## A1 — Reserve Life Index

| Constant | Value | Reasoning |
|---|---|---|
| `RLI_RED` | 5.0 years | Below ~5 years of reserve life a producer is effectively liquidating its asset base. Current earnings say nothing about a company that runs out of mine before a typical DCF horizon closes. |
| `RLI_AMBER` | 8.0 years | Conventional analyst comfort floor. Between 5 and 8 years, reserve replacement becomes the dominant question for the equity story. |

**Known limitation.** RLI assumes production continues at the current rate and that reserves as reported are recoverable. Both assumptions are generous. Treat RLI as an upper bound on remaining life, never a forecast.

---

## A2 — License Cliff Index

| Constant | Value | Reasoning |
|---|---|---|
| `LCI_24M_RED` | 0.20 | If a fifth or more of attributable licensed acreage needs renewing inside two years, permit risk is a first-order driver of the equity, not a footnote. |
| `LCI_24M_AMBER` | 0.10 | Below 10% the exposure is unlikely to move valuation on its own. |
| `NON_CNC_RISK_WEIGHT` | 1.5 | Licenses without Clear & Clean status face materially higher renewal friction, so their hectares are over-weighted. The 1.5 multiplier is a judgement call, not an empirical result — flagged for tuning. |

**Design choices worth defending.**

- **Buckets are cumulative.** `lci_24m` includes everything in `0–12m`. Renewal risk is monotonic — a permit expiring in six months is also a permit expiring within two years.
- **Expired licenses are reported separately.** An already-expired permit is a different and worse fact than an expiring one. Folding the two together would hide the more serious case.
- **Weighting is by hectare, not by count.** One 50,000 ha concession matters more than twelve 200 ha permits, and counting rows would say the opposite.

**Known limitation.** Permits frequently *are* renewed. A high LCI signals unpriced uncertainty and a question worth asking management — it is not a prediction of loss.

---

## A3 — Strip Ratio Drift

| Constant | Value | Reasoning |
|---|---|---|
| `SRD_MIN_POINTS` | 3 | Two points define a line through noise. Three is the minimum for a slope worth reporting. |
| `SRD_RED` | 0.10 /yr | Roughly a 10% annual rise in waste-to-ore ratio. Compounds into structural unit-cost inflation. |
| `SRD_AMBER` | 0.02 /yr | Detectable upward drift, not yet material on its own. |

**The mechanism.** Strip ratio is overburden removed per unit of ore extracted. A rising ratio means each tonne costs more diesel, more equipment hours and more labour to reach. That lands in reported cost of revenue two to four quarters later — which is exactly what makes it a *leading* indicator rather than a description of the past.

**Validation:** correlate SRD against subsequent `cost_of_revenue[YYYY] / revenue[YYYY]` from the screener. Costs no extra credits (screener data is already cached). If the correlation is absent, say so in the README and demote the metric — do not demo a signal we could not verify.

---

## A4 — Destination Concentration

| Constant | Value | Reasoning |
|---|---|---|
| `SINGLE_COUNTRY_RED` | 0.50 | A single destination taking over half of revenue is a policy-risk single point of failure — one export ban or tariff reprices the equity. |
| `HHI_AMBER` | 0.40 | Standard competition-authority concentration boundary, borrowed here for buyer concentration. Roughly the level of 2–3 dominant buyers. |

---

## Ownership traversal

| Constant | Value | Reasoning |
|---|---|---|
| `OWNERSHIP_MAX_DEPTH` | 3 | Beyond three hops, attributed economic interest is small enough and uncertain enough to be noise. Also bounds a potentially expensive graph walk. |

Attribution uses the **dominant control path** — the strongest single chain — not the sum over all paths. Summing would double-count diamond ownership structures, which are common in Indonesian conglomerates.

---

## Entity resolution confidence

| Tier | Score | Basis |
|---|---|---|
| `api_symbol` | 1.00 | `symbol` returned directly by the API |
| `ownership_tree` | 0.95 | `symbol` on a parent/subsidiary node |
| `name_exact` | 0.85 | Normalised exact name match |
| `name_fuzzy` | 0.60 | Token-set similarity ≥ 92 |
| `manual` | 1.00 | Hand-reviewed in `etl/overrides/entity_map.yaml` |

`MIN_CONFIDENCE_FOR_METRICS = 0.85`. Edges below that are **still displayed**, labelled with their tier — they are just excluded from headline numbers. Showing a weak link and marking it weak is more useful than silently dropping it.

---

## Change log

| Date | Change | Reason |
|---|---|---|
| 2026-08-27 | Initial values set | Conventional mining-analyst practice; pre-spike, unvalidated against real distributions |
