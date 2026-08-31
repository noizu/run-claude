"""Tests for run_claude.profiles inspection helpers."""

from run_claude.profiles import (
    format_profile_list,
    format_profile_view,
    inspect_profile,
    list_profile_infos,
    list_profiles,
)


def test_list_profile_infos_includes_display_names():
    infos = {info.name: info for info in list_profile_infos()}
    assert "alibaba" in infos
    assert infos["alibaba"].display_name == "Alibaba Token Plan"
    assert infos["alibaba"].source_path.exists()


def test_list_profiles_matches_infos():
    assert list_profiles() == [info.name for info in list_profile_infos()]


def test_inspect_alibaba_tiers_and_extended():
    inspection = inspect_profile("alibaba")
    assert inspection is not None
    assert inspection.name == "alibaba"
    assert inspection.display_name == "Alibaba Token Plan"
    assert inspection.fable_fallback is False

    opus = inspection.tiers["opus"]
    assert opus.model_name == "alibaba/opus"
    assert opus.internal_name == "anthropic/qwen3.8-max"
    assert opus.key_env == "QWEN_SUB_KEY"
    assert opus.instance == "qwen"
    assert "token-plan.ap-southeast-1.maas.aliyuncs.com" in opus.api_base

    fable = inspection.tiers["fable"]
    assert fable.model_name == "alibaba/fable"
    assert fable.internal_name == "anthropic/kimi-k3"

    sonnet = inspection.tiers["sonnet"]
    assert sonnet.internal_name == "anthropic/glm-5.2"

    haiku = inspection.tiers["haiku"]
    assert haiku.internal_name == "anthropic/qwen3.6-flash"

    extra_names = {item.model_name for item in inspection.extended}
    assert "alibaba/kimi-k2.7-code" in extra_names
    assert "alibaba/deepseek-v4-pro" in extra_names
    assert "alibaba/minimax-m2.5" in extra_names
    # Tier aliases themselves are not repeated as additional models.
    assert "alibaba/opus" not in extra_names


def test_inspect_wafer_tiers():
    inspection = inspect_profile("wafer")
    assert inspection is not None
    assert inspection.name == "wafer"
    assert inspection.display_name == "Wafer Serverless"

    fable = inspection.tiers["fable"]
    assert fable.model_name == "wafer/fable[1m]"
    assert fable.internal_name == "anthropic/Kimi-K3"
    assert fable.key_env == "WAFER_AI_API_KEY"
    assert "pass.wafer.ai" in fable.api_base

    for tier in ("opus", "sonnet", "haiku"):
        binding = inspection.tiers[tier]
        assert binding.internal_name == "anthropic/GLM-5.3-Flash"
        assert binding.key_env == "WAFER_AI_API_KEY"
        assert "pass.wafer.ai" in binding.api_base

    extra_names = {item.model_name for item in inspection.extended}
    assert "wafer/kimi-k2.6[1m]" in extra_names
    assert "wafer/glm-5.2[1m]" in extra_names


def test_inspect_zai_pro_instances():
    inspection = inspect_profile("zai-pro")
    assert inspection is not None
    assert inspection.tiers["fable"].internal_name == "anthropic/glm-5.3"
    assert inspection.tiers["opus"].internal_name == "anthropic/glm-5.3-flash"
    assert inspection.tiers["opus"].key_env == "ZAI_SUB_KEY"
    assert inspection.tiers["opus"].instance == "zai"

    tyna = next(item for item in inspection.extended if item.model_name == "zai-tyna/opus")
    assert tyna.key_env == "ZAI_SUB_KEY_TYNA"
    assert tyna.instance == "tyna"
    assert tyna.internal_name == "anthropic/glm-5.3-flash"


def test_inspect_zai_pro_alt_defaults_to_tyna():
    inspection = inspect_profile("zai-pro-alt")
    assert inspection is not None
    assert inspection.display_name == "Zai Subscription (Alt)"
    assert inspection.tiers["opus"].model_name == "zai-alt/opus"
    assert inspection.tiers["sonnet"].model_name == "zai-alt/sonnet"
    assert inspection.tiers["haiku"].model_name == "zai-alt/haiku"
    assert inspection.tiers["fable"].model_name == "zai-alt/fable"
    assert inspection.tiers["opus"].internal_name == "anthropic/glm-5.3-flash"
    assert inspection.tiers["fable"].internal_name == "anthropic/glm-5.3"
    assert inspection.tiers["opus"].key_env == "ZAI_SUB_KEY_TYNA"
    assert inspection.tiers["opus"].instance == "tyna"

    extra_names = {item.model_name for item in inspection.extended}
    assert "zai-alt/opus[1m]" in extra_names
    assert "zai-alt/glm-5.3" in extra_names
    assert "zai-oa-alt/glm-5.3" in extra_names
    assert "zai-alt/opus" not in extra_names
    assert "zai/opus" not in extra_names


