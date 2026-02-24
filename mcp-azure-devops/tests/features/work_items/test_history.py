from unittest.mock import MagicMock

from mcp_azure_devops.features.work_items.tools.history import (
    _get_work_item_history_impl,
)


def _make_revision(rev, state, assigned_to_name, changed_by, changed_date):
    """Helper to build a mock revision object."""
    mock_revision = MagicMock()
    mock_revision.rev = rev
    mock_revision.fields = {
        "System.State": state,
        "System.AssignedTo": {"displayName": assigned_to_name},
        "System.ChangedBy": {"displayName": changed_by},
        "System.ChangedDate": changed_date,
    }
    return mock_revision


def test_history_includes_state_changes():
    """Revisions where state changed should appear in output."""
    mock_client = MagicMock()
    rev1 = _make_revision(1, "New", "Alice", "Bob", "2024-01-01")
    rev2 = _make_revision(2, "Active", "Alice", "Bob", "2024-01-02")
    mock_client.get_revisions.return_value = [rev1, rev2]

    result = _get_work_item_history_impl(mock_client, 42)

    assert "Revision 1" in result
    assert "Revision 2" in result
    assert "New" in result
    assert "Active" in result


def test_history_filters_unchanged_revisions():
    """Revisions with no state or assignee change should be excluded."""
    mock_client = MagicMock()
    rev1 = _make_revision(1, "Active", "Alice", "Bob", "2024-01-01")
    rev2 = _make_revision(2, "Active", "Alice", "Bob", "2024-01-02")
    mock_client.get_revisions.return_value = [rev1, rev2]

    result = _get_work_item_history_impl(mock_client, 42)

    # Only rev1 should be included (first revision always included)
    assert "Revision 1" in result
    assert "Revision 2" not in result


def test_history_includes_assignee_changes():
    """Revisions where assignee changed should appear in output."""
    mock_client = MagicMock()
    rev1 = _make_revision(1, "Active", "Alice", "Bob", "2024-01-01")
    rev2 = _make_revision(2, "Active", "Charlie", "Bob", "2024-01-02")
    mock_client.get_revisions.return_value = [rev1, rev2]

    result = _get_work_item_history_impl(mock_client, 42)

    assert "Revision 1" in result
    assert "Revision 2" in result
    assert "Alice" in result
    assert "Charlie" in result


def test_history_empty_returns_message():
    """Empty revision list returns appropriate message."""
    mock_client = MagicMock()
    mock_client.get_revisions.return_value = []

    result = _get_work_item_history_impl(mock_client, 42)

    assert "No revision history found" in result
    assert "42" in result


def test_history_api_error_returns_error_string():
    """API errors are returned as formatted error strings."""
    mock_client = MagicMock()
    mock_client.get_revisions.side_effect = Exception("Connection failed")

    result = _get_work_item_history_impl(mock_client, 42)

    assert "Error retrieving history" in result
    assert "42" in result
    assert "Connection failed" in result


def test_history_header_contains_work_item_id():
    """Output header contains the work item ID."""
    mock_client = MagicMock()
    rev = _make_revision(1, "New", "Alice", "Bob", "2024-01-01")
    mock_client.get_revisions.return_value = [rev]

    result = _get_work_item_history_impl(mock_client, 99)

    assert "99" in result


def test_history_passes_top_and_skip_to_client():
    """top and skip parameters are forwarded to the client."""
    mock_client = MagicMock()
    mock_client.get_revisions.return_value = []

    _get_work_item_history_impl(
        mock_client, 10, project="MyProject", top=5, skip=2
    )

    mock_client.get_revisions.assert_called_once_with(
        id=10,
        top=5,
        skip=2,
        expand="all",
        project="MyProject",
    )
