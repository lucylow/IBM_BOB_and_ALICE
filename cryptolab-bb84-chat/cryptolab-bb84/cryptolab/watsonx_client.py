"""Optional IBM watsonx.ai helper for the Bob Copilot panel.

The app works without credentials. When watsonx variables are present, this
client can call IBM watsonx.ai text generation; otherwise it returns a local,
educational fallback so demos never fail.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

LOCAL_FALLBACK = (
    "Local demo response: In BB84, Alice and Bob randomly choose bases. "
    "After transmission, they publicly compare bases and keep only matching "
    "positions. Eve cannot measure unknown quantum states without sometimes "
    "choosing the wrong basis, which introduces detectable QBER."
)


@dataclass(frozen=True)
class WatsonxConfig:
    """Environment-driven watsonx.ai configuration."""

    api_key: str | None = os.getenv("WATSONX_API_KEY") or os.getenv("IBM_CLOUD_API_KEY")
    project_id: str | None = os.getenv("WATSONX_PROJECT_ID")
    url: str = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    model_id: str = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct")

    @property
    def configured(self) -> bool:
        """Return true when enough credentials exist for a live request."""
        return bool(self.api_key and self.project_id)


def _get_iam_token(api_key: str) -> str:
    response = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def ask_watsonx(prompt: str, config: WatsonxConfig | None = None) -> str:
    """Ask watsonx.ai for a short educational response.

    The function intentionally catches network/configuration errors and returns a
    clear fallback because hackathon demos should remain stable even without IBM
    Cloud credentials on the presentation machine.
    """
    config = config or WatsonxConfig()
    if not config.configured:
        return LOCAL_FALLBACK

    try:
        token = _get_iam_token(config.api_key or "")
        endpoint = f"{config.url.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"
        payload: dict[str, Any] = {
            "model_id": config.model_id,
            "project_id": config.project_id,
            "input": (
                "You are a concise quantum cryptography tutor inside CryptoLab: BB84. "
                "Answer in 4 sentences or fewer.\n\nUser question: " + prompt
            ),
            "parameters": {"decoding_method": "greedy", "max_new_tokens": 220, "min_new_tokens": 20},
        }
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [{}])[0].get("generated_text", LOCAL_FALLBACK).strip()
    except Exception as exc:  # pragma: no cover - defensive fallback for demos
        return f"{LOCAL_FALLBACK}\n\nWatsonx live call was skipped: {exc}"
