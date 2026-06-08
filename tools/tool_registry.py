from tools.mcp_client import call_mcp_tool


def call_tool(tool_name: str, args: dict) -> dict:
    """
    Orchestrator calls tools through MCP servers.
    """
    return call_mcp_tool(tool_name, args)
