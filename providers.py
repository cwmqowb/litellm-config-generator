"""Provider 配置"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProviderConfig:
    name: str

    api_base: str

    api_key_envs: List[str]

    api_format: str = "openai"

    extra_headers: Optional[dict] = None


PROVIDERS = {

    "NVIDIA NIM": ProviderConfig(
        name="NVIDIA NIM",
        api_base="https://integrate.api.nvidia.com/v1",
        api_key_envs=[
            "NVIDIA_API_KEY_1",
            "NVIDIA_API_KEY_2",
        ],
    ),

    "OpenRouter": ProviderConfig(
        name="OpenRouter",
        api_base="https://openrouter.ai/api/v1",
        api_key_envs=[
            "OPENROUTER_API_KEY",
        ],
    ),

    "GitHub Models": ProviderConfig(
        name="GitHub Models",
        api_base="https://models.github.ai/inference",
        api_key_envs=[
            "GITHUB_MODELS_API_KEY",
        ],
    ),

    "ModelScope": ProviderConfig(
        name="ModelScope",
        api_base="https://api-inference.modelscope.cn/v1",
        api_key_envs=[
            "MODELSCOPE_API_KEY",
        ],
    ),

    "SambaNova": ProviderConfig(
        name="SambaNova",
        api_base="https://api.sambanova.ai/v1",
        api_key_envs=[
            "SAMBANOVA_API_KEY",
        ],
    ),

    "Agnes AI": ProviderConfig(
        name="Agnes AI",
        api_base="https://apihub.agnes-ai.com/v1",
        api_key_envs=[
            "AGNES_API_KEY",
        ],
    ),

    "Kilo Code": ProviderConfig(
        name="Kilo Code",
        api_base="https://api.kiloai.com/v1",
        api_key_envs=[
            "KILO_API_KEY",
        ],
    ),
}


SUPPORTED_PROVIDERS = set(PROVIDERS.keys())


def get_provider(name: str) -> ProviderConfig | None:
    return PROVIDERS.get(name)