"""
normalizer.py

模型数据标准化

输入:

crawler/parser/detail_parser
        |
        v
dict


输出:

List[ModelInfo]


禁止:

ProviderModel
primary_model
providers
provider_model
"""

from __future__ import annotations

import logging
import re

from typing import Any, Dict, List


from models import (
    ModelInfo,
    ModelCapability,
    ModelPricing,
)


logger = logging.getLogger(__name__)



# ============================================================
# text utils
# ============================================================


def clean_text(
    value: Any
) -> str:

    if value is None:
        return ""

    return (
        str(value)
        .strip()
    )



def normalize_name(
    name: str
) -> str:

    if not name:
        return "unknown"

    name = (
        name
        .lower()
        .strip()
    )

    name = re.sub(
        r"\s+",
        "-",
        name
    )

    return name



# ============================================================
# logical name
# ============================================================


def build_logical_name(
    model_id: str,
    name: str
) -> str:
    """
    根据模型名称生成逻辑模型名称

    示例:

    qwen3-235b
        ->
    qwen

    deepseek-v3
        ->
    deepseek
    """

    source = (
        model_id
        or
        name
        or
        "unknown"
    ).lower()



    keywords = [

        "qwen",

        "deepseek",

        "kimi",

        "glm",

        "chatglm",

        "llama",

        "gemma",

        "mistral",

        "nemotron",

        "mixtral",

    ]


    for keyword in keywords:

        if keyword in source:

            return keyword



    return (
        source
        .replace(
            "/",
            "-"
        )
        .split("-")[0]
    )



# ============================================================
# capability parser
# ============================================================


def parse_capabilities(
    data: Dict
) -> ModelCapability:

    capability = ModelCapability()



    values = []


    raw = (
        data.get(
            "capabilities"
        )
        or
        data.get(
            "capability"
        )
        or
        []
    )



    if isinstance(
        raw,
        str
    ):

        values.append(
            raw
        )


    elif isinstance(
        raw,
        list
    ):

        values.extend(
            raw
        )


    text = (
        " "
        .join(
            [
                str(x)
                for x in values
            ]
        )
        .lower()
    )



    rules = {

        "chat":
            [
                "chat",
                "conversation",
                "instruction",
            ],


        "vision":
            [
                "vision",
                "image",
                "multimodal",
            ],


        "reasoning":
            [
                "reasoning",
                "thinking",
                "cot",
            ],


        "coding":
            [
                "code",
                "coder",
                "coding",
            ],


        "embedding":
            [
                "embedding",
            ],


        "rerank":
            [
                "rerank",
            ],


        "image":
            [
                "image generation",
                "diffusion",
            ],


        "audio":
            [
                "audio",
                "speech",
            ],


        "tool_calling":
            [
                "tool",
                "function calling",
            ],


        "json_mode":
            [
                "json",
                "structured",
            ],

    }



    for field_name, words in rules.items():

        for word in words:

            if word in text:

                setattr(
                    capability,
                    field_name,
                    True
                )

                break



    capability.raw = values


    return capability



# ============================================================
# single normalize
# ============================================================


def normalize_model(
    item: Dict
) -> ModelInfo:
    """
    dict -> ModelInfo
    """



    name = (
        item.get(
            "name"
        )
        or
        item.get(
            "model"
        )
        or
        item.get(
            "model_id"
        )
        or
        "unknown"
    )


    model_id = (
        item.get(
            "model_id"
        )
        or
        item.get(
            "model"
        )
        or
        name
    )



    provider = (
        item.get(
            "provider"
        )
        or
        ""
    )



    logical_name = (
        item.get(
            "logical_name"
        )
        or
        build_logical_name(
            model_id,
            name
        )
    )



    model = ModelInfo(

        name=normalize_name(
            name
        ),

        logical_name=logical_name,

        provider=provider,

        model_id=model_id,


        api_base=(
            item.get(
                "api_base"
            )
            or
            item.get(
                "base_url"
            )
        ),


        api_key_env=(
            item.get(
                "api_key_env"
            )
        ),


        api_format=(
            item.get(
                "api_format"
            )
        ),



        capabilities=parse_capabilities(
            item
        ),



        context_window=(
            item.get(
                "context_window"
            )
        ),


        max_output_tokens=(
            item.get(
                "max_output_tokens"
            )
        ),



        free=(
            item.get(
                "free",
                False
            )
        ),



        pricing=ModelPricing(

            input_price=(
                item.get(
                    "input_price"
                )
            ),

            output_price=(
                item.get(
                    "output_price"
                )
            ),

            free=(
                item.get(
                    "free",
                    False
                )
            )

        ),



        score=float(

            item.get(
                "score",
                0
            )

            or

            0

        ),



        tags=(
            item.get(
                "tags"
            )
            or
            []
        ),



        metadata=item,

    )



    return model



# ============================================================
# batch normalize
# ============================================================


def normalize_models(
    models: List[Dict]
) -> List[ModelInfo]:
    """
    List[dict]

        |

        v

    List[ModelInfo]
    """

    result = []



    for item in models:

        try:

            result.append(
                normalize_model(
                    item
                )
            )


        except Exception:

            logger.exception(
                "normalize model failed: %s",
                item
            )



    return result