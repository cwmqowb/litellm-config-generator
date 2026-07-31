"""
normalizer.py

Normalize raw model dictionaries into ModelInfo.


Architecture:

dict
 |
 v
normalizer.py
 |
 v
ModelInfo


Responsibilities:

- Clean provider
- Clean capability
- Clean modality
- Fill provider defaults


IMPORTANT:

This module MUST NOT create:

- name
- display_name
- title

This module MUST NOT infer fake model_id.

model_id MUST come from:

detail_parser.py

API Details -> Model ID

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


def normalize_list(
    value: Any,
) -> List[str]:
    """
    Normalize list values.
    """

    if value is None:

        return []



    if isinstance(
        value,
        str,
    ):

        return [

            item.strip().lower()

            for item in value.split(",")

            if item.strip()

        ]



    if isinstance(
        value,
        list,
    ):

        return [

            str(item)

            .strip()

            .lower()

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

        return float(value or 0)

    except Exception:

        return 0.0



# ============================================================
# Single normalize
# ============================================================


def normalize_model(
    data: Dict[str, Any],
) -> ModelInfo:
    """
    Convert dict -> ModelInfo.


    Expected input:


    {
        provider,
        model_id,
        api_base,
        score,
        context,
        capability,
        modality,
        detail_url,
        best_for
    }

    """


    if not isinstance(
        data,
        dict,
    ):

        raise TypeError(
            "model data must be dict"
        )



    provider = normalize_provider_name(

        data.get(

            "provider",

            ""

        )

    )



    model_id = (

        data.get(

            "model_id",

            ""

        )

        or ""

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

                    0

                )

            ),



        context=

            data.get(

                "context"

            ),



        capability=

            normalize_list(

                data.get(

                    "capability",

                    []

                )

            ),



        modality=

            normalize_list(

                data.get(

                    "modality",

                    []

                )

            ),



        detail_url=

            data.get(

                "detail_url",

                "",

            ),



        best_for=

            normalize_list(

                data.get(

                    "best_for",

                    []

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


            if not model.is_valid():


                logger.warning(

                    "invalid model skipped: %s",

                    item,

                )

                continue



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



        except Exception:


            logger.exception(

                "normalize failed: %s",

                item,

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