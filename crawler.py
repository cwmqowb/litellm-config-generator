"""
crawler.py

FreeLLM model crawler.

Responsibilities:
- Crawl freellm.net models page
- Extract ranked model list
- Extract:
    - rank
    - name
    - provider
    - score
    - detail url

Detail information should be handled by detail_parser.py
"""

import re
import json
import gzip
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests


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
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        ),
    "Accept":
        (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
}


# -------------------------------------------------
# HTTP
# -------------------------------------------------

def fetch_html(url: str) -> str:
    """
    Fetch page html.
    """

    logger.info(
        "fetch html: %s",
        url
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()


    content = response.content


    # gzip fallback
    if (
        response.headers.get(
            "content-encoding"
        )
        == "gzip"
    ):
        try:
            content = gzip.decompress(
                content
            )
        except Exception:
            pass


    html = content.decode(
        "utf-8",
        errors="ignore"
    )


    return html



# -------------------------------------------------
# helpers
# -------------------------------------------------

def clean_text(value: str) -> str:
    if not value:
        return ""

    return (
        value
        .replace("&amp;", "&")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .strip()
    )



def extract_attr(
    tag: str,
    attr: str
) -> Optional[str]:
    """
    Extract html attribute.

    Example:
        data-score="95"
    """

    pattern = (
        rf'{attr}="([^"]*)"'
    )

    match = re.search(
        pattern,
        tag
    )

    if not match:
        return None

    return match.group(1)



# -------------------------------------------------
# Main parser
# -------------------------------------------------

def parse_model_rows(
    html: str
) -> List[Dict]:


    models = []


    rows = re.findall(
        r'<tr\s+class="model-row".*?</tr>',
        html,
        re.S
    )


    logger.info(
        "model-row found: %s",
        len(rows)
    )


    rank = 1


    for row in rows:


        # -------------------------
        # attributes
        # -------------------------

        name = extract_attr(
            row,
            "data-name"
        )


        provider = extract_attr(
            row,
            "data-provider"
        )


        score = extract_attr(
            row,
            "data-score"
        )


        modality = extract_attr(
            row,
            "data-modality"
        )


        context = extract_attr(
            row,
            "data-context"
        )


        released = extract_attr(
            row,
            "data-released"
        )


        verified = extract_attr(
            row,
            "data-verified"
        )


        if not name:
            continue



        # -------------------------
        # detail url
        # -------------------------

        detail_path = None


        link = re.search(
            r'href="([^"]+/models/[^"]+)"',
            row
        )


        if link:
            detail_path = link.group(1)



        detail_url = (
            urljoin(
                BASE_URL,
                detail_path
            )
            if detail_path
            else None
        )


        try:
            score_value = float(score)
        except Exception:
            score_value = 0



        try:
            context_value = int(context)
        except Exception:
            context_value = None



        model = {

            # ranking
            "rank": rank,


            # basic info
            "id": name,
            "name": clean_text(name),
            "provider": clean_text(provider),


            # ranking score
            "score": score_value,


            # metadata
            "modality": (
                modality.split(",")
                if modality
                else []
            ),

            "context": context_value,

            "released": released,

            "verified":
                verified == "1",


            # detail page
            "detail_url": detail_url,

        }


        models.append(model)


        rank += 1



    return models



# -------------------------------------------------
# fallback json parser
# -------------------------------------------------

def parse_json_models(
    html: str
) -> List[Dict]:

    """
    Old fallback.
    Keep compatibility.
    """

    models = []


    matches = re.findall(
        r'\{"@type":"ListItem".*?\}',
        html
    )


    for item in matches:

        try:

            data = json.loads(
                item
            )

            name = (
                data
                .get("item", {})
                .get("name")
            )

            if name:
                models.append(
                    {
                        "rank":
                            len(models)+1,

                        "id":
                            name,

                        "name":
                            name,

                        "provider":
                            "",

                        "score":
                            0,

                        "detail_url":
                            None,
                    }
                )

        except Exception:
            continue


    return models



# -------------------------------------------------
# public api
# -------------------------------------------------

def crawl_models(
    top_k: int = 50,
    url: str = MODELS_URL
) -> List[Dict]:

    """
    Crawl freellm models.

    Args:
        top_k:
            number of models

    Returns:
        list of models
    """


    logger.info(
        "crawl models from %s",
        url
    )


    html = fetch_html(
        url
    )


    models = parse_model_rows(
        html
    )


    if not models:

        logger.warning(
            "model-row parser failed, "
            "try json fallback"
        )


        models = parse_json_models(
            html
        )


    logger.info(
        "raw extracted models: %s",
        len(models)
    )


    if models:

        logger.info(
            "first model: %s",
            models[0]
        )


    result = models[:top_k]


    logger.info(
        "crawler result: %s",
        len(result)
    )


    return result
