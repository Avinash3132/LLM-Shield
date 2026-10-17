"""Mock CRM Sandbox.

Provides an isolated customer dataset with safe query and mutation methods.
Maintains in-memory state during execution with the ability to reset to baseline fixtures.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


ALLOWED_UPDATE_FIELDS = {"stage", "notes", "annual_revenue", "assigned_representative"}


class CRMSandbox:
    """Isolated CRM sandbox service operating on synthetic data."""

    def __init__(self, data_path: Path | str):
        self.data_path = Path(data_path).resolve()
        self._records: Dict[str, Dict[str, Any]] = {}
        self.reload_from_fixture()

    def reload_from_fixture(self) -> None:
        """Reload records from the baseline JSON fixture."""
        if not self.data_path.exists():
            self._records = {}
            return
        content = self.data_path.read_text(encoding="utf-8")
        raw_list = json.loads(content)
        self._records = {item["id"]: item for item in raw_list}

    def list_records(self, stage: Optional[str] = None) -> Dict[str, Any]:
        """List customer records, optionally filtered by sales stage."""
        results = list(self._records.values())
        if stage:
            results = [r for r in results if r.get("stage", "").lower() == stage.lower()]
        return {
            "success": True,
            "count": len(results),
            "records": results,
        }

    def get_record(self, account_id: str) -> Dict[str, Any]:
        """Retrieve a single CRM record by account ID."""
        cleaned_id = account_id.strip()
        record = self._records.get(cleaned_id)
        if not record:
            return {
                "success": False,
                "error": f"Account '{cleaned_id}' not found in CRM.",
                "account_id": cleaned_id,
            }
        return {
            "success": True,
            "record": record,
        }

    def update_record(self, account_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update mutable fields on a synthetic CRM record."""
        cleaned_id = account_id.strip()
        if cleaned_id not in self._records:
            return {
                "success": False,
                "error": f"Account '{cleaned_id}' not found.",
                "account_id": cleaned_id,
            }

        # Filter out disallowed update fields to maintain schema integrity
        disallowed = [k for k in updates.keys() if k not in ALLOWED_UPDATE_FIELDS]
        if disallowed:
            return {
                "success": False,
                "error": f"Disallowed fields for update: {disallowed}. Allowed: {list(ALLOWED_UPDATE_FIELDS)}",
                "account_id": cleaned_id,
            }

        target = self._records[cleaned_id]
        applied = {}
        for k, v in updates.items():
            if k in ALLOWED_UPDATE_FIELDS:
                target[k] = v
                applied[k] = v

        return {
            "success": True,
            "account_id": cleaned_id,
            "applied_updates": applied,
            "updated_record": target,
        }
