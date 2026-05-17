"""Backend implementations for BB84 simulation.

This module separates the different simulation backends (analytical, Qiskit, density matrix)
into distinct classes following the Strategy pattern for better maintainability.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .models import ProtocolRun, RunConfig


class SimulationBackend(ABC):
    """Abstract base class for BB84 simulation backends."""
    
    @abstractmethod
    def simulate(self, config: "RunConfig", rng: np.random.Generator) -> "ProtocolRun":
        """Execute the BB84 simulation and return results."""
        pass


class AnalyticalBackend(SimulationBackend):
    """Fast analytical BB84 simulation without quantum circuit overhead."""
    
    def simulate(self, config: "RunConfig", rng: np.random.Generator) -> "ProtocolRun":
        """Run analytical BB84 simulation."""
        from .bb84 import (
            random_bits, random_bases, _apply_eve, _measure_prepared_qubit,
            _apply_channel_noise, calculate_qber, security_status
        )
        from .models import ProtocolRun
        
        length = int(config.key_length)
        
        # Step 1: Alice prepares bits and bases
        alice_bits = random_bits(length, rng)
        alice_bases = random_bases(length, rng)
        bob_bases = random_bases(length, rng)
        
        # Step 2: Apply Eve's attack
        channel_bits, channel_bases, eve_intercepted, eve_bases = _apply_eve(
            alice_bits,
            alice_bases,
            config.eve_strategy,
            config.eve_intercept_probability,
            config.eve_basis_bias_z,
            rng,
        )
        
        # Step 3: Bob measures
        bob_bits = _measure_prepared_qubit(channel_bits, channel_bases, bob_bases, rng)
        bob_bits = _apply_channel_noise(bob_bits, config.noise_rate, rng)
        
        # Step 4: Basis sifting
        matching_basis = alice_bases == bob_bases
        sift_indices = np.flatnonzero(matching_basis)
        alice_sifted = alice_bits[sift_indices]
        bob_sifted = bob_bits[sift_indices]
        
        # Step 5: QBER estimation
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
        
        # Step 6: Final key
        alice_final = alice_sifted[key_positions]
        bob_final = bob_sifted[key_positions]
        agreement = bool(np.array_equal(alice_final, bob_final)) if len(alice_final) else False
        
        # Build telemetry
        telemetry = self._build_telemetry(
            length, alice_bits, alice_bases, eve_intercepted, eve_bases,
            bob_bases, bob_bits, matching_basis
        )
        
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
    
    @staticmethod
    def _build_telemetry(
        length: int,
        alice_bits: np.ndarray,
        alice_bases: np.ndarray,
        eve_intercepted: np.ndarray,
        eve_bases: np.ndarray,
        bob_bases: np.ndarray,
        bob_bits: np.ndarray,
        matching_basis: np.ndarray,
    ) -> pd.DataFrame:
        """Build per-qubit telemetry DataFrame."""
        telemetry = pd.DataFrame({
            "index": np.arange(length),
            "alice_bit": alice_bits.astype(int),
            "alice_basis": alice_bases,
            "eve_intercepted": eve_intercepted.astype(bool),
            "eve_basis": eve_bases,
            "bob_basis": bob_bases,
            "bob_bit": bob_bits.astype(int),
            "basis_match": matching_basis.astype(bool),
            "sifted": matching_basis.astype(bool),
        })
        telemetry["bit_error_when_sifted"] = telemetry["sifted"] & (
            telemetry["alice_bit"] != telemetry["bob_bit"]
        )
        return telemetry


class QiskitCircuitBackend(SimulationBackend):
    """Qiskit-based circuit simulation backend."""
    
    def simulate(self, config: "RunConfig", rng: np.random.Generator) -> "ProtocolRun":
        """Run Qiskit circuit-based BB84 simulation."""
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        from .qkd.optimised_circuits import build_bb84_circuit_parallel
        from .qkd.noise_models_improved import get_backend_noise_model
        from .bb84 import random_bits, random_bases, calculate_qber, security_status
        from .models import ProtocolRun
        
        length = int(config.key_length)
        
        alice_bits_list = random_bits(length, rng).tolist()
        alice_bases_list = random_bases(length, rng).tolist()
        bob_bases_list = random_bases(length, rng).tolist()
        
        # Build and run circuit
        qc = build_bb84_circuit_parallel(
            alice_bits_list, alice_bases_list, bob_bases_list, measure_in_bob_basis=True
        )
        
        simulator = AerSimulator()
        noise_model = None
        
        if config.noise_rate > 0:
            try:
                noise_model = get_backend_noise_model("fake_manila")
            except Exception as e:
                print(f"Warning: Could not load noise model, running without noise: {e}")
        
        # Transpile and execute
        if noise_model:
            from qiskit.providers.fake_provider import FakeManilaV2
            fake_backend = FakeManilaV2()
            transpiled_qc = transpile(qc, fake_backend, optimization_level=1)
            job = simulator.run(transpiled_qc, noise_model=noise_model, shots=1024)
        else:
            job = simulator.run(qc, shots=1024)
        
        result = job.result()
        counts = result.get_counts(qc)
        
        # Extract Bob's measurement results
        bob_raw_bits_qiskit = self._extract_measurement_results(counts, length)
        
        # Perform sifting and QBER calculation
        return self._process_results(
            config, alice_bits_list, alice_bases_list, bob_bases_list,
            bob_raw_bits_qiskit, length, rng
        )
    
    @staticmethod
    def _extract_measurement_results(counts: dict, length: int) -> list[int]:
        """Extract Bob's measurement results from Qiskit counts."""
        import random
        bob_raw_bits = []
        for i in range(length):
            if counts:
                most_common_outcome = max(counts, key=counts.get)
                bob_raw_bits.append(int(most_common_outcome[length - 1 - i]))
            else:
                bob_raw_bits.append(random.randint(0, 1))
        return bob_raw_bits
    
    @staticmethod
    def _process_results(
        config: "RunConfig",
        alice_bits_list: list,
        alice_bases_list: list,
        bob_bases_list: list,
        bob_raw_bits_qiskit: list,
        length: int,
        rng: np.random.Generator,
    ) -> "ProtocolRun":
        """Process Qiskit results into ProtocolRun."""
        from .bb84 import calculate_qber, security_status
        from .models import ProtocolRun
        
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
        
        telemetry = pd.DataFrame({
            "index": np.arange(length),
            "alice_bit": alice_bits_list,
            "alice_basis": alice_bases_list,
            "bob_basis": bob_bases_list,
            "bob_bit": bob_raw_bits_qiskit,
            "basis_match": matching_basis.tolist(),
            "sifted": matching_basis.tolist(),
        })
        telemetry["bit_error_when_sifted"] = telemetry["sifted"] & (
            telemetry["alice_bit"] != telemetry["bob_bit"]
        )
        
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