def test_zai_alt_profile_is_alias_of_zai_pro_alt():
    alt = inspect_profile("zai-alt")
    pro_alt = inspect_profile("zai-pro-alt")
    assert alt is not None and pro_alt is not None
    assert alt.tiers["opus"].model_name == pro_alt.tiers["opus"].model_name
    assert alt.tiers["opus"].key_env == "ZAI_SUB_KEY_TYNA"


def test_zai_alt_catalog_clone_mirrors_zai_skus():
    from run_claude.profiles import load_model_definitions

    models = load_model_definitions(force_reload=True, quiet=True)
    assert "zai-alt/opus" in models
    src = models["zai/opus"]
    dst = models["zai-alt/opus"]
    assert dst.litellm_params["model"] == src.litellm_params["model"]
    assert dst.litellm_params["api_base"] == src.litellm_params["api_base"]
    assert src.litellm_params["api_key"] == "os.environ/ZAI_SUB_KEY"
    assert dst.litellm_params["api_key"] == "os.environ/ZAI_SUB_KEY_TYNA"
    assert "zai-alt/opus[1m]" in models
    assert "zai-oa-alt/glm-5.3" in models
    assert models["zai-oa-alt/glm-5.3"].litellm_params["model"] == (
        models["zai-oa/glm-5.3"].litellm_params["model"]
    )


def test_inspect_cerebras_explicit_fable_tier():
    inspection = inspect_profile("cerebras")
    assert inspection is not None
    assert inspection.fable_fallback is False
    assert inspection.tiers["fable"].model_name == "cerebras/zai-glm-4.7"
    assert inspection.tiers["opus"].model_name == "cerebras/gemma-4-31b"
    assert inspection.tiers["sonnet"].model_name == "cerebras/gpt-oss-120b"
    assert inspection.tiers["haiku"].model_name == "cerebras/gpt-oss-120b"
    assert inspection.tiers["opus"].key_env == "CEREBRAS_API_KEY"


def test_inspect_missing_returns_none():
    assert inspect_profile("definitely-not-a-profile") is None


def test_unprefixed_models_group_by_named_key():
    inspection = inspect_profile("anthropic")
    assert inspection is not None
    families = {ks.family for ks in inspection.key_sets}
    assert "anthropic" in families
    assert not any(name.startswith("claude-") for name in families)


def test_format_profile_view_headers():
    inspection = inspect_profile("alibaba")
    text = format_profile_view(inspection)
    assert "ROLE" in text
    assert "MODEL NAME" in text
    assert "INTERNAL NAME" in text
    assert "KEY ENV" in text
    assert "INSTANCE" in text
    assert "Additional models:" in text
    assert "Key sets:" in text
    assert "FAMILY" in text
    assert "DEFAULT ENV" in text
    assert "OVERRIDE" in text
    assert "QWEN_SUB_KEY" in text


def test_inspect_zai_pro_key_sets(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    inspection = inspect_profile("zai-pro")
    assert inspection is not None
    families = {ks.family: ks for ks in inspection.key_sets}
    assert "zai" in families
    assert families["zai"].key_env == "ZAI_SUB_KEY"
    assert families["zai"].instance == "zai"
    assert families["zai"].override == ""
    assert "zai-tyna" in families
    assert families["zai-tyna"].key_env == "ZAI_SUB_KEY_TYNA"


def test_inspect_zai_pro_alt_key_sets(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    inspection = inspect_profile("zai-pro-alt")
    assert inspection is not None
    families = {ks.family: ks for ks in inspection.key_sets}
    assert "zai-alt" in families
    assert families["zai-alt"].key_env == "ZAI_SUB_KEY_TYNA"
    assert families["zai-alt"].instance == "tyna"
    assert "zai" not in families


def test_inspect_key_set_family_override(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    from run_claude.state import State, save_state

    save_state(State(key_families={"zai": "tyna"}))
    inspection = inspect_profile("zai-pro")
    assert inspection is not None
    zai = next(ks for ks in inspection.key_sets if ks.family == "zai")
    assert zai.override == "tyna"
    assert zai.override_env == "ZAI_SUB_KEY_TYNA"
    assert zai.effective_instance == "tyna"
    assert zai.effective_env == "ZAI_SUB_KEY_TYNA"
    text = format_profile_view(inspection)
    assert "tyna" in text
    assert "OVERRIDE" in text


def test_list_profile_infos_with_keys_includes_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    from run_claude.state import State, save_state

    save_state(State(key_families={"zai-alt": "zai"}))
    infos = {info.name: info for info in list_profile_infos(with_keys=True)}
    assert "zai-pro-alt" in infos
    brief = " ".join(ks.brief() for ks in infos["zai-pro-alt"].key_sets)
    assert "zai-alt=" in brief
    assert "->zai" in brief
    listing = format_profile_list(list(infos.values()))
    assert "zai-pro-alt" in listing
    assert "alibaba" in listing
    assert "QWEN_SUB_KEY" in listing
    assert "zai-alt=" in listing
