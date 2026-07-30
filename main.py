from __future__ import annotations


import argparse
import logging
from pathlib import Path


from crawler import crawl_models


from parser import parse_model_detail


from models import (
    ModelInfo,
)


from normalizer import (
    normalize_models,
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
        help="crawl top models",
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



def convert_to_model_info(
    raw_models,
):

    """
    dict
        |
        v
    ModelInfo


    由 parser.py/detail_parser.py
    统一负责字段解析
    """


    result = []


    for item in raw_models:


        try:


            model = parse_model_detail(
                item
            )


            if model:

                result.append(
                    model
                )


        except Exception:


            logging.exception(
                "parse model failed: %s",
                item,
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
    raw_models = crawl_models(
        top_k=args.top
    )



    logging.info(
        "Crawler models: %s",
        len(raw_models),
    )



    #
    # 2. provider filter
    #
    raw_models = filter_supported_models(
        raw_models
    )



    logging.info(
        "Supported models: %s",
        len(raw_models),
    )



    if not raw_models:


        logging.error(
            "No supported models"
        )


        return




    #
    # 3. dict -> ModelInfo
    #
    model_infos = (
        convert_to_model_info(
            raw_models
        )
    )



    logging.info(
        "Parsed ModelInfo: %s",
        len(model_infos),
    )



    if not model_infos:


        logging.error(
            "No valid ModelInfo"
        )


        return




    #
    # 4. normalize
    #
    normalized_models = normalize_models(
        model_infos
    )



    logging.info(
        "Normalized models: %s",
        len(normalized_models),
    )




    #
    # 5. build logical models
    #
    builder = FallbackBuilder()



    build_result = builder.build(
        normalized_models
    )



    logical_models = list(
        build_result.logical_models.values()
    )



    capability_groups = {

        name:
            group.models

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
    # 6. LiteLLM yaml
    #
    config_builder = (
        LiteLLMConfigBuilder()
    )



    config = config_builder.build(
        logical_models,
        capability_groups,
    )





    #
    # 7. save
    #
    config_builder.save(
        config,
        Path(
            args.output
        ),
    )



    logging.info(
        "Generated: %s",
        args.output,
    )




if __name__ == "__main__":

    main()
