# Slack messages — ready to send

Send **1** and **2** today. Message 3 can wait until after the spike run.

---

## 1. `#support` — API key provisioning ⚠️ HIGHEST PRIORITY

> **Why this matters:** the docs state the Sectors Financial API requires an **Insider plan**. The hackathon grants **credits**. If those are not the same thing, the entire architecture needs rethinking — and we need to know in week one, not week three. Escalation trigger: **Wednesday 2 September.**

```
Hi team — quick clarification on API access for the hackathon.

The docs (docs.sectors.app/get-started/v2/overview) say the Sectors Financial
API is available to Insider plan subscribers. The hackathon rules say each
registered team receives 1,000 API credits claimable from the team page.

Could you confirm: does claiming the team credits also provision Financial API
key access, or does the team representative need a separate Insider
subscription to generate a key at sectors.app/api?

Asking early because our project is built entirely on the REST API and we'd
rather resolve this now than discover it mid-build. Thanks!
```

---

## 2. `#discussion` — track fit confirmation

> **Why:** the rules explicitly invite this question, and judges may re-track a project rather than disqualify it. Asking is free insurance, and a public answer also anchors our track choice if it's ever questioned.

```
Hi all — track fit sanity check before we go deep.

We're building a market intelligence tool that joins the Indonesian mining
datasets (mining licenses, sites, reserves, ownership trees) to IDX-listed
issuers, then derives risk indicators from them — things like licence expiry
exposure and reserve life, attributed to a listed parent through its
ownership chain.

It produces scores and a screener, but there's no autonomous pipeline and no
LLM agent at its core — it's analysis output for a human analyst to read.
We've declared Track 03 (Market Intelligence) on that basis.

Does that sound right to you, or would you read a derived-scoring product as
closer to Track 02? Happy to be re-tracked if we've called it wrong.
```

---

## 3. `#support` — credit accounting verification

> **Why:** our credit ledger (`docs/credit-ledger.jsonl`) is a submission artefact. If the documented per-section / per-quarter / per-classification billing doesn't match what the portal actually decrements, the ledger is misleading and we'd rather correct it than defend it.

```
Hi — a question on credit accounting so our internal metering matches yours.

We're logging every call with its expected credit cost based on the v2 docs:
  · /v2/company/report/     → 1 per requested section
  · /v2/subsector/report/   → 1 per requested section
  · /v2/companies/top-changes/ → 1 per classification × period
  · /v2/financials/quarterly/  → 1 per quarter returned
  · /v2/companies/ with ?q=    → 3, with ?where= → 1
  · 400 / 401 / 403 / 429 / 5xx → free; 2xx and 404 → billed

Is that still accurate as of now? And is there an endpoint or dashboard view
that reports remaining team credits, so we can reconcile our own ledger
against your figure?
```

---

## 4. `#support` — committing derived data to a public repository

> **Why:** the rules require the repository to stay public for 90 days after winners are announced, and a judge should be able to clone it and run the product without credits. That means a derived extract of Sectors data is committed. Worth confirming that is acceptable — it protects both sides, and if it is not, far better to know before judging than after.

```
Hi — a terms question about what we commit to our public repo.

Our project caches Sectors API responses and derives a dataset from them
(mining licences, sites, ownership edges, computed metrics). We've committed
that to the public repository so judges can clone it and run the product
end to end without an API key and without spending credits — which also
lets them verify the numbers aren't hand-written for the demo.

That does mean a derived extract of Sectors data sits in a public repo that
the rules require us to keep public for 90 days after the announcement.

Is that acceptable under the API terms? We've added a DATA.md stating the
provenance, that it's included for build reproducibility only, and that it
is not licensed for redistribution or reuse. Happy to reduce it to a small
sample instead if you'd prefer — it would weaken the reproducibility story
but we'd rather ask than assume.
```

---

## Rules to keep in mind while posting

- Code of conduct applies on Slack. Keep it professional.
- Don't share the API key in any channel, ever.
- If anything looks like a rules violation, `#support` is the reporting channel.
