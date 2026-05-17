"""Export helpers for BB84 simulation results.

These functions make the project more submission-ready by allowing learners and
judges to save simulation evidence without depending on the Streamlit UI.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import ProtocolRun


def _json_default(value: Any) -> Any:
    """Serialize common project objects into JSON-safe values."""
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "to_dict"):
        return value.to_dict(orient="records")
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def run_to_dict(result: ProtocolRun, include_telemetry: bool = False) -> dict[str, Any]:
    """Convert a protocol run into a compact dictionary."""
    payload: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": result.config,
        "summary": result.summary(),
        "keys": {
            "alice_sifted_key": result.alice_sifted_key,
            "bob_sifted_key": result.bob_sifted_key,
            "alice_final_key": result.alice_final_key,
            "bob_final_key": result.bob_final_key,
        },
    }
    if include_telemetry:
        payload["telemetry"] = result.telemetry.to_dict(orient="records")
    return payload


def run_to_json(result: ProtocolRun, include_telemetry: bool = False) -> str:
    """Return a pretty JSON export for a BB84 run."""
    return json.dumps(run_to_dict(result, include_telemetry=include_telemetry), indent=2, default=_json_default)


def run_to_markdown(result: ProtocolRun) -> str:
    """Return a concise Markdown report suitable for docs or hackathon evidence."""
    status = "Secure" if result.secure else "Abort"
    return f"""# CryptoLab BB84 Simulation Report

Generated at: {datetime.now(timezone.utc).isoformat()}

| Metric | Value |
|---|---:|
| Security decision | {status} |
| QBER | {result.qber_percent:.2f}% |
| Sifted key length | {result.sifted_length} |
| Revealed sample size | {result.sample_size} |
| Final key length | {result.final_key_length} |
| Final key agreement | {result.agreement} |

## Configuration

```json
{json.dumps(result.config, indent=2)}
```

## Educational interpretation

The run is considered **{status.lower()}** because its sampled QBER is compared against the configured abort threshold. In a clean BB84 exchange, Alice and Bob should agree on unrevealed sifted bits. When Eve measures unknown states, her wrong-basis choices introduce disturbances that appear as sampled errors.
"""


def save_report(result: ProtocolRun, output_path: str | Path, include_telemetry: bool = False) -> Path:
    """Save a JSON or Markdown report based on the output file extension."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".md":
        path.write_text(run_to_markdown(result), encoding="utf-8")
    else:
        path.write_text(run_to_json(result, include_telemetry=include_telemetry), encoding="utf-8")
    return path
