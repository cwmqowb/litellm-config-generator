"""
detail_parser.py

FreeLLM model detail page parser.


Responsibility:

Access model detail page and parse:

API Details:

    - Base URL
    - Model ID


Technical Details:

    - Context window
    - Input
    - Output
    - Capabilities


Best For:

    - Recommended usage


IMPORTANT:

model_id MUST come from:

    Detail Page
        |
        v
    API Details
        |
        v
    Model ID


Never trust crawler output.
"""

from __future__ import annotations


import logging
from typing import Dict, Optional


import requests

from bs4 import BeautifulSoup


from models import ModelInfo


logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 20



# ============================================================
# Parser
# ============================================================


class DetailParser:
    """
    Parse FreeLLM detail page.
    """


    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):

        self.timeout = timeout


        self.session = (
            session
            or requests.Session()
        )


        self.session.headers.update(

            {

                "User-Agent":

                    (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "Chrome/120 Safari/537.36"
                    )

            }

        )



    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------


    def parse(
        self,
        raw_model: Dict,
    ) -> Optional[ModelInfo]:
        """
        Convert crawler result into ModelInfo.

        Input:

        {
            provider,
            score,
            detail_url,
            slug
        }


        Output:

        ModelInfo
        """


        detail_url = (
            raw_model.get(
                "detail_url"
            )
        )


        if not detail_url:

            logger.warning(
                "missing detail url: %s",
                raw_model,
            )

            return None



        html = self._fetch(
            detail_url
        )


        if not html:

            return None



        soup = BeautifulSoup(
            html,
            "html.parser",
        )



        data = {}


        data.update(

            self._parse_api_details(
                soup
            )

        )


        data.update(

            self._parse_technical_details(
                soup
            )

        )


        data.update(

            self._parse_best_for(
                soup
            )

        )



        model_id = (
            data.get(
                "model_id"
            )
        )


        if not model_id:

            logger.warning(
                "detail page has no model id: %s",
                detail_url,
            )

            return None



        return ModelInfo(

            provider=
                raw_model.get(
                    "provider",
                    "",
                ),


            model_id=model_id,


            api_base=
                data.get(
                    "api_base"
                ),


            score=float(
                raw_model.get(
                    "score",
                    0,
                )
                or 0
            ),


            context=
                data.get(
                    "context"
                ),


            capability=
                data.get(
                    "capability",
                    [],
                ),


            modality=
                data.get(
                    "modality",
                    [],
                ),


            detail_url=
                detail_url,


            best_for=
                data.get(
                    "best_for",
                    [],
                ),

        )



    # --------------------------------------------------------
    # HTTP
    # --------------------------------------------------------


    def _fetch(
        self,
        url: str,
    ) -> Optional[str]:

        try:

            response = (
                self.session
                .get(
                    url,
                    timeout=self.timeout,
                )
            )


            response.raise_for_status()


            return response.text



        except Exception as exc:

            logger.warning(

                "detail fetch failed %s: %s",

                url,

                exc,

            )


            return None



    # --------------------------------------------------------
    # API Details
    # --------------------------------------------------------


    def _parse_api_details(
        self,
        soup: BeautifulSoup,
    ) -> Dict:

        result = {}


        section = soup.find(

            "section",

            class_="api-details",

        )


        if not section:

            return result



        base_url = self._find_code_value(

            section,

            "Base URL",

        )


        if base_url:

            result["api_base"] = base_url



        model_id = self._find_code_value(

            section,

            "Model ID",

        )


        if model_id:

            result["model_id"] = model_id



        return result



    def _find_code_value(
        self,
        container,
        label: str,
    ) -> Optional[str]:
        """
        Find:

        <span>
            Model ID
        </span>

        <code>
            z-ai/glm-5.2
        </code>
        """


        span = container.find(

            "span",

            string=lambda x:

                x and label in x,

        )


        if not span:

            return None



        parent = span.parent


        code = parent.find(
            "code"
        )


        if not code:

            return None



        return (
            code
            .get_text(
                strip=True
            )
        )



    # --------------------------------------------------------
    # Technical Details
    # --------------------------------------------------------


    def _parse_technical_details(
        self,
        soup: BeautifulSoup,
    ) -> Dict:

        result = {}


        section = soup.find(

            "section",

            class_="technical-details-card",

        )


        if not section:

            return result



        grid = section.find(

            class_="technical-details-grid"

        )


        if not grid:

            return result



        values = {}



        for item in grid.find_all(
            recursive=False
        ):


            key = item.find(
                "span"
            )


            value = item.find(
                "strong"
            )


            if key and value:

                values[

                    key.get_text(
                        strip=True
                    )

                ] = (

                    value
                    .get_text(
                        strip=True
                    )

                )



        if "Context window" in values:

            result["context"] = (

                values[
                    "Context window"
                ]

            )



        if "Capabilities" in values:

            result["capability"] = [

                x.strip()

                for x in

                values[
                    "Capabilities"
                ]
                .split(",")

                if x.strip()

            ]



        if "Input" in values:

            result["modality"] = [

                x.strip()

                for x in

                values[
                    "Input"
                ]
                .split(",")

                if x.strip()

            ]



        return result



    # --------------------------------------------------------
    # Best For
    # --------------------------------------------------------


    def _parse_best_for(
        self,
        soup: BeautifulSoup,
    ) -> Dict:

        result = {}


        section = soup.find(

            class_="best-for-card"

        )


        if not section:

            return result



        items = []


        for li in section.find_all(
            "li"
        ):


            text = (

                li.get_text(
                    strip=True
                )

            )


            if text:

                items.append(
                    text.lower()
                )



        if items:

            result["best_for"] = items



        return result



# ============================================================
# Compatibility helper
# ============================================================


def parse_model_detail(
    raw_model: Dict,
) -> Optional[ModelInfo]:
    """
    Public helper.
    """

    parser = DetailParser()

    return parser.parse(
        raw_model
    )