"""
parser.py

模型列表解析器


职责:

将 crawler 输出的原始 dict

转换为标准模型字典


输入:

List[dict]


输出:

List[dict]


下一步:

normalizer.py

List[dict]
    |
    v
List[ModelInfo]


禁止:

ProviderModel
LogicalModel
"""


from __future__ import annotations


import logging


from typing import Any, Dict, List




logger = logging.getLogger(__name__)





# ============================================================
# Utils
# ============================================================


def get_value(
    data: Dict[str, Any],
    keys: List[str],
    default=None
):


    for key in keys:


        if key in data:


            return data[key]



    return default





def normalize_provider(
    provider: str
) -> str:


    if not provider:

        return ""



    return (

        str(provider)

        .strip()

        .lower()

    )





# ============================================================
# Parse single model
# ============================================================


def parse_model(
    item: Dict[str, Any]
) -> Dict[str, Any]:
    """
    单模型解析
    """



    model_id = get_value(

        item,

        [

            "model_id",

            "id",

            "model",

        ],

        ""

    )



    name = get_value(

        item,

        [

            "name",

        ],

        model_id

    )



    provider = normalize_provider(

        get_value(

            item,

            [

                "provider",

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

                ],

                "openai"

            ),




        "capability":

            get_value(

                item,

                [

                    "capability",

                    "capabilities",

                ],

                []

            ),




        "context_window":

            get_value(

                item,

                [

                    "context_window",

                    "context",

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




        "score":

            float(

                get_value(

                    item,

                    [

                        "score",

                    ],

                    0

                )

                or 0

            ),




        "free":

            bool(

                get_value(

                    item,

                    [

                        "free",

                    ],

                    True

                )

            ),




        "metadata":

            get_value(

                item,

                [

                    "metadata",

                ],

                item

            ),

    }



    return result





# ============================================================
# Parse list
# ============================================================


def parse_models(
    models: List[Dict]
) -> List[Dict]:


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
# Public API
# ============================================================


def parse(
    models: List[Dict]
) -> List[Dict]:
    """
    parser入口
    """

    return parse_models(

        models

    )