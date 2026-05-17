"""Typed data models for CryptoLab: BB84."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

EveStrategy = Literal["none", "intercept_resend", "probabilistic", "basis_bias"]


@dataclass(frozen=True)
class RunConfig:
    """Configuration for one BB84 protocol run."""

    key_length: int = 128
    noise_rate: float = 0.01
    eve_strategy: EveStrategy = "none"
    eve_intercept_probability: float = 1.0
    eve_basis_bias_z: float = 0.5
    sample_fraction: float = 0.25
    qber_abort_threshold: float = 0.11
    seed: int | None = 84
    simulation_backend: Literal["analytical", "qiskit_circuit", "density_matrix"] = "analytical"


@dataclass
class ProtocolRun:
    """Complete result object for a BB84 simulation."""

    config: dict[str, Any]
    alice_raw_bits: str
    bob_raw_bits: str
    alice_sifted_key: str
    bob_sifted_key: str
    alice_final_key: str
    bob_final_key: str
    qber: float
    sifted_length: int
    sample_size: int
    final_key_length: int
    agreement: bool
    status: str
    telemetry: pd.DataFrame = field(repr=False)

    @property
    def qber_percent(self) -> float:
        """Return QBER as a percentage."""
        return self.qber * 100

    @property
    def secure(self) -> bool:
        """Return true when the simulated run is below the configured abort threshold."""
        return self.status.startswith("SECURE")

    def summary(self) -> dict[str, Any]:
        """Return compact metrics for UI cards and API responses."""
        return {
            "qber": self.qber,
            "qber_percent": self.qber_percent,
            "sifted_length": self.sifted_length,
            "sample_size": self.sample_size,
            "final_key_length": self.final_key_length,
            "agreement": self.agreement,
            "status": self.status,
        }
