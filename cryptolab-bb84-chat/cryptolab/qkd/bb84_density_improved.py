"""Ultra-fast BB84 simulation using density matrices and NumPy (no Qiskit circuits)."""
import numpy as np
import random
from typing import Tuple, List, Dict, Union

# Basis states as density matrices (2x2)
Z0 = np.array([[1, 0], [0, 0]], dtype=complex)   # |0><0|
Z1 = np.array([[0, 0], [0, 1]], dtype=complex)   # |1><1|
Xp = 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)   # |+><+|
Xm = 0.5 * np.array([[1, -1], [-1, 1]], dtype=complex)  # |-><-|

BASIS_MAP: Dict[Tuple[str, int], np.ndarray] = {
    ("Z", 0): Z0,
    ("Z", 1): Z1,
    ("X", 0): Xp,
    ("X", 1): Xm,
}

def prepare_density(bit: int, basis: str) -> np.ndarray:
    """Return the density matrix for a given bit and basis."""
    if basis not in ["Z", "X"]:
        raise ValueError(f"Invalid basis: {basis}. Must be 'Z' or 'X'.")
    if bit not in [0, 1]:
        raise ValueError(f"Invalid bit: {bit}. Must be 0 or 1.")
    return BASIS_MAP[(basis, bit)]

def measure_density(rho: np.ndarray, basis: str) -> Tuple[int, np.ndarray]:
    """
    Perform a projective measurement on a density matrix in Z or X basis.
    Returns (outcome, post-measurement density matrix).
    """
    if basis not in ["Z", "X"]:
        raise ValueError(f"Invalid basis: {basis}. Must be 'Z' or 'X'.")
    if rho.shape != (2, 2):
        raise ValueError("Input density matrix must be 2x2.")
    if not np.isclose(np.trace(rho), 1.0): # Check if trace is approximately 1
        raise ValueError("Input density matrix must have trace 1.")
    if not np.allclose(rho, rho.conj().T): # Check if Hermitian
        raise ValueError("Input density matrix must be Hermitian.")

    proj0 = BASIS_MAP[(basis, 0)]
    proj1 = BASIS_MAP[(basis, 1)]

    p0 = np.trace(proj0 @ rho).real
    p1 = np.trace(proj1 @ rho).real

    # Handle potential floating point inaccuracies leading to p0/p1 slightly outside [0,1]
    p0 = np.clip(p0, 0.0, 1.0)
    p1 = np.clip(p1, 0.0, 1.0)

    if not np.isclose(p0 + p1, 1.0):
        # Renormalize if sum is not 1 due to numerical errors
        total_prob = p0 + p1
        if total_prob > 0:
            p0 /= total_prob
            p1 /= total_prob
        else:
            # If both are zero, it's an invalid state or measurement. Default to random.
            p0 = 0.5
            p1 = 0.5

    outcome = 0 if random.random() < p0 else 1

    if outcome == 0:
        # Avoid division by zero if p0 is extremely small or zero
        rho_new = (proj0 @ rho @ proj0) / p0 if p0 > 1e-9 else proj0 # Use a small epsilon
    else:
        # Avoid division by zero if p1 is extremely small or zero
        rho_new = (proj1 @ rho @ proj1) / p1 if p1 > 1e-9 else proj1 # Use a small epsilon

    # Ensure post-measurement state is normalized and Hermitian
    rho_new = rho_new / np.trace(rho_new) if np.trace(rho_new) > 1e-9 else np.eye(2)/2
    rho_new = (rho_new + rho_new.conj().T) / 2 # Ensure hermiticity after numerical operations

    return outcome, rho_new

def run_bb84_density_fast(
    n_qubits: int,
    noise_level: float = 0.0,
    eve_strategy: str = "none"
) -> Dict:
    """
    Fast BB84 using density matrices. Supports intercept-resend Eve and depolarising noise.
    """
    if not isinstance(n_qubits, int) or n_qubits <= 0:
        raise ValueError("n_qubits must be a positive integer.")
    if not isinstance(noise_level, (int, float)) or not (0.0 <= noise_level <= 1.0):
        raise ValueError("noise_level must be a float between 0.0 and 1.0.")
    if eve_strategy not in ["none", "intercept-resend"]:
        raise ValueError(f"Unsupported Eve strategy: {eve_strategy}. Must be 'none' or 'intercept-resend'.")

    alice_bits = np.random.randint(0, 2, n_qubits).tolist()
    alice_bases = [random.choice(["Z", "X"]) for _ in range(n_qubits)]
    bob_bases = [random.choice(["Z", "X"]) for _ in range(n_qubits)]

    bob_raw = []
    for i in range(n_qubits):
        # Prepare Alice's state
        rho = prepare_density(alice_bits[i], alice_bases[i])

        # Eve intercept-resend
        if eve_strategy == "intercept-resend":
            eve_basis = random.choice(["Z", "X"])
            try:
                outcome, rho = measure_density(rho, eve_basis)
                # Re-prepare based on outcome (resend)
                rho = prepare_density(outcome, eve_basis)
            except ValueError as e:
                print(f"Warning: Eve's measurement failed for qubit {i}: {e}. Skipping Eve's action for this qubit.")
                # Fallback: Eve does nothing, original rho passes through
                pass

        # Depolarising noise (with probability noise_level, replace by I/2)
        if random.random() < noise_level:
            rho = np.eye(2, dtype=complex) / 2

        # Bob measures
        try:
            outcome, _ = measure_density(rho, bob_bases[i])
            bob_raw.append(outcome)
        except ValueError as e:
            print(f"Warning: Bob's measurement failed for qubit {i}: {e}. Assigning random bit.")
            bob_raw.append(random.randint(0,1)) # Assign random bit on measurement failure

    # Sifting
    sifted_indices = [i for i in range(n_qubits) if alice_bases[i] == bob_bases[i]]
    alice_sifted = [alice_bits[i] for i in sifted_indices]
    bob_sifted = [bob_raw[i] for i in sifted_indices]

    if not alice_sifted:
        return {"alice_final_key": [], "bob_final_key": [], "qber": 0.0, "eve_detected": False, "sifted_length": 0}

    # Sample 20% for QBER
    sample_size = max(1, int(0.2 * len(alice_sifted)))
    if len(alice_sifted) < sample_size:
        sample_size = len(alice_sifted) # Adjust sample size if sifted key is too short

    sample_idx = random.sample(range(len(alice_sifted)), sample_size)
    mismatches = sum(1 for j in sample_idx if alice_sifted[j] != bob_sifted[j])
    qber = mismatches / sample_size if sample_size > 0 else 0.0
    eve_detected = qber > 0.15

    # Final key (remaining bits)
    keep_idx = [j for j in range(len(alice_sifted)) if j not in sample_idx]
    alice_final = [alice_sifted[j] for j in keep_idx]
    bob_final = [bob_sifted[j] for j in keep_idx]

    return {
        "alice_final_key": alice_final,
        "bob_final_key": bob_final,
        "qber": qber,
        "eve_detected": eve_detected,
        "sifted_length": len(alice_sifted)
    }
