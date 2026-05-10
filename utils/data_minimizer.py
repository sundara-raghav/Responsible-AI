"""Utilities for applying data minimization controls to tabular data."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


class DataMinimizer:
    """Apply purpose-bound field reduction and privacy-safe masking."""

    def __init__(self, purpose_map_path: str | None = None) -> None:
        """Initialize the minimizer with a purpose-to-fields configuration."""
        base_dir = Path(__file__).resolve().parent.parent
        default_path = base_dir / "config" / "purpose_field_map.json"
        map_path = Path(purpose_map_path) if purpose_map_path else default_path

        with map_path.open("r", encoding="utf-8") as file_handle:
            self.purpose_field_map: dict[str, list[str]] = json.load(file_handle)

        self.data_minimization_log: list[dict[str, Any]] = []

    def is_known_purpose(self, purpose: str) -> bool:
        """Return True when the purpose exists in the loaded configuration."""
        return purpose in self.purpose_field_map

    def minimize(self, df: pd.DataFrame, purpose: str) -> pd.DataFrame:
        """Minimize a dataframe for a given purpose and log the action."""
        if not self.is_known_purpose(purpose):
            raise ValueError(f"Unknown purpose: {purpose}")

        if df is None:
            df = pd.DataFrame()

        minimized_df = df.copy()
        required_fields = set(self.purpose_field_map[purpose])
        fields_masked: list[str] = []

        if "age" in minimized_df.columns:
            minimized_df["age_group"] = minimized_df["age"].apply(self._age_to_group)
            fields_masked.append("age")

        fields_dropped = [
            column for column in minimized_df.columns if column not in required_fields
        ]
        if fields_dropped:
            minimized_df = minimized_df.drop(columns=fields_dropped)

        if "name" in minimized_df.columns:
            minimized_df["name"] = minimized_df["name"].apply(self._mask_name)
            fields_masked.append("name")

        if "email" in minimized_df.columns:
            minimized_df["email"] = minimized_df["email"].apply(self._hash_email)
            fields_masked.append("email")

        if "phone" in minimized_df.columns:
            minimized_df["phone"] = minimized_df["phone"].apply(self._mask_phone)
            fields_masked.append("phone")

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "purpose": purpose,
            "fields_dropped": fields_dropped,
            "fields_masked": sorted(set(fields_masked)),
        }
        self.data_minimization_log.append(log_entry)

        return minimized_df

    def audit_report(self) -> dict[str, Any]:
        """Return a JSON-serializable report of all minimization actions."""
        return {
            "total_actions": len(self.data_minimization_log),
            "actions": self.data_minimization_log,
        }

    @staticmethod
    def _hash_email(value: Any) -> Any:
        """Hash emails using SHA-256 while preserving null values."""
        if pd.isna(value):
            return None
        normalized = str(value).strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _mask_phone(value: Any) -> Any:
        """Mask phone numbers to expose only the last four digits."""
        if pd.isna(value):
            return None
        digits = "".join(char for char in str(value) if char.isdigit())
        if not digits:
            return "****"
        return digits[-4:]

    @staticmethod
    def _mask_name(value: Any) -> Any:
        """Mask names to first letter followed by asterisks."""
        if pd.isna(value):
            return None
        clean_value = str(value).strip()
        if not clean_value:
            return "***"
        return f"{clean_value[0]}***"

    @staticmethod
    def _age_to_group(value: Any) -> str:
        """Convert ages into privacy-preserving age buckets."""
        try:
            age = float(value)
        except (TypeError, ValueError):
            return "unknown"

        if age < 18:
            return "<18"
        if age <= 25:
            return "18-25"
        if age <= 35:
            return "26-35"
        if age <= 50:
            return "36-50"
        return "51+"
