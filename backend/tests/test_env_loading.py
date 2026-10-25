"""REQUIREMENTS.md 13.2 #1 — .env is found in two places, in order."""

import pytest

from app import config


@pytest.fixture(autouse=True)
def _clear_key(monkeypatch):
    monkeypatch.delenv("PORTKEY_API_KEY", raising=False)


def _write_env(directory, value="test-key-not-real"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".env").write_text(f"PORTKEY_API_KEY={value}\n")


def test_loads_from_the_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    _write_env(repo_root, "from-repo-root")
    paths = (repo_root / ".env", tmp_path / ".env")

    assert config.get_portkey_api_key(paths) == "from-repo-root"


def test_loads_from_one_level_above_the_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_env(tmp_path, "from-parent")
    paths = (repo_root / ".env", tmp_path / ".env")

    assert config.get_portkey_api_key(paths) == "from-parent"


def test_the_repo_root_wins_when_both_exist(tmp_path):
    repo_root = tmp_path / "repo"
    _write_env(repo_root, "from-repo-root")
    _write_env(tmp_path, "from-parent")
    paths = (repo_root / ".env", tmp_path / ".env")

    assert config.get_portkey_api_key(paths) == "from-repo-root"


def test_clear_error_when_the_key_is_missing(tmp_path):
    paths = (tmp_path / "repo" / ".env", tmp_path / ".env")

    with pytest.raises(RuntimeError) as excinfo:
        config.get_portkey_api_key(paths)

    message = str(excinfo.value)
    assert "PORTKEY_API_KEY" in message
    # The error must name both places it looked, so the fix is obvious.
    assert str(paths[0]) in message and str(paths[1]) in message


def test_the_error_never_contains_a_key(tmp_path):
    """A missing-key error must not leak anything secret."""
    paths = (tmp_path / "repo" / ".env", tmp_path / ".env")
    with pytest.raises(RuntimeError) as excinfo:
        config.get_portkey_api_key(paths)
    assert "sk-" not in str(excinfo.value)


def test_the_real_search_paths_are_resolved_from_the_file(tmp_path):
    """Resolved from __file__, so the working directory does not matter."""
    first, second = config.ENV_SEARCH_PATHS
    assert first == config.REPO_ROOT / ".env"
    assert second == config.REPO_ROOT.parent / ".env"
    assert first.is_absolute() and second.is_absolute()
