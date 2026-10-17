"""Sandbox Tool Adapter for LLMShield.

Acts as the unified execution boundary between agent execution loops (and authorization interceptors)
and the underlying isolated sandboxes (File Vault, CRM, Email Outbox).
"""

from typing import Dict, Any, Optional
from pydantic import ValidationError

from ..sandboxes import FileVaultSandbox, CRMSandbox, EmailSandbox
from .schemas import (
    FileVaultReadInput,
    FileVaultReadOutput,
    FileVaultListInput,
    FileVaultListOutput,
    CRMGetRecordInput,
    CRMRecordOutput,
    CRMListRecordsInput,
    CRMListOutput,
    CRMUpdateRecordInput,
    CRMUpdateOutput,
    EmailSendInput,
    EmailSendOutput,
)
from .tools import MCPTool, ToolRegistry


class SandboxToolAdapter:
    """Unified adapter providing validated tool execution against isolated sandboxes."""

    def __init__(
        self,
        vault: FileVaultSandbox,
        crm: CRMSandbox,
        email: EmailSandbox,
    ):
        self.vault = vault
        self.crm = crm
        self.email = email
        self.registry = ToolRegistry()
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the standard suite of MCP-compatible sandbox tools."""
        # 1. file_vault.read
        self.registry.register(
            MCPTool(
                name="file_vault.read",
                description="Read contents of a file from the vault. Accepts virtual URI like 'vault://classified/gauntlet-secret.txt'.",
                input_schema_cls=FileVaultReadInput,
                output_schema_cls=FileVaultReadOutput,
                handler=lambda args: self.vault.read_file(args.path),
                aliases=["file_vault_read"],
            )
        )

        # 2. file_vault.list
        self.registry.register(
            MCPTool(
                name="file_vault.list",
                description="List files in the vault sandbox directory.",
                input_schema_cls=FileVaultListInput,
                output_schema_cls=FileVaultListOutput,
                handler=lambda args: self.vault.list_files(args.directory),
                aliases=["file_vault_list"],
            )
        )

        # 3. crm.get_record
        self.registry.register(
            MCPTool(
                name="crm.get_record",
                description="Retrieve a synthetic customer account record by account ID (e.g., 'account-4471').",
                input_schema_cls=CRMGetRecordInput,
                output_schema_cls=CRMRecordOutput,
                handler=lambda args: self.crm.get_record(args.account_id),
                aliases=["crm_get_record"],
            )
        )

        # 4. crm.list_records
        self.registry.register(
            MCPTool(
                name="crm.list_records",
                description="List customer records in the CRM sandbox, optionally filtered by stage.",
                input_schema_cls=CRMListRecordsInput,
                output_schema_cls=CRMListOutput,
                handler=lambda args: self.crm.list_records(args.stage),
                aliases=["crm_list_records"],
            )
        )

        # 5. crm.update_record
        self.registry.register(
            MCPTool(
                name="crm.update_record",
                description="Update mutable fields ('stage', 'notes', 'annual_revenue') on a synthetic CRM account.",
                input_schema_cls=CRMUpdateRecordInput,
                output_schema_cls=CRMUpdateOutput,
                handler=lambda args: self.crm.update_record(args.account_id, args.updates),
                aliases=["crm_update_record"],
            )
        )

        # 6. email.send
        self.registry.register(
            MCPTool(
                name="email.send",
                description="Record an outbound email into the local sandbox outbox. Never transmits to external networks.",
                input_schema_cls=EmailSendInput,
                output_schema_cls=EmailSendOutput,
                handler=lambda args: self.email.send_email(
                    recipient=args.recipient,
                    subject=args.subject,
                    body=args.body,
                ),
                aliases=["email_send"],
            )
        )

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call with strict schema validation and error isolation."""
        tool = self.registry.get(tool_name)
        if not tool:
            return {
                "success": False,
                "is_error": True,
                "error": f"Tool '{tool_name}' is not recognized in sandbox adapter.",
                "tool_name": tool_name,
            }

        # Validate input schema
        try:
            validated_args = tool.validate_input(arguments)
        except ValidationError as e:
            return {
                "success": False,
                "is_error": True,
                "error": f"Validation error for tool '{tool_name}': {e.errors()}",
                "tool_name": tool_name,
                "validation_errors": e.errors(),
            }
        except Exception as e:
            return {
                "success": False,
                "is_error": True,
                "error": f"Validation error for '{tool_name}': {str(e)}",
                "tool_name": tool_name,
            }

        # Execute handler within boundary
        try:
            raw_result = tool.handler(validated_args)
            # Format through output model
            validated_output = tool.output_schema_cls.model_validate(raw_result)
            return validated_output.model_dump()
        except Exception as e:
            return {
                "success": False,
                "is_error": True,
                "error": f"Execution error in '{tool_name}': {str(e)}",
                "tool_name": tool_name,
            }
