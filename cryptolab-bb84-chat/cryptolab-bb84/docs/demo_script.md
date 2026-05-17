# Demo Script

## Opening

Classical encryption faces long-term pressure from quantum computing. CryptoLab: BB84 makes quantum-safe key exchange understandable for developers by turning the BB84 protocol into an interactive simulator.

## Clean-channel run

Open the Playground tab with Eve disabled and low channel noise. Point out Alice’s random bits, Bob’s random bases, basis sifting, low QBER, and agreement on the final key.

## Eve attack run

Enable **Intercept-Resend** in the sidebar and rerun the simulation. Show that Eve’s wrong basis choices disturb the quantum states, which creates sifted errors and raises QBER. Explain that BB84 does not need to identify Eve directly; it detects the physical disturbance caused by measurement.

## Analytics

Open Security Analytics and show the QBER heatmap. Explain that the safe zone corresponds to low noise and low interception, while the abort zone appears when Eve’s intercept probability or channel noise grows.

## IBM Bob story

Open the Bob Copilot tab and the repository. Explain that IBM Bob should be used as a development partner for repository-wide understanding, test generation, documentation, and future Qiskit backend implementation. Before final submission, export the IBM Bob session report into `bob-sessions/`.

## Closing

CryptoLab demonstrates how developers can learn a difficult security protocol faster, test it interactively, and use AI-assisted development to turn a complex idea into a working foundation quickly.
