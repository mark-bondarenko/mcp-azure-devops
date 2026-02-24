"""
Tests for _configure_ssl() in azure_client.
"""
import sys
import warnings

import pytest
import requests
import urllib3

# Capture the real Session.__init__ before any test can monkey-patch it.
_REAL_SESSION_INIT = requests.Session.__init__


def _reload_module(monkeypatch, env_value=None):
    """
    Re-import azure_client with the given AZURE_DEVOPS_VERIFY_SSL value.
    Does NOT restore Session.__init__; the autouse fixture handles that.
    """
    if env_value is None:
        monkeypatch.delenv("AZURE_DEVOPS_VERIFY_SSL", raising=False)
    else:
        monkeypatch.setenv("AZURE_DEVOPS_VERIFY_SSL", env_value)
    sys.modules.pop("mcp_azure_devops.utils.azure_client", None)
    import mcp_azure_devops.utils.azure_client  # noqa: F401


@pytest.fixture(autouse=True)
def restore_session_init():
    """Restore the real Session.__init__ and evict the module after every test."""
    yield
    requests.Session.__init__ = _REAL_SESSION_INIT
    sys.modules.pop("mcp_azure_devops.utils.azure_client", None)


class TestConfigureSsl:
    def test_default_env_not_set_verify_remains_true(self, monkeypatch):
        """Session.verify stays True when env var is absent."""
        _reload_module(monkeypatch, env_value=None)
        assert requests.Session().verify is True

    def test_env_set_to_true_verify_remains_true(self, monkeypatch):
        """Session.verify stays True when AZURE_DEVOPS_VERIFY_SSL=true."""
        _reload_module(monkeypatch, env_value="true")
        assert requests.Session().verify is True

    def test_env_set_to_false_verify_becomes_false(self, monkeypatch):
        """Session.verify becomes False when AZURE_DEVOPS_VERIFY_SSL=false."""
        _reload_module(monkeypatch, env_value="false")
        assert requests.Session().verify is False

    def test_env_false_suppresses_insecure_warning(self, monkeypatch):
        """disable_warnings is called: InsecureRequestWarning has an ignore filter."""
        _reload_module(monkeypatch, env_value="false")
        filtered = [
            f for f in warnings.filters
            if f[0] == "ignore"
            and issubclass(f[2], urllib3.exceptions.InsecureRequestWarning)
        ]
        assert filtered, "Expected an ignore filter for InsecureRequestWarning"

    def test_original_init_still_called(self, monkeypatch):
        """The monkey-patch calls the original __init__ (session is fully initialized)."""
        _reload_module(monkeypatch, env_value="false")
        session = requests.Session()
        # A fully initialized session has transport adapters configured
        assert len(session.adapters) > 0
