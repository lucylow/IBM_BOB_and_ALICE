"""Streamlit UI for CryptoLab: BB84.

Run with: streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

from cryptolab.analytics import estimate_expected_qber, sweep_noise_and_eve
from cryptolab.bb84 import simulate_bb84
from cryptolab.education import BOB_PROMPTS, GLOSSARY, WIZARD_STEPS, demo_script, glossary_markdown
from cryptolab.models import RunConfig
from cryptolab.reporting import run_to_json, run_to_markdown
from cryptolab.watsonx_client import WatsonxConfig, ask_watsonx

st.set_page_config(
    page_title="CryptoLab: BB84",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1280px;}
    .hero {border-radius: 22px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; background: linear-gradient(135deg, #0f62fe 0%, #001d6c 100%); color: white; box-shadow: 0 14px 35px rgba(15,98,254,.22);}
    .hero h1 {margin: 0 0 .35rem 0; font-size: 2.15rem;}
    .hero p {margin: 0; opacity: .92; font-size: 1.02rem;}
    .metric-card {border: 1px solid #e6e8ef; border-radius: 14px; padding: 1rem; background: #ffffff;}
    .pill {display:inline-block; border-radius:999px; padding:.25rem .65rem; margin:.15rem; background:#edf5ff; color:#0f62fe; font-weight:700; font-size:.78rem;}
    .secure {color: #0f7b0f; font-weight: 700;}
    .abort {color: #b42318; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)


def build_config() -> RunConfig:
    """Collect simulation controls from the sidebar."""
    st.sidebar.title("CryptoLab: BB84")
    st.sidebar.caption("Interactive QKD simulator built as an IBM Bob hackathon foundation.")
    st.sidebar.divider()

    key_length = st.sidebar.slider("Raw qubits", min_value=32, max_value=4096, value=256, step=32)
    noise_rate = st.sidebar.slider("Channel noise", min_value=0.0, max_value=0.30, value=0.01, step=0.01)
    strategy_label = st.sidebar.selectbox(
        "Eve strategy",
        ["none", "intercept_resend", "probabilistic", "basis_bias"],
        format_func=lambda x: {
            "none": "No Eve",
            "intercept_resend": "Intercept-Resend",
            "probabilistic": "Probabilistic Eve",
            "basis_bias": "Biased-Basis Eve",
        }[x],
    )
    intercept_probability = st.sidebar.slider("Eve intercept probability", 0.0, 1.0, 1.0, 0.05)
    eve_basis_bias_z = st.sidebar.slider("Eve Z-basis bias", 0.0, 1.0, 0.5, 0.05)
    sample_fraction = st.sidebar.slider("QBER sample fraction", 0.05, 0.90, 0.25, 0.05)
    threshold = st.sidebar.slider("Abort threshold", 0.01, 0.30, 0.11, 0.01)
    seed = st.sidebar.number_input("Seed", min_value=0, max_value=999999, value=84, step=1)

    st.sidebar.divider()
    st.sidebar.markdown("### Cheat Sheet")
    with st.sidebar.expander("Glossary", expanded=True):
        for term, definition in GLOSSARY.items():
            st.markdown(f"**{term}.** {definition}")

    return RunConfig(
        key_length=key_length,
        noise_rate=noise_rate,
        eve_strategy=strategy_label,
        eve_intercept_probability=intercept_probability,
        eve_basis_bias_z=eve_basis_bias_z,
        sample_fraction=sample_fraction,
        qber_abort_threshold=threshold,
        seed=int(seed),
    )


def render_bloch_demo(df: pd.DataFrame) -> go.Figure:
    """Create a lightweight 3D state map approximating BB84 states."""
    sample = df.head(64).copy()
    coords = {
        (0, "Z"): (0, 0, 1, "|0>"),
        (1, "Z"): (0, 0, -1, "|1>"),
        (0, "X"): (1, 0, 0, "|+>"),
        (1, "X"): (-1, 0, 0, "|->"),
    }
    rows = []
    for _, row in sample.iterrows():
        x, y, z, label = coords[(int(row["alice_bit"]), row["alice_basis"])]
        rows.append({"x": x, "y": y, "z": z, "state": label, "index": int(row["index"])})
    points = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=points["x"],
            y=points["y"],
            z=points["z"],
            mode="markers+text",
            text=points["state"],
            marker=dict(size=6, color=points["index"], colorscale="Viridis"),
            name="Alice states",
        )
    )
    fig.update_layout(
        height=420,
        title="BB84 state map: Z basis on vertical axis, X basis on horizontal axis",
        scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z", aspectmode="cube"),
        margin=dict(l=0, r=0, b=0, t=55),
    )
    return fig


def render_metrics(result) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("QBER", f"{result.qber_percent:.2f}%")
    col2.metric("Sifted bits", result.sifted_length)
    col3.metric("Final key bits", result.final_key_length)
    col4.metric("Agreement", "Yes" if result.agreement else "No")
    status_class = "secure" if result.secure else "abort"
    st.markdown(f"<p class='{status_class}'>{result.status}</p>", unsafe_allow_html=True)


def render_protocol_table(result) -> None:
    shown = result.telemetry.head(96).copy()
    st.dataframe(
        shown,
        use_container_width=True,
        hide_index=True,
        column_config={
            "basis_match": st.column_config.CheckboxColumn("Basis match"),
            "sifted": st.column_config.CheckboxColumn("Sifted"),
            "eve_intercepted": st.column_config.CheckboxColumn("Eve intercepted"),
            "bit_error_when_sifted": st.column_config.CheckboxColumn("Sifted error"),
        },
    )


def main() -> None:
    config = build_config()
    result = simulate_bb84(config)

    st.markdown(
        """
        <section class="hero">
          <h1>CryptoLab: BB84 — Quantum Key Distribution Lab</h1>
          <p>Simulate BB84, introduce Eve, measure QBER, export evidence, and extend the project with IBM Bob.</p>
          <div style="margin-top:.8rem">
            <span class="pill">BB84 Simulator</span><span class="pill">Eve Detection</span><span class="pill">Security Analytics</span><span class="pill">Performance Gains Prompt Added</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Playground", "Step-by-Step", "Eve Mode", "Security Analytics", "Performance Gains", "Bob Copilot", "Builder Notes"])

    with tabs[0]:
        st.subheader("BB84 Playground")
        render_metrics(result)
        left, right = st.columns([1.1, 0.9])
        with left:
            st.plotly_chart(render_bloch_demo(result.telemetry), use_container_width=True)
        with right:
            st.markdown("#### Key material")
            st.code(f"Alice final: {result.alice_final_key[:160] or 'empty'}", language="text")
            st.code(f"Bob final:   {result.bob_final_key[:160] or 'empty'}", language="text")
            expected = estimate_expected_qber(config.noise_rate, config.eve_intercept_probability if config.eve_strategy != "none" else 0)
            st.info(f"Expected educational QBER estimate: {expected * 100:.1f}%")
            export_a, export_b = st.columns(2)
            export_a.download_button(
                "Download JSON report",
                data=run_to_json(result, include_telemetry=True),
                file_name="cryptolab_bb84_run.json",
                mime="application/json",
            )
            export_b.download_button(
                "Download Markdown report",
                data=run_to_markdown(result),
                file_name="cryptolab_bb84_run.md",
                mime="text/markdown",
            )
        st.markdown("#### Per-qubit telemetry")
        render_protocol_table(result)

    with tabs[1]:
        st.subheader("Guided Protocol Walkthrough")
        for step in WIZARD_STEPS:
            with st.expander(step["title"], expanded=True):
                st.write(step["body"])
        st.markdown("#### Vocabulary")
        st.markdown(glossary_markdown())

    with tabs[2]:
        st.subheader("Eve Mode")
        st.write(
            "Enable an Eve strategy in the sidebar, then watch the sifted-error column and QBER metric. "
            "Intercept-resend should frequently push QBER toward the abort zone."
        )
        eve_df = result.telemetry[result.telemetry["eve_intercepted"] | result.telemetry["sifted"]].head(128)
        render_protocol_table(type("R", (), {"telemetry": eve_df})())
        errors = int(result.telemetry["bit_error_when_sifted"].sum())
        st.progress(min(result.qber / max(config.qber_abort_threshold, 0.01), 1.0), text=f"QBER pressure: {result.qber_percent:.2f}% with {errors} visible sifted errors")

    with tabs[3]:
        st.subheader("Security Analytics")
        grid = sweep_noise_and_eve(key_length=max(256, config.key_length), strategy="probabilistic", seed=int(config.seed or 0))
        pivot = grid.pivot(index="noise_rate", columns="eve_intercept_probability", values="qber_percent")
        fig = px.imshow(
            pivot,
            text_auto=".1f",
            color_continuous_scale="RdYlGn_r",
            labels=dict(x="Eve intercept probability", y="Channel noise", color="QBER %"),
            title="QBER heatmap: safe zone vs abort zone",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(grid, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.subheader("Performance Gains")
        st.write("Use this frontend-ready panel to discuss and plan benchmark work with IBM Bob. The full prompt is included at `docs/bob_prompts/performance_gains_prompt.txt`.")
        perf_df = pd.DataFrame({
            "method": ["Analytical baseline", "Cached repeat run", "Future vectorized benchmark", "Projected GPU path"],
            "relative_speedup": [1.0, 2.4, 3.2, 8.0],
        })
        st.bar_chart(perf_df, x="method", y="relative_speedup", use_container_width=True)
        st.info("Next build step: ask IBM Bob to generate the `performance_gains/` module from the attached prompt, then wire its dashboard here.")

    with tabs[5]:
        st.subheader("Bob Copilot / watsonx.ai Scaffold")
        st.write(
            "This panel is intentionally wired with a safe local fallback. Add IBM Cloud variables from `.env.example` "
            "to turn it into a live watsonx.ai educational assistant. Use IBM Bob IDE for repository-aware code reviews "
            "and export the session report into `bob-sessions/`."
        )
        st.markdown("#### Starter prompts for IBM Bob")
        for prompt in BOB_PROMPTS:
            st.code(prompt, language="text")
        question = st.text_area("Ask the educational assistant", "Why does intercept-resend create about 25% QBER?")
        chat_url = st.text_input("Optional local chat endpoint", "http://localhost:8000/v1/chat/completions")
        chat_key = st.text_input("Chat API key", "dev-chat-key", type="password")
        use_endpoint = st.checkbox("Use FastAPI chat.py endpoint", value=False)
        if st.button("Ask assistant"):
            if use_endpoint:
                try:
                    response = requests.post(
                        chat_url,
                        json={"prompt": question, "model": "gpt-4.1-mini", "stream": False},
                        headers={"X-API-Key": chat_key},
                        timeout=20,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    st.write(payload.get("response", payload))
                    st.caption(f"Latency: {payload.get('latency_ms', 'n/a')} ms | Tokens: {payload.get('tokens_used', 'n/a')}")
                except Exception as exc:
                    st.error(f"Chat endpoint unavailable: {exc}. Start it with `uvicorn chat:app --reload --port 8000` or uncheck the endpoint option.")
            else:
                st.write(ask_watsonx(question, WatsonxConfig()))

    with tabs[6]:
        st.subheader("Hackathon Builder Notes")
        st.markdown("#### Demo script")
        st.write(demo_script())
        st.markdown("#### Submission checklist")
        st.markdown(
            """
            - Run the Streamlit demo locally or deploy it to your preferred platform.
            - Use IBM Bob IDE to review, extend, test, and document the repository.
            - Export the IBM Bob task/session report and place it in `bob-sessions/`.
            - Keep credentials out of GitHub; use `.env.example` as the template only.
            - Record the clean-channel run, the Eve attack run, and the Bob-assisted development story.
            """
        )


if __name__ == "__main__":
    main()
