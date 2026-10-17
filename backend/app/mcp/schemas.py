"""Strict input and output schemas for MCP tools."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# File Vault Schemas
# ============================================================================

class FileVaultReadInput(BaseModel):
    """Input parameters for reading a file from the vault."""
    path: str = Field(
        ...,
        description="The virtual file path to read (e.g., 'vault://classified/gauntlet-secret.txt' or 'public/company_handbook.txt').",
        min_length=1,
    )

    @field_validator("path")
    @classmethod
    def clean_path(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Path cannot be empty or whitespace.")
        return cleaned


class FileVaultListInput(BaseModel):
    """Input parameters for listing files in the vault."""
    directory: str = Field(
        default="",
        description="Optional subdirectory within vault to inspect (e.g. 'classified' or 'public'). Defaults to root.",
    )


class FileVaultReadOutput(BaseModel):
    success: bool
    path: str
    content: Optional[str] = None
    bytes: Optional[int] = None
    error: Optional[str] = None
    security_violation: Optional[str] = None


class FileVaultListOutput(BaseModel):
    success: bool
    directory: str
    files: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    error: Optional[str] = None


# ============================================================================
# CRM Sandbox Schemas
# ============================================================================

class CRMGetRecordInput(BaseModel):
    """Input parameters for retrieving a CRM record."""
    account_id: str = Field(
        ...,
        description="Unique identifier for the synthetic account (e.g. 'account-4471').",
        min_length=1,
    )

    @field_validator("account_id")
    @classmethod
    def clean_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Account ID cannot be empty.")
        return cleaned


class CRMListRecordsInput(BaseModel):
    """Input parameters for listing CRM records."""
    stage: Optional[str] = Field(
        default=None,
        description="Optional stage filter (e.g. 'Discovery', 'Negotiation', 'Closed Won').",
    )


class CRMUpdateRecordInput(BaseModel):
    """Input parameters for mutating a CRM record."""
    account_id: str = Field(
        ...,
        description="Unique account ID to update (e.g. 'account-4471').",
        min_length=1,
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="Dictionary of updates. Allowed fields: 'stage', 'notes', 'annual_revenue', 'assigned_representative'.",
    )

    @field_validator("account_id")
    @classmethod
    def clean_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Account ID cannot be empty.")
        return cleaned

    @field_validator("updates")
    @classmethod
    def validate_updates(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("Updates must be a dictionary.")
        if not v:
            raise ValueError("Updates payload cannot be empty.")
        return v


class CRMRecordOutput(BaseModel):
    success: bool
    record: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CRMListOutput(BaseModel):
    success: bool
    count: int
    records: List[Dict[str, Any]] = Field(default_factory=list)


class CRMUpdateOutput(BaseModel):
    success: bool
    account_id: str
    applied_updates: Optional[Dict[str, Any]] = None
    updated_record: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Email Sandbox Schemas
# ============================================================================

class EmailSendInput(BaseModel):
    """Input parameters for sending an email to the sandbox outbox."""
    recipient: str = Field(
        ...,
        description="Destination email address (e.g., 'ops@partner.sandbox').",
        min_length=3,
    )
    subject: str = Field(
        ...,
        description="Email subject line.",
        min_length=1,
    )
    body: str = Field(
        ...,
        description="Full email body content.",
    )

    @field_validator("recipient")
    @classmethod
    def clean_recipient(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Recipient address cannot be empty.")
        if "@" not in cleaned:
            raise ValueError(f"Invalid email address format: '{cleaned}'.")
        return cleaned

    @field_validator("subject")
    @classmethod
    def clean_subject(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Subject line cannot be empty.")
        return cleaned


class EmailSendOutput(BaseModel):
    success: bool
    message_id: Optional[str] = None
    recipient: str
    subject: str
    timestamp: Optional[str] = None
    status: str
    egress_prevented: bool = True
    warning: Optional[str] = None
    error: Optional[str] = None
