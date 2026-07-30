"""
providers.py

Provider统一定义


作用:

维护模型Provider基础信息


不负责:

- ProviderModel
- 模型聚合
- fallback
- logical model


架构:

ProviderInfo
      |
      v
ModelInfo.provider
"""


from __future__ import annotations


from dataclasses import dataclass, field

from typing import Dict, Optional



# ============================================================
# ProviderInfo
# ============================================================


@dataclass
class ProviderInfo:
    """
    API Provider信息
    """


    name: str



    api_base: Optional[str] = None



    api_key_env: Optional[str] = None



    api_format: str = "openai"



    enabled: bool = True



    metadata: Dict = field(

        default_factory=dict

    )



# ============================================================
# Provider Registry
# ============================================================


SUPPORTED_PROVIDERS = {


    "NVIDIA NIM": ProviderInfo(

        name="NVIDIA NIM",

        api_base="https://integrate.api.nvidia.com/v1",

        api_key_env="NVIDIA_API_KEY",

    ),



    "OpenRouter": ProviderInfo(

        name="OpenRouter",

        api_base="https://openrouter.ai/api/v1",

        api_key_env="OPENROUTER_API_KEY",

    ),



    "GitHub Models": ProviderInfo(

        name="GitHub Models",

        api_base="https://models.inference.ai.azure.com",

        api_key_env="GITHUB_MODELS_API_KEY",

    ),



    "ModelScope": ProviderInfo(

        name="ModelScope",

        api_base="https://api-inference.modelscope.cn/v1",

        api_key_env="MODELSCOPE_API_KEY",

    ),



    "SambaNova": ProviderInfo(

        name="SambaNova",

        api_base="https://api.sambanova.ai/v1",

        api_key_env="SAMBANOVA_API_KEY",

    ),



    "Agnes AI": ProviderInfo(

        name="Agnes AI",

        api_base="https://api.agnes-ai.com/v1",

        api_key_env="AGNES_API_KEY",

    ),



    "Kilo Code": ProviderInfo(

        name="Kilo Code",

        api_base="",

        api_key_env="KILO_API_KEY",

    ),



}



# ============================================================
# helpers
# ============================================================


def get_provider(
    name: str
) -> Optional[ProviderInfo]:
    """
    获取Provider配置
    """


    if not name:

        return None



    for key, value in SUPPORTED_PROVIDERS.items():


        if key.lower() == name.lower():

            return value



    return None





def is_supported_provider(
    name: str
) -> bool:


    return (
        get_provider(
            name
        )
        is not None
    )





def get_provider_api_base(
    name: str
) -> Optional[str]:


    provider = get_provider(

        name

    )


    if provider:

        return provider.api_base



    return None





def get_provider_key_env(
    name: str
) -> Optional[str]:


    provider = get_provider(

        name

    )


    if provider:

        return provider.api_key_env



    return None