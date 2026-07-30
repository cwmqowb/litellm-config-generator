"""
config_builder.py

LiteLLM config.yaml生成器


输入:

List[LogicalModel]


结构:

LogicalModel
      |
      +-- ModelInfo
              |
              +-- provider
              +-- model_id
              +-- api_base
              +-- api_key_env


输出:

LiteLLM config.yaml


禁止:

ProviderModel
primary_model
providers
mode
"""


from __future__ import annotations


from typing import Any, Dict, List


import yaml


from models import (
    LogicalModel,
    ModelInfo,
)



# ============================================================
# LiteLLM model name
# ============================================================


def build_litellm_model_name(
    model: ModelInfo
) -> str:
    """
    生成 LiteLLM provider/model 格式
    """

    model_id = (
        model.model_id
        or
        model.name
    )


    if "/" in model_id:

        return model_id



    provider = (
        model.provider
        .lower()
        .replace(
            " ",
            ""
        )
    )


    if provider:

        return (
            provider
            +
            "/"
            +
            model_id
        )


    return model_id



# ============================================================
# Deployment
# ============================================================


def build_model_entry(
    logical_model: LogicalModel,
    model: ModelInfo
) -> Dict[str, Any]:
    """
    单个 LiteLLM deployment
    """



    litellm_model = (
        build_litellm_model_name(
            model
        )
    )



    params = {

        "model":
            litellm_model

    }



    if model.api_base:


        params["api_base"] = (
            model.api_base
        )



    if model.api_key_env:


        params["api_key"] = (

            "os.environ/"
            +
            model.api_key_env

        )



    return {

        "model_name":
            logical_model.logical_name,


        "litellm_params":
            params,


        "metadata":
        {

            "provider":
                model.provider,


            "model_id":
                model.model_id,


            "score":
                model.score

        }

    }



# ============================================================
# LogicalModel
# ============================================================


def build_logical_model_entries(
    logical_model: LogicalModel
) -> List[Dict[str, Any]]:
    """
    LogicalModel.models

        |

        v

    LiteLLM model_list

    """


    entries = []



    for model in logical_model.models:


        entries.append(

            build_model_entry(

                logical_model,

                model

            )

        )



    return entries



# ============================================================
# Config
# ============================================================


def build_config(
    logical_models: List[LogicalModel]
) -> Dict[str, Any]:
    """
    生成完整 LiteLLM 配置
    """



    model_list = []



    for logical_model in logical_models:


        for entry in build_logical_model_entries(
            logical_model
        ):

            model_list.append(
                entry
            )



    return {


        "model_list":

            model_list,



        "router_settings":
        {

            "routing_strategy":
                "simple-shuffle",


            "enable_pre_call_checks":
                True

        },



        "litellm_settings":
        {

            "drop_params":
                True

        }

    }



# ============================================================
# Save
# ============================================================


def save_config(
    logical_models: List[LogicalModel],
    output_file: str = "config.generated.yaml"
):


    config = build_config(
        logical_models
    )



    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as f:


        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False

        )



    return output_file