from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metrics.names import name_key, normalise_company_name
from metrics.thresholds import CONFIDENCE, OWNERSHIP_MAX_DEPTH

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

FUZZY_MIN = 92


def _parents_index(edges: list[dict]) -> dict[str, list[dict]]:
    """
    child_slug -> edges naming its owners.

    Both edge sources are owner->child in shape: a `parents` edge came from
    querying the child, a `subsidiaries` edge from querying the owner. Filtering
    to one source throws away half the graph.
    """
    idx: dict[str, list[dict]] = {}
    for e in edges:
        child = e.get("child_slug")
        if child and e.get("parent_slug"):
            idx.setdefault(child, []).append(e)
    return idx


def resolve(companies: list[dict], edges: list[dict]) -> dict[str, dict]:
    """Map every mining company slug to a listed IDX ticker where possible."""
    own_symbol = {c["slug"]: c["symbol"] for c in companies if c.get("slug") and c.get("symbol")}
    parents = _parents_index(edges)

    listed_names = {}
    for c in companies:
        if c.get("symbol") and c.get("name"):
            listed_names[name_key(c["name"])] = (c["symbol"], c["name"])

    out: dict[str, dict] = {}

    for c in companies:
        slug = c.get("slug")
        if not slug:
            continue

        if slug in own_symbol:
            out[slug] = {
                "symbol": own_symbol[slug],
                "method": "api_symbol",
                "confidence": CONFIDENCE["api_symbol"],
                "attributable_share": 1.0,
                "hops": 0,
                "path": [slug],
            }
            continue

        best = _walk_up(slug, parents, own_symbol)
        if best:
            out[slug] = best
            continue

        matched = _match_name(c.get("name"), listed_names)
        if matched:
            out[slug] = matched

    return out


def _walk_up(slug: str, parents: dict[str, list[dict]], own_symbol: dict[str, str]) -> dict | None:
    best: dict | None = None
    stack = [(slug, 1.0, 0, [slug], frozenset({slug}))]

    while stack:
        node, share, hops, path, seen = stack.pop()
        if hops >= OWNERSHIP_MAX_DEPTH:
            continue
        for edge in parents.get(node, []):
            p_slug = edge["parent_slug"]
            if p_slug in seen:
                continue
            pct = edge.get("pct")
            nxt_share = share * (float(pct) / 100.0 if pct is not None else 1.0)
            symbol = edge.get("parent_symbol") or own_symbol.get(p_slug)
            if symbol:
                cand = {
                    "symbol": symbol,
                    "method": "ownership_tree",
                    "confidence": CONFIDENCE["ownership_tree"],
                    "attributable_share": nxt_share,
                    "hops": hops + 1,
                    "path": path + [p_slug],
                    "pct_chain_known": pct is not None,
                }
                if best is None or cand["attributable_share"] > best["attributable_share"]:
                    best = cand
            else:
                stack.append((p_slug, nxt_share, hops + 1, path + [p_slug], seen | {p_slug}))
    return best


def _match_name(name: str | None, listed_names: dict[str, tuple[str, str]]) -> dict | None:
    if not name:
        return None
    key = name_key(name)
    if key in listed_names:
        symbol, matched_name = listed_names[key]
        return {
            "symbol": symbol,
            "method": "name_exact",
            "confidence": CONFIDENCE["name_exact"],
            "attributable_share": 1.0,
            "hops": 0,
            "matched_name": matched_name,
        }
    if fuzz is None:
        return None

    norm = normalise_company_name(name)
    best_score, best_key = 0, None
    for cand_key in listed_names:
        score = fuzz.token_set_ratio(norm, cand_key)
        if score > best_score:
            best_score, best_key = score, cand_key
    if best_key and best_score >= FUZZY_MIN:
        symbol, matched_name = listed_names[best_key]
        return {
            "symbol": symbol,
            "method": "name_fuzzy",
            "confidence": CONFIDENCE["name_fuzzy"],
            "attributable_share": 1.0,
            "hops": 0,
            "matched_name": matched_name,
            "fuzzy_score": best_score,
        }
    return None


def gate2_report(resolution: dict[str, dict], licenses: list[dict], min_confidence: float = 0.85) -> dict:
    """Tickers resolving to at least one license at or above min_confidence."""
    licensed_slugs: dict[str, float] = {}
    for lic in licenses:
        slug = lic.get("company_slug")
        if slug:
            licensed_slugs[slug] = licensed_slugs.get(slug, 0.0) + float(lic.get("licensed_area_ha") or 0)

    per_ticker: dict[str, dict] = {}
    for slug, area in licensed_slugs.items():
        res = resolution.get(slug)
        if not res or res["confidence"] < min_confidence:
            continue
        entry = per_ticker.setdefault(res["symbol"], {
            "symbol": res["symbol"], "slugs": [], "attributable_ha": 0.0, "raw_ha": 0.0, "methods": set(),
        })
        entry["slugs"].append(slug)
        entry["raw_ha"] += area
        entry["attributable_ha"] += area * res.get("attributable_share", 1.0)
        entry["methods"].add(res["method"])

    for e in per_ticker.values():
        e["methods"] = sorted(e["methods"])
        e["license_slug_count"] = len(e["slugs"])

    unresolved = sorted(
        ((s, a) for s, a in licensed_slugs.items() if s not in resolution),
        key=lambda kv: -kv[1],
    )

    methods: dict[str, int] = {}
    for r in resolution.values():
        methods[r["method"]] = methods.get(r["method"], 0) + 1

    return {
        "tickers_resolved": len(per_ticker),
        "license_holding_slugs": len(licensed_slugs),
        "resolved_slugs": sum(1 for s in licensed_slugs if s in resolution),
        "unresolved_slugs": len(unresolved),
        "unresolved_top_by_area": unresolved[:15],
        "resolution_methods": methods,
        "per_ticker": sorted(per_ticker.values(), key=lambda e: -e["attributable_ha"]),
    }
