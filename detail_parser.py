"""
detail_parser.py

Parse freellm.net model detail pages.

Responsibilities:
- Fetch model detail page
- Extract real API model id
- Extract provider endpoint
- Extract capabilities
- Extract context window
- Normalize metadata

The list page is NOT trusted for model id.
"""


from __future__ import annotations

import re
import logging
from typing import Optional, Dict

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 15


class DetailParser:
    """
    Parser for freellm.net model detail pages
    """


    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ):

        self.timeout = timeout

        self.session = session or requests.Session()

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


    # -------------------------------------------------
    # public
    # -------------------------------------------------

    def parse(
        self,
        url: str,
    ) -> Dict:

        """
        Parse detail page.

        Returns:

        {
            model_id,
            api_base,
            context,
            capability,
            modality
        }

        """


        html = self._fetch(url)

        if not html:
            return {}


        soup = BeautifulSoup(
            html,
            "html.parser",
        )


        result = {}


        result.update(
            self._parse_api_details(
                soup
            )
        )


        result.update(
            self._parse_technical_details(
                soup
            )
        )


        result.update(
            self._parse_best_for(
                soup
            )
        )


        return result



    # -------------------------------------------------
    # fetch
    # -------------------------------------------------

    def _fetch(
        self,
        url: str,
    ) -> Optional[str]:

        try:

            resp = self.session.get(
                url,
                timeout=self.timeout,
            )


            resp.raise_for_status()


            return resp.text


        except Exception as e:

            logger.warning(
                "detail fetch failed %s : %s",
                url,
                e,
            )

            return None



    # -------------------------------------------------
    # API Details
    # -------------------------------------------------

    def _parse_api_details(
        self,
        soup: BeautifulSoup,
    ) -> Dict:


        data = {}


        section = soup.find(
            "section",
            class_="api-details",
        )


        if not section:
            return data



        text = section.get_text(
            "\n",
            strip=True,
        )


        # -----------------------
        # Base URL
        # -----------------------

        base_url = self._find_code_after_label(
            section,
            "Base URL",
        )


        if base_url:
            data["api_base"] = base_url



        # -----------------------
        # Model ID
        # -----------------------

        model_id = self._find_code_after_label(
            section,
            "Model ID",
        )


        if model_id:

            data["model_id"] = (
                model_id.strip()
            )



        return data




    def _find_code_after_label(
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
                x and label in x
        )


        if not span:
            return None



        parent = span.parent


        code = parent.find(
            "code"
        )


        if code:

            return code.get_text(
                strip=True
            )



        return None




    # -------------------------------------------------
    # Technical Details
    # -------------------------------------------------

    def _parse_technical_details(
        self,
        soup: BeautifulSoup,
    ) -> Dict:


        data = {}


        section = soup.find(
            "section",
            class_="technical-details-card",
        )


        if not section:
            return data



        grid = section.find(
            class_="technical-details-grid"
        )


        if not grid:
            return data



        items = {}


        for div in grid.find_all(
            recursive=False
        ):


            span = div.find(
                "span"
            )


            strong = div.find(
                "strong"
            )


            if span and strong:

                key = span.get_text(
                    strip=True
                )


                value = strong.get_text(
                    strip=True
                )


                items[key] = value



        # context

        if "Context window" in items:

            data["context"] = (
                items["Context window"]
            )



        # input

        if "Input" in items:

            data["input"] = (
                items["Input"]
            )



        # output

        if "Output" in items:

            data["output"] = (
                items["Output"]
            )



        # capabilities

        if "Capabilities" in items:

            caps = items["Capabilities"]

            data["capability"] = [
                x.strip()
                for x in caps.split(",")
                if x.strip()
            ]



        # modality

        if "Input" in items:

            data["modality"] = [
                x.strip()
                for x in items["Input"].split(",")
                if x.strip()
            ]



        return data




    # -------------------------------------------------
    # Best for
    # -------------------------------------------------

    def _parse_best_for(
        self,
        soup: BeautifulSoup,
    ) -> Dict:


        data = {}


        section = soup.find(
            class_="best-for-card"
        )


        if not section:
            return data



        values = []


        for li in section.find_all(
            "li"
        ):

            txt = li.get_text(
                strip=True
            )


            if txt:

                values.append(
                    txt.lower()
                )



        if values:

            data["best_for"] = values



        return data



# -----------------------------------------------------
# compatibility helper
# -----------------------------------------------------

def parse_model_detail(
    url: str,
) -> Dict:

    """
    Backward compatible helper
    """

    parser = DetailParser()

    return parser.parse(
        url
    )
