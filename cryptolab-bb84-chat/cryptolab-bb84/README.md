# CryptoLab: BB84

**CryptoLab: BB84** is an interactive educational interface for learning and testing the BB84 Quantum Key Distribution protocol. It is designed as a strong foundation for the IBM Bob Hackathon: the project gives developers a working simulator, a visual Streamlit interface, a watsonx.ai scaffold, automated tests, and a clear repository structure that IBM Bob can extend with full project context.

> The project reframes quantum cryptography as a practical developer-learning tool: a user can run a clean BB84 exchange, introduce Eve, observe QBER rise, and understand why BB84 detects eavesdropping.

## Why this fits the IBM Bob Hackathon

The hackathon expects a proof of concept that demonstrates how **IBM Bob** helps teams move from idea to impact faster. This repository is structured to make Bob useful immediately: the simulation engine is isolated, the UI is readable, tests are present, educational content is modular, and the `bob-sessions/` folder is ready for exported Bob IDE task/session reports.

| Hackathon need | Project response |
|---|---|
| Demonstrate meaningful IBM Bob usage | Includes Bob prompt pack, Bob session folder, development workflow notes, and code that can be reviewed or extended with Bob IDE. |
| Build something developers would use | Helps developers and students learn QKD concepts quickly through an interactive simulator rather than static notes. |
| Strong technical foundation | Provides analytical BB84 protocol simulation, eavesdropping models, QBER estimation, heatmaps, tests, and optional watsonx.ai integration. |
| Presentation-ready prototype | Includes Streamlit tabs for Playground, Step-by-Step learning, Eve Mode, Security Analytics, Bob Copilot, and Builder Notes. |

## Feature set

The first version includes a fast analytical BB84 simulator that handles random Alice bits and bases, Bob basis measurement, key sifting, QBER sampling, and final key comparison. It supports clean channels, intercept-resend attacks, probabilistic eavesdropping, biased-basis eavesdropping, and independent channel noise. The Streamlit application turns this into a polished educational interface with metrics, per-qubit telemetry, a BB84 state map, security heatmaps, and a guided walkthrough.

The watsonx.ai integration is intentionally optional. If IBM Cloud environment variables are available, the Bob Copilot panel can call watsonx.ai text generation. If credentials are not configured, the application uses a safe local fallback so the demo still works during judging.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Then open the local Streamlit URL shown in the terminal.

## Running tests

```bash
pip install -r requirements.txt
pytest -q
```

The tests verify that a clean channel produces low QBER, intercept-resend increases QBER, QBER calculation works, report exports are valid, the CLI can save a run, and the analytics grid is generated correctly.

## Command-line reports

The project now includes a CLI so simulations can be run in scripts, CI, or demo preparation without opening Streamlit.

```bash
python -m cryptolab.cli --key-length 512 --eve-strategy intercept_resend --output reports/eve_run.md
python -m cryptolab.cli --key-length 512 --noise-rate 0.02 --output reports/clean_run.json --include-telemetry
```

The Streamlit Playground also includes JSON and Markdown download buttons for saving judging evidence directly from the interface.

## Chat endpoint

A lightweight FastAPI endpoint is included in `chat.py` for local chat completions with performance metrics.

```bash
export CHAT_API_KEY=dev-chat-key
uvicorn chat:app --reload --port 8000
```

The Streamlit **Bob Copilot** tab can call this endpoint when **Use FastAPI chat.py endpoint** is enabled. By default, the endpoint runs in safe simulation mode; set `CHAT_SIMULATION_MODE=false` and provide `OPENAI_API_KEY` to use a real OpenAI-compatible model.

## Optional watsonx.ai configuration

Copy `.env.example` to `.env` or export variables in your shell. Never commit real credentials.

```bash
export IBM_CLOUD_API_KEY="your_key"
export WATSONX_PROJECT_ID="your_project_id"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"
export WATSONX_MODEL_ID="ibm/granite-3-8b-instruct"
```

After those variables are set, the Bob Copilot panel can attempt live watsonx.ai calls. Without them, the application remains fully usable with local explanatory responses.

## Repository structure

```text
cryptolab-bb84/
├── app/
│   └── streamlit_app.py          # Interactive educational UI
├── bob-sessions/
│   └── README.md                 # Place exported IBM Bob reports here
├── cryptolab/
│   ├── analytics.py              # QBER sweeps and educational estimates
│   ├── bb84.py                   # Core protocol simulator
│   ├── education.py              # Glossary, walkthrough, Bob prompt pack
│   ├── models.py                 # Typed run/result data structures
│   └── watsonx_client.py         # Optional watsonx.ai scaffold
├── docs/
│   ├── architecture.md           # Technical architecture and extension plan
│   └── demo_script.md            # Hackathon pitch flow
├── tests/
│   └── test_bb84.py              # Unit tests
├── .env.example                  # Credential template only
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Recommended IBM Bob workflow

Open this repository in IBM Bob IDE and use Bob as the development partner for the next iteration. Recommended prompts are also visible inside the app.

```text
Review cryptolab/bb84.py and explain the full BB84 flow in plain English.
Generate additional pytest coverage for noisy-channel and biased-basis Eve scenarios.
Refactor the Streamlit app into smaller components without changing behavior.
Add a Qiskit-backed simulator mode behind the same RunConfig interface.
Write submission-ready documentation explaining how Bob helped build this repository.
```

Export your Bob IDE task/session report and place it in `bob-sessions/` before submitting the GitHub repository.

## Demo flow

Start with Eve disabled and channel noise set near zero. Run the Playground tab to show Alice and Bob deriving matching final keys with QBER below the abort threshold. Next, enable the **Intercept-Resend** Eve strategy and rerun the simulation. The QBER should increase sharply, showing how BB84 converts eavesdropping into measurable disturbance. Finish by opening **Security Analytics** to show the heatmap and **Bob Copilot** to explain how Bob can accelerate learning, testing, documentation, and extension.

## Extension ideas for Bob-assisted development

A strong next step is adding a true Qiskit backend behind the same `RunConfig` interface while keeping analytical mode for fast demos. Other useful extensions include exportable PDF reports, classroom quiz mode, a deployable API endpoint, persistent saved simulations, and richer visualizations of quantum states.

## License

Use this project as a hackathon foundation. Add your preferred open-source license before public submission.
