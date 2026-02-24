# Azure DevOps MCP features package
from mcp_azure_devops.features import (
    builds,
    code_search,
    projects,
    pull_requests,
    repositories,
    teams,
    work_items,
)


def register_all(mcp):
    """
    Register all features with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """
    work_items.register(mcp)
    projects.register(mcp)
    teams.register(mcp)
    code_search.register(mcp)
    pull_requests.register(mcp)
    builds.register(mcp)
    repositories.register(mcp)
