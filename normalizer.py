"""
normalizer.py

模型标准化


职责:

输入:

parser/detail_parser输出的dict


输出:

List[ModelInfo]


核心:

dict
    |
    v
ModelInfo


禁止:

ProviderModel
primary_model
providers
provider_models
"""


from __future__ import annotations


import logging


from typing import Any, Dict, List



from models import (
    ModelInfo,
    ModelCapability,
    ModelPricing,
)



from providers import (
    get_api_base,
    get_api_key_env,
    normalize_provider_name,
)



logger = logging.getLogger(__name__)





# ============================================================
# Capability
# ============================================================


def build_capability(
    values: Any
) -> ModelCapability:
    """
    构造能力对象
    """



    capability = ModelCapability()



    if isinstance(

        values,

        str

    ):


        values = [

            values

        ]



    if not isinstance(

        values,

        list

    ):


        values = []



    normalized = [

        str(x).lower()

        for x in values

    ]



    capability.raw = normalized



    for item in normalized:


        if item == "chat":

            capability.chat = True



        elif item == "vision":

            capability.vision = True



        elif item == "reasoning":

            capability.reasoning = True



        elif item == "coding":

            capability.coding = True



        elif item == "embedding":

            capability.embedding = True



        elif item == "rerank":

            capability.rerank = True



        elif item == "image":

            capability.image = True



        elif item == "audio":

            capability.audio = True



        elif item in (

            "tool",

            "tool_calling"

        ):

            capability.tool_calling = True



        elif item == "json":

            capability.json_mode = True




    if not normalized:

        capability.chat = True



    return capability





# ============================================================
# Normalize
# ============================================================


def normalize_model(
    data: Dict[str, Any]
) -> ModelInfo:
    """
    dict -> ModelInfo
    """



    model_id = (

        data.get(

            "model_id"

        )

        or ""

    )



    name = (

        data.get(

            "name"

        )

        or model_id

    )



    provider = normalize_provider_name(

        data.get(

            "provider"

        )

        or ""

    )



    if not provider and "/" in model_id:


        provider = (

            model_id

            .split("/")[0]

        )



    capability = build_capability(

        data.get(

            "capability"

        )

    )



    api_base = (

        data.get(

            "api_base"

        )

        or

        get_api_base(

            provider

        )

    )



    api_key_env = (

        data.get(

            "api_key_env"

        )

        or

        get_api_key_env(

            provider

        )

    )



    score = float(

        data.get(

            "score",

            0

        )

        or 0

    )



    pricing = ModelPricing(

        free=

            bool(

                data.get(

                    "free",

                    True

                )

            )

    )





    return ModelInfo(

        name=name,


        model_id=model_id,


        provider=provider,



        api_base=api_base,


        api_key_env=api_key_env,



        api_format=

            data.get(

                "api_format",

                "openai"

            ),



        capability=capability,



        context_window=

            data.get(

                "context_window"

            ),



        max_output_tokens=

            data.get(

                "max_output_tokens"

            ),



        free=

            pricing.free,



        pricing=pricing,



        score=score,



        metadata=

            data.get(

                "metadata",

                {}

            ),

    )





# ============================================================
# Public API
# ============================================================


def normalize_models(
    models: List[Dict[str, Any]]
) -> List[ModelInfo]:
    """
    批量标准化
    """



    result = []



    seen = set()



    for item in models:


        try:


            model = normalize_model(

                item

            )



            if not model.model_id:


                continue



            if model.model_id in seen:


                continue



            seen.add(

                model.model_id

            )



            result.append(

                model

            )



        except Exception:


            logger.exception(

                "normalize failed: %s",

                item

            )



    return result