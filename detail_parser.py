"""
detail_parser.py

FreeLLM model detail page parser.


Responsibility:

Parse model detail.html.


Input:

crawler.py output:

{
    provider,
    detail_url,
    slug,
    display_name,
    extra
}


Output:

ModelInfo


Important:

model_id MUST come from:

API Details -> Model ID


Never use:

- display_name
- slug

as LiteLLM model name.


"""

from __future__ import annotations


import logging
from typing import Any, Dict, List, Optional


import requests
from bs4 import BeautifulSoup


from models import ModelInfo


from providers import normalize_provider_name



logger = logging.getLogger(__name__)



HEADERS = {

    "User-Agent":

        (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "Chrome/120 Safari/537.36"
        )

}



# ============================================================
# HTTP
# ============================================================


def fetch_detail_html(
    url: str,
) -> str:
    """
    Fetch model detail page.
    """


    response = requests.get(

        url,

        headers=HEADERS,

        timeout=30,

    )


    response.raise_for_status()


    return response.text



# ============================================================
# Helpers
# ============================================================


def clean_text(
    value: Optional[str],
) -> str:
    """
    Normalize text.
    """

    if not value:

        return ""

    return (

        value

        .strip()

        .replace(

            "\n",

            " "

        )

    )



def split_values(
    value: str,
) -> List[str]:
    """
    Convert:

    "text, reasoning"

    into:

    [
        "text",
        "reasoning"
    ]

    """

    if not value:

        return []


    return [

        item.strip()

        for item in value.split(",")

        if item.strip()

    ]



# ============================================================
# API Details
# ============================================================


def parse_api_details(
    soup: BeautifulSoup,
) -> Dict[str, str]:
    """
    Parse:

    <section class="api-details">

        <div class="api-detail">

            <span>Base URL</span>

            <div class="api-detail-value">

                <code>...</code>

            </div>

        </div>


    </section>


    Extract:

    Base URL

    Model ID

    """

    result = {}


    section = soup.select_one(

        ".api-details"

    )


    if not section:

        return result



    for item in section.select(

        ".api-detail"

    ):


        label = item.find(

            "span"

        )


        if not label:

            continue



        key = clean_text(

            label.get_text()

        )


        value = ""



        code = item.select_one(

            "code"

        )


        if code:

            value = clean_text(

                code.get_text()

            )



        else:


            strong = item.find(

                "strong"

            )


            if strong:

                value = clean_text(

                    strong.get_text()

                )



        if key and value:


            result[key] = value



    return result



# ============================================================
# Technical Details
# ============================================================


def parse_technical_details(
    soup: BeautifulSoup,
) -> Dict[str, str]:
    """
    Parse:

    .technical-details-grid


    Example:

    Context window
    1.0M


    Input
    text, reasoning


    Capabilities
    reasoning, tool calling


    """

    result = {}


    grid = soup.select_one(

        ".technical-details-grid"

    )


    if not grid:

        return result



    for item in grid.find_all(

        "div",

        recursive=False,

    ):


        label = item.find(

            "span"

        )


        value = item.find(

            "strong"

        )


        if not label or not value:

            continue



        key = clean_text(

            label.get_text()

        )


        val = clean_text(

            value.get_text()

        )


        if key:

            result[key] = val



    return result



# ============================================================
# Best For
# ============================================================


def parse_best_for(
    soup: BeautifulSoup,
) -> List[str]:
    """
    Parse:

    .best-for-list

    """

    result = []


    for item in soup.select(

        ".best-for-list li"

    ):


        value = clean_text(

            item.get_text()

        )


        if value:

            result.append(

                value

            )


    return result



# ============================================================
# Recommendation / Benchmark extra
# ============================================================


def parse_extra(
    soup: BeautifulSoup,
) -> Dict[str, Any]:
    """
    Preserve useful fields.

    Not used for LiteLLM model name.

    """

    extra = {}



    benchmark = []


    for item in soup.select(

        ".benchmark-row"

    ):


        label = item.find(

            "strong"

        )


        value = item.select_one(

            ".benchmark-value"

        )


        if label and value:


            benchmark.append(

                {

                    "name":

                        clean_text(

                            label.get_text()

                        ),


                    "value":

                        clean_text(

                            value.get_text()

                        ),

                }

            )



    if benchmark:

        extra["benchmark"] = benchmark



    return extra



# ============================================================
# Public parser
# ============================================================


def parse_detail_page(
    model: Dict[str, Any],
) -> Optional[ModelInfo]:
    """
    Parse one crawler model.

    """

    detail_url = model.get(

        "detail_url"

    )


    if not detail_url:

        return None



    html = fetch_detail_html(

        detail_url

    )


    soup = BeautifulSoup(

        html,

        "html.parser"

    )


    api_details = parse_api_details(

        soup

    )


    technical = parse_technical_details(

        soup

    )


    best_for = parse_best_for(

        soup

    )


    model_id = api_details.get(

        "Model ID"

    )



    if not model_id:


        logger.warning(

            "missing model id: %s",

            detail_url,

        )


        return None



    provider = normalize_provider_name(

        model.get(

            "provider",

            ""

        )

    )



    api_base = api_details.get(

        "Base URL"

    )



    context = technical.get(

        "Context window"

    )



    capabilities = split_values(

        technical.get(

            "Capabilities",

            ""

        )

    )



    modality = split_values(

        technical.get(

            "Input",

            ""

        )

    )



    extra = {}



    if model.get(

        "extra"

    ):

        extra.update(

            model["extra"]

        )



    extra.update(

        parse_extra(

            soup

        )

    )



    return ModelInfo(

        provider=provider,


        model_id=model_id,


        api_base=api_base,


        score=float(

            model.get(

                "score",

                0.0

            )

            or 0.0

        ),


        context=context,


        capability=capabilities,


        modality=modality,


        detail_url=detail_url,


        best_for=best_for,


        extra=extra,

    )



# ============================================================
# Batch parser
# ============================================================


def parse_details(
    models: List[Dict[str, Any]],
) -> List[ModelInfo]:
    """
    Parse crawler result list.
    """

    result = []


    for index, model in enumerate(

        models,

        start=1,

    ):


        logger.info(

            "parse detail %s/%s: %s",

            index,

            len(models),

            model.get(

                "detail_url"

            ),

        )



        try:


            parsed = parse_detail_page(

                model

            )


            if parsed:

                result.append(

                    parsed

                )


        except Exception as exc:


            logger.warning(

                "detail parse failed: %s",

                exc,

            )



    logger.info(

        "detail parsed models: %s",

        len(result),

    )


    return result