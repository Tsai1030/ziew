from kbparse.providers.mock_provider import MockVLMProvider


def test_mock_provider_returns_deterministic_description():
    provider = MockVLMProvider()
    result = provider.describe_image(
        image_path="assets/figures/p0001_fig001.png",
        prompt="describe",
        context={"caption_nearby": "系統架構圖"},
    )
    assert result["alt_text_short"] == "系統架構圖"
    assert result["confidence"] == 1.0
