"""Turning tokens into an estimated dollar figure (REQUIREMENTS.md 8, 15).

The token counts are real, measured per run from PydanticAI's usage. The
dollar rates are NOT: gpt-6-luna is served through the course Portkey key and
its price per token is not published anywhere this app can read.

So the rates below are an explicit, overridable assumption, and the UI labels
the figure as an estimate. Override with environment variables rather than
editing this file:

    READYHOME_RATE_INPUT=0.00000125    # dollars per input token
    READYHOME_RATE_CACHED=0.000000125  # dollars per cached input token
    READYHOME_RATE_OUTPUT=0.00001      # dollars per output token

TODO(camille): put the real per-token rates here once the course confirms
them, and say in the report that the figure is an estimate on these rates.
"""

import os

from .config import MODEL_NAME

# Placeholder rates in dollars per token, in the usual shape for this model
# class: cached input an order of magnitude cheaper, output several times
# the input rate.
DEFAULT_RATE_INPUT = 1.25e-6
DEFAULT_RATE_CACHED = 1.25e-7
DEFAULT_RATE_OUTPUT = 1.0e-5

RATES_ARE_ESTIMATES = True


def _rate(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


RATES = {
    "input_per_token": _rate("READYHOME_RATE_INPUT", DEFAULT_RATE_INPUT),
    "cached_per_token": _rate("READYHOME_RATE_CACHED", DEFAULT_RATE_CACHED),
    "output_per_token": _rate("READYHOME_RATE_OUTPUT", DEFAULT_RATE_OUTPUT),
    "are_estimates": RATES_ARE_ESTIMATES,
    "note": (
        "Token counts are measured. Dollar rates are an assumption for "
        f"{MODEL_NAME}; see backend/app/pricing.py."
    ),
}


def cost_usd(input_tokens: int, cached_tokens: int, output_tokens: int) -> float:
    """Estimated dollars for one set of token counts.

    Cached input tokens are billed at the cached rate, so they are taken out
    of the plain input count rather than charged twice.
    """
    billable_input = max(input_tokens - cached_tokens, 0)
    total = (
        billable_input * RATES["input_per_token"]
        + cached_tokens * RATES["cached_per_token"]
        + output_tokens * RATES["output_per_token"]
    )
    return round(total, 6)


def projections(session_cost: float) -> dict:
    """What this session would cost at the scales the report asks for."""
    return {
        "per_session": round(session_cost, 6),
        "per_100_users": round(session_cost * 100, 2),
        "per_10000_users": round(session_cost * 10_000, 2),
        "assumption": "One completed survey per user per month.",
    }
