"""
config_builder.py

Build LiteLLM configuration.

Responsibility:

ModelInfo
    |
    v
LiteLLM yaml


Responsible for:

- logical model grouping
- provider model naming
- metadata generation
- yaml output


Not responsible for:

- html parsing
- model crawling
- provider discovery
- validation
"""


from __future__ import annotations


import yaml
import logging

from typing import List, Dict, Any


from providers import (
    get_provider,
    normalize_provider_name,
)


logger = logging.getLogger(__name__)



# ============================================================
# Logical Model Detection
# ============================================================


def detect_logical_model(
    model: Dict[str, Any],
) -> str:
    """
    Detect LiteLLM logical model name.


    Priority:

    vision
        >
    reasoning
        >
    chat

    """


    capability = model.get(
        "capability",
        []
    )


    if not capability:

        capability = []


    capability = [

        str(x).lower()

        for x in capability

    ]



    extra = model.get(
        "extra",
        {}
    )


    best_for = model.get(
        "best_for",
        []
    )


    best_for = [

        str(x).lower()

        for x in best_for

    ]



    #
    # Vision / multimodal
    #

    vision_keywords = [

        "vision",

        "image",

        "file attachments",

        "multimodal",

    ]


    for item in capability + best_for:

        if item in vision_keywords:

            return "vision"



    #
    # Reasoning
    #

    reasoning_keywords = [

        "reasoning",

    ]


    for item in capability:

        if item in reasoning_keywords:

            return "reasoning"



    return "chat"




# ============================================================
# LiteLLM model name
# ============================================================


def build_litellm_model_name(
    model: Dict[str, Any],
) -> str:
    """
    Build provider/model format.

    Example:

        nvidia
        z-ai/glm-5.2

    becomes:

        nvidia/z-ai/glm-5.2

    """


    provider = normalize_provider_name(

        model.get(

            "provider",

            ""

        )

    )


    name = (

        model.get(

            "model_id"

        )

        or model.get(

            "name"

        )

        or ""

    )



    if not name:

        return ""



    #
    # already formatted
    #

    if "/" in name:

        #
        # avoid duplicate prefix
        #

        if name.startswith(

            provider + "/"

        ):

            return name



    if provider:

        return (

            provider

            +

            "/"

            +

            name

        )


    return name





# ============================================================
# Metadata
# ============================================================


def build_metadata(
    model: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Preserve model information.
    """


    metadata = {


        "provider":

            model.get(

                "provider"

            ),



        "score":

            model.get(

                "score",

                0.0

            ),



        "capability":

            model.get(

                "capability",

                []

            ),



        "context":

            model.get(

                "context"

            ),



        "best_for":

            model.get(

                "best_for",

                []

            ),


    }



    extra = model.get(

        "extra"

    )


    if extra:

        metadata["extra"] = extra



    return metadata





# ============================================================
# Build Config
# ============================================================


def build_config(
    models: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build LiteLLM config.

    Keep public interface stable.
    """


    model_list = []



    for model in models:


        provider = normalize_provider_name(

            model.get(

                "provider",

                ""

            )

        )



        #
        # Provider validation
        #

        provider_info = get_provider(

            provider

        )


        if not provider_info:


            logger.warning(

                "skip unsupported provider: %s",

                provider,

            )


            continue




        litellm_model = build_litellm_model_name(

            model

        )


        if not litellm_model:


            logger.warning(

                "skip model without id: %s",

                model,

            )


            continue



        logical_name = detect_logical_model(

            model

        )



        params = {


            "model":

                litellm_model,



            "api_base":

                provider_info.api_base,



        }



        if provider_info.api_key_env:


            params["api_key"] = (

                "os.environ/"

                +

                provider_info.api_key_env

            )




        item = {


            "model_name":

                logical_name,



            "litellm_params":

                params,



            "metadata":

                build_metadata(

                    model

                ),


        }



        model_list.append(

            item

        )



    return {


        "model_list":

            model_list


    }





# ============================================================
# Save YAML
# ============================================================


def save_config(
    config: Dict[str, Any],
    output: str,
):
    """
    Save yaml file.
    """


    with open(

        output,

        "w",

        encoding="utf-8"

    ) as f:


        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False,

        )


    logger.info(

        "saved config: %s",

        output,

    )