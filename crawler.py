"""
freellm crawler

Fetch model list and model detail pages.

Flow:

models/?free=1

    ↓

model detail urls

    ↓

parse_model_detail()

    ↓

ModelDetail

"""

import logging
import re
import time
from typing import List

import requests

from parser import parse_model_detail
from models import ModelDetail


logger = logging.getLogger(__name__)


BASE_URL = "https://freellm.net"


SUPPORTED_PROVIDERS = {
    "NVIDIA NIM",
    "OpenRouter",
    "GitHub Models",
    "ModelScope",
    "SambaNova",
    "Agnes AI",
    "Kilo Code",
}


BAD_NAME_KEYWORDS = [
    "free",
    "api key",
    "rate limits",
    "models",
    "model count",
]



class FreeLLMCrawler:
    """
    freellm crawler
    """


    def __init__(
        self,
        timeout: int = 20,
    ):

        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                (
                    "Mozilla/5.0 "
                    "Chrome/120 Safari/537"
                )
            }
        )



    # -------------------------------------------------
    # http
    # -------------------------------------------------

    def fetch(
        self,
        url: str
    ) -> str:

        try:

            response = self.session.get(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.text


        except Exception:

            logger.exception(
                "fetch failed %s",
                url
            )

            return ""



    # -------------------------------------------------
    # list page
    # -------------------------------------------------

    def fetch_model_list(
        self,
        top: int = 200,
    ) -> List[ModelDetail]:


        url = (
            f"{BASE_URL}/models/?free=1"
        )


        html = self.fetch(url)


        if not html:

            return []


        models = []


        candidates = (
            self._parse_links(html)
        )


        logger.info(
            "Found %s model links",
            len(candidates)
        )


        for index, item in enumerate(
            candidates[:top],
            start=1,
        ):

            try:

                logger.info(
                    "[%s/%s] %s %s",
                    index,
                    top,
                    item.get("provider"),
                    item.get("name"),
                )


                detail = (
                    self.fetch_detail(
                        item
                    )
                )


                if detail:

                    models.append(
                        detail
                    )


                # avoid aggressive crawling

                time.sleep(
                    0.3
                )


            except Exception:

                logger.exception(
                    "parse model failed"
                )

                continue



        return models



    # -------------------------------------------------
    # detail
    # -------------------------------------------------

    def fetch_detail(
        self,
        item: dict,
    ):

        url = item.get(
            "url"
        )


        if not url:

            return None


        if not url.startswith(
            "http"
        ):

            url = (
                BASE_URL
                +
                url
            )


        html = self.fetch(url)


        if not html:

            return None



        parsed = (
            parse_model_detail(
                html
            )
        )


        provider = (
            item.get(
                "provider",
                ""
            )
        )


        result = ModelDetail(

            provider=provider,

            logical_name=
                parsed.get(
                    "logical_name",
                    "",
                ),

            model_id=
                parsed.get(
                    "model_id",
                    "",
                ),

            base_url=
                parsed.get(
                    "base_url",
                    "",
                ),

            api_format=
                parsed.get(
                    "api_format",
                    "",
                ),

            context_window=
                parsed.get(
                    "context_window"
                ),

            max_output_tokens=
                parsed.get(
                    "max_output_tokens"
                ),

            capabilities=
                parsed.get(
                    "capabilities",
                    [],
                ),

            tags=
                parsed.get(
                    "tags",
                    [],
                ),

        )


        # -----------------------------
        # validate
        # -----------------------------

        if not self.validate_model(
            result
        ):

            logger.warning(
                "drop invalid model %s",
                url
            )

            return None



        # fallback logical name

        if not result.logical_name:

            result.logical_name = (
                self.slug_to_name(
                    url
                )
            )


        return result



    # -------------------------------------------------
    # validate
    # -------------------------------------------------

    def validate_model(
        self,
        model: ModelDetail,
    ) -> bool:


        if not model.provider:

            return False


        if (
            model.provider
            not in SUPPORTED_PROVIDERS
        ):

            return False



        name = (
            model.logical_name
            or ""
        ).lower()


        for keyword in BAD_NAME_KEYWORDS:

            if keyword in name:

                return False



        return True



    # -------------------------------------------------
    # slug fallback
    # -------------------------------------------------

    def slug_to_name(
        self,
        url: str
    ) -> str:

        """
        /models/nvidia-nim/z-ai-glm-5-2

        ↓

        glm-5.2

        """


        try:

            slug = (
                url.rstrip("/")
                .split("/")
                [-1]
            )


            name = slug.replace(
                "-",
                ".",
            )


            # remove provider prefix

            parts = name.split(".")


            if len(parts) > 3:

                name = ".".join(
                    parts[-3:]
                )


            return name


        except Exception:

            return ""



    # -------------------------------------------------
    # extract links
    # -------------------------------------------------

    def _parse_links(
        self,
        html: str
    ) -> List[dict]:


        result = []


        # current implementation keeps
        # compatibility with old crawler

        pattern = (
            r'href="'
            r'(/models/[^"]+)"'
        )


        links = re.findall(
            pattern,
            html
        )


        seen = set()


        for link in links:


            if link in seen:

                continue


            seen.add(link)



            parts = (
                link.strip("/")
                .split("/")
            )


            if len(parts) < 3:

                continue



            provider_slug = parts[1]

            model_slug = parts[2]



            provider = (
                provider_slug
                .replace(
                    "-",
                    " "
                )
                .title()
            )


            result.append(
                {
                    "url": link,

                    "provider":
                        provider,

                    "name":
                        model_slug,
                }
            )



        return result
