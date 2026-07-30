"""
config_builder.py

LiteLLM config.yaml生成器


输入:

List[LogicalModel]


输出:

LiteLLM YAML


当前模型体系:

LogicalModel

    name

    models[]



ModelInfo

    name

    model_id

    provider

    api_base

    api_key_env

    score

"""


from typing import (
    List,
    Dict,
    Any,
)

from pathlib import Path

import yaml


from models import (
    LogicalModel,
    ModelInfo,
)



# ============================================================
# LiteLLM模型名称
# ============================================================


def build_litellm_model_name(
    model: ModelInfo,
) -> str:


    provider = getattr(
        model,
        "provider",
        "",
    )


    model_id = (

        getattr(
            model,
            "model_id",
            None,
        )

        or

        getattr(
            model,
            "name",
            None,
        )

        or

        "unknown"

    )


    if "/" in model_id:

        return model_id



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
# 单个Deployment
# ============================================================


def build_model_entry(
    model: ModelInfo,
) -> Dict[str, Any]:


    litellm_model = (
        build_litellm_model_name(
            model
        )
    )


    params = {


        "model":

            litellm_model,


    }



    api_base = getattr(
        model,
        "api_base",
        None,
    )


    if api_base:

        params[
            "api_base"
        ] = api_base



    api_key_env = getattr(
        model,
        "api_key_env",
        None,
    )


    if api_key_env:

        params[
            "api_key"
        ] = (
            "os.environ/"
            +
            api_key_env
        )



    return {


        "model_name":

            litellm_model,


        "litellm_params":

            params,


    }



# ============================================================
# LogicalModel
# ============================================================


def build_logical_model_entries(
    logical_model: LogicalModel,
):

    entries = []



    for model in logical_model.models:


        entries.append(

            build_model_entry(
                model
            )

        )



    return entries



# ============================================================
# Config
# ============================================================


def build_config(
    logical_models: List[LogicalModel],
):


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


            "drop_params":

                True


        }


    }



# ============================================================
# Save
# ============================================================


def save_config(
    logical_models: List[LogicalModel],

    output_file="config.generated.yaml",

):


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
