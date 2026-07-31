"""
config_builder.py

Build LiteLLM configuration
from unified ModelInfo.


Input:

    List[ModelInfo]


Output:

    LiteLLM config dictionary


Rules:

1. LiteLLM model MUST use:

       model.model_id


2. Never use:

       name
       title
       display_name
       slug


3. Provider API settings come from:

       providers.py


4. Preserve metadata:

       provider
       score
       capability
       context
       best_for
       extra

"""

from __future__ import annotations


import logging
from typing import Any, Dict, List


import yaml


from models import ModelInfo


from providers import (
    get_api_base,
    get_api_key_env,
)



logger = logging.getLogger(__name__)



# ============================================================
# Builder
# ============================================================


class ConfigBuilder:
    """
    Convert ModelInfo list
    into LiteLLM config.
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
    ) -> Dict[str, Any]:
        """
        Build LiteLLM config.
        """


        valid_models = [

            model

            for model in self.models

            if model.is_valid()

        ]



        return {

            "model_list":

                [

                    self.build_model(

                        model

                    )

                    for model in sorted(

                        valid_models,

                        key=lambda x:

                            x.score,

                        reverse=True,

                    )

                ]

        }



    # --------------------------------------------------------
    # Single model
    # --------------------------------------------------------


    def build_model(
        self,
        model: ModelInfo,
    ) -> Dict[str, Any]:
        """
        Build one LiteLLM model item.
        """


        params = {


            # IMPORTANT:
            #
            # Real provider model id
            #

            "model":

                model.model_id

        }



        api_base = (

            model.api_base

            or

            get_api_base(

                model.provider

            )

        )



        if api_base:


            params[

                "api_base"

            ] = api_base



        api_key_env = get_api_key_env(

            model.provider

        )



        if api_key_env:


            params[

                "api_key"

            ] = (

                f"os.environ/{api_key_env}"

            )



        return {


            #
            # Logical routing name
            #

            "model_name":

                self.resolve_model_group(

                    model

                ),



            "litellm_params":

                params,



            "metadata":

                self.build_metadata(

                    model

                )

        }



    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------


    def build_metadata(
        self,
        model: ModelInfo,
    ) -> Dict[str, Any]:
        """
        Preserve model information.
        """


        metadata = {


            "provider":

                model.provider,



            "score":

                model.score,



            "capability":

                model.capability,



            "context":

                model.context,



            "best_for":

                model.best_for,



        }



        if model.extra:


            metadata[

                "extra"

            ] = model.extra



        return metadata



    # --------------------------------------------------------
    # Logical grouping
    # --------------------------------------------------------


    def resolve_model_group(
        self,
        model: ModelInfo,
    ) -> str:
        """
        Generate logical model group.

        Examples:

            chat
            vision
            reasoning

        """


        capability = [

            x.lower()

            for x in model.capability

        ]



        modality = [

            x.lower()

            for x in model.modality

        ]



        if (

            "image"

            in modality

            or

            "vision"

            in capability

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
) -> Dict[str, Any]:
    """
    Public builder.
    """

    return ConfigBuilder(

        models

    ).build()



def save_config(
    config: Dict[str, Any],
    path: str = "config.generated.yaml",
) -> None:
    """
    Save yaml config.
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

        "saved config: %s",

        path,

    )