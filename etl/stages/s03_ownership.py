from __future__ import annotations

from _common import load, log, save

MAX_SLUGS = 160


def _targets() -> list[tuple[str, float]]:
    """
    Rank by licensed hectares held, not by listed status.

    A listed holding company is already resolved via api_symbol and usually holds
    no licenses itself — spending a credit on its tree buys only its subsidiary
    list. The licence-holding subsidiaries are what need resolving, so they go
    first. Listed companies follow, since their subsidiary lists resolve children
    in bulk (one call can cover a dozen).
    """
    licenses = load("licenses")
    companies = load("companies")

    area_by_slug: dict[str, float] = {}
    for lic in licenses:
        slug = lic.get("company_slug")
        if not slug:
            continue
        area_by_slug[slug] = area_by_slug.get(slug, 0.0) + float(lic.get("licensed_area_ha") or 0)

    listed = {c["slug"] for c in companies if c.get("symbol") and c.get("slug")}

    holders = sorted(((s, a) for s, a in area_by_slug.items() if s not in listed), key=lambda kv: -kv[1])
    listed_ranked = sorted(((s, area_by_slug.get(s, 0.0)) for s in listed), key=lambda kv: -kv[1])
    return holders + listed_ranked


def run(client) -> dict:
    companies = load("companies")
    own_symbol = {c["slug"]: c["symbol"] for c in companies if c.get("slug") and c.get("symbol")}

    targets = _targets()
    log(f"{len(targets)} candidate slugs; capping at {MAX_SLUGS}")
    if len(targets) > MAX_SLUGS:
        dropped = sum(a for _, a in targets[MAX_SLUGS:])
        log(f"DROPPING {len(targets) - MAX_SLUGS} slugs holding {dropped:,.0f} ha "
            f"— recorded so coverage is not silently overstated")

    selected = targets[:MAX_SLUGS]
    edges: list[dict] = []
    trees: dict[str, dict] = {}
    failures: list[str] = []

    for slug, area in selected:
        try:
            tree = client.get(f"/v2/mining/companies/ownership/{slug}/")
        except Exception as exc:
            failures.append(f"{slug}: {type(exc).__name__}")
            continue
        if not isinstance(tree, dict):
            continue

        parents = tree.get("parents") or []
        subs = tree.get("subsidiaries") or []
        trees[slug] = {"parents": parents, "subsidiaries": subs, "licensed_area_ha": area}

        for p in parents:
            if not isinstance(p, dict) or not p.get("slug"):
                continue
            edges.append({
                "parent_slug": p["slug"],
                "parent_name": p.get("name"),
                "parent_symbol": p.get("symbol"),
                "child_slug": slug,
                "pct": p.get("percentage_ownership"),
                "source": "parents",
            })
        for s in subs:
            if not isinstance(s, dict) or not s.get("slug"):
                continue
            # The queried slug IS the owner here, so carry its own ticker across.
            # Dropping this discarded every subsidiary of every listed company.
            edges.append({
                "parent_slug": slug,
                "parent_name": None,
                "parent_symbol": own_symbol.get(slug),
                "child_slug": s["slug"],
                "pct": s.get("percentage_ownership"),
                "source": "subsidiaries",
                "child_symbol": s.get("symbol"),
            })

    with_listed_parent = {e["child_slug"] for e in edges if e.get("parent_symbol")}
    log(f"{len(trees)} trees fetched, {len(edges)} edges, "
        f"{len(with_listed_parent)} slugs have a listed parent")
    if failures:
        log(f"{len(failures)} failures: {failures[:5]}")

    save("ownership_edges", edges)
    save("ownership_trees", trees)
    return {
        "candidates": len(targets),
        "selected": len(selected),
        "dropped": max(0, len(targets) - MAX_SLUGS),
        "trees_fetched": len(trees),
        "edges": len(edges),
        "slugs_with_listed_parent": len(with_listed_parent),
        "failures": failures,
    }
