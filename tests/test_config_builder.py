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
    assert {"reasoning": ["glm-5.2", "minimax-m3"]} in fallback_aliases

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
        {"reasoning": ["glm-5.2", "minimax-m3"]},
    ]
    assert config["litellm_settings"] == {"drop_params": True}

    # Verify concrete model entries use provider model IDs
    provider_models_in_config = {
        item["litellm_params"]["model"]
        for item in config["model_list"]
        if item["model_name"] in ["glm-5.2", "minimax-m3"]
    }
    assert provider_models_in_config == {
        "z-ai/glm-5.2",
        "minimax/minimax-m3",
    }

    # Verify logical capability entries reference model_name aliases, NOT provider model IDs
    chat_entry = next(item for item in config["model_list"] if item["model_name"] == "chat")
    reasoning_entry = next(item for item in config["model_list"] if item["model_name"] == "reasoning")
    assert chat_entry["litellm_params"]["model"] == "glm-5.2"
    assert reasoning_entry["litellm_params"]["model"] == "glm-5.2"


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

    assert metadata["provider_model"] == "z-ai/glm-5.2"
    assert metadata["provider_priority"] == 1
    assert metadata["uid"] == "nvidia/glm-5.2"
    assert metadata["context"] == "1.0M"
    assert metadata["context_tokens"] == 1048576
    assert metadata["capability"] == ["reasoning", "tool", "json"]
    assert metadata["capability_type"] == [
        "reasoning",
        "coding",
        "agent",
        "long-context",
    ]
    assert metadata["supports"] == ["tool_call", "json"]
    assert metadata["extra"]["source"] == "freellm"
    assert metadata["extra"]["benchmark"]["intelligence"] == 51.1
    assert metadata["extra"]["benchmark"]["coding"] == 68.8
    assert metadata["extra"]["benchmark"]["agentic"] == 43.1
    assert metadata["extra"]["benchmark"]["speed"] == 106
    assert metadata["extra"]["benchmark"]["context_tokens"] == 1048576
    assert metadata["extra"]["benchmark"]["overall"] == 54.3

    model_names = {item["model_name"] for item in config["model_list"]}
    assert {"chat", "reasoning", "coding", "agent", "long-context"}.issubset(
        model_names
    )
