from unittest.mock import MagicMock

from mcp_azure_devops.features.builds.tools import (
    _get_builds_impl,
    _get_build_status_impl,
    _get_build_log_impl,
    _get_build_log_by_id_impl,
)


def _make_build(build_id, build_number, status="completed",
                result="succeeded", source_branch="refs/heads/main"):
    build = MagicMock()
    build.id = build_id
    build.build_number = build_number
    build.status = status
    build.result = result
    build.source_branch = source_branch
    build.queue_time = "2024-01-01T10:00:00Z"
    build.finish_time = "2024-01-01T10:05:00Z"
    defn = MagicMock()
    defn.name = "CI Pipeline"
    build.definition = defn
    return build


# Tests for _get_builds_impl

def test_get_builds_returns_builds():
    """Builds are returned and formatted correctly."""
    mock_client = MagicMock()
    mock_client.get_builds.return_value = [
        _make_build(1, "20240101.1"),
        _make_build(2, "20240101.2", status="inProgress", result=None),
    ]

    result = _get_builds_impl(mock_client, "MyProject")

    assert "Build 1" in result
    assert "20240101.1" in result
    assert "CI Pipeline" in result
    assert "Build 2" in result
    assert "20240101.2" in result


def test_get_builds_no_results():
    """Empty builds list returns appropriate message."""
    mock_client = MagicMock()
    mock_client.get_builds.return_value = []

    result = _get_builds_impl(mock_client, "MyProject")

    assert "No builds found" in result


def test_get_builds_api_error():
    """API errors are returned as error strings."""
    mock_client = MagicMock()
    mock_client.get_builds.side_effect = Exception("Network error")

    result = _get_builds_impl(mock_client, "MyProject")

    assert "Error retrieving builds" in result
    assert "Network error" in result


def test_get_builds_forwards_filters():
    """Filter parameters are forwarded to the client."""
    mock_client = MagicMock()
    mock_client.get_builds.return_value = []

    _get_builds_impl(
        mock_client,
        project="P",
        definitions=[42],
        branch_name="refs/heads/main",
        status_filter="completed",
        result_filter="succeeded",
        top=5,
        repository_id="repo-123",
    )

    mock_client.get_builds.assert_called_once_with(
        project="P",
        definitions=[42],
        branch_name="refs/heads/main",
        status_filter="completed",
        result_filter="succeeded",
        top=5,
        repository_id="repo-123",
    )


# Tests for _get_build_status_impl

def test_get_build_status_success():
    """Build status details are formatted correctly."""
    mock_client = MagicMock()
    mock_client.get_build.return_value = _make_build(
        42, "20240101.42", source_branch="refs/heads/feature/x"
    )

    result = _get_build_status_impl(mock_client, "MyProject", 42)

    assert "Build 42" in result
    assert "20240101.42" in result
    assert "completed" in result
    assert "succeeded" in result
    assert "refs/heads/feature/x" in result


def test_get_build_status_not_found():
    """None return from client returns not-found message."""
    mock_client = MagicMock()
    mock_client.get_build.return_value = None

    result = _get_build_status_impl(mock_client, "MyProject", 99)

    assert "not found" in result
    assert "99" in result


def test_get_build_status_api_error():
    """API errors are returned as error strings."""
    mock_client = MagicMock()
    mock_client.get_build.side_effect = Exception("Timeout")

    result = _get_build_status_impl(mock_client, "MyProject", 5)

    assert "Error retrieving build" in result
    assert "5" in result
    assert "Timeout" in result


# Tests for _get_build_log_impl

def test_get_build_log_returns_entries():
    """Log entries are returned and formatted."""
    mock_client = MagicMock()
    log1 = MagicMock()
    log1.id = 1
    log1.type = "Task"
    log1.created_on = "2024-01-01T10:00:00Z"
    log1.last_changed_on = "2024-01-01T10:01:00Z"
    mock_client.get_build_logs.return_value = [log1]

    result = _get_build_log_impl(mock_client, "MyProject", 10)

    assert "Log ID: 1" in result
    assert "Task" in result


def test_get_build_log_no_logs():
    """Empty logs list returns appropriate message."""
    mock_client = MagicMock()
    mock_client.get_build_logs.return_value = []

    result = _get_build_log_impl(mock_client, "MyProject", 10)

    assert "No logs found" in result
    assert "10" in result


def test_get_build_log_api_error():
    """API errors are returned as error strings."""
    mock_client = MagicMock()
    mock_client.get_build_logs.side_effect = Exception("Forbidden")

    result = _get_build_log_impl(mock_client, "MyProject", 7)

    assert "Error retrieving logs" in result
    assert "7" in result
    assert "Forbidden" in result


# Tests for _get_build_log_by_id_impl

def test_get_build_log_by_id_returns_lines():
    """Log lines are returned as text."""
    mock_client = MagicMock()
    mock_client.get_build_log_lines.return_value = [
        "Step 1: start",
        "Step 2: done",
    ]

    result = _get_build_log_by_id_impl(mock_client, "P", 10, 3)

    assert "Step 1: start" in result
    assert "Step 2: done" in result


def test_get_build_log_by_id_empty():
    """Empty log lines return appropriate message."""
    mock_client = MagicMock()
    mock_client.get_build_log_lines.return_value = []

    result = _get_build_log_by_id_impl(mock_client, "P", 10, 3)

    assert "No content found" in result


def test_get_build_log_by_id_api_error():
    """API errors are returned as error strings."""
    mock_client = MagicMock()
    mock_client.get_build_log_lines.side_effect = Exception("Not found")

    result = _get_build_log_by_id_impl(mock_client, "P", 10, 99)

    assert "Error retrieving log" in result
    assert "99" in result


def test_get_build_log_by_id_forwards_line_range():
    """start_line and end_line are forwarded to the client."""
    mock_client = MagicMock()
    mock_client.get_build_log_lines.return_value = ["line"]

    _get_build_log_by_id_impl(
        mock_client, "P", 10, 3,
        start_line=5, end_line=20,
    )

    mock_client.get_build_log_lines.assert_called_once_with(
        project="P",
        build_id=10,
        log_id=3,
        start_line=5,
        end_line=20,
    )
