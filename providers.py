from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProviderConfig:
    name: str

    api_base: str

    api_key_envs: List[str]

    api_format: str = "openai"

    extra_headers: Optional[dict] = None


PROVIDER_PRIORITY = [
    "NVIDIA NIM",
    "OpenRouter",
    "GitHub Models",
    "ModelScope",
    "SambaNova",
    "Agnes AI",
    "Kilo Code",
]


PROVIDERS: Dict[str, ProviderConfig] = {

    "NVIDIA NIM": ProviderConfig(
        name="NVIDIA NIM",
        api_base="https://integrate.api.nvidia.com/v1",
        api_key_envs=[
            "NVIDIA_API_KEY",
            "NVIDIA_API_KEY_1",
            "NVIDIA_API_KEY_2",
            "NVIDIA_API_KEY_3",
            "NVIDIA_API_KEY_4",
            "NVIDIA_API_KEY_5",
        ],
    ),

    "OpenRouter": ProviderConfig(
        name="OpenRouter",
        api_base="https://openrouter.ai/api/v1",
        api_key_envs=[
            "OPENROUTER_API_KEY",
            "OPENROUTER_API_KEY_1",
            "OPENROUTER_API_KEY_2",
            "OPENROUTER_API_KEY_3",
        ],
    ),

    "GitHub Models": ProviderConfig(
        name="GitHub Models",
        api_base="https://models.inference.ai.azure.com",
        api_key_envs=[
            "GITHUB_MODELS_API_KEY",
            "GITHUB_MODELS_API_KEY_1",
            "GITHUB_MODELS_API_KEY_2",
        ],
    ),

    "ModelScope": ProviderConfig(
        name="ModelScope",
        api_base="https://api-inference.modelscope.cn/v1",
        api_key_envs=[
            "MODELSCOPE_API_KEY",
            "MODELSCOPE_API_KEY_1",
            "MODELSCOPE_API_KEY_2",
        ],
    ),

    "SambaNova": ProviderConfig(
        name="SambaNova",
        api_base="https://api.sambanova.ai/v1",
        api_key_envs=[
            "SAMBANOVA_API_KEY",
            "SAMBANOVA_API_KEY_1",
        ],
    ),

    "Agnes AI": ProviderConfig(
        name="Agnes AI",
        api_base="https://apihub.agnes-ai.com/v1",
        api_key_envs=[
            "AGNES_API_KEY",
            "AGNES_API_KEY_1",
        ],
    ),

    "Kilo Code": ProviderConfig(
        name="Kilo Code",
        api_base="https://api.kiloai.com/v1",
        api_key_envs=[
            "KILO_API_KEY",
            "KILO_API_KEY_1",
        ],
    ),
}


SUPPORTED_PROVIDERS = set(PROVIDER_PRIORITY)


def get_provider(name: str) -> Optional[ProviderConfig]:
    return PROVIDERS.get(name)


def provider_priority(name: str) -> int:
    try:
        return PROVIDER_PRIORITY.index(name)
    except ValueError:
        return 999


def sort_provider_models(provider_models):
    return sorted(
        provider_models,
        key=lambda x: provider_priority(x.provider),
    )
