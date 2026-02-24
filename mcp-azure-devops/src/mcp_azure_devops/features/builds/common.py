"""
Common utilities for Azure DevOps build features.
"""
from azure.devops.v7_1.build.build_client import BuildClient

from mcp_azure_devops.utils.azure_client import get_connection


class AzureDevOpsClientError(Exception):
    """Exception raised for errors in Azure DevOps client operations."""
    pass


def get_build_client() -> BuildClient:
    """
    Get the build client for Azure DevOps.

    Returns:
        BuildClient instance

    Raises:
        AzureDevOpsClientError: If connection or client creation fails
    """
    connection = get_connection()

    if not connection:
        raise AzureDevOpsClientError(
            "Azure DevOps PAT or organization URL not found in "
            "environment variables."
        )

    build_client = connection.clients_v7_1.get_build_client()

    if build_client is None:
        raise AzureDevOpsClientError("Failed to get build client.")

    return build_client
