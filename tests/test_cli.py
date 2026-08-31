"""Tests for run_claude.cli module."""

import pytest
from unittest.mock import patch
from run_claude.cli import main


class TestMain:
    """Tests for main CLI entry point."""

    def test_no_args_shows_help(self, capsys):
        """Running without arguments should show help and exit 0."""
        with patch("sys.argv", ["run-claude"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "run-claude" in captured.out
        assert "keys" in captured.out

    def test_invalid_command_exits_with_error(self, capsys):
        """Running with invalid command should exit with error."""
        with patch("sys.argv", ["run-claude", "invalid-command"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err


class TestEnvCommand:
    """Tests for the env command."""

    def test_env_missing_profile(self, capsys):
        """env command with nonexistent profile should error."""
        with patch("sys.argv", ["run-claude", "env", "nonexistent-profile"]):
            result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_env_outputs_anthropic_vars(self, capsys):
        """env command should output ANTHROPIC_* environment variables."""
        with patch("sys.argv", ["run-claude", "env", "cerebras"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        # Should contain base URL and auth token
        assert "ANTHROPIC_BASE_URL=" in output
        assert "API_TIMEOUT_MS=" in output

    def test_env_outputs_model_mappings(self, capsys):
        """env command should output model tier mappings from profile."""
        with patch("sys.argv", ["run-claude", "env", "cerebras"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        # cerebras profile maps fable->zai-glm-4.7, opus->gemma-4-31b, sonnet/haiku->gpt-oss-120b
        assert "ANTHROPIC_DEFAULT_OPUS_MODEL=" in output
        assert "ANTHROPIC_DEFAULT_SONNET_MODEL=" in output
        assert "ANTHROPIC_DEFAULT_HAIKU_MODEL=" in output

    def test_env_cerebras_profile_uses_available_models(self, capsys):
        """cerebras profile should map tiers to the 3 available Cerebras models."""
        with patch("sys.argv", ["run-claude", "env", "cerebras"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        assert "ANTHROPIC_DEFAULT_FABLE_MODEL=cerebras/zai-glm-4.7" in output
        assert "ANTHROPIC_DEFAULT_OPUS_MODEL=cerebras/gemma-4-31b" in output
        assert "ANTHROPIC_DEFAULT_SONNET_MODEL=cerebras/gpt-oss-120b" in output
        assert "ANTHROPIC_DEFAULT_HAIKU_MODEL=cerebras/gpt-oss-120b" in output

    def test_env_alibaba_profile_uses_qwen_models(self, capsys):
        """alibaba profile should map opus/sonnet/haiku to Token Plan aliases."""
        with patch("sys.argv", ["run-claude", "env", "alibaba"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        assert "ANTHROPIC_DEFAULT_OPUS_MODEL=alibaba/opus" in output
        assert "ANTHROPIC_DEFAULT_SONNET_MODEL=alibaba/sonnet" in output
        assert "ANTHROPIC_DEFAULT_HAIKU_MODEL=alibaba/haiku" in output
        assert "ANTHROPIC_DEFAULT_FABLE_MODEL=alibaba/fable" in output
        assert "ANTHROPIC_DEFAULT_FABLE_MODEL=alibaba/opus" not in output

    def test_env_export_flag_adds_export_prefix(self, capsys):
        """env --export should prefix lines with 'export'."""
        with patch("sys.argv", ["run-claude", "env", "cerebras", "--export"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        output = captured.out

        # Each line should start with 'export '
        for line in output.strip().split("\n"):
            assert line.startswith("export "), f"Line missing export prefix: {line}"


class TestProfilesCommand:
    """Tests for the profiles command."""

    def test_profiles_list(self, capsys):
        """profiles list should show available profiles."""
        with patch("sys.argv", ["run-claude", "profiles", "list"]):
            result = main()
        assert result == 0

    def test_profiles_list_includes_alibaba(self, capsys):
        """profiles list should include the Alibaba Token Plan profile."""
        with patch("sys.argv", ["run-claude", "profiles", "list"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "alibaba" in output
        assert "Alibaba Token Plan" in output
        assert "QWEN_SUB_KEY" in output
        assert "zai-pro" in output
        assert "ZAI_SUB_KEY" in output
        assert "qwen=" in output or "QWEN_SUB_KEY" in output

    def test_profiles_list_names_only(self, capsys):
        """profiles list --names-only should print bare names, one per line."""
        with patch("sys.argv", ["run-claude", "profiles", "list", "--names-only"]):
            result = main()
        assert result == 0
        names = capsys.readouterr().out.strip().splitlines()
        assert "alibaba" in names
        assert "Alibaba Token Plan" not in names
        assert all(" " not in name for name in names)

    def test_profiles_list_json(self, capsys):
        """profiles list --json should include name, display_name, and source."""
        import json
        with patch("sys.argv", ["run-claude", "profiles", "list", "--json"]):
            result = main()
        assert result == 0
        payload = json.loads(capsys.readouterr().out)
        alibaba = next(item for item in payload if item["name"] == "alibaba")
        assert alibaba["display_name"] == "Alibaba Token Plan"
        assert alibaba["source"]
        assert any(ks["key_env"] == "QWEN_SUB_KEY" for ks in alibaba["key_sets"])
        zai_pro = next(item for item in payload if item["name"] == "zai-pro")
        assert any(ks["family"] == "zai" and ks["key_env"] == "ZAI_SUB_KEY" for ks in zai_pro["key_sets"])

    def test_profiles_show_alibaba(self, capsys):
        """profiles show alibaba should map Token Plan tiers and extra chat SKUs."""
        with patch("sys.argv", ["run-claude", "profiles", "show", "alibaba"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "opus:   alibaba/opus" in output
        assert "sonnet: alibaba/sonnet" in output
        assert "haiku:  alibaba/haiku" in output
        assert "fable:  alibaba/fable" in output
        assert "alibaba/qwen3.8-max" in output
        assert "alibaba/glm-5.2" in output
        assert "alibaba/kimi-k3" in output
        assert "alibaba/kimi-k2.7-code" in output
        assert "alibaba/deepseek-v4-pro" in output
        assert "alibaba/minimax-m2.5" in output
        assert "anthropic/qwen3.8-max" in output
        assert "anthropic/kimi-k3" in output
        assert "QWEN_SUB_KEY" in output
        assert "INSTANCE" in output
        assert "INTERNAL NAME" in output
        assert "KEY ENV" in output
        assert "Key sets:" in output
        assert "FAMILY" in output

    def test_profiles_view_is_show_alias(self, capsys):
        """profiles view should produce the same inspection as show."""
        with patch("sys.argv", ["run-claude", "profiles", "view", "alibaba"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "Profile: alibaba" in output
        assert "fable" in output
        assert "QWEN_SUB_KEY" in output

    def test_profiles_view_zai_pro_bindings(self, capsys):
        """profiles view zai-pro should show instance, internal names, and key env vars."""
        with patch("sys.argv", ["run-claude", "profiles", "view", "zai-pro"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "opus:   zai/opus" in output
        assert "fable:  zai/fable" in output
        assert "anthropic/glm-5.3-flash" in output
        assert "anthropic/glm-5.3" in output
        assert "ZAI_SUB_KEY" in output
        assert "ZAI_SUB_KEY_TYNA" in output
        assert "zai-tyna/opus" in output

    def test_profiles_view_zai_pro_alt_bindings(self, capsys):
        """profiles view zai-pro-alt should default tiers to the zai-alt family."""
        with patch("sys.argv", ["run-claude", "profiles", "view", "zai-pro-alt"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "opus:   zai-alt/opus" in output
        assert "fable:  zai-alt/fable" in output
        assert "anthropic/glm-5.3-flash" in output
        assert "anthropic/glm-5.3" in output
        assert "ZAI_SUB_KEY_TYNA" in output
        assert "zai-alt/opus[1m]" in output

    def test_profiles_view_json(self, capsys):
        """profiles view --json should expose instance/internal/key_env per tier."""
        import json
        with patch("sys.argv", ["run-claude", "profiles", "view", "alibaba", "--json"]):
            result = main()
        assert result == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["name"] == "alibaba"
        opus = payload["tiers"]["opus"]
        assert opus["model_name"] == "alibaba/opus"
        assert opus["internal_name"] == "anthropic/qwen3.8-max"
        assert opus["key_env"] == "QWEN_SUB_KEY"
        assert opus["instance"] == "qwen"
        assert any(item["model_name"] == "alibaba/kimi-k2.7-code" for item in payload["extended"])
        assert any(ks["family"] and ks["key_env"] == "QWEN_SUB_KEY" for ks in payload["key_sets"])

    def test_profiles_view_does_not_leak_secrets(self, capsys, monkeypatch):
        """Profile view must print env var names, never hydrated key values."""
        monkeypatch.setenv("QWEN_SUB_KEY", "sk-secret-value-do-not-print")
        with patch("sys.argv", ["run-claude", "profiles", "view", "alibaba"]):
            result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "sk-secret-value-do-not-print" not in captured.out
        assert "sk-secret-value-do-not-print" not in captured.err
        assert "QWEN_SUB_KEY" in captured.out

    def test_profiles_show_missing(self, capsys):
        """profiles show with nonexistent profile should error."""
        with patch("sys.argv", ["run-claude", "profiles", "show", "nonexistent"]):
            result = main()
        assert result == 1


class TestModelsCommand:
    """Tests for the models command."""

    def test_models_list(self, capsys):
        """models list should show available model definitions."""
        with patch("sys.argv", ["run-claude", "models", "list"]):
            result = main()
        assert result == 0

    def test_models_list_includes_alibaba_qwen(self, capsys):
        """models list should include Alibaba Token Plan chat aliases."""
        with patch("sys.argv", ["run-claude", "models", "list"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "alibaba/opus" in output
        assert "alibaba/fable" in output
        assert "alibaba/qwen3.8-max" in output
        assert "alibaba/qwen3.6-flash" in output
        assert "alibaba/glm-5.2" in output
        assert "alibaba/kimi-k3" in output
        assert "alibaba/kimi-k2.7-code" in output
        assert "alibaba/deepseek-v4-flash" in output
        assert "alibaba/minimax-m2.5" in output

    def test_models_show_alibaba_opus_uses_token_plan_anthropic(self, capsys):
        """alibaba/opus should use QWEN_SUB_KEY and the Token Plan Anthropic base URL."""
        with patch("sys.argv", ["run-claude", "models", "show", "alibaba/opus"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "anthropic/qwen3.8-max" in output
        assert "os.environ/QWEN_SUB_KEY" in output
        assert "https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic" in output

    def test_models_show_alibaba_sonnet_uses_glm(self, capsys):
        """alibaba/sonnet should map to GLM-5.2 on the Token Plan Anthropic endpoint."""
        with patch("sys.argv", ["run-claude", "models", "show", "alibaba/sonnet"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "anthropic/glm-5.2" in output
        assert "os.environ/QWEN_SUB_KEY" in output

    def test_models_show_alibaba_fable_uses_kimi_k3(self, capsys):
        """alibaba/fable should map to Kimi K3 on the Token Plan Anthropic endpoint."""
        with patch("sys.argv", ["run-claude", "models", "show", "alibaba/fable"]):
            result = main()
        assert result == 0
        output = capsys.readouterr().out
        assert "anthropic/kimi-k3" in output
        assert "os.environ/QWEN_SUB_KEY" in output
        assert "https://token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic" in output

    def test_models_show_missing(self, capsys):
        """models show with nonexistent model should error."""
        with patch("sys.argv", ["run-claude", "models", "show", "nonexistent"]):
            result = main()
        assert result == 1
