from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List


from crawler import crawl_models

from models import (
    ProviderModel,
    ModelCapability,
)

from builder import (
    FallbackBuilder,
)

from config_builder import (
    LiteLLMConfigBuilder,
)

from providers import (
    SUPPORTED_PROVIDERS,
)

from normalizer import (
    normalize_model_name,
)



OUTPUT_FILE = "config.generated.yaml"



logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)



def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Generate LiteLLM config "
            "from freellm models"
        )
    )


    parser.add_argument(
        "--top",
        type=int,
        default=200,
        help="freellm top models",
    )


    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help="output yaml file",
    )


    return parser.parse_args()



def filter_supported_models(
    models,
):

    result = []


    for model in models:

        try:

            provider = (
                model.get(
                    "provider",
                    "",
                )
                .strip()
            )


            if provider not in SUPPORTED_PROVIDERS:

                continue


            result.append(
                model
            )


        except Exception:

            logging.exception(
                "filter model failed"
            )


    return result



def normalize_models(
    models,
):

    result = []


    for model in models:

        try:

            name = (
                model.get(
                    "logical_name"
                )
                or
                model.get(
                    "name"
                )
                or
                model.get(
                    "model"
                )
            )


            model["logical_name"] = (
                normalize_model_name(
                    name
                )
            )


            result.append(
                model
            )


        except Exception:

            logging.exception(
                "normalize model failed"
            )


    return result



def build_capability(
    data,
) -> ModelCapability:

    """
    dict capability
    转换为 ModelCapability
    """


    if isinstance(
        data,
        ModelCapability,
    ):

        return data


    capability = ModelCapability()


    if not isinstance(
        data,
        dict,
    ):

        return capability



    for field in vars(
        capability
    ):

        if data.get(
            field,
            False,
        ):

            setattr(
                capability,
                field,
                True,
            )


    return capability



def convert_to_provider_models(
    models,
) -> List[ProviderModel]:

    """
    crawler 输出:

    dict

    转换:

    ProviderModel
    """


    result = []


    for item in models:

        try:

            provider = item.get(
                "provider",
                "",
            )


            logical_name = (
                item.get(
                    "logical_name"
                )
                or
                item.get(
                    "name"
                )
                or
                item.get(
                    "model"
                )
            )


            model_id = (
                item.get(
                    "model_id"
                )
                or
                item.get(
                    "model"
                )
                or
                logical_name
            )


            provider_model = ProviderModel(

                provider=provider,


                logical_name=normalize_model_name(
                    logical_name
                ),


                model_id=model_id,


                api_base=item.get(
                    "base_url",
                    ""
                )
                or
                item.get(
                    "api_base",
                    ""
                ),


                api_format=item.get(
                    "api_format",
                    ""
                ),


                api_key_env=item.get(
                    "api_key_env",
                    ""
                ),


                api_key_envs=item.get(
                    "api_key_envs",
                    [],
                ),


                deployment_name=(
                    provider
                    +
                    "-"
                    +
                    model_id
                ),


                context_window=item.get(
                    "context_window"
                ),


                max_output_tokens=item.get(
                    "max_output_tokens"
                ),


                capability=build_capability(
                    item.get(
                        "capability",
                        {}
                    )
                    or
                    item.get(
                        "capabilities",
                        {}
                    )
                ),


                raw_tags=item.get(
                    "tags",
                    []
                ),


                metadata=item,

            )


            result.append(
                provider_model
            )


        except Exception:

            logging.exception(
                "convert ProviderModel failed"
            )


    return result



def main():

    args = parse_args()



    logging.info(
        "Start crawling top %s models",
        args.top,
    )



    #
    # 1. crawl
    #
    models = crawl_models(
        top_k=args.top
    )



    logging.info(
        "Crawler models: %s",
        len(models),
    )



    #
    # 2. provider filter
    #
    models = filter_supported_models(
        models
    )


    logging.info(
        "Supported models: %s",
        len(models),
    )



    #
    # 3. normalize
    #
    models = normalize_models(
        models
    )



    #
    # 4. dict -> ProviderModel
    #
    provider_models = (
        convert_to_provider_models(
            models
        )
    )



    logging.info(
        "ProviderModel count: %s",
        len(provider_models),
    )



    if not provider_models:

        logging.error(
            "No valid ProviderModel"
        )

        return



    #
    # 5. Builder
    #
    builder = FallbackBuilder()



    build_result = builder.build(
        provider_models
    )



    logical_models = list(
        build_result.logical_models.values()
    )



    capability_groups = {
    name: group.models
    for name, group
    in build_result.capability_groups.items()
}



    logging.info(
        "Logical models: %s",
        len(logical_models),
    )


    logging.info(
        "Capability groups: %s",
        len(capability_groups),
    )



    #
    # 6. LiteLLM config
    #
    config_builder = (
        LiteLLMConfigBuilder()
    )


    config = config_builder.build(
        logical_models,
        capability_groups,
    )



    #
    # 7. Save
    #
    config_builder.save(
        config,
        Path(
            args.output
        ),
    )



    logging.info(
        "Generated %s",
        args.output,
    )



if __name__ == "__main__":

    main()
