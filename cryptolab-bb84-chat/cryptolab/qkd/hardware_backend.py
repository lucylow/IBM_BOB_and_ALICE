"""Run BB84 on real IBM quantum hardware with error mitigation."""
import os
import random
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Options
from qiskit_ibm_runtime.accounts import AccountError
from typing import Optional, Dict, List

def get_least_busy_backend(min_qubits: int = 5, service: Optional[QiskitRuntimeService] = None):
    """Retrieve the least busy IBMQ backend with at least min_qubits."""
    if service is None:
        try:
            service = QiskitRuntimeService(channel="ibm_quantum", token=os.getenv("IBMQ_TOKEN"))
        except AccountError:
            raise ConnectionError("IBMQ token not found or invalid. Please set IBMQ_TOKEN environment variable.")

    try:
        backends = service.backends(operational=True, min_num_qubits=min_qubits)
        if not backends:
            raise RuntimeError(f"No operational backends found with at least {min_qubits} qubits.")
        least_busy = min(backends, key=lambda b: b.status().pending_jobs)
        return least_busy
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve least busy backend: {e}")

def run_bb84_on_hardware(
    n_qubits: int,
    shots: int = 1024,
    backend_name: Optional[str] = None,
    error_mitigation: bool = True
) -> Dict:
    """
    Run a simplified BB84 circuit on real hardware.
    Because hardware has limited qubits, we run sequentially on up to 5 qubits.
    """
    if not isinstance(n_qubits, int) or n_qubits <= 0:
        raise ValueError("n_qubits must be a positive integer.")
    if not isinstance(shots, int) or shots <= 0:
        raise ValueError("shots must be a positive integer.")

    original_n_qubits = n_qubits
    if n_qubits > 5: # IBMQ free tier often limits to 5 qubits
        n_qubits = 5
        print(f"Warning: Hardware limited to 5 qubits for demonstration. Using {n_qubits}.")

    # Generate random bits and bases
    alice_bits: List[int] = [random.randint(0,1) for _ in range(n_qubits)]
    alice_bases: List[str] = [random.choice(["Z","X"]) for _ in range(n_qubits)]
    bob_bases: List[str] = [random.choice(["Z","X"]) for _ in range(n_qubits)]

    # Build a circuit where each qubit is prepared and then measured in Bob's basis
    qc = QuantumCircuit(n_qubits, n_qubits)
    for i in range(n_qubits):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == "X":
            qc.h(i)
        # Bob's basis rotation before measurement
        if bob_bases[i] == "X":
            qc.h(i)
        qc.measure(i, i)

    # Get backend
    service = None
    try:
        service = QiskitRuntimeService(channel="ibm_quantum", token=os.getenv("IBMQ_TOKEN"))
    except AccountError as e:
        return {"error": f"IBMQ service initialization failed: {e}. Check IBMQ_TOKEN.", "status": "FAILED"}

    backend = None
    try:
        if backend_name:
            backend = service.backend(backend_name)
        else:
            backend = get_least_busy_backend(min_qubits=n_qubits, service=service)
    except Exception as e:
        return {"error": f"Backend selection failed: {e}", "status": "FAILED"}

    if backend is None:
        return {"error": "No suitable backend found.", "status": "FAILED"}

    # Transpile with optimization
    try:
        transpiled = transpile(qc, backend, optimization_level=3)
    except Exception as e:
        return {"error": f"Transpilation failed: {e}", "status": "FAILED"}

    options = Options()
    if error_mitigation:
        options.resilience_level = 1 # Level 1 is a good balance for educational purposes
        options.optimization_level = 3

    sampler = Sampler(backend=backend, options=options)
    job = None
    try:
        job = sampler.run([transpiled], shots=shots)
        result = job.result()
        counts = result.quasi_dists[0].binary_probabilities()
    except Exception as e:
        return {"error": f"Job execution failed on IBMQ: {e}", "status": "FAILED"}

    # Find most probable outcome
    if not counts:
        return {"error": "No counts returned from sampler.", "status": "FAILED"}

    most_probable_bitstring = max(counts, key=counts.get)
    # Convert bitstring to list of integers
    bob_results = [int(bit) for bit in most_probable_bitstring]

    # Sifting
    sifted_idx = [i for i in range(n_qubits) if alice_bases[i] == bob_bases[i]]
    alice_sifted = [alice_bits[i] for i in sifted_idx]
    bob_sifted = [bob_results[i] for i in sifted_idx]

    qber = 0.0
    if alice_sifted:
        mismatches = sum(1 for a,b in zip(alice_sifted, bob_sifted) if a!=b)
        qber = mismatches / len(alice_sifted)
    else:
        # If no sifted bits, QBER is undefined or can be considered 0 if no comparison possible
        # Or 1.0 if it implies total failure. For now, 0.0 if no bits to compare.
        qber = 0.0

    eve_detected = qber > 0.15 # Threshold for detection

    return {
        "alice_key": alice_sifted,
        "bob_key": bob_sifted,
        "qber": qber,
        "eve_detected": eve_detected,
        "job_id": job.job_id() if job else "N/A",
        "backend": backend.name,
        "counts": counts,
        "status": "SUCCESS"
    }
