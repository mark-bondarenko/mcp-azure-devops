"""
Repository tools for Azure DevOps.

This module provides MCP tools for managing Git branches.
"""
from typing import Optional

from azure.devops.v7_1.git.git_client import GitClient
from mcp.server.fastmcp import FastMCP

from mcp_azure_devops.features.repositories.common import (
    AzureDevOpsClientError,
    get_git_client,
)

_ZERO_OID = "0000000000000000000000000000000000000000"


def _list_branches_impl(
    git_client: GitClient,
    project: str,
    repository: str,
    filter_contains: Optional[str] = None,
    top: int = 100,
) -> str:
    """
    Implementation of branch listing.

    Args:
        git_client: Git client
        project: Azure DevOps project name
        repository: Azure DevOps repository name
        filter_contains: Optional string to filter branch names (optional)
        top: Maximum number of branches to return (default: 100)

    Returns:
        Formatted string listing branch names and their commit IDs
    """
    try:
        refs = git_client.get_refs(
            repository_id=repository,
            project=project,
            filter="heads/",
            filter_contains=filter_contains,
        )

        if not refs:
            return f"No branches found in repository '{repository}'."

        branches = []
        for ref in refs:
            name = ref.name or ""
            if name.startswith("refs/heads/"):
                name = name[len("refs/heads/"):]
            branches.append((name, ref))

        branches.sort(key=lambda x: x[0], reverse=True)
        branches = branches[:top]

        lines = [f"# Branches in {repository}"]
        for name, ref in branches:
            commit_id = (
                ref.object_id
                if hasattr(ref, "object_id")
                else "?"
            )
            lines.append(f"- {name} (commit: {commit_id})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing branches: {str(e)}"


def _create_branch_impl(
    git_client: GitClient,
    project: str,
    repository: str,
    branch_name: str,
    source_branch: str = "main",
    source_commit_id: Optional[str] = None,
) -> str:
    """
    Implementation of branch creation.

    Args:
        git_client: Git client
        project: Azure DevOps project name
        repository: Azure DevOps repository name
        branch_name: Name for the new branch
        source_branch: Source branch to create from (default: "main")
        source_commit_id: Specific commit ID to branch from (optional)

    Returns:
        Formatted string confirming branch creation or describing error
    """
    try:
        commit_id = source_commit_id
        if not commit_id:
            refs = git_client.get_refs(
                repository_id=repository,
                project=project,
                filter=f"heads/{source_branch}",
            )
            if not refs:
                return (
                    f"Source branch '{source_branch}' not found."
                )
            commit_id = refs[0].object_id

        ref_update = {
            "name": f"refs/heads/{branch_name}",
            "newObjectId": commit_id,
            "oldObjectId": _ZERO_OID,
        }

        results = git_client.update_refs(
            ref_updates=[ref_update],
            repository_id=repository,
            project=project,
        )

        if results and len(results) > 0:
            result = results[0]
            success = getattr(result, "success", True)
            if not success:
                custom_message = getattr(
                    result, "custom_message", ""
                )
                return (
                    f"Failed to create branch '{branch_name}': "
                    f"{custom_message}"
                )

        return (
            f"Branch '{branch_name}' created successfully from "
            f"'{source_branch}' (commit: {commit_id})."
        )
    except Exception as e:
        return f"Error creating branch '{branch_name}': {str(e)}"


def _delete_branch_impl(
    git_client: GitClient,
    project: str,
    repository: str,
    branch_name: str,
) -> str:
    """
    Implementation of branch deletion.

    Args:
        git_client: Git client
        project: Azure DevOps project name
        repository: Azure DevOps repository name
        branch_name: Name of the branch to delete

    Returns:
        Formatted string confirming deletion or describing error
    """
    try:
        refs = git_client.get_refs(
            repository_id=repository,
            project=project,
            filter=f"heads/{branch_name}",
        )

        if not refs:
            return (
                f"Branch '{branch_name}' not found in "
                f"repository '{repository}'."
            )

        current_commit_id = refs[0].object_id

        ref_update = {
            "name": f"refs/heads/{branch_name}",
            "newObjectId": _ZERO_OID,
            "oldObjectId": current_commit_id,
        }

        results = git_client.update_refs(
            ref_updates=[ref_update],
            repository_id=repository,
            project=project,
        )

        if results and len(results) > 0:
            result = results[0]
            success = getattr(result, "success", True)
            if not success:
                custom_message = getattr(
                    result, "custom_message", ""
                )
                return (
                    f"Failed to delete branch '{branch_name}': "
                    f"{custom_message}"
                )

        return f"Branch '{branch_name}' deleted successfully."
    except Exception as e:
        return f"Error deleting branch '{branch_name}': {str(e)}"


def register_tools(mcp: FastMCP) -> None:
    """
    Register repository tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    def list_branches(
        project: str,
        repository: str,
        filter_contains: Optional[str] = None,
        top: int = 100,
    ) -> str:
        """
        Lists branches in an Azure DevOps repository.

        Use this tool when you need to:
        - See all branches in a repository
        - Find branches matching a specific pattern
        - Check what branches exist before creating a new one

        Args:
            project: Azure DevOps project name
            repository: Azure DevOps repository name
            filter_contains: Optional filter to match branches
                containing this string (optional)
            top: Maximum number of branches to return (default: 100)

        Returns:
            Formatted string listing branch names and their latest
            commit IDs
        """
        try:
            git_client = get_git_client()
            return _list_branches_impl(
                git_client=git_client,
                project=project,
                repository=repository,
                filter_contains=filter_contains,
                top=top,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def create_branch(
        project: str,
        repository: str,
        branch_name: str,
        source_branch: str = "main",
        source_commit_id: Optional[str] = None,
    ) -> str:
        """
        Creates a new branch in an Azure DevOps repository.

        Use this tool when you need to:
        - Create a feature branch from an existing branch
        - Start a new branch from a specific commit
        - Set up a branch for a new work item or PR

        Args:
            project: Azure DevOps project name
            repository: Azure DevOps repository name
            branch_name: Name for the new branch
            source_branch: Source branch to create from
                (default: "main")
            source_commit_id: Specific commit ID to branch from
                (optional, overrides source_branch)

        Returns:
            Formatted string confirming branch creation or describing
            the error
        """
        try:
            git_client = get_git_client()
            return _create_branch_impl(
                git_client=git_client,
                project=project,
                repository=repository,
                branch_name=branch_name,
                source_branch=source_branch,
                source_commit_id=source_commit_id,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def delete_branch(
        project: str,
        repository: str,
        branch_name: str,
    ) -> str:
        """
        Deletes a branch from an Azure DevOps repository.

        Use this tool when you need to:
        - Remove a feature branch after merging
        - Clean up stale or unused branches
        - Delete a branch that was created by mistake

        IMPORTANT: This action is irreversible. Ensure the branch has
        been merged or its commits are accessible via another branch
        before deleting.

        Args:
            project: Azure DevOps project name
            repository: Azure DevOps repository name
            branch_name: Name of the branch to delete

        Returns:
            Formatted string confirming deletion or describing the
            error
        """
        try:
            git_client = get_git_client()
            return _delete_branch_impl(
                git_client=git_client,
                project=project,
                repository=repository,
                branch_name=branch_name,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
