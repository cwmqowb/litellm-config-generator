"""
Model normalizer

负责：

1. 模型名称标准化
2. Provider namespace 清理
3. free 标识清理
4. 品牌模型归一
5. ModelInfo 标准化
6. 模型评分
7. LogicalModel 聚合


数据流：

ModelInfo
    |
    v
normalize_model()
    |
    v
ModelInfo
    |
    v
build_logical_models()
    |
    v
LogicalModel

"""


from __future__ import annotations


import re
from typing import Dict, List


from models import (
    ModelInfo,
    LogicalModel,
)



# =====================================================
# Vendor namespace
# =====================================================


VENDOR_PREFIXES = {

    "z-ai",
    "zhipuai",
    "glm",

    "deepseek",
    "deepseek-ai",

    "moonshot",
    "moonshotai",

    "qwen",
    "alibaba",

    "google",
    "gemini",

    "meta",
    "meta-llama",

    "mistralai",

    "nvidia",

}



# =====================================================
# Provider suffix
# =====================================================


PROVIDER_SUFFIX = [

    "__nvidia",

    "__nvidia_nim",

    "__openrouter",

    "__github",

    "__github_models",

    "__modelscope",

    "__sambanova",

    "__agnes",

    "__kilo",

]



# =====================================================
# Free suffix
# =====================================================


FREE_SUFFIX = [

    ":free",

    "-free",

    "_free",

    "(free)",

    "[free]",

]



# =====================================================
# text cleanup
# =====================================================


def clean_text(
    value: str,
) -> str:


    if not value:

        return ""


    value = (
        str(value)
        .strip()
        .lower()
    )


    value = value.replace(
        " ",
        "-"
    )


    return value



# =====================================================
# remove vendor
# =====================================================


def remove_vendor_prefix(
    name: str,
) -> str:


    if "/" not in name:

        return name



    parts = name.split("/")


    if len(parts) != 2:

        return name



    prefix, model = parts



    if prefix.lower() in VENDOR_PREFIXES:

        return model



    return model



# =====================================================
# remove provider suffix
# =====================================================


def remove_provider_suffix(
    name: str,
) -> str:


    for suffix in PROVIDER_SUFFIX:

        name = name.replace(
            suffix,
            ""
        )


    return name



# =====================================================
# remove free tag
# =====================================================


def remove_free_tag(
    name: str,
) -> str:


    for suffix in FREE_SUFFIX:

        name = name.replace(
            suffix,
            ""
        )


    name = re.sub(
        r"\s*\(free\)",
        "",
        name,
        flags=re.I
    )


    return name



# =====================================================
# brand normalize
# =====================================================


def normalize_brand(
    name: str,
) -> str:


    alias = {


        "glm5.2":
            "glm-5.2",


        "glm-5-2":
            "glm-5.2",


        "deepseekv4":
            "deepseek-v4",


        "deepseekv4flash":
            "deepseek-v4-flash",


        "qwen3":
            "qwen3",


    }


    key = (

        name
        .lower()
        .replace(
            "-",
            ""
        )
        .replace(
            "_",
            ""
        )
        .replace(
            ".",
            ""
        )

    )


    return alias.get(
        key,
        name
    )



# =====================================================
# public name normalize
# =====================================================


def normalize_model_name(
    name: str,
) -> str:


    if not name:

        return ""



    name = clean_text(
        name
    )


    name = remove_vendor_prefix(
        name
    )


    name = remove_provider_suffix(
        name
    )


    name = remove_free_tag(
        name
    )


    name = normalize_brand(
        name
    )



    name = re.sub(
        r"_+",
        "-",
        name
    )


    name = re.sub(
        r"-+",
        "-",
        name
    )


    return name.strip("-")



# =====================================================
# ModelInfo normalize
# =====================================================


def normalize_model(
    model: ModelInfo,
) -> ModelInfo:


    """
    标准化 ModelInfo

    不创建新对象
    保留 metadata
    """


    model.name = normalize_model_name(
        model.name
    )


    model.model_id = normalize_model_name(
        model.model_id
    )


    return model



# =====================================================
# score calculation
# =====================================================


def calculate_model_score(
    model: ModelInfo,
) -> int:


    score = 50



    provider = (
        model.provider
        .lower()
        if model.provider
        else ""
    )


    provider_bonus = {


        "nvidia nim": 15,

        "nvidia": 15,


        "modelscope": 12,


        "sambanova": 12,


        "github models": 10,


        "agnes ai": 10,


        "openrouter": 8,

    }



    score += provider_bonus.get(
        provider,
        0
    )



    caps = model.capabilities



    if caps:


        if caps.reasoning:

            score += 10



        if caps.vision:

            score += 5



        if caps.tool_calling:

            score += 5



    if (
        model.context_window
        and
        model.context_window >= 128000
    ):

        score += 10


    elif (
        model.context_window
        and
        model.context_window >= 32000
    ):

        score += 5



    return min(
        score,
        100
    )



# =====================================================
# logical model builder
# =====================================================


def build_logical_models(
    models: List[ModelInfo],
) -> Dict[str, LogicalModel]:


    logical_models = {}



    for model in models:


        model = normalize_model(
            model
        )


        model.score = (
            calculate_model_score(
                model
            )
        )



        key = model.name



        if not key:

            continue



        if key not in logical_models:


            logical_models[key] = LogicalModel(

                name=key,

                models=[],

            )



        logical_models[key].models.append(
            model
        )



    # 排序

    for logical in logical_models.values():


        logical.models.sort(

            key=lambda m:

                m.score
                or 0,

            reverse=True

        )


        if logical.models:


            logical.primary_model = (
                logical.models[0]
            )



    return logical_models
