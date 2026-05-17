# Architecture

CryptoLab: BB84 is organized around a simple principle: keep quantum protocol logic independent from the interface so IBM Bob or future contributors can extend each layer safely. The analytical simulator is the stable core, Streamlit is the presentation layer, and the watsonx.ai client is an optional assistant layer.

| Layer | Files | Responsibility |
|---|---|---|
| Protocol core | `cryptolab/bb84.py`, `cryptolab/models.py` | Generate Alice/Bob states, model Eve, sift keys, calculate QBER, and return typed results. |
| Analytics | `cryptolab/analytics.py` | Run parameter sweeps and produce heatmap-ready QBER data. |
| Education | `cryptolab/education.py` | Keep glossary, walkthrough steps, demo prompts, and teaching copy out of UI code. |
| AI scaffold | `cryptolab/watsonx_client.py` | Provide optional watsonx.ai text generation with a local fallback. |
| Interface | `app/streamlit_app.py` | Render controls, charts, telemetry tables, the guided walkthrough, and Bob Copilot panel. |
| Quality | `tests/test_bb84.py` | Validate the most important simulation behaviors. |

## Simulation flow

The simulator starts with random Alice bits and bases. It optionally applies Eve’s attack, then Bob measures in random bases. Alice and Bob publicly compare only their bases and keep matching positions. A sample of sifted bits is revealed to estimate QBER. If QBER is above the configured threshold, the run is marked as unsafe; otherwise, unrevealed sifted bits form the final educational key.

## Extension path

The best next extension is a second backend named `qiskit_backend.py` that implements the same `RunConfig -> ProtocolRun` contract. The Streamlit interface would then expose a backend selector: **Analytical Turbo Mode** for fast live demos and **Qiskit Validation Mode** for circuit-level correctness.

Other future extensions include persistent saved runs, a FastAPI service for programmatic access, downloadable run reports, classroom quizzes, and richer Bloch sphere animation. IBM Bob is particularly useful for refactoring the UI, generating tests for edge cases, and adding documentation whenever the project grows.
