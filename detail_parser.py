"""
detail_parser.py

FreeLLM模型详情解析器


职责:

补充模型详情信息:

- provider
- api_base
- api_key_env
- capability
- score
- metadata


输入:

crawler/parser产生的模型dict


输出:

List[dict]


后续:

normalizer.py

List[ModelInfo]


禁止:

ProviderModel
LogicalModel
"""

from __future__ import annotations


import html

import json

import logging

import re


from typing import Any, Dict, List




logger = logging.getLogger(__name__)





# ============================================================
# Capability Detect
# ============================================================


def detect_capability(
    model_id: str,
    name: str = ""
) -> List[str]:
    """
    根据模型名称判断能力


    """



    text = (

        f"{model_id} {name}"

        .lower()

    )



    result = []



    if any(
        x in text
        for x in [

            "embed",

            "embedding",

        ]
    ):


        result.append(
            "embedding"
        )



    if any(
        x in text
        for x in [

            "vision",

            "-vl",

            "vl-",

            "multimodal",

            "image",

        ]
    ):


        result.append(
            "vision"
        )



    if any(
        x in text
        for x in [

            "rerank",

        ]
    ):


        result.append(
            "rerank"
        )



    if any(
        x in text
        for x in [

            "coder",

            "code",

            "coding",

        ]
    ):


        result.append(
            "coding"
        )



    if any(
        x in text
        for x in [

            "reasoning",

            "think",

            "r1",

        ]
    ):


        result.append(
            "reasoning"
        )



    if not result:


        result.append(
            "chat"
        )



    return result





# ============================================================
# JSON extraction
# ============================================================


def decode_html(
    content: str
) -> str:


    return html.unescape(

        content

    )





def extract_provider_info(
    source: str
) -> Dict[str, Any]:
    """
    提取页面provider信息


    freellm:

    providers:

        xxx:

            baseUrl

            verifiedProtocols

    """



    result = {}



    source = decode_html(

        source

    )



    patterns = {


        "api_base":

            r'"baseUrl"\s*:\s*"([^"]+)"',



        "score":

            r'"score"\s*:\s*([0-9.]+)',


    }



    for key, pattern in patterns.items():


        match = re.search(

            pattern,

            source

        )



        if match:


            result[key] = match.group(1)



    return result





# ============================================================
# Detail merge
# ============================================================


def enrich_model(
    model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    补充模型详情
    """



    model_id = model.get(

        "model_id",

        ""

    )


    name = model.get(

        "name",

        ""

    )



    capability = detect_capability(

        model_id,

        name

    )



    metadata = model.get(

        "metadata",

        {}

    )



    detail = {



        "capability":

            capability,



        "score":

            model.get(

                "score",

                0

            ),



        "api_base":

            model.get(

                "api_base"

            ),



        "api_key_env":

            model.get(

                "api_key_env"

            ),



        "metadata":

            metadata,

    }



    model.update(

        detail

    )



    return model





# ============================================================
# Public API
# ============================================================


def parse_details(
    models: List[Dict]
) -> List[Dict]:
    """
    批量详情解析
    """



    result = []



    for model in models:


        try:


            result.append(

                enrich_model(

                    model

                )

            )


        except Exception:


            logger.exception(

                "detail parse failed: %s",

                model

            )



    return result