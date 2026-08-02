from config_builder import build_config, build_litellm_model_name


def test_build_config_emits_specific_alias_and_capability_fallback_order():
    models = [
        {
            "provider": "nvidia",
            "model_id": "z-ai/glm-5.2",
            "api_base": "https://integrate.api.nvidia.com/v1",
            "score": 0.0,
            "capability": ["reasoning", "tool calling", "structured output"],
            "context": "128k",
            "best_for": ["Chat"],
            "extra": {"position": 2},
        },
        {
            "provider": "openrouter",
            "model_id": "z-ai/glm-5.2",
            "api_base": "https://openrouter.ai/api/v1",
            "score": 0.0,
            "capability": ["reasoning", "tool calling", "structured output"],
            "context": "128k",
            "best_for": ["Chat"],
            "extra": {"position": 5},
        },
        {
            "provider": "openrouter",
            "model_id": "minimax/minimax-m3",
            "api_base": "https://openrouter.ai/api/v1",
            "score": 0.0,
            "capability": ["reasoning", "tool calling", "structured output"],
            "context": "128k",
            "best_for": ["Chat"],
            "extra": {"position": 4},
        },
    ]

    config = build_config(models)

    fallback_aliases = config["router_settings"]["fallbacks"]
    assert {"chat": ["glm-5.2", "minimax-m3"]} in fallback_aliases
    assert {"reasoning": ["chat"]} in fallback_aliases

    model_names = [item["model_name"] for item in config["model_list"]]
    assert model_names.count("glm-5.2") == 3
    assert model_names.count("minimax-m3") == 1
    assert model_names.count("chat") == 1
    assert model_names.count("reasoning") == 1

    glm_entries = [
        item
        for item in config["model_list"]
        if item["model_name"] == "glm-5.2"
    ]
    assert [
        item["litellm_params"]["api_key"]
        for item in glm_entries
    ] == [
        "os.environ/NVIDIA_API_KEY_1",
        "os.environ/NVIDIA_API_KEY_2",
        "os.environ/OPENROUTER_API_KEY",
    ]


def test_build_litellm_model_name_keeps_real_provider_model_id():
    model = {
        "provider": "NVIDIA NIM",
        "model_id": "z-ai/glm-5.2",
        "name": "ignored",
    }

    assert build_litellm_model_name(model) == "z-ai/glm-5.2"


def test_build_config_adds_router_and_litellm_settings_and_preserves_model_id():
    models = [
        {
            "provider": "nvidia",
            "model_id": "z-ai/glm-5.2",
            "api_base": "https://integrate.api.nvidia.com/v1",
            "score": 0.0,
            "capability": ["reasoning"],
            "context": "128k",
            "best_for": ["reasoning"],
            "extra": {"position": 2},
        },
        {
            "provider": "openrouter",
            "model_id": "minimax/minimax-m3",
            "api_base": "https://openrouter.ai/api/v1",
            "score": 0.0,
            "capability": ["reasoning"],
            "context": "128k",
            "best_for": ["reasoning"],
            "extra": {"position": 4},
        },
    ]

    config = build_config(models)

    assert config["router_settings"]["routing_strategy"] == "simple-shuffle"
    assert config["router_settings"]["num_retries"] == 2
    assert config["router_settings"]["timeout"] == 60
    assert config["router_settings"]["fallbacks"] == [
        {"chat": ["glm-5.2", "minimax-m3"]},
        {"reasoning": ["chat"]},
    ]
    assert config["litellm_settings"] == {"drop_params": True}

    models_in_config = {
        item["litellm_params"]["model"]
        for item in config["model_list"]
    }
    assert models_in_config == {
        "z-ai/glm-5.2",
        "minimax/minimax-m3",
    }
    model_names = {item["model_name"] for item in config["model_list"]}
    assert {"glm-5.2", "minimax-m3", "chat", "reasoning"}.issubset(model_names)


def test_build_config_classifies_reasoning_models_into_chat_and_reasoning():
    models = [
        {
            "provider": "nvidia",
            "model_id": "z-ai/glm-5.2",
            "api_base": "https://integrate.api.nvidia.com/v1",
            "score": 0.0,
            "capability": ["reasoning", "tool calling", "structured output"],
            "context": "128k",
            "best_for": ["Chat"],
            "extra": {"position": 2},
        }
    ]

    config = build_config(models)
    model_names = {item["model_name"] for item in config["model_list"]}

    assert {"glm-5.2", "chat", "reasoning", "agent"}.issubset(model_names)


def test_build_config_normalizes_metadata_and_auto_generates_capability_models():
    models = [
        {
            "provider": "nvidia",
            "model_id": "z-ai/glm-5.2",
            "api_base": "https://integrate.api.nvidia.com/v1",
            "score": 0.0,
            "capability": ["reasoning", "tool calling", "structured output"],
            "context": "1.0M",
            "best_for": ["Chat"],
            "extra": {
                "position": 2,
                "source": "models.html",
                "benchmark": [
                    {"name": "Intelligence", "value": "51.1/100"},
                    {"name": "Coding", "value": "68.8/100"},
                    {"name": "Agentic", "value": "43.1/100"},
                    {"name": "Speed", "value": "106 tok/s"},
                    {"name": "Context", "value": "1.0M"},
                ],
            },
        }
    ]

    config = build_config(models)

    provider_entry = next(
        item
        for item in config["model_list"]
        if item["model_name"] == "glm-5.2"
    )
    metadata = provider_entry["metadata"]

    assert metadata["context"] == "1.0M"
    assert metadata["context_tokens"] == 1048576
    assert metadata["capability_type"] == [
        "chat",
        "reasoning",
        "coding",
        "agent",
        "long-context",
    ]
    assert metadata["extra"]["source"] == "freellm"
    assert metadata["extra"]["benchmark"] == {
        "intelligence": 51.1,
        "coding": 68.8,
        "agentic": 43.1,
        "speed": 106,
        "context_tokens": 1048576,
    }

    model_names = {item["model_name"] for item in config["model_list"]}
    assert {"chat", "reasoning", "coding", "agent", "long-context"}.issubset(
        model_names
    )
