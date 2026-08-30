"""Tests for run_claude.profiles inspection helpers."""

from run_claude.profiles import (
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


def test_format_profile_view_headers():
    inspection = inspect_profile("alibaba")
    text = format_profile_view(inspection)
    assert "ROLE" in text
    assert "MODEL NAME" in text
    assert "INTERNAL NAME" in text
    assert "KEY ENV" in text
    assert "INSTANCE" in text
    assert "Additional models:" in text
