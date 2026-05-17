"""CryptoLab: BB84 educational simulator package."""

from .bb84 import calculate_qber, run_default_demo, simulate_bb84
from .models import ProtocolRun, RunConfig
from .reporting import run_to_dict, run_to_json, run_to_markdown, save_report

__all__ = [
    "RunConfig",
    "ProtocolRun",
    "simulate_bb84",
    "calculate_qber",
    "run_default_demo",
    "run_to_dict",
    "run_to_json",
    "run_to_markdown",
    "save_report",
]
