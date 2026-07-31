"""
normalizer.py

Normalize raw model data.

Architecture:

crawler.py
        |
        v
detail_parser.py
        |
        v
ModelInfo
        |
        v
normalizer.py


Responsibilities:

- Normalize provider
- Normalize list fields
- Normalize extra metadata


IMPORTANT:

normalizer.py MUST NOT:

- generate model_id
- infer model_id from slug
- infer model_id from display_name


Correct source:

detail_parser.py

    detail.html
        |
        v
    API Details
        |
        v
    Model ID


"""

from __future__ import annotations


import logging
from typing import Any, Dict, List


from models import ModelInfo


from providers import (
    normalize_provider_name,
    get_api_base,
)



logger = logging.getLogger(__name__)



# ============================================================
# Helpers
# ============================================================


def normalize_string(
    value: Any,
) -> str:
    """
    Normalize string.
    """

    if value is None:

        return ""



    return str(value).strip()



def normalize_list(
    value: Any,
) -> List[str]:
    """
    Normalize list fields.
    """


    if value is None:

        return []



    if isinstance(

        value,

        str,

    ):

        return [

            item.strip()

            for item in value.split(",")

            if item.strip()

        ]



    if isinstance(

        value,

        list,

    ):

        return [

            str(item).strip()

            for item in value

            if str(item).strip()

        ]



    return []



def normalize_score(
    value: Any,
) -> float:
    """
    Normalize score.
    """

    try:

        return float(value)

    except Exception:

        return 0.0



def normalize_extra(
    value: Any,
) -> Dict[str, Any]:
    """
    Normalize extra metadata.
    """

    if isinstance(

        value,

        dict,

    ):

        return value



    return {}



# ============================================================
# Model normalize
# ============================================================


def normalize_model(
    data: Dict[str, Any],
) -> ModelInfo:
    """
    Convert dictionary into ModelInfo.


    Expected:

    {
        provider,
        model_id,
        api_base,
        score,
        context,
        capability,
        modality,
        detail_url,
        best_for,
        extra
    }


    model_id MUST already exist.

    """



    if not isinstance(

        data,

        dict,

    ):

        raise TypeError(

            "model data must be dict"

        )



    provider = normalize_provider_name(

        normalize_string(

            data.get(

                "provider"

            )

        )

    )



    model_id = normalize_string(

        data.get(

            "model_id"

        )

    )



    if not model_id:


        logger.warning(

            "skip model without model_id"

        )


        raise ValueError(

            "model_id missing"

        )



    api_base = (

        data.get(

            "api_base"

        )

        or

        get_api_base(

            provider

        )

    )



    return ModelInfo(


        provider=

            provider,



        model_id=

            model_id,



        api_base=

            api_base,



        score=

            normalize_score(

                data.get(

                    "score",

                    0,

                )

            ),



        context=

            data.get(

                "context"

            ),



        capability=

            normalize_list(

                data.get(

                    "capability"

                )

            ),



        modality=

            normalize_list(

                data.get(

                    "modality"

                )

            ),



        detail_url=

            normalize_string(

                data.get(

                    "detail_url"

                )

            ),



        best_for=

            normalize_list(

                data.get(

                    "best_for"

                )

            ),



        extra=

            normalize_extra(

                data.get(

                    "extra"

                )

            ),

    )



# ============================================================
# Batch normalize
# ============================================================


def normalize_models(
    models: List[Dict[str, Any]],
) -> List[ModelInfo]:
    """
    Normalize model list.
    """


    result = []


    seen = set()



    for item in models:


        try:


            model = normalize_model(

                item

            )



            if model.model_id in seen:


                logger.info(

                    "duplicate model skipped: %s",

                    model.model_id,

                )


                continue



            seen.add(

                model.model_id

            )



            result.append(

                model

            )



        except Exception as exc:


            logger.warning(

                "normalize failed: %s",

                exc,

            )



    return result



# ============================================================
# Public API
# ============================================================


def normalize(
    models: List[Dict[str, Any]],
) -> List[ModelInfo]:
    """
    Public entry.
    """

    return normalize_models(

        models

    )