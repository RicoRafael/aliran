"""
Metric unit tests — no network, no API key, zero credits.

These must be green before any live data is pulled. Getting the maths wrong
against real data is far harder to debug than getting it wrong against fixtures.
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from metrics.cross import group_physical_backing  # noqa: E402
from metrics.names import name_key, normalise_company_name  # noqa: E402
from metrics.track_a import (  # noqa: E402
    attributable_share,
    destination_hhi,
    ev_per_tonne,
    license_cliff_index,
    realized_price_spread,
    reserve_life_index,
    rli_flag,
    srd_flag,
    strip_ratio_drift,
)
from metrics.track_b import group_insider_pulse, interlock_score  # noqa: E402

AS_OF = dt.date(2026, 1, 1)


# ── A1 Reserve Life Index ────────────────────────────────────────────────

def test_rli_normal():
    assert reserve_life_index(100.0, 10.0) == pytest.approx(10.0)


@pytest.mark.parametrize(
    "reserves,production",
    [(100.0, 0.0), (100.0, None), (None, 10.0), (100.0, -5.0), (-1.0, 10.0)],
)
def test_rli_returns_none_on_bad_input(reserves, production):
    """Government-scraped data has gaps. None, never an exception."""
    assert reserve_life_index(reserves, production) is None


def test_rli_flags():
    assert rli_flag(3.0) == "red"
    assert rli_flag(6.0) == "amber"
    assert rli_flag(20.0) == "neutral"
    assert rli_flag(None) == "unknown"


# ── Ownership attribution ────────────────────────────────────────────────

def test_attributable_share_direct():
    edges = [{"parent": "ADRO", "child": "sub-a", "pct": 100.0}]
    assert attributable_share(edges, "ADRO", "sub-a") == pytest.approx(1.0)


def test_attributable_share_two_level_chain():
    edges = [
        {"parent": "ADRO", "child": "mid", "pct": 80.0},
        {"parent": "mid", "child": "deep", "pct": 60.0},
    ]
    assert attributable_share(edges, "ADRO", "deep") == pytest.approx(0.48)


def test_attributable_share_diamond_picks_dominant_path():
    """Two routes to the same target: take the strongest, never the sum."""
    edges = [
        {"parent": "X", "child": "a", "pct": 50.0},
        {"parent": "X", "child": "b", "pct": 90.0},
        {"parent": "a", "child": "t", "pct": 50.0},   # 0.25
        {"parent": "b", "child": "t", "pct": 90.0},   # 0.81
    ]
    assert attributable_share(edges, "X", "t") == pytest.approx(0.81)


def test_attributable_share_respects_depth_cap():
    edges = [
        {"parent": "a", "child": "b", "pct": 100.0},
        {"parent": "b", "child": "c", "pct": 100.0},
        {"parent": "c", "child": "d", "pct": 100.0},
        {"parent": "d", "child": "e", "pct": 100.0},  # 4 hops
    ]
    assert attributable_share(edges, "a", "e", max_depth=3) == 0.0
    assert attributable_share(edges, "a", "e", max_depth=4) == pytest.approx(1.0)


def test_attributable_share_survives_cycle():
    edges = [
        {"parent": "a", "child": "b", "pct": 50.0},
        {"parent": "b", "child": "a", "pct": 50.0},
    ]
    assert attributable_share(edges, "a", "b") == pytest.approx(0.5)


def test_attributable_share_self_and_unreachable():
    assert attributable_share([], "a", "a") == 1.0
    assert attributable_share([], "a", "b") == 0.0


# ── A2 License Cliff Index ───────────────────────────────────────────────

def _lic(slug, expiry, ha, cnc="CNC"):
    return {
        "company_slug": slug,
        "license_expiry_date": expiry,
        "licensed_area_ha": ha,
        "cnc": cnc,
    }


def test_lci_buckets_are_cumulative():
    licenses = [
        _lic("s", "2026-06-01", 100),   # ~5 months  -> 0_12m
        _lic("s", "2027-06-01", 100),   # ~17 months -> 12_24m
        _lic("s", "2028-06-01", 100),   # ~29 months -> 24_36m
        _lic("s", "2040-01-01", 100),   # far future -> total only
    ]
    r = license_cliff_index(licenses, AS_OF)
    assert r["lci_12m"] == pytest.approx(0.25)
    assert r["lci_24m"] == pytest.approx(0.50)   # cumulative
    assert r["lci_36m"] == pytest.approx(0.75)   # cumulative
    assert r["counts"]["total"] == 4


def test_lci_expired_reported_separately_not_in_buckets():
    """An already-expired permit is a different, worse fact than an expiring one."""
    licenses = [_lic("s", "2025-06-01", 100), _lic("s", "2040-01-01", 100)]
    r = license_cliff_index(licenses, AS_OF)
    assert r["expired_share"] == pytest.approx(0.5)
    assert r["lci_12m"] == pytest.approx(0.0)
    assert r["counts"]["expired"] == 1


def test_lci_applies_non_cnc_uplift():
    """100ha non-CnC weighs 150; 100ha CnC weighs 100. Total 250."""
    licenses = [
        _lic("s", "2026-06-01", 100, cnc="Non CNC"),  # 150 weighted, in 0_12m
        _lic("s", "2040-01-01", 100, cnc="CNC"),      # 100 weighted
    ]
    r = license_cliff_index(licenses, AS_OF)
    assert r["total_ha_weighted"] == pytest.approx(250.0)
    assert r["lci_12m"] == pytest.approx(0.6)


def test_lci_applies_attributable_share():
    licenses = [_lic("owned-68", "2026-06-01", 100), _lic("owned-full", "2040-01-01", 100)]
    r = license_cliff_index(licenses, AS_OF, shares={"owned-68": 0.68, "owned-full": 1.0})
    assert r["total_ha_weighted"] == pytest.approx(168.0)
    assert r["lci_12m"] == pytest.approx(68.0 / 168.0)


@pytest.mark.parametrize("cnc_value", ["CNC", "CNC-1", "CNC-8", "CNC-27", "cnc"])
def test_lci_treats_all_cnc_variants_as_clean(cnc_value):
    """Spike P3 observed CNC, CNC-1, CNC-8, CNC-27. The suffix is a certificate
    batch, not a negation, so none of them should attract the risk weight."""
    r = license_cliff_index([_lic("s", "2040-01-01", 100, cnc=cnc_value)], AS_OF)
    assert r["total_ha_weighted"] == pytest.approx(100.0)


@pytest.mark.parametrize("cnc_value", [None, "", "-", "Non CNC", "pending"])
def test_lci_treats_unknown_cnc_as_unclean(cnc_value):
    """Unknown status must still attract the 1.5x renewal-risk weight."""
    r = license_cliff_index([_lic("s", "2040-01-01", 100, cnc=cnc_value)], AS_OF)
    assert r["total_ha_weighted"] == pytest.approx(150.0)


def test_lci_flags():
    assert license_cliff_index([_lic("s", "2026-06-01", 100)], AS_OF)["flag"] == "red"
    neutral = license_cliff_index(
        [_lic("s", "2026-06-01", 5), _lic("s", "2040-01-01", 95)], AS_OF
    )
    assert neutral["flag"] == "neutral"


def test_lci_empty_and_undated():
    empty = license_cliff_index([], AS_OF)
    assert empty["flag"] == "unknown" and empty["lci_24m"] is None

    undated = license_cliff_index([_lic("s", None, 100)], AS_OF)
    assert undated["counts"]["no_date"] == 1
    assert undated["lci_24m"] == pytest.approx(0.0)


def test_lci_ignores_malformed_expiry_date():
    r = license_cliff_index([_lic("s", "not-a-date", 100)], AS_OF)
    assert r["counts"]["no_date"] == 1


# ── A3 Strip Ratio Drift ─────────────────────────────────────────────────

def test_srd_rising_and_falling():
    assert strip_ratio_drift([(2022, 3.0), (2023, 3.5), (2024, 4.0)]) == pytest.approx(0.5)
    assert strip_ratio_drift([(2022, 4.0), (2023, 3.5), (2024, 3.0)]) == pytest.approx(-0.5)


def test_srd_flat():
    assert strip_ratio_drift([(2022, 3.0), (2023, 3.0), (2024, 3.0)]) == pytest.approx(0.0)


def test_srd_too_few_points():
    assert strip_ratio_drift([(2023, 3.0), (2024, 3.5)]) is None
    assert strip_ratio_drift([]) is None


def test_srd_zero_x_variance():
    """All observations in one year -> slope undefined, not a crash."""
    assert strip_ratio_drift([(2024, 1.0), (2024, 2.0), (2024, 3.0)]) is None


def test_srd_flags():
    assert srd_flag(0.5) == "red"
    assert srd_flag(0.05) == "amber"
    assert srd_flag(-0.1) == "neutral"
    assert srd_flag(None) == "unknown"


# ── A4 Destination concentration ─────────────────────────────────────────

def test_hhi_single_buyer():
    r = destination_hhi({"China": 100.0})
    assert r["hhi"] == pytest.approx(1.0)
    assert r["max_share"] == pytest.approx(1.0)
    assert r["top_country"] == "China"
    assert r["flag"] == "red"


def test_hhi_four_equal_buyers():
    r = destination_hhi({"China": 25.0, "India": 25.0, "Japan": 25.0, "Korea": 25.0})
    assert r["hhi"] == pytest.approx(0.25)
    assert r["flag"] == "neutral"


def test_hhi_ignores_zero_and_empty():
    assert destination_hhi({"China": 0.0})["hhi"] is None
    assert destination_hhi({})["flag"] == "unknown"


# ── A5 / A6 ──────────────────────────────────────────────────────────────

def test_ev_per_tonne():
    assert ev_per_tonne(1000.0, 200.0, 50.0, 100.0) == pytest.approx(11.5)
    assert ev_per_tonne(1000.0, None, None, 100.0) == pytest.approx(10.0)
    assert ev_per_tonne(1000.0, 0.0, 0.0, 0.0) is None
    assert ev_per_tonne(None, 0.0, 0.0, 100.0) is None


def test_realized_price_spread():
    assert realized_price_spread(1000.0, 10.0, 125.0) == pytest.approx(-0.2)
    assert realized_price_spread(1000.0, 10.0, 100.0) == pytest.approx(0.0)
    assert realized_price_spread(1000.0, 0.0, 100.0) is None


# ── Names ────────────────────────────────────────────────────────────────

def test_normalise_company_name():
    assert normalise_company_name("PT Adaro Energy Indonesia Tbk.") == "ADARO ENERGY INDONESIA"
    assert normalise_company_name("PT Bukit Asam (Persero) Tbk") == "BUKIT ASAM"
    assert normalise_company_name(None) == ""


def test_normalise_is_idempotent():
    once = normalise_company_name("PT Adaro Energy Indonesia Tbk.")
    assert normalise_company_name(once) == once


def test_name_key_is_order_insensitive():
    assert name_key("PT Bank Negara Tbk") == name_key("Negara Bank")


# ── Track B ──────────────────────────────────────────────────────────────

def test_interlock_score_weights_executives_double():
    a = {"symbol": "AAAA", "executives": ["Budi Santoso"], "shareholders": ["PT Induk Jaya"]}
    b = {"symbol": "BBBB", "executives": ["Budi Santoso"], "shareholders": ["PT Induk Jaya Tbk"]}
    r = interlock_score(a, b)
    assert r["score"] == 3          # 2*1 exec + 1 holder
    assert len(r["shared_executives"]) == 1
    assert len(r["shared_shareholders"]) == 1   # matched despite the 'Tbk'


def test_interlock_score_no_overlap():
    a = {"symbol": "A", "executives": ["X"], "shareholders": []}
    b = {"symbol": "B", "executives": ["Y"], "shareholders": []}
    assert interlock_score(a, b)["score"] == 0


def _filing(group, kind, value, ts, holder="insider", symbol="AAAA"):
    return {
        "idx_conglomerates_group_slug": [group],
        "transaction_type": kind,
        "transaction_value": value,
        "timestamp": ts,
        "holder_type": holder,
        "symbol": symbol,
    }


def test_group_insider_pulse_nets_signed_value():
    filings = [
        _filing("barito", "buy", 1_000.0, "2025-12-20"),
        _filing("barito", "sell", 3_000.0, "2025-12-22"),
    ]
    r = group_insider_pulse(filings, "barito", AS_OF, window_days=30)
    assert r["net_value"] == pytest.approx(-2_000.0)
    assert r["direction"] == "distributing"


def test_group_insider_pulse_filters_window_group_and_holder_type():
    filings = [
        _filing("barito", "buy", 500.0, "2025-12-20"),      # counted
        _filing("barito", "buy", 999.0, "2024-01-01"),       # outside window
        _filing("salim", "buy", 999.0, "2025-12-20"),        # wrong group
        _filing("barito", "buy", 999.0, "2025-12-20", holder="institution"),  # not insider
        _filing("barito", "others", 999.0, "2025-12-20"),    # unsigned
    ]
    r = group_insider_pulse(filings, "barito", AS_OF, window_days=30)
    assert r["net_value"] == pytest.approx(500.0)
    assert r["buy_count"] == 1


def test_group_insider_pulse_handles_scalar_group_slug():
    """The schema says array, but tolerate a bare string."""
    f = _filing("barito", "buy", 100.0, "2025-12-20")
    f["idx_conglomerates_group_slug"] = "barito"
    assert group_insider_pulse([f], "barito", AS_OF)["net_value"] == pytest.approx(100.0)


# ── X1 Cross-lens ────────────────────────────────────────────────────────

def test_group_physical_backing_weights_by_market_cap():
    """Equal weighting would give 0.50. Market-cap weighting gives 0.18."""
    members = [
        {"symbol": "BIG", "market_cap": 900.0, "lci_24m": 0.10, "rli": 20.0},
        {"symbol": "SMALL", "market_cap": 100.0, "lci_24m": 0.90, "rli": 4.0},
    ]
    r = group_physical_backing(members)
    assert r["group_lci_24m"] == pytest.approx(0.18)
    assert r["group_rli"] == pytest.approx(18.4)
    assert r["coverage"] == pytest.approx(1.0)


def test_group_physical_backing_reports_partial_coverage():
    """A cliff derived from 10% of market cap is a weak claim — say so."""
    members = [
        {"symbol": "BIG", "market_cap": 900.0, "lci_24m": None, "rli": None},
        {"symbol": "SMALL", "market_cap": 100.0, "lci_24m": 0.90, "rli": 4.0},
    ]
    r = group_physical_backing(members)
    assert r["group_lci_24m"] == pytest.approx(0.90)
    assert r["coverage"] == pytest.approx(0.10)


def test_group_physical_backing_empty():
    r = group_physical_backing([])
    assert r["flag"] == "unknown"
    assert "insufficient" in r["headline"]
