"""
config_builder.py

Build LiteLLM config from unified ModelInfo.


Input:

    List[ModelInfo]


Output:

    LiteLLM compatible config.yaml


Rules:

1. litellm_params.model MUST use:

       ModelInfo.model_id


2. Never use:

       name
       display_name
       title


3. Provider API key mapping:

       providers.py


4. Metadata keeps:

       provider
       score
       capability
       context

"""

from __future__ import annotations


import logging
from typing import Dict, List


import yaml


from models import ModelInfo


from providers import (
    get_api_base,
    get_api_key_env,
)


logger = logging.getLogger(__name__)



# ============================================================
# Config Builder
# ============================================================


class ConfigBuilder:
    """
    Convert ModelInfo list into LiteLLM config.
    """



    def __init__(
        self,
        models: List[ModelInfo],
    ):

        self.models = models



    # --------------------------------------------------------
    # Public
    # --------------------------------------------------------


    def build(
        self,
    ) -> Dict:
        """
        Build config dictionary.
        """


        valid_models = [

            model

            for model in self.models

            if model.is_valid()

        ]


        return {

            "model_list":

                self._build_model_list(
                    valid_models
                )

        }



    # --------------------------------------------------------
    # model_list
    # --------------------------------------------------------


    def _build_model_list(
        self,
        models: List[ModelInfo],
    ) -> List[Dict]:


        result = []


        for model in sorted(

            models,

            key=lambda x:

                x.score,

            reverse=True,

        ):


            result.append(

                self._build_single(
                    model
                )

            )


        return result



    # --------------------------------------------------------
    # single model
    # --------------------------------------------------------


    def _build_single(
        self,
        model: ModelInfo,
    ) -> Dict:
        """
        Build one LiteLLM model entry.
        """


        litellm_params = {


            # IMPORTANT:
            #
            # real provider model id
            #

            "model":

                model.model_id

        }



        # api_base

        api_base = (

            model.api_base

            or

            get_api_base(
                model.provider
            )

        )


        if api_base:

            litellm_params[

                "api_base"

            ] = api_base



        # api key

        api_key_env = (

            get_api_key_env(
                model.provider
            )

        )


        if api_key_env:

            litellm_params[

                "api_key"

            ] = (

                f"os.environ/{api_key_env}"

            )



        return {


            #
            # LiteLLM logical routing name
            #

            "model_name":

                self._resolve_logical_name(
                    model
                ),



            "litellm_params":

                litellm_params,



            "metadata":

                {

                    "provider":

                        model.provider,


                    "score":

                        model.score,


                    "capability":

                        model.capability,


                    "context":

                        model.context,

                }

        }



    # --------------------------------------------------------
    # logical model
    # --------------------------------------------------------


    def _resolve_logical_name(
        self,
        model: ModelInfo,
    ) -> str:
        """
        Generate logical model group.

        Example:

        chat
        vision
        reasoning

        """


        capability = [

            item.lower()

            for item in

            model.capability

        ]



        modality = [

            item.lower()

            for item in

            model.modality

        ]



        if (

            "vision"

            in capability

            or

            "image"

            in modality

        ):

            return "vision"



        if (

            "reasoning"

            in capability

        ):

            return "reasoning"



        return "chat"



# ============================================================
# Helpers
# ============================================================


def build_config(
    models: List[ModelInfo],
) -> Dict:
    """
    Public helper.
    """

    return (

        ConfigBuilder(
            models
        )
        .build()

    )



def save_config(
    config: Dict,
    path: str = "config.generated.yaml",
):
    """
    Save yaml file.
    """


    with open(

        path,

        "w",

        encoding="utf-8",

    ) as file:


        yaml.safe_dump(

            config,

            file,

            allow_unicode=True,

            sort_keys=False,

        )


    logger.info(

        "config saved: %s",

        path,

    )