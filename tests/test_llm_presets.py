import pytest

from counterfoil.llm import PRESETS, preset


def test_local_preset_needs_no_key():
    cfg = preset("qwen2.5")
    assert cfg.base_url.startswith("http://localhost") and cfg.model == "qwen2.5-8k" and cfg.seed == 7


def test_unknown_preset_is_refused():
    with pytest.raises(ValueError):
        preset("gpt-9")


@pytest.mark.parametrize("name", [n for n, p in PRESETS.items() if p[2]])
def test_cloud_presets_refuse_to_run_without_their_key(name, monkeypatch):
    monkeypatch.delenv(PRESETS[name][2], raising=False)
    monkeypatch.setenv("ASTRA_MODEL_ID", "x")
    with pytest.raises(RuntimeError):
        preset(name)


def test_anthropic_presets_do_not_send_seed(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert preset("haiku-5.5").seed is None


def test_astra_needs_its_model_id(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.delenv("ASTRA_MODEL_ID", raising=False)
    with pytest.raises(RuntimeError, match="ASTRA_MODEL_ID"):
        preset("gpt6-astra")
