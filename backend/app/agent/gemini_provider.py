"""Dedicated Gemini Provider Module using the official Google Gen AI Python SDK."""

import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from ..config import settings
from ..mcp.tools import ToolRegistry


class ToolCallRequest(BaseModel):
    """Normalized tool call requested by the model."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class ModelTurnResult(BaseModel):
    """Normalized result of an LLM turn."""
    text: Optional[str] = None
    tool_calls: List[ToolCallRequest] = Field(default_factory=list)
    finish_reason: Optional[str] = None
    raw_content: Optional[Any] = None


class GeminiProvider:
    """Dedicated provider managing Gemini SDK interaction and function calling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        mock_handler: Optional[Any] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.model = model or settings.gemini_model
        self.mock_handler = mock_handler
        self._client = None

        if self.is_configured and GENAI_AVAILABLE:
            self._client = genai.Client(api_key=self.api_key)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    def build_sdk_tools(self, tool_registry: ToolRegistry) -> Optional[List[Any]]:
        """Convert MCP ToolRegistry declarations to Gemini types.Tool."""
        if not GENAI_AVAILABLE:
            return None

        function_declarations = []
        for tool in tool_registry.list_tools():
            schema_dict = tool.input_schema_cls.model_json_schema()
            properties = {}
            for prop_name, prop_data in schema_dict.get("properties", {}).items():
                p_type = prop_data.get("type", "string").upper()
                if p_type == "OBJECT":
                    p_type = "OBJECT"
                elif p_type == "ARRAY":
                    p_type = "ARRAY"
                elif p_type in ("NUMBER", "INTEGER"):
                    p_type = "NUMBER"
                elif p_type == "BOOLEAN":
                    p_type = "BOOLEAN"
                else:
                    p_type = "STRING"

                properties[prop_name] = types.Schema(
                    type=p_type,
                    description=prop_data.get("description", ""),
                )

            decl = types.FunctionDeclaration(
                name=tool.name.replace(".", "_"),
                description=tool.description,
                parameters=types.Schema(
                    type="OBJECT",
                    properties=properties,
                    required=schema_dict.get("required", []),
                ),
            )
            function_declarations.append(decl)

        return [types.Tool(function_declarations=function_declarations)]

    async def generate_turn(
        self,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None,
    ) -> ModelTurnResult:
        """Execute a single model inference turn, returning thoughts and proposed tool calls."""
        if self.mock_handler:
            import inspect
            if inspect.iscoroutinefunction(self.mock_handler):
                return await self.mock_handler(contents, system_instruction, tools)
            res = self.mock_handler(contents, system_instruction, tools)
            if inspect.isawaitable(res):
                return await res
            return res

        if not self.is_configured:
            raise RuntimeError(
                "Gemini API is not configured. Please supply a valid GEMINI_API_KEY in .env."
            )

        if not self._client:
            raise RuntimeError("Google Gen AI client is uninitialized.")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.2,
        )

        # Call Gemini SDK with automatic retry for transient 503 high-demand spikes
        response = None
        for attempt in range(1, 4):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "high demand" in err_str or "UNAVAILABLE" in err_str) and attempt < 3:
                    await asyncio.sleep(1.5 * attempt)
                    continue
                raise e

        if not response:
            raise RuntimeError("No response from Gemini API.")

        turn_text = ""
        tool_calls: List[ToolCallRequest] = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if getattr(part, "text", None):
                        turn_text += part.text
                    if getattr(part, "function_call", None):
                        fc = part.function_call
                        tool_calls.append(
                            ToolCallRequest(
                                name=fc.name,
                                arguments=dict(fc.args) if fc.args else {},
                            )
                        )

            return ModelTurnResult(
                text=turn_text.strip() or None,
                tool_calls=tool_calls,
                finish_reason=str(candidate.finish_reason) if candidate.finish_reason else None,
                raw_content=candidate.content,
            )

        return ModelTurnResult(text=response.text or None)
