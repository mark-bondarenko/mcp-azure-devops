"""
Work item history tools for Azure DevOps.

This module provides MCP tools for retrieving work item revision history.
"""
from typing import Optional

from azure.devops.v7_1.work_item_tracking import WorkItemTrackingClient

from mcp_azure_devops.features.work_items.common import (
    AzureDevOpsClientError,
    get_work_item_client,
)


def _get_work_item_history_impl(
    wit_client: WorkItemTrackingClient,
    work_item_id: int,
    project: Optional[str] = None,
    top: int = 50,
    skip: int = 0,
) -> str:
    """
    Implementation of work item revision history retrieval.

    Args:
        wit_client: Work item tracking client
        work_item_id: ID of the work item
        project: Azure DevOps project name (optional)
        top: Maximum number of revisions to return (default: 50)
        skip: Number of revisions to skip (default: 0)

    Returns:
        Formatted string containing work item revision history
    """
    try:
        revisions = wit_client.get_revisions(
            id=work_item_id,
            top=top,
            skip=skip,
            expand="all",
            project=project,
        )

        if not revisions:
            return (
                f"No revision history found for work item {work_item_id}."
            )

        lines = [f"# Revision History for Work Item {work_item_id}"]

        prev_state = None
        prev_assigned_to = None

        included = []
        for revision in revisions:
            fields = revision.fields or {}
            state = fields.get("System.State")
            assigned_to_raw = fields.get("System.AssignedTo")
            if isinstance(assigned_to_raw, dict):
                assigned_to = assigned_to_raw.get("displayName", "")
            else:
                assigned_to = assigned_to_raw or ""

            state_changed = state != prev_state
            assignee_changed = assigned_to != prev_assigned_to

            if state_changed or assignee_changed or prev_state is None:
                included.append((revision, fields, state, assigned_to))

            prev_state = state
            prev_assigned_to = assigned_to

        if not included:
            return (
                f"No significant changes found in revision history "
                f"for work item {work_item_id}."
            )

        for revision, fields, state, assigned_to in included:
            changed_date = fields.get(
                "System.ChangedDate", "Unknown date"
            )
            changed_by_raw = fields.get("System.ChangedBy")
            if isinstance(changed_by_raw, dict):
                changed_by = changed_by_raw.get(
                    "displayName", "Unknown"
                )
            else:
                changed_by = changed_by_raw or "Unknown"

            rev_num = getattr(revision, "rev", "?")
            lines.append(f"\n## Revision {rev_num}")
            lines.append(f"Changed By: {changed_by}")
            lines.append(f"Changed Date: {changed_date}")
            if state:
                lines.append(f"State: {state}")
            if assigned_to:
                lines.append(f"Assigned To: {assigned_to}")

        return "\n".join(lines)
    except Exception as e:
        return (
            f"Error retrieving history for work item "
            f"{work_item_id}: {str(e)}"
        )


def register_tools(mcp) -> None:
    """
    Register work item history tools with the MCP server.

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    def get_work_item_history(
        id: int,
        project: Optional[str] = None,
        top: int = 50,
        skip: int = 0,
    ) -> str:
        """
        Retrieves the revision history of a work item showing state
        and assignee changes.

        Use this tool when you need to:
        - See how a work item's state has changed over time
        - Track who was assigned to a work item and when
        - Audit the history of a bug, task, or user story
        - Understand the progression of a work item through its lifecycle

        Args:
            id: The work item ID
            project: Azure DevOps project name (optional)
            top: Maximum number of revisions to return (default: 50)
            skip: Number of revisions to skip for pagination (default: 0)

        Returns:
            Formatted string containing revision history with state and
            assignee changes, filtered to show only meaningful changes
        """
        try:
            wit_client = get_work_item_client()
            return _get_work_item_history_impl(
                wit_client=wit_client,
                work_item_id=id,
                project=project,
                top=top,
                skip=skip,
            )
        except AzureDevOpsClientError as e:
            return f"Error: {str(e)}"
