"""Analytics utilities for BB84 security exploration."""

from __future__ import annotations

import pandas as pd

from .bb84 import simulate_bb84
from .models import RunConfig


def sweep_noise_and_eve(
    key_length: int = 512,
    noise_values: list[float] | None = None,
    intercept_values: list[float] | None = None,
    strategy: str = "probabilistic",
    seed: int = 2026,
) -> pd.DataFrame:
    """Generate a heatmap-ready QBER grid across channel noise and Eve strength."""
    noise_values = noise_values or [0.0, 0.02, 0.05, 0.08, 0.11, 0.15, 0.20]
    intercept_values = intercept_values or [0.0, 0.25, 0.50, 0.75, 1.0]

    rows: list[dict[str, float | str | bool | int]] = []
    run_id = 0
    for noise in noise_values:
        for intercept in intercept_values:
            run_id += 1
            cfg = RunConfig(
                key_length=key_length,
                noise_rate=noise,
                eve_strategy="none" if intercept == 0 else strategy,  # type: ignore[arg-type]
                eve_intercept_probability=intercept,
                seed=seed + run_id,
            )
            result = simulate_bb84(cfg)
            rows.append(
                {
                    "noise_rate": noise,
                    "eve_intercept_probability": intercept,
                    "qber": result.qber,
                    "qber_percent": result.qber_percent,
                    "secure": result.secure,
                    "final_key_length": result.final_key_length,
                }
            )
    return pd.DataFrame(rows)


def estimate_expected_qber(noise_rate: float, intercept_probability: float) -> float:
    """Approximate expected QBER for the educational explanation panel.

    A full intercept-resend attack contributes roughly 25% QBER on sifted bits.
    Independent channel noise contributes additional bit flips. The expression is
    intentionally simple and transparent for learners.
    """
    eve_component = 0.25 * intercept_probability
    combined = noise_rate + eve_component - (2 * noise_rate * eve_component)
    return max(0.0, min(1.0, combined))
