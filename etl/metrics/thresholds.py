"""
Single source of truth for every flag boundary.

docs/thresholds.md cites this module by name so documentation and code
cannot drift apart. Tune these after the Gate-1 spike measures the real
distributions, and record the reasoning in docs/thresholds.md.
"""

# ── A1 Reserve Life Index (years) ────────────────────────────────────────
# Conventional mining-analyst practice: under 5 years of reserve life a
# producer is effectively in liquidation regardless of current earnings.
RLI_RED = 5.0
RLI_AMBER = 8.0

# ── A2 License Cliff Index (fraction of attributable hectares) ───────────
LCI_24M_RED = 0.20
LCI_24M_AMBER = 0.10

# Licenses without Clear & Clean status carry materially higher renewal
# risk, so their hectares are over-weighted when computing the cliff.
NON_CNC_RISK_WEIGHT = 1.5

# ── A3 Strip Ratio Drift ────────────────────────────────────────────────
# Slope of strip_ratio per year. Positive = more waste rock per tonne of
# ore = structurally rising unit cash cost.
SRD_MIN_POINTS = 3
SRD_RED = 0.10
SRD_AMBER = 0.02

# ── Reserve Replacement Ratio ───────────────────────────────────────────
# 1.0 means the company replaced exactly what it mined. Below that it is
# depleting its asset base.
RRR_GREEN = 1.0
RRR_AMBER = 0.5

# A ratio this far from 1.0 is not mining activity — it is a reserve
# restatement, a reclassification, or an acquisition/divestment. Flag it as an
# outlier rather than presenting it as a replacement rate.
RRR_OUTLIER_ABS = 3.0

# ── A4 Destination Concentration ────────────────────────────────────────
HHI_AMBER = 0.40
SINGLE_COUNTRY_RED = 0.50

# ── Ownership traversal ─────────────────────────────────────────────────
# Chains deeper than 3 hops are noise, not control.
OWNERSHIP_MAX_DEPTH = 3

# ── Entity resolution confidence tiers (MASTER.md §6.4) ─────────────────
CONFIDENCE = {
    "api_symbol": 1.00,
    "ownership_tree": 0.95,
    "name_exact": 0.85,
    "name_fuzzy": 0.60,
    "manual": 1.00,
}
# Edges below this are excluded from headline metrics but still displayed.
MIN_CONFIDENCE_FOR_METRICS = 0.85
FUZZY_MATCH_MIN_SCORE = 92

DAYS_PER_MONTH = 30.4375
