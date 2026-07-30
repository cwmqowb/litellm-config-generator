"""
main.py

LiteLLM Config Generator

流程:

crawler
    |
    v
raw model dict
    |
    v
ModelInfo
    |
    v
LogicalModel
    |
    v
LiteLLM yaml


当前架构:

ModelInfo
    |
    v
LogicalModel.models

已废弃:

ProviderModel
primary_model
providers
"""



from __future__ import annotations


import argparse

import logging

from pathlib import Path

from typing import List



from crawler import (
    crawl_models,
)



from models import (
    ModelInfo,
)



from builder import (
    FallbackBuilder,
)



from config_builder import (
    build_config,
)



from providers import (
    SUPPORTED_PROVIDERS,
)



from normalizer import (
    normalize_model_name,
)





OUTPUT_FILE = (
    "config.generated.yaml"
)





logging.basicConfig(

    level=logging.INFO,

    format="%(levelname)s %(message)s",

)






# ============================================================
# args
# ============================================================



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

        help="top models",

    )


    parser.add_argument(

        "--output",

        default=OUTPUT_FILE,

        help="output yaml",

    )


    return parser.parse_args()







# ============================================================
# Provider过滤
# ============================================================



def filter_supported_models(

    models,

):


    result = []



    for model in models:


        try:


            provider = (

                model.get(

                    "provider",

                    ""

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







# ============================================================
# dict -> ModelInfo
# ============================================================



def convert_to_model_infos(

    models,

) -> List[ModelInfo]:

    """
    crawler dict

    转换:

    ModelInfo[]
    """



    result = []



    for item in models:


        try:


            name = (

                item.get(

                    "name"

                )

                or

                item.get(

                    "model"

                )

                or

                "unknown"

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

                name

            )



            info = ModelInfo(


                name=normalize_model_name(

                    name

                ),



                model_id=model_id,



                provider=(

                    item.get(

                        "provider",

                        ""

                    )

                ),



                api_base=(

                    item.get(

                        "api_base"

                    )

                    or

                    item.get(

                        "base_url"

                    )

                ),



                api_key_env=(

                    item.get(

                        "api_key_env"

                    )

                ),



                capability=(

                    item.get(

                        "capability",

                        {}

                    )

                ),



                score=(

                    item.get(

                        "score",

                        0

                    )

                    or

                    0

                ),



                metadata=item,

            )



            result.append(

                info

            )



        except Exception:


            logging.exception(

                "convert ModelInfo failed"

            )



    return result







# ============================================================
# main
# ============================================================



def main():


    args = parse_args()



    logging.info(

        "Start crawling top %s models",

        args.top,

    )




    # --------------------------------------------------------
    # 1 crawl
    # --------------------------------------------------------


    raw_models = crawl_models(

        top_k=args.top

    )



    logging.info(

        "Crawler models: %s",

        len(raw_models),

    )





    # --------------------------------------------------------
    # 2 provider filter
    # --------------------------------------------------------


    raw_models = filter_supported_models(

        raw_models

    )



    logging.info(

        "Supported models: %s",

        len(raw_models),

    )






    # --------------------------------------------------------
    # 3 ModelInfo
    # --------------------------------------------------------


    model_infos = convert_to_model_infos(

        raw_models

    )



    logging.info(

        "ModelInfo count: %s",

        len(model_infos),

    )



    if not model_infos:


        logging.error(

            "No valid ModelInfo"

        )

        return






    # --------------------------------------------------------
    # 4 LogicalModel builder
    # --------------------------------------------------------



    builder = FallbackBuilder()



    build_result = builder.build(

        model_infos

    )



    logical_models = list(

        build_result.logical_models.values()

    )



    logging.info(

        "Logical models: %s",

        len(logical_models),

    )






    # --------------------------------------------------------
    # 5 LiteLLM config
    # --------------------------------------------------------



    config = build_config(

        logical_models

    )






    # --------------------------------------------------------
    # 6 save
    # --------------------------------------------------------



    output = Path(

        args.output

    )



    import yaml



    with open(

        output,

        "w",

        encoding="utf-8",

    ) as f:


        yaml.safe_dump(

            config,

            f,

            allow_unicode=True,

            sort_keys=False,

        )




    logging.info(

        "Generated %s",

        output,

    )







if __name__ == "__main__":

    main()
