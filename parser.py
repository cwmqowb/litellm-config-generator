"""
freellm model detail parser

Parse model detail page:

- model id
- logical name
- base url
- api format
- context window
- max output tokens
- capabilities
- tags

The parser is intentionally tolerant because freellm
frontend structure may change.
"""

import re
import logging
from typing import Dict, Any, List

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# text helpers
# ---------------------------------------------------------

def clean_text(value: Any) -> str:
    """
    Normalize text.
    """

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def normalize_number(value: str):
    """
    Convert:

    1M
    128K
    32768

    to integer.

    """

    if not value:
        return None

    value = value.upper().replace(",", "").strip()

    try:

        if value.endswith("M"):
            return int(float(value[:-1]) * 1024 * 1024)

        if value.endswith("K"):
            return int(float(value[:-1]) * 1024)

        return int(float(value))

    except Exception:
        return None


# ---------------------------------------------------------
# safe field extraction
# ---------------------------------------------------------

def find_field_value(
    soup: BeautifulSoup,
    labels: List[str],
) -> str:
    """
    Extract value near label.

    Avoid global regex matching.

    Old:

        soup.find(string=re.compile("Model"))

    caused:

        Models
        Free Models
        Rate Limits

    pollution.

    """

    for label in labels:

        # exact text nodes
        nodes = soup.find_all(
            string=lambda x:
                x and clean_text(x).lower() == label.lower()
        )

        for node in nodes:

            parent = node.parent

            if not parent:
                continue


            # sibling value

            sibling = parent.find_next_sibling()

            if sibling:

                value = clean_text(
                    sibling.get_text(" ", strip=True)
                )

                if value:
                    return value


            # parent container

            text = clean_text(
                parent.get_text(
                    " ",
                    strip=True
                )
            )


            if text.lower().startswith(
                label.lower()
            ):

                value = clean_text(
                    text[
                        len(label):
                    ]
                )

                if value:
                    return value


            # nearby element

            nearby = parent.find_next()

            if nearby:

                value = clean_text(
                    nearby.get_text(
                        " ",
                        strip=True
                    )
                )

                if (
                    value
                    and value.lower()
                    != label.lower()
                ):
                    return value


    return ""



# ---------------------------------------------------------
# model name cleaning
# ---------------------------------------------------------

def normalize_model_name(
    name: str
) -> str:

    if not name:
        return ""


    bad_keywords = [
        "free",
        "api key",
        "rate limits",
        "models",
        "model count",
    ]


    lower = name.lower()


    for keyword in bad_keywords:

        if keyword in lower:

            return ""


    return clean_text(name)



# ---------------------------------------------------------
# capability parser
# ---------------------------------------------------------

def parse_capabilities(
    text: str
) -> List[str]:

    if not text:
        return []


    text = text.lower()

    result = set()


    mapping = {

        "vision":
            [
                "vision",
                "image",
                "multimodal",
            ],

        "reasoning":
            [
                "reasoning",
                "think",
                "cot",
                "r1",
            ],

        "coding":
            [
                "code",
                "coder",
                "programming",
            ],

        "embedding":
            [
                "embedding",
                "embed",
            ],

        "rerank":
            [
                "rerank",
                "ranking",
            ],

        "image":
            [
                "image generation",
                "text to image",
                "diffusion",
            ],

        "audio":
            [
                "audio",
                "speech",
                "voice",
            ],

        "chat":
            [
                "chat",
                "instruction",
                "conversation",
            ],
    }


    for capability, keywords in mapping.items():

        for keyword in keywords:

            if keyword in text:

                result.add(capability)
                break


    return sorted(result)



# ---------------------------------------------------------
# main parser
# ---------------------------------------------------------

def parse_model_detail(
    html: str
) -> Dict[str, Any]:

    result = {

        "logical_name": "",

        "model_id": "",

        "base_url": "",

        "api_format": "",

        "context_window": None,

        "max_output_tokens": None,

        "capabilities": [],

        "tags": [],

    }


    if not html:

        return result


    try:

        soup = BeautifulSoup(
            html,
            "html.parser"
        )


        # complete page text

        page_text = clean_text(
            soup.get_text(
                " ",
                strip=True
            )
        )


        # -----------------------------
        # model id
        # -----------------------------

        model_id = find_field_value(
            soup,
            [
                "Model ID",
                "Model Name",
                "Model",
            ],
        )


        model_id = normalize_model_name(
            model_id
        )


        if model_id:

            result["model_id"] = model_id


            result["logical_name"] = (
                model_id.split("/")[-1]
            )



        # -----------------------------
        # api base
        # -----------------------------

        base_url = find_field_value(
            soup,
            [
                "Base URL",
                "API Base",
                "Endpoint",
            ],
        )


        if (
            base_url.startswith(
                "http"
            )
        ):

            result["base_url"] = base_url



        # -----------------------------
        # api format
        # -----------------------------

        result["api_format"] = (
            find_field_value(
                soup,
                [
                    "API Format",
                    "Protocol",
                ],
            )
        )


        # -----------------------------
        # context window
        # -----------------------------

        context = find_field_value(
            soup,
            [
                "Context Window",
                "Context Length",
                "Context Size",
            ],
        )


        result["context_window"] = (
            normalize_number(context)
        )



        # -----------------------------
        # max output
        # -----------------------------

        output = find_field_value(
            soup,
            [
                "Max Output Tokens",
                "Max Tokens",
                "Output Tokens",
            ],
        )


        result["max_output_tokens"] = (
            normalize_number(output)
        )



        # -----------------------------
        # capabilities
        # -----------------------------

        result["capabilities"] = (
            parse_capabilities(
                page_text
            )
        )


        # -----------------------------
        # tags
        # -----------------------------

        tags = find_field_value(
            soup,
            [
                "Tags",
                "Capabilities",
            ],
        )


        if tags:

            result["tags"] = [
                clean_text(x)
                for x in re.split(
                    r"[,|/]",
                    tags
                )
                if clean_text(x)
            ]



    except Exception:

        logger.exception(
            "parse model detail failed"
        )


    return result
