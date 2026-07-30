"""
main.py

LiteLLM Config Generator


完整流程:

crawler
    |
    v
parser/detail_parser
    |
    v
raw model dict
    |
    v
normalizer
    |
    v
List[ModelInfo]
    |
    v
ModelBuilder
    |
    v
LogicalModel.models
    |
    v
config_builder
    |
    v
config.generated.yaml


禁止:

ProviderModel
primary_model
providers
FallbackBuilder
"""


from __future__ import annotations


import argparse

import logging

from pathlib import Path


from crawler import (
    crawl_models,
)


from normalizer import (
    normalize_models,
)


from builder import (
    ModelBuilder,
)


from config_builder import (
    build_config,
)



# ============================================================
# config
# ============================================================


OUTPUT_FILE = "config.generated.yaml"



logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s %(message)s"

)



logger = logging.getLogger(__name__)



# ============================================================
# args
# ============================================================


def parse_args():

    parser = argparse.ArgumentParser(

        description=
        "Generate LiteLLM config"

    )


    parser.add_argument(

        "--top",

        type=int,

        default=200,

        help=
        "number of models"

    )



    parser.add_argument(

        "--output",

        default=OUTPUT_FILE,

        help=
        "yaml output file"

    )


    return parser.parse_args()



# ============================================================
# main
# ============================================================


def main():

    args = parse_args()



    logger.info(

        "crawl top %s models",

        args.top

    )



    # --------------------------------------------------------
    # 1. crawler
    # --------------------------------------------------------


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
    # 2. normalize
    # --------------------------------------------------------


    model_infos = normalize_models(

        raw_models

    )



    logger.info(

        "ModelInfo count: %s",

        len(model_infos)

    )



    if not model_infos:


        logger.error(

            "no valid ModelInfo"

        )

        return



    # --------------------------------------------------------
    # 3. build LogicalModel
    # --------------------------------------------------------


    builder = ModelBuilder()



    result = builder.build(

        model_infos

    )



    logical_models = list(

        result.logical_models.values()

    )



    logger.info(

        "LogicalModel count: %s",

        len(logical_models)

    )



    # --------------------------------------------------------
    # 4. build LiteLLM config
    # --------------------------------------------------------


    config = build_config(

        logical_models

    )



    # --------------------------------------------------------
    # 5. save yaml
    # --------------------------------------------------------


    output = Path(

        args.output

    )



    import yaml



    with open(

        output,

        "w",

        encoding="utf-8"

    ) as f:


        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False

        )



    logger.info(

        "generated: %s",

        output

    )



# ============================================================
# entry
# ============================================================


if __name__ == "__main__":

    main()