"""Tests for data minimization utility and API endpoint."""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import MINIMIZER, app
from utils.data_minimizer import DataMinimizer


@pytest.fixture
def minimizer() -> DataMinimizer:
    """Provide a fresh minimizer instance for each test."""
    return DataMinimizer()


@pytest.fixture
def client():
    """Provide Flask test client with isolated minimization log."""
    app.config["TESTING"] = True
    MINIMIZER.data_minimization_log.clear()
    with app.test_client() as test_client:
        yield test_client


def sample_dataframe() -> pd.DataFrame:
    """Create representative sample records with PII and extra fields."""
    return pd.DataFrame(
        [
            {
                "user_id": 1,
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "phone": "+1-202-555-0134",
                "age": 24,
                "country": "US",
                "transaction_amount": 120.0,
                "is_fraud": 0,
                "extra_field": "drop me",
            }
        ]
    )


def test_minimizer_drops_unneeded_columns(minimizer: DataMinimizer) -> None:
    """Minimizer should drop columns not required for the selected purpose."""
    minimized = minimizer.minimize(sample_dataframe(), "analytics")
    assert "extra_field" not in minimized.columns
    assert "name" not in minimized.columns
    assert "email" not in minimized.columns


def test_email_is_hashed(minimizer: DataMinimizer) -> None:
    """Email should be hashed when retained by the purpose mapping."""
    minimized = minimizer.minimize(sample_dataframe(), "user_display")
    assert minimized.loc[0, "email"] != "alice@example.com"
    assert len(minimized.loc[0, "email"]) == 64


def test_phone_masks_to_last_four_digits(minimizer: DataMinimizer) -> None:
    """Phone number should retain only the final four digits."""
    minimized = minimizer.minimize(sample_dataframe(), "user_display")
    assert minimized.loc[0, "phone"] == "0134"


def test_age_is_bucketed(minimizer: DataMinimizer) -> None:
    """Age should be converted into an age_group bucket."""
    minimized = minimizer.minimize(sample_dataframe(), "analytics")
    assert minimized.loc[0, "age_group"] == "18-25"


def test_audit_report_has_expected_keys(minimizer: DataMinimizer) -> None:
    """Audit report should be JSON serializable and contain standard keys."""
    minimizer.minimize(sample_dataframe(), "analytics")
    report = minimizer.audit_report()
    json.dumps(report)

    assert "total_actions" in report
    assert "actions" in report
    assert {"timestamp", "fields_dropped", "fields_masked", "purpose"}.issubset(
        report["actions"][-1].keys()
    )


def test_unknown_purpose_raises_value_error(minimizer: DataMinimizer) -> None:
    """Unknown purpose should raise ValueError."""
    with pytest.raises(ValueError):
        minimizer.minimize(sample_dataframe(), "unknown_purpose")


def test_empty_dataframe_handled_gracefully(minimizer: DataMinimizer) -> None:
    """An empty dataframe should return an empty dataframe without failure."""
    minimized = minimizer.minimize(pd.DataFrame(), "analytics")
    assert minimized.empty


def test_minimize_api_returns_200(client) -> None:
    """API should return minimized output for a known purpose."""
    payload = {
        "purpose": "analytics",
        "data": [
            {
                "user_id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "phone": "2025550134",
                "age": 24,
                "country": "US",
                "transaction_amount": 120.0,
                "is_fraud": 0,
            }
        ],
    }

    response = client.post("/api/minimize", json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert "data" in body
    assert "audit_log" in body


def test_minimize_api_returns_400_for_unknown_purpose(client) -> None:
    """API should reject unknown purposes with HTTP 400."""
    payload = {"purpose": "unknown", "data": [{"name": "Alice"}]}
    response = client.post("/api/minimize", json=payload)
    assert response.status_code == 400
