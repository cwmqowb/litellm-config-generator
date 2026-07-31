"""
parser.py

Generic HTML parsing utilities.


Responsibility:

Provide reusable HTML helper functions.


Used by:

crawler.py
detail_parser.py


NOT responsible for:

- model extraction
- model_id generation
- provider mapping
- LiteLLM config generation


Business parsing belongs to:

crawler.py

detail_parser.py

"""

from __future__ import annotations


import json
import logging
from typing import Any, Dict, List, Optional



from bs4 import BeautifulSoup



logger = logging.getLogger(__name__)



# ============================================================
# HTML
# ============================================================


def create_soup(
    html: str,
) -> BeautifulSoup:
    """
    Create BeautifulSoup object.
    """

    return BeautifulSoup(

        html,

        "html.parser",

    )



def extract_text(
    element,
    default: str = "",
) -> str:
    """
    Extract clean text.
    """


    if element is None:

        return default



    text = element.get_text(

        " ",

        strip=True,

    )


    return text or default



# ============================================================
# JSON-LD
# ============================================================


def extract_json_ld(
    html: str,
) -> List[Any]:
    """
    Extract JSON-LD blocks.

    Example:

    <script type="application/ld+json">

    """



    soup = create_soup(

        html

    )


    result = []



    scripts = soup.find_all(

        "script",

        attrs={

            "type":

                "application/ld+json"

        },

    )



    for script in scripts:


        if not script.string:

            continue



        try:


            data = json.loads(

                script.string

            )


            result.append(

                data

            )



        except Exception:


            logger.debug(

                "invalid json ld"

            )



    return result



# ============================================================
# DOM helpers
# ============================================================


def find_section(
    soup: BeautifulSoup,
    class_name: str,
):
    """
    Find section by class.
    """

    return soup.find(

        "section",

        class_=class_name,

    )



def find_value_by_label(
    container,
    label: str,
) -> Optional[str]:
    """
    Generic key-value parser.


    Example:


    Label:

        Model ID


    Value:

        z-ai/glm-5.2


    """



    if container is None:

        return None



    text = container.get_text(

        "\n",

        strip=True,

    )



    lines = [

        line.strip()

        for line in text.splitlines()

        if line.strip()

    ]



    for index, line in enumerate(lines):


        if line.lower() == label.lower():


            if index + 1 < len(lines):


                return lines[index + 1]



    return None



# ============================================================
# Lists
# ============================================================


def extract_list_items(
    container,
) -> List[str]:
    """
    Extract li text.
    """

    if container is None:

        return []



    result = []



    for item in container.find_all(

        "li"

    ):


        text = extract_text(

            item

        )


        if text:

            result.append(

                text

            )



    return result



def split_values(
    value: str,
) -> List[str]:
    """
    Split comma separated values.
    """

    if not value:

        return []



    return [

        item.strip()

        for item in value.split(",")

        if item.strip()

    ]



# ============================================================
# Recursive search
# ============================================================


def find_key_recursive(
    data: Any,
    key: str,
):
    """
    Recursive dictionary search.

    Useful for:

    JSON-LD

    """



    if isinstance(

        data,

        dict,

    ):


        if key in data:

            return data[key]



        for value in data.values():


            result = find_key_recursive(

                value,

                key,

            )


            if result is not None:

                return result



    elif isinstance(

        data,

        list,

    ):


        for item in data:


            result = find_key_recursive(

                item,

                key,

            )


            if result is not None:

                return result



    return None