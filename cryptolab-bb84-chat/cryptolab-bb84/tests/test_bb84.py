from cryptolab.analytics import estimate_expected_qber, sweep_noise_and_eve
from cryptolab.bb84 import calculate_qber, simulate_bb84
from cryptolab.models import RunConfig


def test_clean_channel_has_low_qber_and_final_key():
    result = simulate_bb84(RunConfig(key_length=512, noise_rate=0.0, eve_strategy="none", seed=7))
    assert result.qber == 0.0
    assert result.sifted_length > 150
    assert result.final_key_length > 50
    assert result.agreement is True
    assert result.secure is True


def test_intercept_resend_increases_qber():
    clean = simulate_bb84(RunConfig(key_length=1024, noise_rate=0.0, eve_strategy="none", seed=11))
    attacked = simulate_bb84(
        RunConfig(key_length=1024, noise_rate=0.0, eve_strategy="intercept_resend", seed=11)
    )
    assert attacked.qber > clean.qber
    assert attacked.qber > 0.10


def test_qber_calculation():
    assert calculate_qber([0, 1, 1, 0], [0, 0, 1, 1]) == 0.5


def test_analytics_grid_shape():
    grid = sweep_noise_and_eve(key_length=128, noise_values=[0.0, 0.1], intercept_values=[0.0, 1.0], seed=1)
    assert len(grid) == 4
    assert {"noise_rate", "eve_intercept_probability", "qber_percent", "secure"}.issubset(grid.columns)


def test_expected_qber_estimate_bounds():
    assert 0.0 <= estimate_expected_qber(0.01, 1.0) <= 1.0