class DensityMatrixBackend(SimulationBackend):
    """Density matrix simulation backend."""
    
    def simulate(self, config: "RunConfig", rng: np.random.Generator) -> "ProtocolRun":
        """Run density matrix BB84 simulation."""
        from .qkd.bb84_density_improved import run_bb84_density_fast
        from .bb84 import security_status
        from .models import ProtocolRun
        
        length = int(config.key_length)
        
        density_matrix_result = run_bb84_density_fast(
            n_qubits=length,
            noise_level=config.noise_rate,
            eve_strategy=config.eve_strategy
        )
        
        alice_final = density_matrix_result["alice_final_key"]
        bob_final = density_matrix_result["bob_final_key"]
        qber = density_matrix_result["qber"]
        sifted_length = density_matrix_result["sifted_length"]
        
        agreement = bool(np.array_equal(alice_final, bob_final)) if len(alice_final) else False
        status = security_status(qber, config.qber_abort_threshold)
        
        return ProtocolRun(
            config=asdict(config),
            alice_raw_bits="-",
            bob_raw_bits="-",
            alice_sifted_key="".join(map(str, alice_final)),
            bob_sifted_key="".join(map(str, bob_final)),
            alice_final_key="".join(map(str, alice_final)),
            bob_final_key="".join(map(str, bob_final)),
            qber=qber,
            sifted_length=sifted_length,
            sample_size=0,
            final_key_length=len(alice_final),
            agreement=agreement,
            status=status,
            telemetry=pd.DataFrame(),
        )


def get_backend(backend_name: str) -> SimulationBackend:
    """Factory function to get the appropriate simulation backend."""
    backends = {
        "analytical": AnalyticalBackend,
        "qiskit_circuit": QiskitCircuitBackend,
        "density_matrix": DensityMatrixBackend,
    }
    
    backend_class = backends.get(backend_name)
    if backend_class is None:
        raise ValueError(
            f"Unsupported simulation backend: {backend_name}. "
            f"Available backends: {', '.join(backends.keys())}"
        )
    
    return backend_class()

# Made with Bob
