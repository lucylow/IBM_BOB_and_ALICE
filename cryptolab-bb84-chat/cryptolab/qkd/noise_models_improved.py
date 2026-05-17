"""Realistic noise models using Qiskit Aer and real IBM backend data."""
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error, thermal_relaxation_error
from qiskit.providers.fake_provider import FakeManilaV2, FakeJakartaV2, FakeLagosV2
from qiskit import QuantumCircuit, transpile
from typing import Optional

def get_backend_noise_model(backend_name: str = "fake_manila") -> NoiseModel:
    """
    Return a noise model derived from a real IBM Q backend.
    Options: 'fake_manila', 'fake_jakarta', 'fake_lagos'.
    """
    backends = {
        "fake_manila": FakeManilaV2,
        "fake_jakarta": FakeJakartaV2,
        "fake_lagos": FakeLagosV2,
    }
    if backend_name not in backends:
        raise ValueError(f"Unknown backend: {backend_name}. Choose from {list(backends.keys())}")

    backend = backends[backend_name]()
    noise_model = NoiseModel.from_backend(backend)

    # Add extra depolarizing noise to the quantum channel (optional)
    # Ensure the error applies to relevant gates and qubit numbers
    depol_error = depolarizing_error(0.01, 1)  # 1% depolarizing on 1-qubit gates
    noise_model.add_all_qubit_quantum_error(depol_error, ['u1', 'u2', 'u3', 'rx', 'ry', 'rz', 'h', 'x'])
    depol_error_cx = depolarizing_error(0.01, 2) # 1% depolarizing on 2-qubit gates
    noise_model.add_all_qubit_quantum_error(depol_error_cx, ['cx'])

    # Add thermal relaxation (T1 and T2 times)
    # These values should ideally come from the backend properties for realism
    t1 = 100e-6   # 100 µs
    t2 = 80e-6    # 80 µs
    gate_time = 0.1e-6  # 100 ns (typical gate time)
    thermal_error = thermal_relaxation_error(t1, t2, gate_time)
    noise_model.add_all_qubit_quantum_error(thermal_error, ['x', 'h', 'id'])

    # Add readout error (5% misidentification)
    # Apply to all qubits, not just qubit 0
    readout_error = ReadoutError([[0.95, 0.05], [0.04, 0.96]])
    # Assuming a maximum of 5 qubits for fake backends for simplicity, adjust as needed
    for i in range(backend.num_qubits):
        noise_model.add_readout_error(readout_error, [i])

    return noise_model

def apply_noise_to_circuit(circuit: QuantumCircuit, noise_model: NoiseModel, backend) -> QuantumCircuit:
    """Transpile and return a circuit with noise inserted (for simulation)."""
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError("Input 'circuit' must be a QuantumCircuit object.")
    if not isinstance(noise_model, NoiseModel):
        raise TypeError("Input 'noise_model' must be a NoiseModel object.")
    # Backend can be a FakeBackend or a real Backend object
    if not hasattr(backend, 'name') or not hasattr(backend, 'configuration'):
        raise TypeError("Input 'backend' must be a Qiskit backend object.")

    transpiled = transpile(circuit, backend, optimization_level=3)
    return transpiled
