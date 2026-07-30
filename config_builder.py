"""
config_builder.py

LiteLLM config.yaml生成器


输入:

List[LogicalModel]


输出:

config.generated.yaml


结构:

LogicalModel.models


禁止:

ProviderModel
primary_model
providers
mode
"""


from __future__ import annotations


import logging


from pathlib import Path


from typing import Any, Dict, List



import yaml



from models import (
    LogicalModel,
    ModelInfo,
)



logger = logging.getLogger(__name__)





# ============================================================
# LiteLLM item
# ============================================================


def build_model_entry(
    logical_name: str,
    model: ModelInfo
) -> Dict[str, Any]:
    """
    单个LiteLLM model_list节点
    """



    params = {



        "model":

            model.model_id,



    }



    if model.api_base:


        params["api_base"] = model.api_base



    if model.api_key_env:


        params["api_key"] = (

            f"os.environ/{model.api_key_env}"

        )



    return {


        "model_name":

            logical_name,



        "litellm_params":

            params,



        "metadata": {


            "provider":

                model.provider,



            "model_id":

                model.model_id,



            "score":

                model.score,



            "capability":

                model.capability.raw,

        }

    }





# ============================================================
# Config
# ============================================================


def build_config(
    logical_models: List[LogicalModel]
) -> Dict[str, Any]:
    """
    生成LiteLLM配置对象
    """



    model_list = []



    for logical_model in logical_models:



        for model in logical_model.models:


            model_list.append(

                build_model_entry(

                    logical_model.logical_name,

                    model

                )

            )



    return {



        "model_list":

            model_list,



        "router_settings": {


            "routing_strategy":

                "simple-shuffle",



            "enable_pre_call_checks":

                True,


        },



        "litellm_settings": {


            "drop_params":

                True,


        },


    }





# ============================================================
# Write YAML
# ============================================================


def write_config(
    logical_models: List[LogicalModel],
    output_file: str = "config.generated.yaml"
):
    """
    写入yaml
    """



    config = build_config(

        logical_models

    )



    path = Path(

        output_file

    )



    with path.open(

        "w",

        encoding="utf-8"

    ) as f:



        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False

        )



    logger.info(

        "generated config: %s",

        path

    )



    return path