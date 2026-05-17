"""Core BB84 Quantum Key Distribution simulation engine (Refactored).

The implementation is deliberately dependency-light so the demo runs quickly in
hackathon settings. It models the BB84 information flow analytically and exposes
clean data structures that can later be swapped for Qiskit-backed execution.

This refactored version uses the Strategy pattern to separate backend implementations.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from .models import ProtocolRun, RunConfig
from .bb84_backends import get_backend

Basis = Literal["Z", "X"]
EveStrategy = Literal["none", "intercept_resend", "probabilistic", "basis_bias"]


def random_bits(length: int, rng: np.random.Generator) -> np.ndarray:
    """Return random classical bits as a NumPy array of 0s and 1s."""
    return rng.integers(0, 2, size=length, dtype=np.int8)


def random_bases(length: int, rng: np.random.Generator, bias_z: float = 0.5) -> np.ndarray:
    """Return random BB84 bases, where ``Z`` is computational and ``X`` is diagonal."""
    choices = rng.random(length) < bias_z
    return np.where(choices, "Z", "X")


def _measure_prepared_qubit(
    prepared_bits: np.ndarray,
    prepared_bases: np.ndarray,
    measurement_bases: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Measure BB84 states under the textbook rule.

    If the preparation and measurement bases match, the result is deterministic.
    If they differ, the result is uniformly random.
    """
    measured = prepared_bits.copy()
    mismatch = prepared_bases != measurement_bases
    measured[mismatch] = random_bits(int(mismatch.sum()), rng)
    return measured


def _apply_channel_noise(bits: np.ndarray, noise_rate: float, rng: np.random.Generator) -> np.ndarray:
    """Flip measured bits with independent probability ``noise_rate``."""
    if noise_rate <= 0:
        return bits
    noisy = bits.copy()
    flips = rng.random(len(bits)) < noise_rate
    noisy[flips] = 1 - noisy[flips]
    return noisy


def _apply_eve(
    alice_bits: np.ndarray,
    alice_bases: np.ndarray,
    strategy: EveStrategy,
    intercept_probability: float,
    eve_basis_bias_z: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return the post-Eve bits/bases that Bob receives plus Eve telemetry.

    Eve measures selected qubits, then resends her measured state. Non-intercepted
    qubits keep Alice's original state. This is enough to demonstrate why Eve
    creates a measurable QBER spike after basis sifting.
    """
    length = len(alice_bits)
    if strategy == "none" or intercept_probability <= 0:
        return (
            alice_bits.copy(),
            alice_bases.copy(),
            np.zeros(length, dtype=bool),
            np.full(length, "-", dtype=object),
        )

    if strategy == "intercept_resend":
        intercept_mask = np.ones(length, dtype=bool)
        bias = 0.5
    elif strategy == "probabilistic":
        intercept_mask = rng.random(length) < intercept_probability
        bias = 0.5
    elif strategy == "basis_bias":
        intercept_mask = rng.random(length) < intercept_probability
        bias = eve_basis_bias_z
    else:
        raise ValueError(f"Unsupported Eve strategy: {strategy}")

    eve_bases = np.full(length, "-", dtype=object)
    eve_bases[intercept_mask] = random_bases(int(intercept_mask.sum()), rng, bias_z=bias)

    resent_bits = alice_bits.copy()
    resent_bases = alice_bases.copy()
    if intercept_mask.any():
        measured = _measure_prepared_qubit(
            alice_bits[intercept_mask],
            alice_bases[intercept_mask],
            eve_bases[intercept_mask],
            rng,
        )
        resent_bits[intercept_mask] = measured
        resent_bases[intercept_mask] = eve_bases[intercept_mask]

    return resent_bits, resent_bases, intercept_mask, eve_bases


def calculate_qber(alice_key: np.ndarray, bob_key: np.ndarray) -> float:
    """Calculate Quantum Bit Error Rate for aligned sifted keys.

    Inputs may be NumPy arrays, Python lists, or other sequence-like objects.
    """
    alice = np.asarray(alice_key, dtype=np.int8)
    bob = np.asarray(bob_key, dtype=np.int8)
    if len(alice) == 0:
        return 0.0
    if len(alice) != len(bob):
        raise ValueError("alice_key and bob_key must have the same length")
    return float(np.mean(alice != bob))


def security_status(qber: float, threshold: float) -> str:
    """Return a human-readable security decision for a BB84 run."""
    if qber <= threshold:
        return "SECURE: continue privacy amplification"
    return "ABORT: possible eavesdropping or excessive channel noise"


def validate_config(config: RunConfig) -> None:
    """Validate configuration parameters before simulation."""
    if config.key_length < 8:
        raise ValueError("key_length must be at least 8 for meaningful sifting")
    if not 0 <= config.noise_rate <= 1:
        raise ValueError("noise_rate must be between 0 and 1")
    if not 0 <= config.sample_fraction <= 0.95:
        raise ValueError("sample_fraction must be between 0 and 0.95")
    if not 0 <= config.eve_intercept_probability <= 1:
        raise ValueError("eve_intercept_probability must be between 0 and 1")
    if not 0 <= config.eve_basis_bias_z <= 1:
        raise ValueError("eve_basis_bias_z must be between 0 and 1")
    if not 0 <= config.qber_abort_threshold <= 1:
        raise ValueError("qber_abort_threshold must be between 0 and 1")


def simulate_bb84(config: RunConfig) -> ProtocolRun:
    """Run a BB84 simulation according to ``config``.

    The result includes full per-qubit telemetry for visualization, sampled error
    checks, final key material after revealed bits are removed, and demo-friendly
    statistics.
    
    This refactored version uses the Strategy pattern to delegate to specific backends.
    """
    # Validate configuration
    validate_config(config)
    
    # Create RNG
    rng = np.random.default_rng(config.seed)
    
    # Get appropriate backend and run simulation
    try:
        backend = get_backend(config.simulation_backend)
        return backend.simulate(config, rng)
    except Exception as e:
        raise RuntimeError(
            f"{config.simulation_backend} simulation failed: {e}. "
            f"Check that required dependencies are installed."
        ) from e


def run_default_demo() -> ProtocolRun:
    """Convenience function used by tests, docs, and quick demos."""
    return simulate_bb84(RunConfig())

# Made with Bob
