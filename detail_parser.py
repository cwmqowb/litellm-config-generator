"""
detail_parser.py

Parse FreeLLM model detail page.

Extract real API information.
"""


import re
import logging
from typing import Dict, Optional, List

import requests


logger = logging.getLogger(__name__)


HEADERS = {
    "User-Agent":
        (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        )
}



# ------------------------------------------------
# HTTP
# ------------------------------------------------

def fetch_html(url: str) -> str:

    logger.info(
        "fetch detail page: %s",
        url
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()


    return response.text



# ------------------------------------------------
# helpers
# ------------------------------------------------


def clean_text(
    text: Optional[str]
) -> str:

    if not text:
        return ""

    return (
        text
        .replace(
            "&amp;",
            "&"
        )
        .replace(
            "&#39;",
            "'"
        )
        .replace(
            "&quot;",
            '"'
        )
        .strip()
    )



def extract_between(
    html: str,
    label: str
) -> Optional[str]:

    """
    Extract value after label.

    Example:

    Model ID
    <code>
       z-ai/glm-5.2
    </code>
    """


    pattern = (
        rf"{label}.*?"
        r"<code[^>]*>"
        r"(.*?)"
        r"</code>"
    )


    match = re.search(
        pattern,
        html,
        re.S | re.I
    )


    if not match:
        return None


    return clean_text(
        match.group(1)
    )



def extract_code_values(
    html: str
) -> List[str]:

    values = re.findall(
        r"<code[^>]*>(.*?)</code>",
        html,
        re.S
    )

    return [
        clean_text(x)
        for x in values
    ]



def extract_section_value(
    html: str,
    title: str
):

    """
    Extract technical cards.

    Example:

    Context window
    <strong>
      1.0M
    </strong>
    """


    pattern = (
        rf"{title}"
        r".*?"
        r"<strong[^>]*>"
        r"(.*?)"
        r"</strong>"
    )


    match = re.search(
        pattern,
        html,
        re.S | re.I
    )


    if not match:
        return None


    return clean_text(
        match.group(1)
    )



# ------------------------------------------------
# capability
# ------------------------------------------------


def extract_capabilities(
    html: str
) -> List[str]:

    match = re.search(
        r"Capabilities</span>\s*"
        r"<strong[^>]*>"
        r"(.*?)"
        r"</strong>",
        html,
        re.S | re.I
    )


    if not match:
        return []


    value = clean_text(
        match.group(1)
    )


    return [
        x.strip()
        for x in value.split(",")
    ]



def extract_provider(
    html: str
):

    match = re.search(
        r"Provider\s*</span>\s*"
        r"<strong[^>]*>"
        r"(.*?)"
        r"</strong>",
        html,
        re.S | re.I
    )


    if match:
        return clean_text(
            match.group(1)
        )


    return ""



# ------------------------------------------------
# main parser
# ------------------------------------------------


def parse_detail(
    model: Dict
) -> Dict:


    """
    Add detail information.

    input:

    {
       name,
       detail_url
    }

    return:
    enriched model
    """


    detail_url = (
        model
        .get("detail_url")
    )


    if not detail_url:

        logger.warning(
            "no detail url: %s",
            model.get("name")
        )

        return model



    try:

        html = fetch_html(
            detail_url
        )


    except Exception as e:

        logger.error(
            "detail fetch failed %s %s",
            detail_url,
            e
        )

        return model



    result = dict(
        model
    )



    # -----------------------------
    # API Base
    # -----------------------------


    api_base = extract_between(
        html,
        "Base URL"
    )


    if api_base:

        result["api_base"] = api_base



    # -----------------------------
    # Real Model ID
    # -----------------------------


    model_id = extract_between(
        html,
        "Model ID"
    )


    if model_id:

        result["model_id"] = model_id


    else:

        result["model_id"] = (
            model.get("name")
        )



    # -----------------------------
    # provider
    # -----------------------------


    provider = extract_provider(
        html
    )


    if provider:

        result["provider"] = provider



    # -----------------------------
    # technical
    # -----------------------------


    context = extract_section_value(
        html,
        "Context window"
    )


    if context:

        result["context"] = context



    max_output = extract_section_value(
        html,
        "Max output"
    )


    if max_output:

        result["max_output"] = max_output



    # -----------------------------
    # capability
    # -----------------------------


    caps = extract_capabilities(
        html
    )


    if caps:

        result["capability"] = caps



    # -----------------------------
    # raw html codes
    # -----------------------------


    result["detail_parsed"] = True



    return result



# ------------------------------------------------
# batch api
# ------------------------------------------------


def parse_details(
    models: List[Dict]
) -> List[Dict]:

    result = []


    for model in models:

        result.append(
            parse_detail(
                model
            )
        )


    logger.info(
        "detail parser result: %s",
        len(result)
    )


    return result
