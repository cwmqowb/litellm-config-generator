"""
builder.py

逻辑模型构建器


职责:

List[ModelInfo]

        |

        v

List[LogicalModel]


设计:

按照模型能力生成逻辑入口:


chat

vision

embedding

rerank

coding

reasoning


禁止:

ProviderModel
primary_model
providers
provider_models
"""


from __future__ import annotations


import logging


from typing import Dict, List



from models import (
    ModelInfo,
    LogicalModel,
)



logger = logging.getLogger(__name__)





# ============================================================
# Capability mapping
# ============================================================


CAPABILITY_PRIORITY = [

    "chat",

    "reasoning",

    "coding",

    "vision",

    "embedding",

    "rerank",

]





def get_logical_name(
    model: ModelInfo
) -> str:
    """
    根据能力生成逻辑模型名称
    """



    capability = model.capability



    if capability.embedding:

        return "embedding"



    if capability.rerank:

        return "rerank"



    if capability.vision:

        return "vision"



    if capability.coding:

        return "coding"



    if capability.reasoning:

        return "reasoning"



    return "chat"





# ============================================================
# Build
# ============================================================


def build_logical_models(
    models: List[ModelInfo]
) -> List[LogicalModel]:
    """
    构建逻辑模型


    示例:


    chat

        |

        + model A

        + model B



    vision

        |

        + model C

    """



    groups: Dict[str,List[ModelInfo]] = {}



    for model in models:


        logical_name = get_logical_name(

            model

        )



        model.logical_name = logical_name



        if logical_name not in groups:


            groups[logical_name] = []



        groups[logical_name].append(

            model

        )



    result = []



    for name, items in groups.items():


        # 高分优先

        items.sort(

            key=lambda x:

                x.score,

            reverse=True

        )



        result.append(

            LogicalModel(

                logical_name=name,

                models=items,

                strategy="simple-shuffle",

            )

        )



    return result





# ============================================================
# Compatibility-free entry
# ============================================================


def build(
    models: List[ModelInfo]
) -> List[LogicalModel]:
    """
    Public API
    """

    return build_logical_models(

        models

    )