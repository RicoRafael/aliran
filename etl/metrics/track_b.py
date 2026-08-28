"""
Track B — conglomerate & ownership lens.

Same pure-function discipline as track_a. Group membership arrives from
`idx_conglomerates_group_slug` on IDX filings, which the schema declares as
an ARRAY — a filing can belong to several groups.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Iterable, Sequence

from .names import name_key


# ══════════════════════════════════════════════════════════════════════════
#  B2 — Interlock Score
# ══════════════════════════════════════════════════════════════════════════


def interlock_score(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """
    Governance-concentration proxy between two issuers.

    a, b: {"symbol": str, "executives": [names], "shareholders": [names]}

    Matching runs on order-insensitive normalised name keys, so
    'PT Adaro Energy Tbk' and 'Adaro Energy' collide correctly.
    """
    def keys(items: Iterable[str] | None) -> set[str]:
        return {k for k in (name_key(x) for x in (items or [])) if k}

    shared_execs = keys(a.get("executives")) & keys(b.get("executives"))
    shared_holders = keys(a.get("shareholders")) & keys(b.get("shareholders"))

    return {
        "pair": (a.get("symbol"), b.get("symbol")),
        "shared_executives": sorted(shared_execs),
        "shared_shareholders": sorted(shared_holders),
        # Executives weighted 2x: a shared director is a stronger control
        # signal than a shared (possibly passive) shareholder.
        "score": 2 * len(shared_execs) + len(shared_holders),
    }


# ══════════════════════════════════════════════════════════════════════════
#  B3 — Group Insider Pulse
# ══════════════════════════════════════════════════════════════════════════


def _groups_of(filing: dict[str, Any]) -> set[str]:
    raw = filing.get("idx_conglomerates_group_slug") or filing.get("group_slug")
    if raw is None:
        return set()
    if isinstance(raw, str):
        return {raw}
    return {str(g) for g in raw if g}


def _ts_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def group_insider_pulse(
    filings: Sequence[dict[str, Any]],
    group_slug: str,
    as_of: dt.date,
    window_days: int = 30,
) -> dict[str, Any]:
    """
    Signed net insider transaction value for one conglomerate group.

    Positive = insiders were net buyers. Ticker-level insider flow is common;
    GROUP-level is not, which is what makes this worth building.

    Only holder_type == 'insider' counts. Institutions and corporate
    investors are excluded — they are not insiders.
    """
    start = as_of - dt.timedelta(days=window_days)
    net = 0.0
    buys = sells = 0
    tickers: set[str] = set()

    for f in filings:
        if group_slug not in _groups_of(f):
            continue
        if (f.get("holder_type") or "").lower() != "insider":
            continue
        when = _ts_date(f.get("timestamp"))
        if when is None or not (start <= when <= as_of):
            continue

        value = f.get("transaction_value")
        if value is None:
            continue
        value = abs(float(value))
        kind = (f.get("transaction_type") or "").lower()
        if kind == "buy":
            net += value
            buys += 1
        elif kind == "sell":
            net -= value
            sells += 1
        else:
            continue  # 'others' is unsigned; excluding it beats guessing
        if f.get("symbol"):
            tickers.add(f["symbol"])

    return {
        "group_slug": group_slug,
        "window_days": window_days,
        "as_of": as_of.isoformat(),
        "net_value": net,
        "buy_count": buys,
        "sell_count": sells,
        "tickers": sorted(tickers),
        "direction": "accumulating" if net > 0 else "distributing" if net < 0 else "flat",
    }
