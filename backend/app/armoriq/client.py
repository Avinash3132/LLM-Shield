"""ArmorIQ HTTP Client Adapter.

Provides a clearly isolated integration adapter for the ArmorIQ platform.
If credentials or connectivity are unavailable, all methods fail-secure
and report the exact failure reason without fabricating success states.
"""

import asyncio
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import httpx

from ..config import settings


class AuthorizationDecision(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    POLICY_DENIED = "POLICY_DENIED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    AUTHORIZATION_TIMEOUT = "AUTHORIZATION_TIMEOUT"
    INVALID_REQUEST = "INVALID_REQUEST"


class AuthorizationResult(BaseModel):
    """Result returned from ArmorIQ authorization request."""
    decision: AuthorizationDecision
    policy_id: Optional[str] = None
    reason: str = ""
    is_live: bool = False
    raw_response: Optional[Dict[str, Any]] = None


class ArmorIQClient:
    """HTTP client adapter for the ArmorIQ governance platform.

    NOTE: This is an integration adapter built against placeholder endpoints.
    When actual ArmorIQ documentation and credentials become available, the
    request/response format should be verified and updated. No fake success
    states are ever generated.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        agent_id: Optional[str] = None,
        timeout_seconds: float = 5.0,
        simulate_timeout: bool = False,
        mock_auth_handler: Optional[Any] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.armoriq_api_key
        self.endpoint = (endpoint if endpoint is not None else settings.armoriq_endpoint).rstrip("/")
        self.agent_id = agent_id if agent_id is not None else settings.armoriq_agent_id
        self.timeout = timeout_seconds
        self.simulate_timeout = simulate_timeout
        self.mock_auth_handler = mock_auth_handler

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    async def check_authorization(
        self,
        agent_role: str,
        tool_name: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuthorizationResult:
        """Request authorization from ArmorIQ for a specific tool invocation.

        Fail-secure: any error, timeout, or missing credential results in
        a blocked decision. Never fabricates an AUTHORIZED result.
        """
        # If mock handler provided for testing
        if self.mock_auth_handler:
            import inspect
            if inspect.iscoroutinefunction(self.mock_auth_handler):
                return await self.mock_auth_handler(agent_role, tool_name, action, context)
            res = self.mock_auth_handler(agent_role, tool_name, action, context)
            if inspect.isawaitable(res):
                return await res
            return res

        # Simulate timeout for Scenario E testing
        if self.simulate_timeout:
            return AuthorizationResult(
                decision=AuthorizationDecision.AUTHORIZATION_TIMEOUT,
                reason="Authorization service unreachable (simulated timeout for testing).",
                is_live=False,
            )

        # Fail-secure if not configured
        if not self.is_configured:
            return AuthorizationResult(
                decision=AuthorizationDecision.AUTHENTICATION_FAILED,
                reason="ArmorIQ API key is not configured. Cannot authorize without valid credentials.",
                is_live=False,
            )

        # Attempt live authorization request
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "agent_id": self.agent_id,
                    "agent_role": agent_role,
                    "tool_name": tool_name,
                    "action": action,
                    "context": context or {},
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                response = await client.post(
                    f"{self.endpoint}/authorize",
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    decision_str = data.get("decision", "AUTHORIZATION_ERROR")
                    try:
                        decision = AuthorizationDecision(decision_str)
                    except ValueError:
                        decision = AuthorizationDecision.AUTHORIZATION_ERROR

                    return AuthorizationResult(
                        decision=decision,
                        policy_id=data.get("policy_id"),
                        reason=data.get("reason", ""),
                        is_live=True,
                        raw_response=data,
                    )
                elif response.status_code == 401 or response.status_code == 403:
                    return AuthorizationResult(
                        decision=AuthorizationDecision.AUTHENTICATION_FAILED,
                        reason=f"ArmorIQ returned HTTP {response.status_code}: authentication/authorization rejected.",
                        is_live=True,
                    )
                else:
                    return AuthorizationResult(
                        decision=AuthorizationDecision.AUTHORIZATION_ERROR,
                        reason=f"ArmorIQ returned unexpected HTTP {response.status_code}.",
                        is_live=True,
                    )

        except httpx.TimeoutException:
            return AuthorizationResult(
                decision=AuthorizationDecision.AUTHORIZATION_TIMEOUT,
                reason="ArmorIQ authorization request timed out.",
                is_live=False,
            )
        except httpx.ConnectError:
            return AuthorizationResult(
                decision=AuthorizationDecision.AUTHORIZATION_TIMEOUT,
                reason="Failed to connect to ArmorIQ endpoint.",
                is_live=False,
            )
        except Exception as e:
            return AuthorizationResult(
                decision=AuthorizationDecision.AUTHORIZATION_ERROR,
                reason=f"Unexpected error during ArmorIQ request: {str(e)}",
                is_live=False,
            )

    async def health_check(self) -> Dict[str, Any]:
        """Check ArmorIQ service health."""
        if not self.is_configured:
            return {"status": "unconfigured", "message": "API key not set."}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.endpoint}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return {"status": "reachable", "http_status": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
