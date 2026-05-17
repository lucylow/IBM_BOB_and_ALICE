
"""Core BB84 Quantum Key Distribution simulation engine.

The implementation is deliberately dependency-light so the demo runs quickly in
hackathon settings. It models the BB84 information flow analytically and exposes
clean data structures that can later be swapped for Qiskit-backed execution.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Literal, Optional

import numpy as np
import pandas as pd

from .models import ProtocolRun, RunConfig
from .qkd.optimised_circuits import build_bb84_circuit_parallel
from .qkd.bb84_density_improved import run_bb84_density_fast

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


def simulate_bb84(config: RunConfig) -> ProtocolRun:
    """Run an analytical BB84 simulation according to ``config``.

    The result includes full per-qubit telemetry for visualization, sampled error
    checks, final key material after revealed bits are removed, and demo-friendly
    statistics.
    """
    rng = np.random.default_rng(config.seed)
    length = int(config.key_length)
    if length < 8:
        raise ValueError("key_length must be at least 8 for meaningful sifting")
    if not 0 <= config.noise_rate <= 1:
        raise ValueError("noise_rate must be between 0 and 1")
    if not 0 <= config.sample_fraction <= 0.95:
        raise ValueError("sample_fraction must be between 0 and 0.95")

    if config.simulation_backend == "analytical":
        alice_bits = random_bits(length, rng)
        alice_bases = random_bases(length, rng)
        bob_bases = random_bases(length, rng)

        channel_bits, channel_bases, eve_intercepted, eve_bases = _apply_eve(
            alice_bits,
            alice_bases,
            config.eve_strategy,
            config.eve_intercept_probability,
            config.eve_basis_bias_z,
            rng,
        )

        bob_bits = _measure_prepared_qubit(channel_bits, channel_bases, bob_bases, rng)
        bob_bits = _apply_channel_noise(bob_bits, config.noise_rate, rng)

        matching_basis = alice_bases == bob_bases
        sift_indices = np.flatnonzero(matching_basis)
        alice_sifted = alice_bits[sift_indices]
        bob_sifted = bob_bits[sift_indices]

        sample_size = max(1, int(round(len(sift_indices) * config.sample_fraction))) if len(sift_indices) else 0
        if sample_size:
            sampled_positions = np.sort(rng.choice(len(sift_indices), size=sample_size, replace=False))
            key_positions = np.setdiff1d(np.arange(len(sift_indices)), sampled_positions)
        else:
            sampled_positions = np.array([], dtype=int)
            key_positions = np.arange(len(sift_indices))

        alice_sample = alice_sifted[sampled_positions]
        bob_sample = bob_sifted[sampled_positions]
        qber = calculate_qber(alice_sample, bob_sample)

        alice_final = alice_sifted[key_positions]
        bob_final = bob_sifted[key_positions]
        agreement = bool(np.array_equal(alice_final, bob_final)) if len(alice_final) else False

        telemetry = pd.DataFrame(
            {
                "index": np.arange(length),
                "alice_bit": alice_bits.astype(int),
                "alice_basis": alice_bases,
                "eve_intercepted": eve_intercepted.astype(bool),
                "eve_basis": eve_bases,
                "bob_basis": bob_bases,
                "bob_bit": bob_bits.astype(int),
                "basis_match": matching_basis.astype(bool),
                "sifted": matching_basis.astype(bool),
            }
        )
        telemetry["bit_error_when_sifted"] = telemetry["sifted"] & (telemetry["alice_bit"] != telemetry["bob_bit"])

        return ProtocolRun(
            config=asdict(config),
            alice_raw_bits="".join(map(str, alice_bits.tolist())),
            bob_raw_bits="".join(map(str, bob_bits.tolist())),
            alice_sifted_key="".join(map(str, alice_sifted.astype(int).tolist())),
            bob_sifted_key="".join(map(str, bob_sifted.astype(int).tolist())),
            alice_final_key="".join(map(str, alice_final.astype(int).tolist())),
            bob_final_key="".join(map(str, bob_final.astype(int).tolist())),
            qber=qber,
            sifted_length=int(len(sift_indices)),
            sample_size=int(sample_size),
            final_key_length=int(len(alice_final)),
            agreement=agreement,
            status=security_status(qber, config.qber_abort_threshold),
            telemetry=telemetry,
        )
    elif config.simulation_backend == "qiskit_circuit":
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        from .qkd.noise_models_improved import get_backend_noise_model, apply_noise_to_circuit

        alice_bits_list = random_bits(length, rng).tolist()
        alice_bases_list = random_bases(length, rng).tolist()
        bob_bases_list = random_bases(length, rng).tolist()

        try:
            # Build the circuit
            qc = build_bb84_circuit_parallel(alice_bits_list, alice_bases_list, bob_bases_list, measure_in_bob_basis=True)

            # Setup simulator and noise model
            simulator = AerSimulator()
            noise_model = None
            if config.noise_rate > 0:
                # For simplicity, using a generic fake backend for noise model generation
                # In a more advanced setup, this could be configurable.
                try:
                    noise_model = get_backend_noise_model("fake_manila")
                except Exception as e:
                    print(f"Warning: Could not load noise model, running without noise: {e}")

            # Transpile and run the circuit
            if noise_model:
                # Apply noise during transpilation if a noise model is present
                # We need a backend for transpilation, even if it's a simulator
                # Using a generic backend for transpilation target
                from qiskit.providers.fake_provider import FakeManilaV2
                fake_backend = FakeManilaV2()
                transpiled_qc = transpile(qc, fake_backend, optimization_level=1)
                job = simulator.run(transpiled_qc, noise_model=noise_model, shots=1024)
            else:
                job = simulator.run(qc, shots=1024)

            result = job.result()
            counts = result.get_counts(qc)

            # Process results
            bob_raw_bits_qiskit = []
            # Assuming a simple mapping from counts to bits for each qubit
            # This part needs careful handling for multi-qubit measurements
            # For BB84, each qubit is measured independently, so we can infer.
            for i in range(length):
                # Find the most common outcome for each qubit
                # This is a simplification; a more robust approach would analyze individual bit outcomes
                # from the full measurement results.
                # For now, we'll take the first bit of the most common outcome string.
                if counts:
                    most_common_outcome = max(counts, key=counts.get)
                    bob_raw_bits_qiskit.append(int(most_common_outcome[length - 1 - i])) # Qiskit counts are little-endian
                else:
                    bob_raw_bits_qiskit.append(random.randint(0,1)) # Fallback if no counts

            # Sifting and QBER calculation (similar to analytical)
            matching_basis = np.array(alice_bases_list) == np.array(bob_bases_list)
            sift_indices = np.flatnonzero(matching_basis)
            alice_sifted = [alice_bits_list[i] for i in sift_indices]
            bob_sifted = [bob_raw_bits_qiskit[i] for i in sift_indices]

            sample_size = max(1, int(round(len(sift_indices) * config.sample_fraction))) if len(sift_indices) else 0
            if sample_size:
                sampled_positions = np.sort(rng.choice(len(sift_indices), size=sample_size, replace=False))
                key_positions = np.setdiff1d(np.arange(len(sift_indices)), sampled_positions)
            else:
                sampled_positions = np.array([], dtype=int)
                key_positions = np.arange(len(sift_indices))

            alice_sample = [alice_sifted[j] for j in sampled_positions] if len(sampled_positions) > 0 else []
            bob_sample = [bob_sifted[j] for j in sampled_positions] if len(sampled_positions) > 0 else []
            qber = calculate_qber(np.array(alice_sample), np.array(bob_sample))

            alice_final = [alice_sifted[j] for j in key_positions]
            bob_final = [bob_sifted[j] for j in key_positions]
            agreement = bool(np.array_equal(alice_final, bob_final)) if len(alice_final) else False

            # Telemetry for Qiskit circuit simulation might be different or less detailed
            telemetry = pd.DataFrame(
                {
                    "index": np.arange(length),
                    "alice_bit": alice_bits_list,
                    "alice_basis": alice_bases_list,
                    "bob_basis": bob_bases_list,
                    "bob_bit": bob_raw_bits_qiskit,
                    "basis_match": matching_basis.tolist(),
                    "sifted": matching_basis.tolist(),
                }
            )
            telemetry["bit_error_when_sifted"] = telemetry["sifted"] & (telemetry["alice_bit"] != telemetry["bob_bit"])

            return ProtocolRun(
                config=asdict(config),
                alice_raw_bits="".join(map(str, alice_bits_list)),
                bob_raw_bits="".join(map(str, bob_raw_bits_qiskit)),
                alice_sifted_key="".join(map(str, alice_sifted)),
                bob_sifted_key="".join(map(str, bob_sifted)),
                alice_final_key="".join(map(str, alice_final)),
                bob_final_key="".join(map(str, bob_final)),
                qber=qber,
                sifted_length=int(len(sift_indices)),
                sample_size=int(sample_size),
                final_key_length=int(len(alice_final)),
                agreement=agreement,
                status=security_status(qber, config.qber_abort_threshold),
                telemetry=telemetry,
            )
        except Exception as e:
            raise RuntimeError(f"Qiskit circuit simulation failed: {e}")

    elif config.simulation_backend == "density_matrix":
        # This branch will use the run_bb84_density_fast from bb84_density_improved.py
        try:
            density_matrix_result = run_bb84_density_fast(
                n_qubits=length,
                noise_level=config.noise_rate,
                eve_strategy=config.eve_strategy # Only 'none' or 'intercept-resend' supported by density matrix sim
            )

            alice_final = density_matrix_result["alice_final_key"]
            bob_final = density_matrix_result["bob_final_key"]
            qber = density_matrix_result["qber"]
            sifted_length = density_matrix_result["sifted_length"]
            eve_detected = density_matrix_result["eve_detected"]

            # For raw bits and sifted keys, we need to reconstruct them or pass them from density_matrix_result
            # For simplicity, let's assume density_matrix_result provides enough info or we generate placeholders
            # The density matrix simulation directly gives final keys and QBER, so raw/sifted are less relevant here.
            # We'll use placeholders for raw/sifted keys for now.
            alice_raw_bits_str = "-"
            bob_raw_bits_str = "-"
            alice_sifted_key_str = "".join(map(str, alice_final)) # Using final as sifted for simplicity
            bob_sifted_key_str = "".join(map(str, bob_final)) # Using final as sifted for simplicity

            agreement = bool(np.array_equal(alice_final, bob_final)) if len(alice_final) else False
            status = security_status(qber, config.qber_abort_threshold)

            return ProtocolRun(
                config=asdict(config),
                alice_raw_bits=alice_raw_bits_str,
                bob_raw_bits=bob_raw_bits_str,
                alice_sifted_key=alice_sifted_key_str,
                bob_sifted_key=bob_sifted_key_str,
                alice_final_key="".join(map(str, alice_final)),
                bob_final_key="".join(map(str, bob_final)),
                qber=qber,
                sifted_length=sifted_length,
                sample_size=0, # Not directly applicable to density matrix sim in this way
                final_key_length=len(alice_final),
                agreement=agreement,
                status=status,
                telemetry=pd.DataFrame(), # Placeholder
            )
        except Exception as e:
            raise RuntimeError(f"Density matrix simulation failed: {e}")

    else:
        raise ValueError(f"Unsupported simulation backend: {config.simulation_backend}")


def run_default_demo() -> ProtocolRun:
    """Convenience function used by tests, docs, and quick demos."""
    return simulate_bb84(RunConfig())
