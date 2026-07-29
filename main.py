from __future__ import annotations

import argparse
import logging
from pathlib import Path


from crawler import crawl_models
from normalizer import normalize_model_name

from builder import (
    build_logical_models,
    build_capability_models,
)

from config_builder import (
    LiteLLMConfigBuilder,
)

from providers import SUPPORTED_PROVIDERS



OUTPUT_FILE = "config.generated.yaml"



logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)



def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Generate LiteLLM config "
            "from freellm free models"
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


            if (
                provider
                not in SUPPORTED_PROVIDERS
            ):
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
                "normalize failed"
            )


    return result



def main():


    args = parse_args()



    logging.info(
        "Start crawling freellm top %s models",
        args.top,
    )



    #
    # 1. Crawl
    #
    try:

        models = crawl_models(
            top_k=args.top
        )


    except Exception:

        logging.exception(
            "crawl failed"
        )

        return



    logging.info(
        "Crawler returned %s models",
        len(models),
    )



    #
    # 2. Provider filter
    #
    models = filter_supported_models(
        models
    )


    logging.info(
        "After provider filter: %s",
        len(models),
    )



    #
    # 3. Normalize brand name
    #
    models = normalize_models(
        models
    )



    #
    # 4. Build logical models
    #
    try:

        logical_models = (
            build_logical_models(
                models
            )
        )


    except Exception:

        logging.exception(
            "build logical models failed"
        )

        return



    logging.info(
        "Logical models: %s",
        len(logical_models),
    )



    #
    # 5. Capability models
    #
    try:

        capability_models = (
            build_capability_models(
                logical_models
            )
        )


    except Exception:

        logging.exception(
            "capability build failed"
        )

        capability_models = {}



    #
    # 6. Build LiteLLM config
    #
    builder = (
        LiteLLMConfigBuilder()
    )


    config = builder.build(
        logical_models,
        capability_models,
    )



    #
    # 7. Save
    #
    builder.save(
        config,
        Path(args.output),
    )



    logging.info(
        "Generated %s",
        args.output,
    )



if __name__ == "__main__":

    main()
