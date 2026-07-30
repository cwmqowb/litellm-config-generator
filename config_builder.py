"""
config_builder.py

LiteLLM config.yaml 生成器

输入:
    List[LogicalModel]

输出:
    LiteLLM YAML 配置

当前模型体系:

LogicalModel
    name
    models[]
    strategy
    capabilities


ModelInfo
    name
    model
    provider
    api_base
    api_key
    capabilities
    score
"""


from typing import List, Dict, Any

import yaml

from models import (
    LogicalModel,
    ModelInfo,
)



# ============================================================
# Provider -> LiteLLM model name 转换
# ============================================================


def build_litellm_model_name(
    model: ModelInfo,
) -> str:
    """
    构造 LiteLLM provider/model 格式

    例如:

    openrouter:
        openrouter/qwen/qwen3

    nvidia:
        nvidia/nvidia/nemotron

    """

    provider = getattr(
        model,
        "provider",
        ""
    )

    model_name = getattr(
        model,
        "model",
        None
    )


    if not model_name:

        model_name = getattr(
            model,
            "name",
            ""
        )


    if "/" in model_name:

        return model_name


    if provider:

        return f"{provider}/{model_name}"


    return model_name



# ============================================================
# 单模型转换
# ============================================================


def build_model_entry(
    model: ModelInfo,
) -> Dict[str, Any]:
    """
    ModelInfo -> LiteLLM model_list entry
    """

    litellm_model = build_litellm_model_name(
        model
    )


    params = {

        "model": litellm_model,

    }


    api_base = getattr(
        model,
        "api_base",
        None
    )

    if api_base:

        params["api_base"] = api_base



    api_key = getattr(
        model,
        "api_key",
        None
    )


    if api_key:

        params["api_key"] = api_key



    return {

        "model_name":
            litellm_model,


        "litellm_params":
            params,

    }



# ============================================================
# LogicalModel 转换
# ============================================================


def build_logical_model_entries(
    logical_model: LogicalModel,
) -> List[Dict[str, Any]]:
    """
    LogicalModel.models

    生成多个 LiteLLM deployment


    不再使用:

        primary_model

        providers

        provider_model

    """

    entries = []


    for model in logical_model.models:

        entries.append(

            build_model_entry(
                model
            )

        )


    return entries



# ============================================================
# YAML 构建
# ============================================================


def build_config(
    logical_models: List[LogicalModel],
) -> Dict[str, Any]:
    """
    生成完整 LiteLLM 配置
    """

    model_list = []


    for logical_model in logical_models:


        model_list.extend(

            build_logical_model_entries(
                logical_model
            )

        )



    return {

        "model_list":
            model_list,


        "litellm_settings": {

            "drop_params": True

        }

    }



# ============================================================
# 保存 YAML
# ============================================================


def save_config(
    logical_models: List[LogicalModel],
    output_file: str = "config.generated.yaml",
):
    """
    输出 YAML 文件
    """


    config = build_config(
        logical_models
    )


    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:


        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False,

        )



    return output_file
