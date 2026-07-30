"""
normalizer.py

模型标准化模块

输入:
    List[ModelInfo]

输出:
    List[LogicalModel]

负责:
    1. 模型名称归一化
    2. 按逻辑模型聚合
    3. 生成 LogicalModel.models

当前架构:

LogicalModel
    name
    models[]
    strategy


ModelInfo
    name
    model_id
    provider
    api_base
    api_key_env
    capability
    score
"""


from typing import List, Dict

from models import (
    ModelInfo,
    LogicalModel,
)



# ============================================================
# 名称归一化
# ============================================================


def normalize_model_name(
    name: str,
) -> str:

    if not name:
        return "unknown"


    name = (
        name
        .strip()
        .lower()
    )


    replacements = {

        "-": "_",

        ".": "_",

        "/": "_",

    }


    for k, v in replacements.items():

        name = name.replace(
            k,
            v,
        )


    return name



# ============================================================
# 判断逻辑模型
# ============================================================


def get_logical_name(
    model: ModelInfo,
) -> str:

    """
    根据真实模型名称
    生成逻辑模型名

    示例:

    qwen3-235b
        ->
    qwen3

    deepseek-v3
        ->
    deepseek
    """


    name = (
        getattr(
            model,
            "name",
            None,
        )
        or
        getattr(
            model,
            "model_id",
            None,
        )
        or
        "unknown"
    )


    name = normalize_model_name(
        name
    )


    keywords = [

        "qwen",

        "deepseek",

        "kimi",

        "glm",

        "llama",

        "gemma",

        "mistral",

        "nemotron",

    ]


    for keyword in keywords:

        if keyword in name:

            return keyword



    return name



# ============================================================
# 主入口
# ============================================================


def normalize_models(
    models: List[ModelInfo],
) -> List[LogicalModel]:

    """
    ModelInfo[]

    转换:

    LogicalModel[]
    """


    groups: Dict[
        str,
        List[ModelInfo]
    ] = {}



    for model in models:


        logical_name = (
            get_logical_name(
                model
            )
        )


        groups.setdefault(
            logical_name,
            []
        )


        groups[
            logical_name
        ].append(
            model
        )



    result = []



    for name, items in groups.items():


        # 按 score 排序
        items.sort(
            key=lambda x:
                getattr(
                    x,
                    "score",
                    0
                )
                or 0,

            reverse=True,
        )


        logical_model = LogicalModel(

            name=name,


            models=items,


            strategy="fallback",

        )


        result.append(
            logical_model
        )



    return result
