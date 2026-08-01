from main import filter_supported_models


def test_filter_supported_models_keeps_only_registry_providers():
    raw_models = [
        {
            "provider": "Open Router",
            "detail_url": "https://freellm.net/models/openrouter/test-a",
            "slug": "test-a",
            "extra": {},
        },
        {
            "provider": "Google Gemini",
            "detail_url": "https://freellm.net/models/google-gemini/test-b",
            "slug": "test-b",
            "extra": {},
        },
        {
            "provider": "NVIDIA NIM",
            "detail_url": "https://freellm.net/models/nvidia-nim/test-c",
            "slug": "test-c",
            "extra": {},
        },
    ]

    filtered = filter_supported_models(raw_models)

    assert len(filtered) == 2
    assert {item["provider"] for item in filtered} == {"Open Router", "NVIDIA NIM"}
