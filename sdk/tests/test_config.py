from __future__ import annotations

import pytest

import llm_lens.config as config_module
from llm_lens.config import configure, get_config, is_configured


@pytest.fixture(autouse=True)
def _reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "_config", None)
    monkeypatch.setattr("llm_lens.sender.restart_sender", lambda config: None)


def test_configure_requires_project_or_api_key() -> None:
    with pytest.raises(ValueError):
        configure(base_url="http://localhost:8000")


def test_is_configured_false_until_configure_called() -> None:
    assert is_configured() is False


def test_configure_with_project_name_only() -> None:
    configure(project="My App")
    assert is_configured() is True
    config = get_config()
    assert config is not None
    assert config.project == "My App"
    assert config.api_key is None


def test_configure_with_api_key_only() -> None:
    configure(api_key="llk_test")
    config = get_config()
    assert config is not None
    assert config.api_key == "llk_test"
