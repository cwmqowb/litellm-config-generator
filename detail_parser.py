"""
FreeLLM detail parser.

Purpose:
    Parse model detail page and convert into unified ModelInfo.

Flow:

detail.html
    |
    v
detail_parser.py
    |
    v
ModelInfo
    |
    v
LiteLLM config builder

"""

from __future__ import annotations


import logging
import re
from typing import Dict, Any, Optional, List


from bs4 import BeautifulSoup


from models import (
    ModelInfo,
    ModelCapability,
    ModelPricing,
)


logger = logging.getLogger(__name__)


# =====================================================
# text helpers
# =====================================================


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()



def normalize_number(value):

    if not value:
        return None

    value = (
        str(value)
        .replace(",", "")
        .strip()
        .upper()
    )

    try:

        if value.endswith("K"):
            return int(
                float(value[:-1])
                * 1024
            )

        if value.endswith("M"):
            return int(
                float(value[:-1])
                * 1024
                * 1024
            )

        return int(float(value))

    except Exception:
        return None



# =====================================================
# field extractor
# =====================================================


def find_value(
    soup,
    labels: List[str]
):

    for label in labels:

        node = soup.find(
            string=lambda x:
                x
                and clean_text(x).lower()
                ==
                label.lower()
        )

        if not node:
            continue


        parent = node.parent

        if not parent:
            continue


        sibling = (
            parent.find_next_sibling()
        )

        if sibling:

            value = clean_text(
                sibling.get_text(
                    " ",
                    strip=True
                )
            )

            if value:
                return value


    return ""



def extract_tags(text: str):

    tags = []

    mapping = {
        "vision": [
            "vision",
            "image",
            "multimodal"
        ],

        "reasoning": [
            "reasoning",
            "thinking"
        ],

        "coding": [
            "code",
            "coder",
            "coding"
        ],

        "tool_calling": [
            "tool",
            "function calling"
        ],

        "json_mode": [
            "json",
            "structured"
        ],
    }


    lower = text.lower()


    for tag, keys in mapping.items():

        for key in keys:

            if key in lower:
                tags.append(tag)
                break


    return tags



# =====================================================
# parser
# =====================================================


def parse_detail_html(
    html: str,
    provider: str,
    detail_url: str = ""
) -> Optional[ModelInfo]:


    if not html:
        return None


    soup = BeautifulSoup(
        html,
        "html.parser"
    )


    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )


    model_id = find_value(
        soup,
        [
            "Model ID",
            "Model",
            "Model Name"
        ]
    )


    base_url = find_value(
        soup,
        [
            "Base URL",
            "Endpoint",
            "API Base"
        ]
    )


    api_format = find_value(
        soup,
        [
            "API Format",
            "Protocol"
        ]
    )


    context_window = find_value(
        soup,
        [
            "Context Window",
            "Context Length"
        ]
    )


    output_tokens = find_value(
        soup,
        [
            "Max Output Tokens",
            "Max Tokens"
        ]
    )


    if not model_id:

        title = soup.title

        if title:
            model_id = clean_text(
                title.text
            )


    if not model_id:
        return None



    capability = ModelCapability()


    tags = extract_tags(
        page_text
    )


    for tag in tags:

        capability.raw.append(
            tag
        )


        if tag == "vision":
            capability.vision = True


        elif tag == "reasoning":
            capability.reasoning = True


        elif tag == "tool_calling":
            capability.tool_calling = True


        elif tag == "json_mode":
            capability.json_mode = True



    model = ModelInfo(

        name=model_id.split("/")[-1],

        provider=provider,

        model_id=model_id,

        detail_url=detail_url,

        api_base=base_url or None,

        api_format=api_format or None,


        capabilities=capability,


        context_window=
            normalize_number(
                context_window
            ),


        max_output_tokens=
            normalize_number(
                output_tokens
            ),


        free=True,


        pricing=ModelPricing(
            free=True
        ),


        tags=tags,

    )


    return model



# =====================================================
# compatibility wrapper
# =====================================================


def parse_model_detail_to_model(
    html: str,
    provider: str,
    detail_url: str = ""
):

    return parse_detail_html(
        html,
        provider,
        detail_url
    )
