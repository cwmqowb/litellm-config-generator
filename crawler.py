"""
freellm crawler

Flow:

freellm models page

        |
        v

FreeLLMModel

        |
        v

detail page

        |
        v

parser.py

        |
        v

ProviderModel
"""


from __future__ import annotations


import json
import logging
import re
import time

from typing import List, Optional


import requests
from bs4 import BeautifulSoup


from models import (
    FreeLLMModel,
    ProviderModel,
    ModelCapability,
)


from parser import (
    parse_model_detail,
)



logger = logging.getLogger(__name__)



BASE_URL = (
    "https://freellm.net"
)



SUPPORTED_PROVIDERS = {


    "NVIDIA NIM",

    "OpenRouter",

    "GitHub Models",

    "ModelScope",

    "SambaNova",

    "Agnes AI",

    "Kilo Code",

}



PROVIDER_MAPPING = {


    "nvidia-nim":
        "NVIDIA NIM",


    "openrouter":
        "OpenRouter",


    "github-models":
        "GitHub Models",


    "modelscope":
        "ModelScope",


    "sambanova":
        "SambaNova",


    "agnes-ai":
        "Agnes AI",


    "kilo-code":
        "Kilo Code",

}





class FreeLLMCrawler:


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





    # =====================================================
    # HTTP
    # =====================================================


    def fetch(
        self,
        url: str,
    ) -> str:


        try:


            response = (
                self.session.get(
                    url,
                    timeout=self.timeout,
                )
            )


            response.raise_for_status()


            return response.text



        except Exception as e:


            logger.warning(
                "fetch failed %s %s",
                url,
                e,
            )


            return ""





    # =====================================================
    # models.html
    # =====================================================


    def fetch_models(
        self,
        top: int = 200,
    ) -> List[FreeLLMModel]:


        url = (

            f"{BASE_URL}/models/?free=1"

        )


        html = self.fetch(
            url
        )


        if not html:

            return []



        models = (

            self.parse_model_list(
                html
            )

        )


        return models[:top]





    def parse_model_list(
        self,
        html: str,
    ) -> List[FreeLLMModel]:


        result = []

        seen = set()



        #
        # 1. Next.js data
        #

        next_data = (

            self.extract_next_data(
                html
            )

        )


        items = (

            self.find_model_items(
                next_data
            )

        )



        for item in items:


            if not isinstance(
                item,
                dict
            ):

                continue



            url = (

                item.get("url")

                or item.get("href")

                or item.get("detail_url")

                or item.get("link")

            )


            if not url:

                continue



            if "/models/" not in url:

                continue



            model = (

                self.build_free_model(
                    item.get(
                        "provider",
                        ""
                    ),
                    item.get(
                        "name",
                        ""
                    ),
                    url,
                )

            )


            if model and model.detail_url not in seen:


                seen.add(
                    model.detail_url
                )

                result.append(
                    model
                )





        #
        # 2. href fallback
        #

        if not result:


            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            for a in soup.find_all(
                "a",
                href=True,
            ):


                href = a["href"]


                if (
                    "/models/"
                    not in href
                ):

                    continue



                if href in seen:

                    continue



                parts = (

                    href.strip("/")
                    .split("/")
                )


                if len(parts) < 3:

                    continue



                provider = (

                    self.normalize_provider(
                        parts[1]
                    )

                )


                name = (

                    a.get_text(
                        " ",
                        strip=True
                    )

                    or parts[2]

                )



                model = (

                    self.build_free_model(
                        provider,
                        name,
                        href,
                    )

                )


                if model:


                    seen.add(
                        href
                    )


                    result.append(
                        model
                    )



        logger.info(
            "parsed %s models",
            len(result),
        )


        return result





    # =====================================================
    # detail page
    # =====================================================


    def fetch_provider_model(
        self,
        model: FreeLLMModel,
    ) -> Optional[ProviderModel]:


        url = model.detail_url


        if not url.startswith(
            "http"
        ):

            url = (
                BASE_URL
                +
                url
            )



        html = self.fetch(
            url
        )


        if not html:

            return None



        detail = (

            parse_model_detail(
                html
            )

        )



        capability = (

            self.build_capability(
                detail.get(
                    "capabilities",
                    []
                )
            )

        )



        provider_model = ProviderModel(


            provider=model.provider,


            logical_name=(

                detail.get(
                    "logical_name"
                )

                or

                model.name

            ),


            model_id=(

                detail.get(
                    "model_id"
                )

                or

                model.name

            ),


            api_base=(

                detail.get(
                    "base_url",
                    ""
                )

            ),


            api_format=(

                detail.get(
                    "api_format",
                    ""
                )

            ),


            context_window=(

                detail.get(
                    "context_window"
                )

            ),


            max_output_tokens=(

                detail.get(
                    "max_output_tokens"
                )

            ),


            capability=capability,


            raw_tags=(

                detail.get(
                    "tags",
                    []
                )

            ),


        )



        return provider_model





    # =====================================================
    # NEXT DATA
    # =====================================================


    def extract_next_data(
        self,
        html: str,
    ):


        try:


            soup = BeautifulSoup(
                html,
                "html.parser"
            )


            node = soup.find(
                "script",
                id="__NEXT_DATA__",
            )


            if not node:

                return {}



            return json.loads(
                node.string
            )


        except Exception:


            return {}





    def find_model_items(
        self,
        data,
    ):


        result = []


        if isinstance(
            data,
            dict
        ):


            for key, value in data.items():


                if key.lower() in (

                    "models",
                    "items",
                    "results",

                ):


                    if isinstance(
                        value,
                        list,
                    ):

                        result.extend(
                            value
                        )


                result.extend(

                    self.find_model_items(
                        value
                    )

                )



        elif isinstance(
            data,
            list,
        ):


            for item in data:


                result.extend(

                    self.find_model_items(
                        item
                    )

                )


        return result





    # =====================================================
    # helpers
    # =====================================================


    def build_free_model(
        self,
        provider,
        name,
        url,
    ):


        provider = (

            self.normalize_provider(
                provider
            )

        )


        if not provider:

            return None



        if provider not in SUPPORTED_PROVIDERS:

            return None



        return FreeLLMModel(

            provider=provider,

            name=name.strip(),

            detail_url=url,

        )





    def normalize_provider(
        self,
        value: str,
    ):


        if not value:

            return ""



        value = (

            value.lower()
            .strip()
        )



        if value in PROVIDER_MAPPING:

            return PROVIDER_MAPPING[value]



        return (

            value
            .replace(
                "-",
                " ",
            )
            .title()

        )





    def build_capability(
        self,
        values,
    ):


        cap = ModelCapability()



        for item in values:


            name = str(
                item
            ).lower()



            if hasattr(
                cap,
                name,
            ):


                setattr(
                    cap,
                    name,
                    True,
                )



        return cap
