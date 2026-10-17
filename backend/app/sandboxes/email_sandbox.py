"""Mock Email Sandbox.

Stores all outbound email payloads locally within the test outbox.
Zero external network egress: never connects to real SMTP or external email APIs.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


class EmailSandbox:
    """Isolated email outbox for testing exfiltration attempts safely."""

    def __init__(self, outbox_path: Path | str):
        self.outbox_path = Path(outbox_path).resolve()
        if not self.outbox_path.parent.exists():
            self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.outbox_path.exists():
            self.outbox_path.write_text("[]", encoding="utf-8")
        self._outbox: List[Dict[str, Any]] = []
        self.reload_from_disk()

    def reload_from_disk(self) -> None:
        """Reload outbox from local JSON file."""
        if not self.outbox_path.exists():
            self._outbox = []
            return
        try:
            content = self.outbox_path.read_text(encoding="utf-8")
            self._outbox = json.loads(content)
        except Exception:
            self._outbox = []

    def _persist(self) -> None:
        """Persist current outbox state to disk."""
        self.outbox_path.write_text(json.dumps(self._outbox, indent=2), encoding="utf-8")

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        sender: str = "agent@llmshield.sandbox",
    ) -> Dict[str, Any]:
        """Record an outbound email into the local sandbox outbox."""
        if not recipient or not recipient.strip():
            return {"success": False, "error": "Recipient email address is required."}
        if not subject or not subject.strip():
            return {"success": False, "error": "Email subject line is required."}

        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "message_id": msg_id,
            "sender": sender.strip(),
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "body": body,
            "timestamp": timestamp,
            "character_count": len(body),
            "egress_prevented": True,
            "destination": "LOCAL_SANDBOX_OUTBOX_ONLY",
        }

        self._outbox.append(record)
        self._persist()

        return {
            "success": True,
            "message_id": msg_id,
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "timestamp": timestamp,
            "status": "STORED_IN_SANDBOX_OUTBOX",
            "warning": "Message stored locally in sandbox outbox. No external network transmission occurred.",
        }

    def list_outbox(self) -> Dict[str, Any]:
        """List all messages currently stored in the sandbox outbox."""
        return {
            "success": True,
            "count": len(self._outbox),
            "messages": list(self._outbox),
        }

    def clear_outbox(self) -> Dict[str, Any]:
        """Clear all messages from the sandbox outbox."""
        count = len(self._outbox)
        self._outbox = []
        self._persist()
        return {
            "success": True,
            "cleared_count": count,
        }
