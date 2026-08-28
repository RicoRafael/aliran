"""Company-name normalisation, shared by entity resolution and interlock scoring."""

from __future__ import annotations

import re

# Indonesian corporate affixes that carry no identifying information.
_NOISE = (
    r"\bPT\b", r"\bTBK\b", r"\bPERSERO\b", r"\bPERUSAHAAN\b",
    r"\bTERBUKA\b", r"\bLTD\b", r"\bLIMITED\b", r"\bINC\b",
    r"\bCORP\b", r"\bCORPORATION\b", r"\bPLC\b", r"\bBV\b", r"\bNV\b",
    r"\bPTE\b", r"\bSDN\b", r"\bBHD\b",
)
_NOISE_RE = re.compile("|".join(_NOISE))
_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def normalise_company_name(raw: str | None) -> str:
    """
    'PT Adaro Energy Indonesia Tbk.' -> 'ADARO ENERGY INDONESIA'

    Uppercase, strip corporate affixes and punctuation, collapse whitespace.
    Deterministic and idempotent: f(f(x)) == f(x).
    """
    if not raw:
        return ""
    s = raw.upper()
    s = _PUNCT_RE.sub(" ", s)     # punctuation first, so "Tbk." -> "TBK "
    s = _NOISE_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s)
    return s.strip()


def name_key(raw: str | None) -> str:
    """Order-insensitive key for matching reordered names ('BANK NEGARA' vs 'NEGARA BANK')."""
    return " ".join(sorted(normalise_company_name(raw).split()))
