"""
main.py

Application entry.

Pipeline:


models.html
        |
        v
crawler.py

        |
        |
        v

raw model list


        |
        v

detail_parser.py

        |
        v

ModelInfo


        |
        v

normalizer.py


        |
        v

config_builder.py


        |
        v

config.generated.yaml



Usage:


python main.py --top 100


"""

from __future__ import annotations


import argparse
import logging
from typing import List



from crawler import crawl_models


from detail_parser import (
    DetailParser,
)


from normalizer import (
    normalize_models,
)


from config_builder import (
    build_config,
    save_config,
)



from models import ModelInfo



logger = logging.getLogger(__name__)



# ============================================================
# Logging
# ============================================================


def setup_logging():

    logging.basicConfig(

        level=logging.INFO,

        format=

            "%(levelname)s %(message)s",

    )



# ============================================================
# Arguments
# ============================================================


def parse_args():

    parser = argparse.ArgumentParser(

        description=

            "Generate LiteLLM config from FreeLLM models"

    )


    parser.add_argument(

        "--top",

        type=int,

        default=50,

        help=

            "number of models to crawl",

    )


    parser.add_argument(

        "--output",

        default=

            "config.generated.yaml",

        help=

            "output yaml file",

    )


    return parser.parse_args()



# ============================================================
# Detail processing
# ============================================================


def parse_details(
    raw_models: List[dict],
) -> List[ModelInfo]:
    """
    Parse detail pages.

    crawler output:

        provider
        detail_url
        slug
        extra


    detail_parser output:

        ModelInfo
    """



    parser = DetailParser()



    result = []



    for index, raw in enumerate(

        raw_models,

        start=1,

    ):


        logger.info(

            "parse detail %s/%s: %s",

            index,

            len(raw_models),

            raw.get(

                "detail_url"

            ),

        )



        try:


            model = parser.parse(

                raw

            )



            if model:


                result.append(

                    model

                )


        except Exception as exc:


            logger.warning(

                "detail parse failed: %s",

                exc,

            )



    return result



# ============================================================
# Main pipeline
# ============================================================


def generate_config(
    top: int,
    output: str,
):
    """
    Complete generation flow.
    """



    #
    # Step 1
    #
    # models.html
    #

    logger.info(

        "crawl top %s models",

        top,

    )


    raw_models = crawl_models(

        top_k=top

    )



    logger.info(

        "crawler models: %s",

        len(raw_models),

    )



    if not raw_models:


        raise RuntimeError(

            "No models extracted from models.html"

        )



    #
    # Step 2
    #
    # detail.html
    #

    detail_models = parse_details(

        raw_models

    )



    logger.info(

        "detail parsed models: %s",

        len(detail_models),

    )



    #
    # Step 3
    #
    # normalize ModelInfo
    #

    normalized = normalize_models(

        [

            model.__dict__

            for model in detail_models

        ]

    )



    logger.info(

        "valid ModelInfo: %s",

        len(normalized),

    )



    if not normalized:


        raise RuntimeError(

            "No valid models found"

        )



    #
    # Step 4
    #
    # LiteLLM config
    #

    config = build_config(

        normalized

    )



    #
    # Step 5
    #
    # save yaml
    #

    save_config(

        config,

        output,

    )



    logger.info(

        "config generated successfully"

    )



# ============================================================
# Entry
# ============================================================


def main():

    setup_logging()


    args = parse_args()



    generate_config(

        top=args.top,

        output=args.output,

    )



if __name__ == "__main__":

    main()