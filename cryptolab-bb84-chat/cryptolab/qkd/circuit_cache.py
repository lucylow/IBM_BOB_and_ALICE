"""Cache transpiled circuits for repeated use to save time."""
from functools import lru_cache
from qiskit import QuantumCircuit, transpile
from qiskit.providers.backend import Backend
from qiskit.exceptions import QiskitError
import hashlib
from typing import Optional

# A simple in-memory cache for transpiled circuits
_circuit_cache = {}

def get_transpiled_circuit(
    circuit: QuantumCircuit,
    backend: Backend,
    optimization_level: int = 3
) -> QuantumCircuit:
    """
    Cache transpiled circuits by the circuit's QASM string, backend name, and optimization level.
    This avoids repeated transpilation for identical circuits.
    """
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError("Input 'circuit' must be a QuantumCircuit object.")
    if not isinstance(backend, Backend):
        raise TypeError("Input 'backend' must be a Qiskit Backend object.")
    if not isinstance(optimization_level, int) or not (0 <= optimization_level <= 3):
        raise ValueError("optimization_level must be an integer between 0 and 3.")

    qasm_str = circuit.qasm()
    cache_key = hashlib.md5(f"{qasm_str}-{backend.name}-{optimization_level}".encode()).hexdigest()

    if cache_key in _circuit_cache:
        return _circuit_cache[cache_key]
    else:
        try:
            transpiled_circuit = transpile(circuit, backend, optimization_level=optimization_level)
            _circuit_cache[cache_key] = transpiled_circuit
            return transpiled_circuit
        except QiskitError as e:
            raise RuntimeError(f"Qiskit error during transpilation: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during transpilation: {e}")

def compile_circuit(circuit: QuantumCircuit, backend: Backend, optimization_level: int = 3) -> QuantumCircuit:
    """
    Transpile with caching based on backend and circuit. This is an alias for get_transpiled_circuit.
    """
    return get_transpiled_circuit(circuit, backend, optimization_level)
