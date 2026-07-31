"""
crawler.py

FreeLLM model list crawler.

Responsibility ONLY:

- Download models.html
- Parse model list page
- Extract:

    provider
    score
    detail_url
    slug


IMPORTANT:

crawler.py MUST NOT parse:

- model_id
- display name
- title
- model name

Real model_id MUST come from:

detail_parser.py

detail page:

API Details -> Model ID
"""

from __future__ import annotations


import gzip
import logging
import re
from typing import Dict, List, Optional
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



# ============================================================
# HTTP
# ============================================================


def fetch_html(
    url: str,
) -> str:
    """
    Download html page.
    """

    logger.info(
        "fetch html: %s",
        url,
    )


    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )


    response.raise_for_status()


    content = response.content


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



    return content.decode(
        "utf-8",
        errors="ignore",
    )



# ============================================================
# HTML helpers
# ============================================================


def extract_attr(
    html: str,
    attr: str,
) -> Optional[str]:
    """
    Extract html attribute.

    Example:

    data-provider="NVIDIA NIM"

    """

    match = re.search(
        rf'{attr}="([^"]*)"',
        html,
    )


    if not match:

        return None


    return (
        match.group(1)
        .strip()
    )



def clean_text(
    value: Optional[str],
) -> str:

    if not value:

        return ""


    return (
        value
        .replace("&amp;", "&")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
        .strip()
    )



# ============================================================
# Parser
# ============================================================


def parse_model_rows(
    html: str,
) -> List[Dict]:
    """
    Parse model list page.

    Output example:

    {
        "provider": "NVIDIA NIM",
        "score": 95.5,
        "detail_url":
            "https://freellm.net/models/xxx",
        "slug": "xxx"
    }


    NO model_id here.
    """

    models = []


    rows = re.findall(
        r'<tr\s+class="model-row".*?</tr>',
        html,
        re.S,
    )


    logger.info(
        "model rows found: %s",
        len(rows),
    )


    for row in rows:


        provider = extract_attr(
            row,
            "data-provider",
        )


        score = extract_attr(
            row,
            "data-score",
        )


        slug = extract_attr(
            row,
            "data-slug",
        )



        if not provider:

            continue



        detail_url = None



        link = re.search(
            r'href="([^"]+/models/[^"]+)"',
            row,
        )


        if link:

            detail_url = urljoin(
                BASE_URL,
                link.group(1),
            )



        if not slug and detail_url:

            slug = (
                detail_url
                .rstrip("/")
                .split("/")
                [-1]
            )



        try:

            score_value = float(
                score or 0
            )

        except Exception:

            score_value = 0.0



        models.append(

            {

                "provider":
                    clean_text(
                        provider
                    ),


                "score":
                    score_value,


                "detail_url":
                    detail_url
                    or "",


                "slug":
                    clean_text(
                        slug
                    ),

            }

        )



    return models



# ============================================================
# JSON fallback
# ============================================================


def parse_json_models(
    html: str,
) -> List[Dict]:
    """
    Fallback parser.

    Only extracts:

    provider
    detail_url
    slug

    """

    result = []


    matches = re.findall(
        r'\{"@type":"ListItem".*?\}',
        html,
    )


    for item in matches:

        slug = item


        result.append(

            {

                "provider":
                    "",


                "score":
                    0,


                "detail_url":
                    "",


                "slug":
                    slug,

            }

        )


    return result



# ============================================================
# Public API
# ============================================================


def crawl_models(
    top_k: int = 50,
    url: str = MODELS_URL,
) -> List[Dict]:
    """
    Crawl model list.

    Return:

    List[
        {
            provider,
            score,
            detail_url,
            slug
        }
    ]

    """

    html = fetch_html(
        url
    )


    models = parse_model_rows(
        html
    )


    if not models:

        logger.warning(
            "html parser empty, "
            "try json fallback",
        )


        models = parse_json_models(
            html
        )



    logger.info(
        "crawler extracted: %s",
        len(models),
    )


    return models[:top_k]