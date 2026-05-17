"""Educational text used by the Streamlit interface.

This module keeps learning copy separate from UI logic so IBM Bob can later help
expand lessons, quizzes, and glossary entries without touching simulation code.
"""

from __future__ import annotations

GLOSSARY: dict[str, str] = {
    "BB84": "The first quantum key distribution protocol, proposed by Bennett and Brassard in 1984. It lets Alice and Bob discover whether a key exchange was disturbed.",
    "Qubit": "A two-state quantum information carrier. BB84 uses four states: |0>, |1>, |+>, and |->.",
    "Basis": "A measurement frame. BB84 alternates between the Z basis and the X basis so an eavesdropper cannot copy states without risk.",
    "Sifting": "The public comparison where Alice and Bob keep only positions measured with the same basis, without revealing the actual key bits.",
    "QBER": "Quantum Bit Error Rate: the fraction of sampled sifted bits where Alice and Bob disagree. High QBER indicates noise or eavesdropping.",
    "Intercept-Resend": "An attack where Eve measures a qubit and sends a replacement. Wrong basis choices disturb the state and create detectable errors.",
}

WIZARD_STEPS: list[dict[str, str]] = [
    {
        "title": "1. Alice prepares random bits and bases",
        "body": "Alice generates a random bit string and randomly encodes each bit in either the Z basis or X basis.",
    },
    {
        "title": "2. Qubits travel through the quantum channel",
        "body": "The encoded quantum states travel to Bob. Noise or Eve can disturb them before Bob measures.",
    },
    {
        "title": "3. Bob measures in random bases",
        "body": "Bob independently chooses Z or X for each received qubit. Matching bases reproduce Alice's bit; mismatches produce random outcomes.",
    },
    {
        "title": "4. Alice and Bob sift over a public channel",
        "body": "They reveal only their bases, discard mismatches, and keep the remaining candidate key bits.",
    },
    {
        "title": "5. They estimate QBER",
        "body": "A subset of sifted bits is revealed. If disagreement is too high, the protocol aborts because the channel is unsafe.",
    },
    {
        "title": "6. The final key is accepted or rejected",
        "body": "If QBER is below threshold, unrevealed sifted bits become the shared key after privacy amplification in production systems.",
    },
]

BOB_PROMPTS: list[str] = [
    "Explain the BB84 protocol from the perspective of a first-year software engineer.",
    "Review cryptolab/bb84.py and suggest one refactor that improves readability without changing behavior.",
    "Generate pytest cases for the no-Eve and intercept-resend scenarios.",
    "Explain why intercept-resend attacks produce about 25% QBER in sifted BB84 bits.",
    "Help me turn the README into a concise hackathon pitch focused on developer productivity.",
]


def glossary_markdown() -> str:
    """Return glossary content as Markdown."""
    return "\n".join(f"**{term}.** {definition}" for term, definition in GLOSSARY.items())


def demo_script() -> str:
    """Return a compact demo narrative for the app's Builder Notes tab."""
    return (
        "Run a clean channel first to show Alice and Bob agreeing. Then enable "
        "Intercept-Resend and rerun. The QBER should rise sharply, making the "
        "attack visible. Finish by showing the Bob Copilot prompts and the "
        "bob-sessions folder to prove the project was built with IBM Bob as a "
        "development partner."
    )
