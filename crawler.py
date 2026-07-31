"""
crawler.py

FreeLLM models.html crawler.


Responsibility:

Only parse model list page.


Source:

https://freellm.net/models/?free=1


Extract:

- provider
- detail_url
- slug
- display_name
- raw metadata


DO NOT extract:

- model_id
- api_base
- context
- capability


model_id source:

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


import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


import requests
from bs4 import BeautifulSoup



logger = logging.getLogger(__name__)



BASE_URL = "https://freellm.net"


MODELS_URL = (
    "https://freellm.net/models/?free=1"
)



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


def fetch_html(
    url: str = MODELS_URL,
) -> str:
    """
    Download models.html.
    """

    response = requests.get(

        url,

        headers=HEADERS,

        timeout=30,

    )


    response.raise_for_status()


    logger.info(

        "html length: %s",

        len(response.text),

    )


    return response.text



# ============================================================
# JSON-LD
# ============================================================


def extract_json_ld(
    html: str,
) -> List[Any]:
    """
    Extract JSON-LD blocks.
    """

    soup = BeautifulSoup(

        html,

        "html.parser",

    )


    result = []



    for script in soup.find_all(

        "script",

        attrs={

            "type":

                "application/ld+json"

        },

    ):


        content = script.get_text(

            strip=True

        )


        if not content:

            continue



        try:


            result.append(

                json.loads(

                    content

                )

            )


        except Exception:


            logger.debug(

                "invalid json ld"

            )



    logger.info(

        "json ld blocks: %s",

        len(result),

    )


    return result



# ============================================================
# Find ItemList
# ============================================================


def find_item_list(
    data: Any,
) -> Optional[List[Dict[str, Any]]]:
    """
    Find:

    {
        "@type":"ItemList",
        "itemListElement":[]
    }

    """



    if isinstance(

        data,

        dict,

    ):


        if (

            data.get(

                "@type"

            )

            ==

            "ItemList"

            and

            isinstance(

                data.get(

                    "itemListElement"

                ),

                list,

            )

        ):

            return data[

                "itemListElement"

            ]



        for value in data.values():


            found = find_item_list(

                value

            )


            if found is not None:

                return found



    elif isinstance(

        data,

        list,

    ):


        for item in data:


            found = find_item_list(

                item

            )


            if found is not None:

                return found



    return None



# ============================================================
# Parse item
# ============================================================


def parse_item(
    item: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Parse one ListItem.


    Real structure:


    {
      "@type":"ListItem",

      "position":1,

      "item":{

          "@type":"SoftwareApplication",

          "name":"z-ai/glm-5.2",

          "url":"https://freellm.net/models/nvidia-nim/z-ai-glm-5-2",

          "provider":{

              "name":"NVIDIA NIM"

          }

      }

    }


    """



    if not isinstance(

        item,

        dict,

    ):

        return None



    software = item.get(

        "item"

    )



    if not isinstance(

        software,

        dict,

    ):

        return None



    display_name = (

        software.get(

            "name"

        )

        or ""

    ).strip()



    detail_url = (

        software.get(

            "url"

        )

        or ""

    ).strip()



    if not detail_url:

        return None



    provider = ""



    provider_data = software.get(

        "provider"

    )



    if isinstance(

        provider_data,

        dict,

    ):


        provider = (

            provider_data.get(

                "name"

            )

            or ""

        ).strip()



    slug = (

        urlparse(

            detail_url

        )

        .path

        .rstrip("/")

        .split("/")

        [-1]

    )



    return {


        "provider":

            provider,



        "detail_url":

            detail_url,



        "slug":

            slug,



        #
        # Only for display/debug.
        #
        # NEVER used as LiteLLM model.
        #

        "display_name":

            display_name,



        "extra":

            {

                "position":

                    item.get(

                        "position"

                    ),



                "source":

                    "models.html",

            }

    }



# ============================================================
# Public API
# ============================================================


def crawl_models(
    top_k: int = 50,
    url: str = MODELS_URL,
) -> List[Dict[str, Any]]:
    """
    Crawl model list.

    Return raw crawler data.

    """


    html = fetch_html(

        url

    )


    json_blocks = extract_json_ld(

        html

    )


    item_list = None



    for block in json_blocks:


        item_list = find_item_list(

            block

        )


        if item_list is not None:

            break



    if not item_list:


        logger.warning(

            "ItemList not found"

        )


        return []



    logger.info(

        "ItemList models: %s",

        len(item_list),

    )



    result = []



    for item in item_list:


        parsed = parse_item(

            item

        )


        if parsed:

            result.append(

                parsed

            )



    logger.info(

        "crawler result: %s",

        len(result),

    )



    return result[:top_k]