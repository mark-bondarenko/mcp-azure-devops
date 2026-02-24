"""
Build tools for Azure DevOps.

This module provides MCP tools for interacting with Azure DevOps builds.
"""
from typing import Optional, List

from azure.devops.v7_1.build.build_client import BuildClient
from mcp.server.fastmcp import FastMCP

from mcp_azure_devops.features.builds.common import (
    AzureDevOpsClientError,
    get_build_client,
)


def _get_builds_impl(
    build_client: BuildClient,
    project: str,
    definitions: Optional[List[int]] = None,
    branch_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    result_filter: Optional[str] = None,
    top: int = 10,
    repository_id: Optional[str] = None,
) -> str:
    """
    Implementation of builds retrieval.

    Args:
        build_client: Build client
        project: Azure DevOps project name
        definitions: List of build definition IDs to filter by (optional)
        branch_name: Filter by source branch name (optional)
        status_filter: Filter by build status (optional)
        result_filter: Filter by build result (optional)
        top: Maximum number of builds to return (default: 10)
        repository_id: Filter by repository ID (optional)

    Returns:
        Formatted string containing build information
    """
    try:
        builds = build_client.get_builds(
            project=project,
            definitions=definitions,
            branch_name=branch_name,
            status_filter=status_filter,
            result_filter=result_filter,
            top=top,
            repository_id=repository_id,
        )

        if not builds:
            return "No builds found."

        lines = []
        for build in builds:
            lines.append(f"# Build {build.id}: {build.build_number}")
            if hasattr(build, "definition") and build.definition:
                lines.append(f"Definition: {build.definition.name}")
            if hasattr(build, "status") and build.status:
                lines.append(f"Status: {build.status}")
            if hasattr(build, "result") and build.result:
                lines.append(f"Result: {build.result}")
            if hasattr(build, "source_branch") and build.source_branch:
                lines.append(f"Source Branch: {build.source_branch}")
            if hasattr(build, "queue_time") and build.queue_time:
                lines.append(f"Queue Time: {build.queue_time}")
            if hasattr(build, "finish_time") and build.finish_time:
                lines.append(f"Finish Time: {build.finish_time}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving builds: {str(e)}"


def _get_build_status_impl(
    build_client: BuildClient,
    project: str,
    build_id: int,
) -> str:
    """
    Implementation of build status retrieval.

    Args:
        build_client: Build client
        project: Azure DevOps project name
        build_id: ID of the build

    Returns:
        Formatted string containing build status and details
    """
    try:
        build = build_client.get_build(
            project=project, build_id=build_id
        )

        if not build:
            return f"Build {build_id} not found."

        lines = [f"# Build {build.id}: {build.build_number}"]
        if hasattr(build, "definition") and build.definition:
            lines.append(f"Definition: {build.definition.name}")
        if hasattr(build, "status") and build.status:
            lines.append(f"Status: {build.status}")
        if hasattr(build, "result") and build.result:
            lines.append(f"Result: {build.result}")
        if hasattr(build, "source_branch") and build.source_branch:
            lines.append(f"Source Branch: {build.source_branch}")
        if hasattr(build, "source_version") and build.source_version:
            lines.append(f"Source Version: {build.source_version}")
        if hasattr(build, "queue_time") and build.queue_time:
            lines.append(f"Queue Time: {build.queue_time}")
        if hasattr(build, "finish_time") and build.finish_time:
            lines.append(f"Finish Time: {build.finish_time}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving build {build_id}: {str(e)}"


def _get_build_log_impl(
    build_client: BuildClient,
    project: str,
    build_id: int,
) -> str:
    """
    Implementation of build log listing.

    Args:
        build_client: Build client
        project: Azure DevOps project name
        build_id: ID of the build

    Returns:
        Formatted string listing all log entries
    """
    try:
        logs = build_client.get_build_logs(
            project=project, build_id=build_id
        )

        if not logs:
            return f"No logs found for build {build_id}."

        lines = [f"# Logs for Build {build_id}"]
        for log in logs:
            lines.append(f"## Log ID: {log.id}")
            if hasattr(log, "type") and log.type:
                lines.append(f"Type: {log.type}")
            if hasattr(log, "created_on") and log.created_on:
                lines.append(f"Created: {log.created_on}")
            if (
                hasattr(log, "last_changed_on")
                and log.last_changed_on
            ):
                lines.append(
                    f"Last Changed: {log.last_changed_on}"
                )
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving logs for build {build_id}: {str(e)}"


def _get_build_log_by_id_impl(
    build_client: BuildClient,
    project: str,
    build_id: int,
    log_id: int,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> str:
    """
    Implementation of build log content retrieval.

    Args:
        build_client: Build client
        project: Azure DevOps project name
        build_id: ID of the build
        log_id: ID of the log entry
        start_line: Starting line number (optional)
        end_line: Ending line number (optional)

    Returns:
        Formatted string containing log content
    """
    try:
        log_lines = build_client.get_build_log_lines(
            project=project,
            build_id=build_id,
            log_id=log_id,
            start_line=start_line,
            end_line=end_line,
        )

        if not log_lines:
            return (
                f"No content found for log {log_id} "
                f"in build {build_id}."
            )

        return "\n".join(log_lines)
    except Exception as e:
        return (
            f"Error retrieving log {log_id} "
            f"for build {build_id}: {str(e)}"
        )


def register_tools(mcp: FastMCP) -> None:
    """
    Register build tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    def get_builds(
        project: str,
        definitions: Optional[List[int]] = None,
        branch_name: Optional[str] = None,
        status_filter: Optional[str] = None,
        result_filter: Optional[str] = None,
        top: int = 10,
        repository_id: Optional[str] = None,
    ) -> str:
        """
        Retrieves a list of builds for an Azure DevOps project.

        Use this tool when you need to:
        - List recent builds for a project or pipeline
        - Filter builds by status, result, or branch
        - Find builds for a specific repository or definition

        Args:
            project: Azure DevOps project name
            definitions: List of build definition IDs to filter by
                (optional)
            branch_name: Filter by source branch name (optional)
            status_filter: Filter by status (inProgress, completed,
                cancelling, postponed, notStarted, all) (optional)
            result_filter: Filter by result (succeeded,
                partiallySucceeded, failed, canceled) (optional)
            top: Maximum number of builds to return (default: 10)
            repository_id: Filter by repository ID (optional)

        Returns:
            Formatted string containing build information
        """
        try:
            build_client = get_build_client()
            return _get_builds_impl(
                build_client=build_client,
                project=project,
                definitions=definitions,
                branch_name=branch_name,
                status_filter=status_filter,
                result_filter=result_filter,
                top=top,
                repository_id=repository_id,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_build_status(
        project: str,
        build_id: int,
    ) -> str:
        """
        Retrieves the status and details of a specific build.

        Use this tool when you need to:
        - Check if a build succeeded or failed
        - Get the source branch and commit for a build
        - Find when a build started and finished

        Args:
            project: Azure DevOps project name
            build_id: ID of the build

        Returns:
            Formatted string containing build status and details
        """
        try:
            build_client = get_build_client()
            return _get_build_status_impl(
                build_client=build_client,
                project=project,
                build_id=build_id,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_build_log(
        project: str,
        build_id: int,
    ) -> str:
        """
        Retrieves the list of log entries for a specific build.

        Use this tool when you need to:
        - See what log entries are available for a build
        - Find log IDs to retrieve specific log content
        - Check when each build step was executed

        Args:
            project: Azure DevOps project name
            build_id: ID of the build

        Returns:
            Formatted string listing all log entries with their IDs
            and timestamps
        """
        try:
            build_client = get_build_client()
            return _get_build_log_impl(
                build_client=build_client,
                project=project,
                build_id=build_id,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    def get_build_log_by_id(
        project: str,
        build_id: int,
        log_id: int,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
    ) -> str:
        """
        Retrieves the content of a specific build log entry.

        Use this tool when you need to:
        - Read the output of a specific build step
        - Diagnose build failures by examining log output
        - Extract specific lines from a build log

        Args:
            project: Azure DevOps project name
            build_id: ID of the build
            log_id: ID of the log entry (use get_build_log to find IDs)
            start_line: Starting line number (optional, 0-indexed)
            end_line: Ending line number (optional, inclusive)

        Returns:
            Formatted string containing the log content
        """
        try:
            build_client = get_build_client()
            return _get_build_log_by_id_impl(
                build_client=build_client,
                project=project,
                build_id=build_id,
                log_id=log_id,
                start_line=start_line,
                end_line=end_line,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
