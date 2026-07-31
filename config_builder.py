"""
config_builder.py

Build LiteLLM config.yaml from unified ModelInfo.

Input:
    List[ModelInfo]

Output:
    LiteLLM compatible yaml

"""

from __future__ import annotations


import os
import logging
from typing import List, Dict


import yaml


from models import ModelInfo



logger = logging.getLogger(__name__)



# --------------------------------------------------
# Provider API Key mapping
# --------------------------------------------------

PROVIDER_KEY_MAP = {

    "nvidia":
        "os.environ/NVIDIA_API_KEY",

    "nvidia nim":
        "os.environ/NVIDIA_API_KEY",


    "openrouter":
        "os.environ/OPENROUTER_API_KEY",


    "github models":
        "os.environ/GITHUB_MODELS_API_KEY",


    "github":
        "os.environ/GITHUB_MODELS_API_KEY",


    "modelscope":
        "os.environ/MODELSCOPE_API_KEY",


    "sambanova":
        "os.environ/SAMBANOVA_API_KEY",


    "agnes ai":
        "os.environ/AGNES_API_KEY",


    "agnes":
        "os.environ/AGNES_API_KEY",


    "kilo code":
        "os.environ/KILO_API_KEY",

}




# --------------------------------------------------
# Provider Base URL fallback
# --------------------------------------------------

PROVIDER_BASE_URL = {


    "nvidia":
        "https://integrate.api.nvidia.com/v1",


    "nvidia nim":
        "https://integrate.api.nvidia.com/v1",


    "openrouter":
        "https://openrouter.ai/api/v1",


}




# --------------------------------------------------
# Builder
# --------------------------------------------------


class ConfigBuilder:


    def __init__(
        self,
        models: List[ModelInfo],
    ):

        self.models = models



    # ----------------------------------------------
    # public
    # ----------------------------------------------


    def build(self) -> Dict:


        valid_models = (
            self._filter_models()
        )


        return {


            "model_list":
                self._build_model_list(
                    valid_models
                )

        }




    # ----------------------------------------------
    # filtering
    # ----------------------------------------------


    def _filter_models(
        self,
    ) -> List[ModelInfo]:


        result = []


        for model in self.models:


            if not model.model_id:

                logger.warning(
                    "skip model without id: %s",
                    model
                )

                continue



            if not model.provider:

                logger.warning(
                    "skip model without provider"
                )

                continue



            result.append(
                model
            )


        return result




    # ----------------------------------------------
    # model list
    # ----------------------------------------------


    def _build_model_list(
        self,
        models: List[ModelInfo],
    ) -> List[Dict]:


        items = []


        for model in sorted(
            models,
            key=lambda x:
                x.score or 0,

            reverse=True,
        ):


            item = (
                self._build_single_model(
                    model
                )
            )


            if item:

                items.append(
                    item
                )


        return items




    # ----------------------------------------------
    # single model
    # ----------------------------------------------


    def _build_single_model(
        self,
        model: ModelInfo,
    ) -> Dict:


        params = {

            "model":
                model.model_id,

        }



        # -------------------------
        # api_base
        # -------------------------

        api_base = (
            model.api_base
            or
            self._get_provider_base(
                model.provider
            )
        )


        if api_base:

            params["api_base"] = (
                api_base
            )



        # -------------------------
        # api key
        # -------------------------

        api_key = (
            self._get_api_key(
                model.provider
            )
        )


        if api_key:

            params["api_key"] = (
                api_key
            )



        return {


            "model_name":

                self._resolve_alias(
                    model
                ),



            "litellm_params":

                params,



            "metadata":

                {

                    "provider":
                        model.provider,


                    "model_id":
                        model.model_id,


                    "score":
                        model.score,


                    "capability":
                        model.capability
                        or [],


                    "modality":
                        model.modality
                        or [],


                    "context":
                        model.context,

                }


        }




    # ----------------------------------------------
    # logical model
    # ----------------------------------------------


    def _resolve_alias(
        self,
        model: ModelInfo,
    ) -> str:


        caps = [

            x.lower()

            for x in
            (
                model.capability
                or []
            )

        ]


        modality = [

            x.lower()

            for x in
            (
                model.modality
                or []
            )

        ]



        # vision

        if (
            "vision" in caps
            or
            "image" in modality
        ):

            return "vision"



        # reasoning

        if (
            "reasoning" in caps
            or
            "reasoning" in modality
        ):

            return "reasoning"



        return "chat"




    # ----------------------------------------------
    # provider mapping
    # ----------------------------------------------


    def _get_api_key(
        self,
        provider: str,
    ):


        key = (
            provider
            .lower()
            .strip()
        )


        return (
            PROVIDER_KEY_MAP.get(
                key
            )
        )




    def _get_provider_base(
        self,
        provider: str,
    ):


        key = (
            provider
            .lower()
            .strip()
        )


        return (
            PROVIDER_BASE_URL.get(
                key
            )
        )




# --------------------------------------------------
# yaml helper
# --------------------------------------------------


def save_config(
    config: Dict,
    path: str="config.generated.yaml",
):


    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:


        yaml.safe_dump(
            config,
            f,
            allow_unicode=True,
            sort_keys=False,
        )



    logger.info(
        "config saved: %s",
        path
    )



# --------------------------------------------------
# backward compatibility
# --------------------------------------------------


def build_config(
    models: List[ModelInfo],
):

    builder = ConfigBuilder(
        models
    )

    return builder.build()
