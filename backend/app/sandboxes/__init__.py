"""Sandbox services for Prompt-Injection Gauntlet (LLMShield).
Provides isolated mock environments for file vault, CRM, and email outbox.
"""

from .file_vault import FileVaultSandbox
from .crm_sandbox import CRMSandbox
from .email_sandbox import EmailSandbox

__all__ = ["FileVaultSandbox", "CRMSandbox", "EmailSandbox"]
