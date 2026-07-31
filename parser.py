"""
parser.py

Generic data parser utilities.


Responsibility:

- Parse raw dictionaries
- Extract safe values
- Normalize basic fields


IMPORTANT:

parser.py does NOT create ModelInfo.

The final conversion:

detail_parser.py
        |
        v
ModelInfo


parser.py MUST NOT handle:

- name
- display_name
- title
- model alias
- LiteLLM model name

"""

from __future__ import annotations


import logging
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)



# ============================================================
# Value helpers
# ============================================================


def get_value(
    data: Dict[str, Any],
    keys: List[str],
    default=None,
):
    """
    Get first existing key.

    Example:

    get_value(
        data,
        [
            "provider",
            "vendor"
        ]
    )

    """

    if not isinstance(
        data,
        dict,
    ):

        return default



    for key in keys:


        if key in data:


            value = data[key]


            if value is not None:


                return value



    return default



def get_string(
    value: Any,
    default: str = "",
) -> str:
    """
    Convert value to string.
    """


    if value is None:

        return default



    return str(value).strip()



def get_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safe float conversion.
    """

    try:

        return float(value)

    except Exception:

        return default



def get_list(
    value: Any,
) -> List[str]:
    """
    Convert value to list[str].
    """

    if value is None:

        return []



    if isinstance(
        value,
        str,
    ):

        return [

            x.strip()

            for x in value.split(",")

            if x.strip()

        ]



    if isinstance(
        value,
        list,
    ):

        return [

            str(x).strip()

            for x in value

            if str(x).strip()

        ]



    return []



# ============================================================
# Raw crawler parser
# ============================================================


def parse_crawler_item(
    item: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize crawler output.


    Input:

    {
        provider,
        score,
        detail_url,
        slug
    }


    Output:

    same structure.


    No model_id generated.
    """


    if not isinstance(
        item,
        dict,
    ):

        return {}



    return {


        "provider":

            get_string(

                get_value(

                    item,

                    [
                        "provider"
                    ]

                )

            ),



        "score":

            get_float(

                get_value(

                    item,

                    [
                        "score"
                    ],

                    0

                )

            ),



        "detail_url":

            get_string(

                get_value(

                    item,

                    [
                        "detail_url"
                    ]

                )

            ),



        "slug":

            get_string(

                get_value(

                    item,

                    [
                        "slug"
                    ]

                )

            ),

    }



# ============================================================
# Batch parser
# ============================================================


def parse_crawler_items(
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Parse crawler result list.
    """


    result = []



    for item in items:


        try:


            parsed = parse_crawler_item(

                item

            )


            if parsed:


                result.append(

                    parsed

                )



        except Exception:


            logger.exception(

                "parse crawler item failed: %s",

                item,

            )



    return result



# ============================================================
# Public API
# ============================================================


def parse(
    data,
):
    """
    Public parser entry.


    Currently only normalizes crawler output.

    """

    if isinstance(
        data,
        list,
    ):

        return parse_crawler_items(

            data

        )


    if isinstance(
        data,
        dict,
    ):

        return parse_crawler_item(

            data

        )


    return {}