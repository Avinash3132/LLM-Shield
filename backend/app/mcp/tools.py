"""Tool representation and registry for MCP tools."""

from typing import Dict, Any, Callable, Type, List, Optional
from pydantic import BaseModel


class MCPTool:
    """Represents a standardized MCP tool definition with validation schemas."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema_cls: Type[BaseModel],
        output_schema_cls: Type[BaseModel],
        handler: Callable[..., Any],
        aliases: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.input_schema_cls = input_schema_cls
        self.output_schema_cls = output_schema_cls
        self.handler = handler
        self.aliases = aliases or []

    def to_mcp_dict(self) -> Dict[str, Any]:
        """Export tool in standard Model Context Protocol (MCP) JSON schema format."""
        schema = self.input_schema_cls.model_json_schema()
        # Clean title and extra metadata for standard MCP consumption
        schema.pop("title", None)
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": schema,
        }

    def to_gemini_declaration(self) -> Dict[str, Any]:
        """Export tool in Gemini FunctionDeclaration dictionary schema format."""
        schema = self.input_schema_cls.model_json_schema()
        # Convert Pydantic JSON schema to Gemini function parameter spec
        properties = {}
        for prop_name, prop_data in schema.get("properties", {}).items():
            prop_type = prop_data.get("type", "string").upper()
            properties[prop_name] = {
                "type": prop_type,
                "description": prop_data.get("description", ""),
            }

        return {
            "name": self.name.replace(".", "_"),
            "description": self.description,
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": schema.get("required", []),
            },
        }

    def validate_input(self, raw_args: Dict[str, Any]) -> BaseModel:
        """Validate raw keyword arguments against input schema."""
        return self.input_schema_cls.model_validate(raw_args)


class ToolRegistry:
    """Registry managing available MCP sandbox tools."""

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._alias_map: Dict[str, str] = {}

    def register(self, tool: MCPTool) -> None:
        """Register an MCP tool along with any alternate naming aliases."""
        self._tools[tool.name] = tool
        self._alias_map[tool.name.lower()] = tool.name
        for alias in tool.aliases:
            self._alias_map[alias.lower()] = tool.name

    def get(self, name_or_alias: str) -> Optional[MCPTool]:
        """Look up tool by exact name or alias (case-insensitive)."""
        normalized = name_or_alias.strip().lower()
        primary_name = self._alias_map.get(normalized)
        if primary_name:
            return self._tools.get(primary_name)
        # Try replacing dot with underscore or vice-versa
        alt = normalized.replace(".", "_") if "." in normalized else normalized.replace("_", ".")
        primary_name = self._alias_map.get(alt)
        if primary_name:
            return self._tools.get(primary_name)
        return None

    def list_tools(self) -> List[MCPTool]:
        """Return list of all registered tools."""
        return list(self._tools.values())

    def to_mcp_catalog(self) -> List[Dict[str, Any]]:
        """Return full catalog in MCP format."""
        return [tool.to_mcp_dict() for tool in self._tools.values()]

    def to_gemini_declarations(self) -> List[Dict[str, Any]]:
        """Return all tool declarations formatted for Gemini SDK."""
        return [tool.to_gemini_declaration() for tool in self._tools.values()]
