from unittest.mock import MagicMock, patch

from mcp_azure_devops.features.pull_requests.tools import (
    _format_pull_request,
    _get_pr_changed_files_impl,
    _get_pr_policy_evaluations_impl,
    _approve_with_suggestions_pull_request_impl,
    _wait_for_author_pull_request_impl,
    _reset_pull_request_vote_impl,
    _restart_pr_merge_impl,
)


# ── Policy evaluations ────────────────────────────────────────────────────────

def _make_evaluation(type_name, status, build_def=None, build_id=None):
    evaluation = MagicMock()
    evaluation.status = status

    ptype = MagicMock()
    ptype.display_name = type_name

    config = MagicMock()
    config.type = ptype
    evaluation.configuration = config

    if build_def or build_id:
        # Use camelCase attribute names to match JSON keys from ADO API,
        # which is what the implementation checks first.
        ctx = MagicMock(spec=["buildDefinitionName", "buildId"])
        ctx.buildDefinitionName = build_def
        ctx.buildId = build_id
        evaluation.context = ctx
    else:
        evaluation.context = None

    return evaluation


def test_policy_evaluations_success():
    """Policy evaluations are formatted with name and status."""
    mock_git = MagicMock()
    mock_policy = MagicMock()

    pr = MagicMock()
    pr.artifact_id = "vstfs:///CodeReview/CodeReviewId/proj/123"
    mock_git.get_pull_request.return_value = pr

    mock_policy.get_policy_evaluations.return_value = [
        _make_evaluation("Build", "approved", "CI Pipeline", 99),
        _make_evaluation("Reviewers", "running"),
    ]

    result = _get_pr_policy_evaluations_impl(
        mock_git, mock_policy, "proj", "repo", 123
    )

    assert "Build" in result
    assert "approved" in result
    assert "CI Pipeline" in result
    assert "Reviewers" in result
    assert "running" in result


def test_policy_evaluations_empty():
    """Empty evaluations list returns appropriate message."""
    mock_git = MagicMock()
    mock_policy = MagicMock()

    pr = MagicMock()
    pr.artifact_id = "vstfs:///CodeReview/CodeReviewId/proj/1"
    mock_git.get_pull_request.return_value = pr
    mock_policy.get_policy_evaluations.return_value = []

    result = _get_pr_policy_evaluations_impl(
        mock_git, mock_policy, "proj", "repo", 1
    )

    assert "No policy evaluations found" in result


def test_policy_evaluations_pr_not_found():
    """None PR returns not-found message."""
    mock_git = MagicMock()
    mock_policy = MagicMock()
    mock_git.get_pull_request.return_value = None

    result = _get_pr_policy_evaluations_impl(
        mock_git, mock_policy, "proj", "repo", 999
    )

    assert "not found" in result


def test_policy_evaluations_api_error():
    """API errors are returned as error strings."""
    mock_git = MagicMock()
    mock_policy = MagicMock()
    mock_git.get_pull_request.side_effect = Exception("Unauthorized")

    result = _get_pr_policy_evaluations_impl(
        mock_git, mock_policy, "proj", "repo", 1
    )

    assert "Error" in result
    assert "Unauthorized" in result


# ── Vote tools ────────────────────────────────────────────────────────────────

def _make_vote_mocks(vote_value):
    """Return (git_client, identity_client) mocks wired for vote tests."""
    mock_git = MagicMock()
    mock_identity = MagicMock()

    self_identity = MagicMock()
    self_identity.id = "user-guid-1234"
    mock_identity.get_self.return_value = self_identity

    reviewer_result = MagicMock()
    reviewer_result.display_name = "Test User"
    mock_git.create_pull_request_reviewer.return_value = reviewer_result

    return mock_git, mock_identity


def test_approve_with_suggestions_sends_vote_5():
    """approve_with_suggestions uses vote value 5."""
    mock_git, mock_identity = _make_vote_mocks(5)

    result = _approve_with_suggestions_pull_request_impl(
        mock_git, mock_identity, "proj", "repo", 42
    )

    call_kwargs = mock_git.create_pull_request_reviewer.call_args
    reviewer_arg = call_kwargs[1]["reviewer"] if call_kwargs[1] else call_kwargs[0][0]
    assert reviewer_arg.vote == 5
    assert "approved with suggestions" in result
    assert "42" in result


def test_wait_for_author_sends_vote_minus5():
    """wait_for_author uses vote value -5."""
    mock_git, mock_identity = _make_vote_mocks(-5)

    result = _wait_for_author_pull_request_impl(
        mock_git, mock_identity, "proj", "repo", 42
    )

    call_kwargs = mock_git.create_pull_request_reviewer.call_args
    reviewer_arg = call_kwargs[1]["reviewer"] if call_kwargs[1] else call_kwargs[0][0]
    assert reviewer_arg.vote == -5
    assert "waiting for author" in result
    assert "42" in result


def test_reset_vote_sends_vote_0():
    """reset_vote uses vote value 0."""
    mock_git, mock_identity = _make_vote_mocks(0)

    result = _reset_pull_request_vote_impl(
        mock_git, mock_identity, "proj", "repo", 42
    )

    call_kwargs = mock_git.create_pull_request_reviewer.call_args
    reviewer_arg = call_kwargs[1]["reviewer"] if call_kwargs[1] else call_kwargs[0][0]
    assert reviewer_arg.vote == 0
    assert "reset" in result
    assert "42" in result


