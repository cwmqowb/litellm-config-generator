"""
providers.py

Provider基础配置


职责:

维护 Provider 的连接信息


不负责:

- 模型聚合
- 逻辑模型
- fallback
- ProviderModel


数据流:

ProviderInfo
      |
      v
ModelInfo.api_base / api_key_env
      |
      v
LiteLLM config
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


PROVIDER_REGISTRY: Dict[str, ProviderInfo] = {



    "nvidia": ProviderInfo(

        name="nvidia",

        api_base=
        "https://integrate.api.nvidia.com/v1",

        api_key_env=
        "NVIDIA_API_KEY",

    ),




    "openrouter": ProviderInfo(

        name="openrouter",

        api_base=
        "https://openrouter.ai/api/v1",

        api_key_env=
        "OPENROUTER_API_KEY",

    ),




    "openai": ProviderInfo(

        name="openai",

        api_base=
        "https://api.openai.com/v1",

        api_key_env=
        "OPENAI_API_KEY",

    ),




    "github": ProviderInfo(

        name="github",

        api_base=
        "https://models.inference.ai.azure.com",

        api_key_env=
        "GITHUB_MODELS_API_KEY",

    ),




    "modelscope": ProviderInfo(

        name="modelscope",

        api_base=
        "https://api-inference.modelscope.cn/v1",

        api_key_env=
        "MODELSCOPE_API_KEY",

    ),




    "sambanova": ProviderInfo(

        name="sambanova",

        api_base=
        "https://api.sambanova.ai/v1",

        api_key_env=
        "SAMBANOVA_API_KEY",

    ),




    "agnes": ProviderInfo(

        name="agnes",

        api_base=
        "https://api.agnes-ai.com/v1",

        api_key_env=
        "AGNES_API_KEY",

    ),



}





# ============================================================
# helpers
# ============================================================


def normalize_provider_name(
    name: str
) -> str:
    """
    provider标准化
    """

    if not name:

        return ""



    value = (

        name

       .lower()

       .strip()

    )



    aliases = {


        "nvidia nim":

            "nvidia",


        "github models":

            "github",


        "model scope":

            "modelscope",


        "samba nova":

            "sambanova",


        "agnes ai":

            "agnes",

    }



    return aliases.get(
        value,
        value
    )





def get_provider(
    name: str
) -> Optional[ProviderInfo]:
    """
    获取Provider配置
    """

    key = normalize_provider_name(
        name
    )


    return PROVIDER_REGISTRY.get(
        key
    )





def get_api_base(
    provider: str
) -> Optional[str]:

    info = get_provider(
        provider
    )


    if info:

        return info.api_base



    return None





def get_api_key_env(
    provider: str
) -> Optional[str]:

    info = get_provider(
        provider
    )


    if info:

        return info.api_key_env



    return None