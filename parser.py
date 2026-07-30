"""
parser.py

模型列表解析器


输入:

crawler 获取的模型列表数据


输出:

List[dict]


后续:

normalizer.py

List[dict]
        |
        v
List[ModelInfo]


禁止:

ProviderModel
primary_model
providers
provider_model
"""


from __future__ import annotations


import logging

from typing import Any, Dict, List



logger = logging.getLogger(__name__)




# ============================================================
# helpers
# ============================================================


def get_value(
    data: Dict,
    keys: List[str],
    default=None
):


    for key in keys:


        if key in data:


            return data[key]



    return default




def normalize_provider(
    value: Any
) -> str:


    if not value:

        return ""



    return (

        str(value)

        .strip()

    )





# ============================================================
# single parser
# ============================================================


def parse_model(
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    单个模型记录解析

    dict -> 标准dict
    """



    model_id = get_value(

        item,

        [

            "model_id",

            "model",

            "id",

            "name",

        ],

        ""

    )



    name = get_value(

        item,

        [

            "name",

            "model",

            "id",

        ],

        model_id

    )



    provider = normalize_provider(

        get_value(

            item,

            [

                "provider",

                "organization",

                "vendor",

            ],

            ""

        )

    )




    result = {


        "name":

            name,



        "model_id":

            model_id,



        "provider":

            provider,



        "api_base":

            get_value(

                item,

                [

                    "api_base",

                    "base_url",

                    "endpoint",

                ]

            ),



        "api_key_env":

            get_value(

                item,

                [

                    "api_key_env",

                ]

            ),



        "api_format":

            get_value(

                item,

                [

                    "api_format",

                    "format",

                ]

            ),



        "capabilities":

            get_value(

                item,

                [

                    "capabilities",

                    "capability",

                ],

                []

            ),



        "context_window":

            get_value(

                item,

                [

                    "context_window",

                    "context_length",

                ]

            ),



        "max_output_tokens":

            get_value(

                item,

                [

                    "max_output_tokens",

                    "max_tokens",

                ]

            ),



        "free":

            bool(

                get_value(

                    item,

                    [

                        "free",

                        "is_free",

                    ],

                    False

                )

            ),



        "score":

            float(

                get_value(

                    item,

                    [

                        "score",

                        "ranking",

                    ],

                    0

                )

                or 0

            ),



        "metadata":

            item,

    }



    return result





# ============================================================
# list parser
# ============================================================


def parse_models(
    data: Any
) -> List[Dict[str, Any]]:
    """
    批量解析


    支持:

    [
        {}
    ]


    或:

    {
        "models":[]
    }

    """



    if not data:

        return []



    if isinstance(

        data,

        dict

    ):


        models = (

            data.get(

                "models"

            )

            or

            data.get(

                "data"

            )

            or

            []

        )



    elif isinstance(

        data,

        list

    ):


        models = data



    else:


        return []



    result = []



    for item in models:


        if not isinstance(

            item,

            dict

        ):

            continue



        try:


            result.append(

                parse_model(

                    item

                )

            )



        except Exception:


            logger.exception(

                "parse model failed: %s",

                item

            )



    return result





# ============================================================
# compatibility entry
# ============================================================


def parse(
    data: Any
) -> List[Dict[str, Any]]:
    """
    主入口

    """

    return parse_models(

        data

    )