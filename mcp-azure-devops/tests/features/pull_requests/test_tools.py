from unittest.mock import MagicMock, patch

from mcp_azure_devops.features.pull_requests.tools import (
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