def test_vote_api_error_returns_error_string():
    """API errors in vote tools return formatted error string."""
    mock_git = MagicMock()
    mock_identity = MagicMock()
    mock_identity.get_self.side_effect = Exception("Auth failed")

    result = _approve_with_suggestions_pull_request_impl(
        mock_git, mock_identity, "proj", "repo", 1
    )

    assert "Error" in result
    assert "Auth failed" in result


# ── Restart merge ─────────────────────────────────────────────────────────────

def test_restart_merge_calls_update_with_queued_status():
    """restart_pr_merge calls update_pull_request with merge_status=queued."""
    mock_git = MagicMock()

    result = _restart_pr_merge_impl(mock_git, "proj", "repo", 55)

    assert mock_git.update_pull_request.called
    call_kwargs = mock_git.update_pull_request.call_args[1]
    pr_update = call_kwargs["git_pull_request_to_update"]
    assert pr_update.merge_status == "queued"
    assert "restarted" in result
    assert "55" in result


def test_restart_merge_api_error():
    """API errors in restart merge return formatted error string."""
    mock_git = MagicMock()
    mock_git.update_pull_request.side_effect = Exception("Server error")

    result = _restart_pr_merge_impl(mock_git, "proj", "repo", 10)

    assert "Error" in result
    assert "10" in result
    assert "Server error" in result


# ── _format_pull_request commit SHAs ──────────────────────────────────────────

def _make_pr(source_sha=None, target_sha=None):
    pr = MagicMock(spec=[
        "title", "pull_request_id", "is_draft",
        "source_ref_name", "target_ref_name",
        "status", "merge_status", "reviewers",
        "work_item_refs", "description",
        "last_merge_source_commit", "last_merge_target_commit",
    ])
    pr.title = "Test PR"
    pr.pull_request_id = 1
    pr.is_draft = False
    pr.source_ref_name = "refs/heads/feature"
    pr.target_ref_name = "refs/heads/main"
    pr.status = "active"
    pr.merge_status = None
    pr.reviewers = []
    pr.work_item_refs = None
    pr.description = None

    if source_sha:
        src = MagicMock()
        src.commit_id = source_sha
        pr.last_merge_source_commit = src
    else:
        pr.last_merge_source_commit = None

    if target_sha:
        tgt = MagicMock()
        tgt.commit_id = target_sha
        pr.last_merge_target_commit = tgt
    else:
        pr.last_merge_target_commit = None

    return pr


def test_format_pr_includes_source_commit_sha():
    """Source commit SHA appears in formatted PR output."""
    pr = _make_pr(source_sha="abc123", target_sha="def456")
    result = _format_pull_request(pr)
    assert "abc123" in result
    assert "Source Commit (after)" in result


def test_format_pr_includes_target_commit_sha():
    """Target commit SHA appears in formatted PR output."""
    pr = _make_pr(source_sha="abc123", target_sha="def456")
    result = _format_pull_request(pr)
    assert "def456" in result
    assert "Target Commit (before)" in result


def test_format_pr_omits_commit_sha_when_missing():
    """No commit lines are added when commits are absent."""
    pr = _make_pr()
    result = _format_pull_request(pr)
    assert "Source Commit" not in result
    assert "Target Commit" not in result


# ── _get_pr_changed_files_impl ────────────────────────────────────────────────

def _make_change_entry(path, change_type="edit"):
    entry = MagicMock()
    entry.change_type = change_type
    item = MagicMock()
    item.path = path
    entry.item = item
    return entry


def test_get_pr_changed_files_returns_formatted_lines():
    """Changed files are returned as '<change_type>: <path>' lines."""
    mock_git = MagicMock()

    iteration = MagicMock()
    iteration.id = 3
    mock_git.get_pull_request_iterations.return_value = [iteration]

    changes = MagicMock()
    changes.change_entries = [
        _make_change_entry("/src/foo.py", "edit"),
        _make_change_entry("/src/bar.py", "add"),
    ]
    mock_git.get_pull_request_iteration_changes.return_value = changes

    result = _get_pr_changed_files_impl(mock_git, "proj", "repo", 1)

    assert "edit: /src/foo.py" in result
    assert "add: /src/bar.py" in result


def test_get_pr_changed_files_no_iterations():
    """Empty iterations list returns appropriate message."""
    mock_git = MagicMock()
    mock_git.get_pull_request_iterations.return_value = []

    result = _get_pr_changed_files_impl(mock_git, "proj", "repo", 1)

    assert "No iterations found" in result


def test_get_pr_changed_files_no_change_entries():
    """No change entries returns appropriate message."""
    mock_git = MagicMock()

    iteration = MagicMock()
    iteration.id = 1
    mock_git.get_pull_request_iterations.return_value = [iteration]

    changes = MagicMock()
    changes.change_entries = []
    mock_git.get_pull_request_iteration_changes.return_value = changes

    result = _get_pr_changed_files_impl(mock_git, "proj", "repo", 1)

    assert "No file changes found" in result


def test_get_pr_changed_files_uses_latest_iteration():
    """The last iteration in the list is used (highest iteration ID)."""
    mock_git = MagicMock()

    iter1 = MagicMock()
    iter1.id = 1
    iter2 = MagicMock()
    iter2.id = 2
    mock_git.get_pull_request_iterations.return_value = [iter1, iter2]

    changes = MagicMock()
    changes.change_entries = [_make_change_entry("/x.py")]
    mock_git.get_pull_request_iteration_changes.return_value = changes

    _get_pr_changed_files_impl(mock_git, "proj", "repo", 42)

    call_kwargs = mock_git.get_pull_request_iteration_changes.call_args[1]
    assert call_kwargs["iteration_id"] == 2
