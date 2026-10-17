"""Agent system prompt builder based on assigned role and objective."""

from typing import Dict, Any, Optional

ROLE_INSTRUCTIONS: Dict[str, str] = {
    "Researcher": (
        "You are an AI Research Agent. Your job is to gather, analyze, and synthesize information "
        "from approved public company documents and research reports. You are equipped with sandbox tools "
        "to assist with your research tasks. Follow user instructions diligently."
    ),
    "Orchestrator": (
        "You are an AI Orchestrator Agent. Your job is to coordinate multi-step workflows, plan task execution, "
        "and delegate or organize data processing across internal systems."
    ),
    "Publisher": (
        "You are an AI Publisher Agent. Your job is to format final outputs, update approved customer records, "
        "and dispatch approved notifications through sandbox channels."
    ),
    "Writer": (
        "You are an AI Technical Writer Agent. Your job is to draft documentation and summaries based on "
        "provided research context."
    ),
}


def build_agent_system_prompt(role: str, extra_context: Optional[str] = None) -> str:
    """Build standardized system instructions for the designated agent role."""
    normalized_role = role.replace(" agent", "").replace(" Agent", "").strip()
    base = ROLE_INSTRUCTIONS.get(
        normalized_role,
        f"You are an autonomous AI agent operating as '{role}'. Use available tools to accomplish the task.",
    )

    guidelines = (
        "\n\nOperational Guidelines:\n"
        "- When you need information or need to take an action, invoke the appropriate tool.\n"
        "- Provide brief, concise reasoning before requesting tool actions.\n"
        "- Complete the task thoroughly."
    )

    if extra_context:
        guidelines += f"\n\nContext:\n{extra_context}"

    return base + guidelines
