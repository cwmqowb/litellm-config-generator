"""
providers.py

Provider configuration registry.


Responsibility:

Maintain provider connection information:

    provider
        |
        +-- api_base
        |
        +-- api_key_env


Used by:

config_builder.py


NOT responsible for:

- model parsing
- model aggregation
- logical model
- fallback strategy
- ModelInfo creation

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
    Provider connection information.
    """

    name: str


    api_base: Optional[str] = None


    api_key_env: Optional[str] = None


    api_format: str = "openai"


    metadata: Dict = field(
        default_factory=dict
    )



# ============================================================
# Registry
# ============================================================


PROVIDER_REGISTRY: Dict[str, ProviderInfo] = {


    "nvidia":

        ProviderInfo(

            name="nvidia",

            api_base=

                "https://integrate.api.nvidia.com/v1",

            api_key_env=

                "NVIDIA_API_KEY",

        ),



    "openrouter":

        ProviderInfo(

            name="openrouter",

            api_base=

                "https://openrouter.ai/api/v1",

            api_key_env=

                "OPENROUTER_API_KEY",

        ),



    "github":

        ProviderInfo(

            name="github",

            api_base=

                "https://models.inference.ai.azure.com",

            api_key_env=

                "GITHUB_MODELS_API_KEY",

        ),



    "modelscope":

        ProviderInfo(

            name="modelscope",

            api_base=

                "https://api-inference.modelscope.cn/v1",

            api_key_env=

                "MODELSCOPE_API_KEY",

        ),



    "sambanova":

        ProviderInfo(

            name="sambanova",

            api_base=

                "https://api.sambanova.ai/v1",

            api_key_env=

                "SAMBANOVA_API_KEY",

        ),



    "agnes":

        ProviderInfo(

            name="agnes",

            api_base=

                "https://api.agnes-ai.com/v1",

            api_key_env=

                "AGNES_API_KEY",

        ),



    "kilo":

        ProviderInfo(

            name="kilo",

            api_base=

                "https://api.kilo.ai/v1",

            api_key_env=

                "KILO_API_KEY",

        ),

}



# ============================================================
# Normalize
# ============================================================


def normalize_provider_name(
    name: str,
) -> str:
    """
    Normalize provider name.

    Example:

    NVIDIA NIM
        ->
    nvidia


    GitHub Models
        ->
    github

    """

    if not name:

        return ""



    value = (

        str(name)

        .strip()

        .lower()

    )



    aliases = {


        "nvidia nim":

            "nvidia",



        "nvidia":

            "nvidia",



        "open router":

            "openrouter",



        "openrouter":

            "openrouter",



        "github models":

            "github",



        "github":

            "github",



        "model scope":

            "modelscope",



        "modelscope":

            "modelscope",



        "samba nova":

            "sambanova",



        "sambanova":

            "sambanova",



        "agnes ai":

            "agnes",



        "agnes":

            "agnes",



        "kilo code":

            "kilo",



        "kilo":

            "kilo",

    }



    return aliases.get(

        value,

        value,

    )



# ============================================================
# Lookup helpers
# ============================================================


def get_provider(
    name: str,
) -> Optional[ProviderInfo]:
    """
    Get provider config.
    """


    key = normalize_provider_name(

        name

    )


    return PROVIDER_REGISTRY.get(

        key

    )



def get_api_base(
    provider: str,
) -> Optional[str]:
    """
    Get provider API base.
    """


    info = get_provider(

        provider

    )


    if info:

        return info.api_base



    return None



def get_api_key_env(
    provider: str,
) -> Optional[str]:
    """
    Get API key environment variable.
    """


    info = get_provider(

        provider

    )


    if info:

        return info.api_key_env



    return None