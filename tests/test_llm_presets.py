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


def test_reader_accepts_a_fenced_json_object():
    from types import SimpleNamespace

    from counterfoil.agents import read_email

    fenced = '```json\n{"musteri_email": "a@b.c", "siparis_no": "ST-1", "tutar": "30.00"}\n```'
    llm = SimpleNamespace(chat=lambda *a, **k: SimpleNamespace(content=fenced))
    out, raw = read_email(llm, {"from": "a@b.c", "subject": "s", "body": "b"})
    assert out and out["siparis_no"] == "ST-1" and raw == fenced


def test_claude_5_family_does_not_send_temperature(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    assert preset("opus-5.5").temperature is None
    assert preset("qwen2.5").temperature == 0.0


def test_gpt_5_6_on_the_gateway_turns_reasoning_off(monkeypatch):
    monkeypatch.setenv("ASTRO_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("ASTRO_GATEWAY_API_KEY", "test")
    monkeypatch.setenv("CF_MODEL", "gpt-5-6-terra")
    cfg = preset("astropods")
    assert cfg.reasoning_effort == "none" and cfg.temperature is None and cfg.base_url == "https://gateway.example/v1"


def test_anthropic_reader_does_not_send_json_object(monkeypatch):
    # Anthropic's compatibility layer answers 400 "response_format.type: Input should be 'json_schema'" (2 Nov live demo)
    from types import SimpleNamespace

    from counterfoil.llm import LLM

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    sent = {}

    def create(**kw):
        sent.update(kw)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))])

    for name, expected in [("haiku-5.5", False), ("qwen2.5", True)]:
        sent.clear()
        llm = LLM(preset(name))
        llm.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        llm.chat([{"role": "user", "content": "x"}], json_mode=True)
        assert ("response_format" in sent) is expected, name


def test_reader_accepts_an_object_inside_a_sentence():
    from types import SimpleNamespace

    from counterfoil.agents import read_email

    wrapped = 'Here is the hand-off:\n{"musteri_email": "a@b.c", "siparis_no": "ST-1", "tutar": "30.00"}\nDone.'
    llm = SimpleNamespace(chat=lambda *a, **k: SimpleNamespace(content=wrapped))
    out, _ = read_email(llm, {"from": "a@b.c", "subject": "s", "body": "b"})
    assert out and out["siparis_no"] == "ST-1"
    junk = SimpleNamespace(chat=lambda *a, **k: SimpleNamespace(content="no object {here"))
    assert read_email(junk, {"from": "a@b.c", "subject": "s", "body": "b"})[0] is None
