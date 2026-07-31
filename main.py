"""
main.py

LiteLLM Config Generator


Pipeline:


crawler.py

    |
    v

detail_parser.py

    |
    v

ModelInfo

    |
    v

config_builder.py

    |
    v

config.generated.yaml



Responsibilities:

- CLI
- Pipeline orchestration
- Save generated config


No model parsing logic here.
"""

from __future__ import annotations


import argparse
import logging
from typing import List


from crawler import crawl_models


from detail_parser import (
    DetailParser,
)


from models import (
    ModelInfo,
)


from config_builder import (
    ConfigBuilder,
    save_config,
)


from providers import (
    normalize_provider_name,
)



logging.basicConfig(

    level=logging.INFO,

    format=

        "%(levelname)s %(message)s",

)


logger = logging.getLogger(
    __name__
)



# ============================================================
# Supported providers
# ============================================================


SUPPORTED_PROVIDERS = {


    "nvidia",


    "openrouter",


    "github",


    "modelscope",


    "sambanova",


    "agnes",


    "kilo",


}



# ============================================================
# CLI
# ============================================================


def parse_args():

    parser = argparse.ArgumentParser(

        description=

            "Generate LiteLLM config"

    )


    parser.add_argument(

        "--top",

        type=int,

        default=50,

        help=

            "number of models",

    )


    parser.add_argument(

        "--output",

        default=

            "config.generated.yaml",

    )


    return parser.parse_args()



# ============================================================
# Provider filter
# ============================================================


def is_supported_provider(
    provider: str,
) -> bool:


    normalized = (

        normalize_provider_name(

            provider

        )

    )


    return (

        normalized

        in

        SUPPORTED_PROVIDERS

    )



# ============================================================
# Pipeline
# ============================================================


def build_models(
    raw_models: List[dict],
) -> List[ModelInfo]:
    """
    crawler output

        |

        v

    ModelInfo list

    """


    parser = DetailParser()



    result = []



    for raw in raw_models:


        provider = (

            raw.get(

                "provider",

                ""

            )

        )



        if not is_supported_provider(

            provider

        ):


            logger.info(

                "skip provider: %s",

                provider,

            )


            continue



        try:


            model = parser.parse(

                raw

            )


            if not model:


                continue



            result.append(

                model

            )


            logger.info(

                "%s | %s | %.2f",

                model.provider,

                model.model_id,

                model.score,

            )



        except Exception:


            logger.exception(

                "parse detail failed: %s",

                raw,

            )



    return result



# ============================================================
# Main
# ============================================================


def main():

    args = parse_args()



    logger.info(

        "crawl top %s models",

        args.top,

    )



    # ------------------------------------
    # Step 1
    # crawler
    # ------------------------------------


    raw_models = crawl_models(

        top_k=args.top

    )



    logger.info(

        "crawler models: %s",

        len(raw_models),

    )



    # ------------------------------------
    # Step 2
    # detail parser
    # ------------------------------------


    models = build_models(

        raw_models

    )



    logger.info(

        "valid ModelInfo: %s",

        len(models),

    )



    if not models:


        raise RuntimeError(

            "No valid models found"

        )



    # ------------------------------------
    # Step 3
    # config builder
    # ------------------------------------


    builder = ConfigBuilder(

        models

    )


    config = builder.build()



    # ------------------------------------
    # Step 4
    # save yaml
    # ------------------------------------


    save_config(

        config,

        args.output,

    )



    logger.info(

        "DONE"

    )





if __name__ == "__main__":

    main()