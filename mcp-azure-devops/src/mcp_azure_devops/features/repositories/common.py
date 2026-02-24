"""
Common utilities for Azure DevOps repository features.

Re-exports the Git client from pull_requests to avoid duplicating
connection logic.
"""
from mcp_azure_devops.features.pull_requests.common import (
    AzureDevOpsClientError,
    get_git_client,
)

__all__ = ["AzureDevOpsClientError", "get_git_client"]
