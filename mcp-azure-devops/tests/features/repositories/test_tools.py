from unittest.mock import MagicMock, call

from mcp_azure_devops.features.repositories.tools import (
    _list_branches_impl,
    _create_branch_impl,
    _delete_branch_impl,
    _ZERO_OID,
)


def _make_ref(name, object_id="abc123"):
    ref = MagicMock()
    ref.name = name
    ref.object_id = object_id
    return ref


# ── list_branches ─────────────────────────────────────────────────────────────

def test_list_branches_strips_prefix():
    """refs/heads/ prefix is stripped from branch names."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = [
        _make_ref("refs/heads/main", "aaa"),
        _make_ref("refs/heads/feature/x", "bbb"),
    ]

    result = _list_branches_impl(mock_git, "proj", "repo")

    assert "main" in result
    assert "feature/x" in result
    assert "refs/heads/" not in result


def test_list_branches_no_branches():
    """Empty refs returns appropriate message."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = []

    result = _list_branches_impl(mock_git, "proj", "repo")

    assert "No branches found" in result
    assert "repo" in result


def test_list_branches_applies_top_limit():
    """top parameter limits the number of branches returned."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = [
        _make_ref(f"refs/heads/branch-{i}") for i in range(10)
    ]

    result = _list_branches_impl(mock_git, "proj", "repo", top=3)

    # Only 3 branches should appear
    branch_lines = [l for l in result.split("\n") if l.startswith("- ")]
    assert len(branch_lines) == 3


def test_list_branches_api_error():
    """API errors return formatted error string."""
    mock_git = MagicMock()
    mock_git.get_refs.side_effect = Exception("Not found")

    result = _list_branches_impl(mock_git, "proj", "repo")

    assert "Error listing branches" in result
    assert "Not found" in result


# ── create_branch ─────────────────────────────────────────────────────────────

def test_create_branch_with_explicit_commit():
    """Branch is created from explicit commit ID without extra get_refs call."""
    mock_git = MagicMock()
    mock_git.update_refs.return_value = [MagicMock(success=True)]

    result = _create_branch_impl(
        mock_git, "proj", "repo",
        branch_name="feature/new",
        source_commit_id="deadbeef" * 5,
    )

    mock_git.get_refs.assert_not_called()
    call_args = mock_git.update_refs.call_args[1]
    ref_update = call_args["ref_updates"][0]
    assert ref_update["name"] == "refs/heads/feature/new"
    assert ref_update["newObjectId"] == "deadbeef" * 5
    assert ref_update["oldObjectId"] == _ZERO_OID
    assert "created successfully" in result


def test_create_branch_resolves_source_branch():
    """Without commit ID, source branch is resolved via get_refs."""
    mock_git = MagicMock()
    source_ref = _make_ref("refs/heads/main", "cafebabe" * 5)
    mock_git.get_refs.return_value = [source_ref]
    mock_git.update_refs.return_value = [MagicMock(success=True)]

    result = _create_branch_impl(
        mock_git, "proj", "repo",
        branch_name="feature/from-main",
        source_branch="main",
    )

    assert "cafebabe" * 5 in result or "created successfully" in result


def test_create_branch_source_not_found():
    """Returns error message when source branch does not exist."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = []

    result = _create_branch_impl(
        mock_git, "proj", "repo",
        branch_name="new-branch",
        source_branch="nonexistent",
    )

    assert "not found" in result
    assert "nonexistent" in result


def test_create_branch_api_error():
    """API errors are returned as error strings."""
    mock_git = MagicMock()
    mock_git.get_refs.side_effect = Exception("Permission denied")

    result = _create_branch_impl(
        mock_git, "proj", "repo", "new-branch"
    )

    assert "Error creating branch" in result
    assert "Permission denied" in result


# ── delete_branch ─────────────────────────────────────────────────────────────

def test_delete_branch_sends_zero_oid():
    """delete_branch sends zero OID as new_object_id."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = [
        _make_ref("refs/heads/old-feature", "1234abcd" * 5)
    ]
    mock_git.update_refs.return_value = [MagicMock(success=True)]

    result = _delete_branch_impl(
        mock_git, "proj", "repo", "old-feature"
    )

    call_args = mock_git.update_refs.call_args[1]
    ref_update = call_args["ref_updates"][0]
    assert ref_update["name"] == "refs/heads/old-feature"
    assert ref_update["newObjectId"] == _ZERO_OID
    assert ref_update["oldObjectId"] == "1234abcd" * 5
    assert "deleted successfully" in result


def test_delete_branch_not_found():
    """Returns error message when branch does not exist."""
    mock_git = MagicMock()
    mock_git.get_refs.return_value = []

    result = _delete_branch_impl(
        mock_git, "proj", "repo", "ghost-branch"
    )

    assert "not found" in result
    assert "ghost-branch" in result


def test_delete_branch_api_error():
    """API errors are returned as error strings."""
    mock_git = MagicMock()
    mock_git.get_refs.side_effect = Exception("Server error")

    result = _delete_branch_impl(
        mock_git, "proj", "repo", "my-branch"
    )

    assert "Error deleting branch" in result
    assert "Server error" in result
