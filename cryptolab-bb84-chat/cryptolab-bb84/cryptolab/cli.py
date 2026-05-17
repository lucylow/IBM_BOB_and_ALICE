"""Command-line interface for CryptoLab: BB84."""

from __future__ import annotations

import argparse

from .bb84 import simulate_bb84
from .models import RunConfig
from .reporting import save_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a BB84 QKD simulation and optionally export a report.")
    parser.add_argument("--key-length", type=int, default=256, help="Number of raw qubits to simulate.")
    parser.add_argument("--noise-rate", type=float, default=0.01, help="Independent channel bit-flip noise rate.")
    parser.add_argument(
        "--eve-strategy",
        choices=["none", "intercept_resend", "probabilistic", "basis_bias"],
        default="none",
        help="Eavesdropping model to apply.",
    )
    parser.add_argument("--eve-probability", type=float, default=1.0, help="Probability that Eve intercepts each qubit.")
    parser.add_argument("--sample-fraction", type=float, default=0.25, help="Fraction of sifted bits revealed for QBER.")
    parser.add_argument("--threshold", type=float, default=0.11, help="QBER abort threshold.")
    parser.add_argument("--seed", type=int, default=84, help="Random seed for reproducible demos.")
    parser.add_argument("--output", type=str, default="", help="Optional .json or .md report path.")
    parser.add_argument("--include-telemetry", action="store_true", help="Include per-qubit telemetry in JSON export.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = RunConfig(
        key_length=args.key_length,
        noise_rate=args.noise_rate,
        eve_strategy=args.eve_strategy,
        eve_intercept_probability=args.eve_probability,
        sample_fraction=args.sample_fraction,
        qber_abort_threshold=args.threshold,
        seed=args.seed,
    )
    result = simulate_bb84(config)
    print(f"QBER: {result.qber_percent:.2f}%")
    print(f"Sifted bits: {result.sifted_length}")
    print(f"Final key bits: {result.final_key_length}")
    print(f"Agreement: {result.agreement}")
    print(f"Status: {result.status}")
    if args.output:
        path = save_report(result, args.output, include_telemetry=args.include_telemetry)
        print(f"Report written: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
