import json

from cryptolab.bb84 import simulate_bb84
from cryptolab.cli import main
from cryptolab.models import RunConfig
from cryptolab.reporting import run_to_json, run_to_markdown, save_report


def test_json_report_contains_summary():
    result = simulate_bb84(RunConfig(key_length=128, seed=3))
    payload = json.loads(run_to_json(result))
    assert "summary" in payload
    assert "config" in payload
    assert payload["summary"]["sifted_length"] == result.sifted_length


def test_markdown_report_contains_security_decision():
    result = simulate_bb84(RunConfig(key_length=128, seed=4))
    report = run_to_markdown(result)
    assert "CryptoLab BB84 Simulation Report" in report
    assert "Security decision" in report


def test_save_report_and_cli(tmp_path):
    output = tmp_path / "run.json"
    exit_code = main(["--key-length", "128", "--seed", "5", "--output", str(output)])
    assert exit_code == 0
    assert output.exists()
    assert json.loads(output.read_text())["config"]["key_length"] == 128


def test_save_markdown_report(tmp_path):
    result = simulate_bb84(RunConfig(key_length=128, seed=6))
    output = save_report(result, tmp_path / "run.md")
    assert output.exists()
    assert output.read_text().startswith("# CryptoLab BB84 Simulation Report")
