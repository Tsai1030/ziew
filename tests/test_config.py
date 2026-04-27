from kbparse.config import load_config


def test_config_defaults_to_mock_without_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("VLM_PROVIDER", raising=False)
    cfg = load_config()
    assert cfg.vlm_provider == "mock"
    assert cfg.openai_api_key is None
