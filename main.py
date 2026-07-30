"""
main.py

LiteLLM Config Generator 主入口


完整流程:

crawler
    |
    v
parser
    |
    v
detail_parser
    |
    v
normalizer
    |
    v
List[ModelInfo]
    |
    v
builder
    |
    v
List[LogicalModel]
    |
    v
config_builder
    |
    v
config.generated.yaml


禁止:

ProviderModel
primary_model
FallbackBuilder
"""

from __future__ import annotations


import argparse

import logging



from crawler import crawl_models


from parser import parse


from detail_parser import parse_details


from normalizer import normalize_models


from builder import build


from config_builder import write_config





# ============================================================
# Logging
# ============================================================


logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s %(message)s"

)



logger = logging.getLogger(__name__)





# ============================================================
# Main
# ============================================================


def main():


    parser = argparse.ArgumentParser(

        description=
        "Generate LiteLLM config from FreeLLM models"

    )



    parser.add_argument(

        "--top",

        type=int,

        default=50,

        help="number of models"

    )



    parser.add_argument(

        "--output",

        default="config.generated.yaml",

        help="output yaml file"

    )



    args = parser.parse_args()





    # --------------------------------------------------------
    # 1. crawler
    # --------------------------------------------------------


    logger.info(

        "crawl top %s models",

        args.top

    )



    raw_models = crawl_models(

        top_k=args.top

    )



    logger.info(

        "crawler result: %s",

        len(raw_models)

    )



    if not raw_models:


        logger.error(

            "no models found"

        )

        return





    # --------------------------------------------------------
    # 2. parser
    # --------------------------------------------------------


    parsed_models = parse(

        raw_models

    )



    logger.info(

        "parser result: %s",

        len(parsed_models)

    )





    # --------------------------------------------------------
    # 3. detail parser
    # --------------------------------------------------------


    detail_models = parse_details(

        parsed_models

    )



    logger.info(

        "detail parser result: %s",

        len(detail_models)

    )





    # --------------------------------------------------------
    # 4. normalizer
    # --------------------------------------------------------


    model_infos = normalize_models(

        detail_models

    )



    logger.info(

        "ModelInfo count: %s",

        len(model_infos)

    )



    if not model_infos:


        logger.error(

            "no ModelInfo generated"

        )

        return





    # --------------------------------------------------------
    # 5. builder
    # --------------------------------------------------------


    logical_models = build(

        model_infos

    )



    logger.info(

        "LogicalModel count: %s",

        len(logical_models)

    )



    for logical in logical_models:


        logger.info(

            "logical model %s -> %s",

            logical.logical_name,

            len(logical.models)

        )





    # --------------------------------------------------------
    # 6. config
    # --------------------------------------------------------


    write_config(

        logical_models,

        args.output

    )



    logger.info(

        "finished: %s",

        args.output

    )





if __name__ == "__main__":


    main()