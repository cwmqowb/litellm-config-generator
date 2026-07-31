"""
main.py

LiteLLM Config Generator

Pipeline:

crawler
   |
   v
detail_parser
   |
   v
ModelInfo
   |
   v
config_builder
   |
   v
config.generated.yaml

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



logging.basicConfig(
    level=logging.INFO,
    format=
    "%(levelname)s %(message)s",
)


logger = logging.getLogger(
    __name__
)



# -------------------------------------------------
# Supported providers
# -------------------------------------------------


SUPPORTED_PROVIDERS = {


    "NVIDIA NIM",

    "OpenRouter",

    "GitHub Models",

    "ModelScope",

    "SambaNova",

    "Agnes AI",

    "Kilo Code",

}



# -------------------------------------------------
# CLI
# -------------------------------------------------


def parse_args():


    parser = argparse.ArgumentParser(
        description=
        "Generate LiteLLM config from freellm.net"
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
    )


    parser.add_argument(
        "--no-detail",
        action="store_true",
        help=
        "skip detail page parsing",
    )


    return parser.parse_args()




# -------------------------------------------------
# convert raw -> ModelInfo
# -------------------------------------------------


def convert_to_models(
    raw_models,
    detail_parser: DetailParser,
    skip_detail=False,
) -> List[ModelInfo]:


    result = []



    for raw in raw_models:


        provider = (
            raw.get(
                "provider"
            )
            or ""
        )



        if provider not in SUPPORTED_PROVIDERS:

            logger.info(
                "skip provider %s",
                provider,
            )

            continue



        detail = {}



        if not skip_detail:


            url = (
                raw.get(
                    "detail_url"
                )
            )


            if url:

                detail = (
                    detail_parser.parse(
                        url
                    )
                )



        # -------------------------------------
        # IMPORTANT
        #
        # detail page has final model id
        #
        # -------------------------------------

        model_id = (
            detail.get(
                "model_id"
            )
            or
            raw.get(
                "model_id"
            )
        )


        if not model_id:

            logger.warning(
                "missing model id: %s",
                raw,
            )

            continue




        model = ModelInfo(


            provider=provider,


            model_id=model_id,


            api_base=
                detail.get(
                    "api_base"
                ),


            score=float(
                raw.get(
                    "score",
                    0
                )
            ),


            capability=
                detail.get(
                    "capability",
                    []
                ),


            modality=
                detail.get(
                    "modality",
                    []
                ),


            context=
                detail.get(
                    "context"
                ),



            best_for=
                detail.get(
                    "best_for",
                    []
                ),



            detail_url=
                raw.get(
                    "detail_url"
                ),

        )


        result.append(
            model
        )



        logger.info(
            "%s | %s | score=%s",
            provider,
            model_id,
            model.score,
        )


    return result




# -------------------------------------------------
# main
# -------------------------------------------------


def main():


    args = parse_args()



    logger.info(
        "crawl top %s models",
        args.top,
    )



    # -------------------------------
    # crawl list page
    # -------------------------------

    raw_models = crawl_models(

        top=args.top

    )



    logger.info(
        "crawler returned %s models",
        len(raw_models),
    )




    # -------------------------------
    # detail parse
    # -------------------------------


    detail_parser = DetailParser()



    models = convert_to_models(

        raw_models,

        detail_parser,

        skip_detail=args.no_detail,

    )



    logger.info(
        "valid models %s",
        len(models),
    )



    if not models:

        raise RuntimeError(
            "No valid models found"
        )



    # -------------------------------
    # build config
    # -------------------------------


    builder = ConfigBuilder(

        models

    )


    config = builder.build()



    save_config(

        config,

        args.output

    )



    logger.info(
        "DONE"
    )




if __name__ == "__main__":

    main()
