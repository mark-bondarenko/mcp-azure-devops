"""
Builds feature for Azure DevOps MCP server.
"""
from mcp_azure_devops.features.builds import tools


def register(mcp) -> None:
    """
    Register build components with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """
    tools.register_tools(mcp)
