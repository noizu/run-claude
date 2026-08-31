"""Tests for named-key helpers and runtime switch wiring."""

from __future__ import annotations

from unittest.mock import patch

from run_claude import keys, proxy
from run_claude.cli import main
from run_claude.state import State


def test_name_from_env_canonical():
    assert keys.name_from_env("ZAI_SUB_KEY") == "zai"
    assert keys.name_from_env("ZAI_SUB_KEY_TYNA") == "tyna"
    assert keys.name_from_env("CEREBRAS_SUB_KEY") == "cerebras"
    assert keys.name_from_env("FOO_SUB_KEY") == "foo"
    assert keys.name_from_env("ACME_SUB_KEY_BETA") == "beta"
    assert keys.name_from_env("PATH") is None


def test_canonical_aliases():
    assert keys.canonical_key_name("zai-tyna") == "tyna"
    assert keys.canonical_key_name("TYNA") == "tyna"
    assert keys.canonical_key_name("default") == "zai"


def test_family_match_does_not_bleed_into_tyna():
    assert keys.family_of("zai/opus[1m]") == "zai"
    assert keys.matches_target("zai/haiku", "zai")
    assert keys.matches_target("zai/opus[1m]", "zai")
    assert not keys.matches_target("zai-tyna/haiku", "zai")
    assert keys.matches_target("zai-tyna/haiku", "zai-tyna")
    assert keys.matches_target("zai/opus", "zai/opus")


def test_family_match_does_not_bleed_into_zai_alt():
    assert keys.family_of("zai-alt/opus") == "zai-alt"
    assert not keys.matches_target("zai-alt/haiku", "zai")
    assert not keys.matches_target("zai-oa-alt/glm-5.3", "zai-oa")
    assert keys.matches_target("zai-alt/haiku", "zai-alt")
    assert keys.matches_target("zai-alt/opus[1m]", "zai-alt")
    assert keys.matches_target("zai-oa-alt/glm-5.3", "zai-oa-alt")


def test_hydrate_stamps_api_key_name(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("ZAI_SUB_KEY", "main-secret")
    monkeypatch.setenv("ZAI_SUB_KEY_TYNA", "tyna-secret")
    monkeypatch.setattr(proxy, "load_state", lambda: State())

    hydrated = proxy._hydrate_model_dict({
        "model_name": "zai/opus",
        "litellm_params": {
            "model": "anthropic/glm-5.3",
            "api_key": "os.environ/ZAI_SUB_KEY",
        },
    })
    params = hydrated["litellm_params"]
    assert params["api_key"] == "main-secret"
    assert params["api_key_name"] == "zai"


def test_hydrate_zai_alt_independent_of_zai_family(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("ZAI_SUB_KEY", "main-secret")
    monkeypatch.setenv("ZAI_SUB_KEY_TYNA", "tyna-secret")
    st = State(key_families={"zai": "tyna", "zai-alt": "zai"})
    monkeypatch.setattr(proxy, "load_state", lambda: st)

    main = proxy._hydrate_model_dict({
        "model_name": "zai/opus",
        "litellm_params": {
            "model": "anthropic/glm-5.3-flash",
            "api_key": "os.environ/ZAI_SUB_KEY",
        },
    })
    alt = proxy._hydrate_model_dict({
        "model_name": "zai-alt/opus",
        "litellm_params": {
            "model": "anthropic/glm-5.3-flash",
            "api_key": "os.environ/ZAI_SUB_KEY_TYNA",
        },
    })
    assert main["litellm_params"]["api_key_name"] == "tyna"
    assert main["litellm_params"]["api_key"] == "tyna-secret"
    assert alt["litellm_params"]["api_key_name"] == "zai"
    assert alt["litellm_params"]["api_key"] == "main-secret"


def test_hydrate_applies_persisted_family_binding(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("ZAI_SUB_KEY", "main-secret")
    monkeypatch.setenv("ZAI_SUB_KEY_TYNA", "tyna-secret")
    st = State(key_families={"zai": "tyna"})
    monkeypatch.setattr(proxy, "load_state", lambda: st)

    hydrated = proxy._hydrate_model_dict({
        "model_name": "zai/opus",
        "litellm_params": {
            "model": "anthropic/glm-5.3",
            "api_key": "os.environ/ZAI_SUB_KEY",
        },
    })
    params = hydrated["litellm_params"]
    assert params["api_key_name"] == "tyna"
    assert params["api_key"] == "tyna-secret"


def test_switch_persists_family_binding(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    saved = {}

    def fake_save(st):
        saved["state"] = st

    monkeypatch.setattr(proxy, "load_state", lambda: State())
    monkeypatch.setattr(proxy, "save_state", fake_save)

    class Resp:
        status_code = 200

        def json(self):
            return {"updated": ["zai/opus", "zai/haiku"], "key": "tyna"}

    monkeypatch.setattr(proxy, "_admin_request", lambda *a, **k: Resp())
    payload = proxy.switch_named_key("tyna", target="zai")
    assert payload["updated"] == ["zai/opus", "zai/haiku"]
    assert saved["state"].key_families["zai"] == "tyna"


def test_cli_keys_list_without_proxy(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("ZAI_SUB_KEY", "main")
    monkeypatch.setenv("ZAI_SUB_KEY_TYNA", "tyna")
    monkeypatch.setattr(proxy, "is_proxy_running", lambda: False)
    with patch("sys.argv", ["run-claude", "keys", "list"]):
        assert main() == 0
    out = capsys.readouterr().out
    assert "zai" in out
    assert "tyna" in out


def test_cli_keys_switch_registers_catalog_family(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("ZAI_SUB_KEY", "main")
    monkeypatch.setenv("ZAI_SUB_KEY_TYNA", "tyna")
    monkeypatch.setattr(proxy, "is_proxy_running", lambda: True)
    monkeypatch.setattr(proxy, "ensure_named_keys", lambda debug=False: 0)
    monkeypatch.setattr(proxy, "upsert_named_key", lambda *a, **k: None)
    calls = {"n": 0}

    def fake_switch(key, target=None, using=None, persist=True):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"updated": [], "key": key}
        return {"updated": ["zai-alt/opus", "zai-alt/haiku"], "key": key}

    monkeypatch.setattr(proxy, "switch_named_key", fake_switch)
    monkeypatch.setattr(
        proxy, "ensure_catalog_family", lambda target, debug=False: (2, 0, 0)
    )
    with patch("sys.argv", ["run-claude", "keys", "switch", "zai-alt", "tyna"]):
        assert main() == 0
    out = capsys.readouterr().out
    assert calls["n"] == 2
    assert "Registered catalog family zai-alt" in out
    assert "zai-alt/opus" in out


def test_cli_keys_switch_example_requires_proxy(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(proxy, "is_proxy_running", lambda: False)
    with patch("sys.argv", ["run-claude", "keys", "switch", "zai", "tyna"]):
        assert main() == 1
    assert "not running" in capsys.readouterr().err.lower()
