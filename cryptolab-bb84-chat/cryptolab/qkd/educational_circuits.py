"""Generate step-by-step circuits for educational BB84 walkthrough."""
from qiskit import QuantumCircuit, ClassicalRegister
import streamlit as st
from qiskit.visualization import circuit_drawer
import matplotlib.pyplot as plt

def build_step_circuit(step: int, bit: int, basis: str, bob_basis: str = None) -> QuantumCircuit:
    """
    Return a circuit that visualises a single step of BB84.
    Steps:
    1: Alice prepares qubit
    2: (Optional Eve)
    3: Bob measures
    """
    if not isinstance(step, int) or step not in [1, 2, 3]:
        raise ValueError("Step must be 1, 2, or 3.")
    if not isinstance(bit, int) or bit not in [0, 1]:
        raise ValueError("Bit must be 0 or 1.")
    if basis not in ["Z", "X"]:
        raise ValueError("Alice's basis must be 'Z' or 'X'.")
    if bob_basis is not None and bob_basis not in ["Z", "X"]:
        raise ValueError("Bob's basis must be 'Z' or 'X' if provided.")

    qc = QuantumCircuit(1, 1)
    if step == 1:
        if bit == 1:
            qc.x(0)
        if basis == 'X':
            qc.h(0)
        qc.barrier(label="Alice Preparation")
    elif step == 2:
        # Eve step – we just add a barrier for illustration
        # In a real scenario, Eve's interaction would be modeled here.
        qc.barrier(label="Eve Intercepts (Simplified)")
    elif step == 3:
        # Assuming Alice's preparation has already happened in previous steps or is implicit
        # To make this step self-contained for visualization, we might need to re-apply Alice's ops
        # For a truly step-by-step build, this function would take a circuit from the previous step.
        # For now, let's assume we are building a circuit for *just* this step's operations.
        
        # If we want to show the full circuit up to this step, we need to pass the previous circuit.
        # For simplicity in this function, we'll just show Bob's measurement part.
        if bob_basis == 'X':
            qc.h(0)
        qc.measure(0, 0)
        qc.barrier(label="Bob Measurement")
    return qc

def render_step_diagram(step: int, bit: int, alice_basis: str, bob_basis: str = None):
    """
    Render the circuit diagram in Streamlit.
    This function is designed to be called within a Streamlit application.
    """
    try:
        qc = build_step_circuit(step, bit, alice_basis, bob_basis)
        st.write(f"**Step {step} Circuit**")
        
        # Use Qiskit's matplotlib drawer for better visuals
        fig = qc.draw(output='mpl', style={'backgroundcolor': '#ffffff'})
        st.pyplot(fig)
        plt.close(fig) # Close the figure to prevent it from displaying multiple times

        # Also provide text drawing for accessibility/debugging
        st.code(qc.draw(output='text', idle_wires=False))

    except ValueError as e:
        st.error(f"Error rendering circuit: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred during circuit rendering: {e}")
