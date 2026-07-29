from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from models import FreeLLMModel
from parser import parse_model_detail
from providers import SUPPORTED_PROVIDERS


BASE_URL = "https://freellm.net"

MODEL_LIST_URL = (
    "https://freellm.net/models/?free=1"
)


USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "Chrome/138 Safari/537.36"
)



class FreeLLMCrawler:


    def __init__(
        self,
        timeout: int = 30,
        top_k: int = 200,
    ):

        self.timeout = timeout

        self.top_k = top_k

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
            }
        )



    # ==============================
    # HTTP
    # ==============================


    def _get(
        self,
        url: str,
    ) -> Optional[str]:

        try:

            response = self.session.get(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.text


        except Exception as e:

            logging.warning(
                "GET failed %s : %s",
                url,
                e,
            )

            return None



    # ==============================
    # 首页解析
    # ==============================


    def fetch_model_list(
        self,
    ) -> List[FreeLLMModel]:


        html = self._get(
            MODEL_LIST_URL
        )


        if not html:

            return []



        #
        # 第一优先：
        # Next.js JSON
        #
        models = self._parse_next_data(
            html
        )


        if models:

            return models[:self.top_k]



        #
        # 第二：
        # HTML table
        #
        models = self._parse_table(
            html
        )


        if models:

            return models[:self.top_k]



        #
        # 第三：
        # link fallback
        #
        return self._parse_links(
            html
        )[:self.top_k]



    # ==============================
    # Next DATA
    # ==============================


    def _parse_next_data(
        self,
        html: str,
    ) -> List[FreeLLMModel]:


        result = []


        soup = BeautifulSoup(
            html,
            "html.parser",
        )


        script = soup.find(
            "script",
            id="__NEXT_DATA__",
        )


        if not script:

            return []



        try:

            data = json.loads(
                script.text
            )


        except Exception:

            return []



        #
        # 递归寻找 models 数组
        #
        arrays = []


        def walk(obj):

            if isinstance(
                obj,
                dict,
            ):

                for value in obj.values():

                    walk(value)


            elif isinstance(
                obj,
                list,
            ):

                if obj and isinstance(
                    obj[0],
                    dict,
                ):

                    arrays.append(obj)


                for item in obj:

                    walk(item)



        walk(data)



        for array in arrays:

            for item in array:

                model = self._build_model(
                    item
                )

                if model:

                    result.append(
                        model
                    )


        return self._deduplicate(
            result
        )



    # ==============================
    # Table
    # ==============================


    def _parse_table(
        self,
        html: str,
    ) -> List[FreeLLMModel]:


        soup = BeautifulSoup(
            html,
            "html.parser",
        )


        result = []


        for row in soup.select(
            "table tbody tr"
        ):


            cells = [
                c.get_text(
                    " ",
                    strip=True,
                )
                for c in row.find_all(
                    "td"
                )
            ]


            if len(cells) < 2:

                continue



            provider = cells[0]

            model_name = cells[1]


            if provider not in SUPPORTED_PROVIDERS:

                continue



            href = ""

            link = row.find(
                "a"
            )

            if link:

                href = link.get(
                    "href",
                    "",
                )


            if href.startswith("/"):

                href = (
                    BASE_URL
                    +
                    href
                )


            result.append(
                FreeLLMModel(
                    provider=provider,
                    name=model_name,
                    detail_url=href,
                )
            )


        return self._deduplicate(
            result
        )



    # ==============================
    # fallback
    # ==============================


    def _parse_links(
        self,
        html: str,
    ) -> List[FreeLLMModel]:


        soup = BeautifulSoup(
            html,
            "html.parser",
        )


        result = []


        for link in soup.find_all(
            "a",
            href=True,
        ):


            href = link["href"]


            if (
                "/model"
                not in href
            ):

                continue



            text = link.get_text(
                " ",
                strip=True,
            )


            if not text:

                continue



            result.append(
                FreeLLMModel(
                    provider="",
                    name=text,
                    detail_url=(
                        BASE_URL + href
                        if href.startswith("/")
                        else href
                    ),
                )
            )


        return self._deduplicate(
            result
        )



    # ==============================
    # JSON Model
    # ==============================


    def _build_model(
        self,
        item: Dict[str, Any],
    ) -> Optional[FreeLLMModel]:


        provider = (
            item.get("provider")
            or item.get("provider_name")
            or ""
        )


        name = (
            item.get("model")
            or item.get("name")
            or ""
        )


        url = (
            item.get("url")
            or item.get("detail_url")
            or ""
        )


        if not provider or not name:

            return None



        if provider not in SUPPORTED_PROVIDERS:

            return None



        if url.startswith("/"):

            url = (
                BASE_URL
                +
                url
            )


        return FreeLLMModel(
            provider=provider,
            name=name,
            detail_url=url,
        )



    # ==============================
    # Detail
    # ==============================


    def fetch_detail(
        self,
        model: FreeLLMModel,
    ):


        if not model.detail_url:

            return None



        html = self._get(
            model.detail_url
        )


        if not html:

            return None



        try:

            data = parse_model_detail(
                html
            )


        except Exception:

            logging.exception(
                "parse detail failed"
            )

            data = {}



        data["provider"] = (
            model.provider
        )


        if not data.get(
            "logical_name"
        ):

            data["logical_name"] = (
                model.name
            )


        return data



    # ==============================
    # Crawl
    # ==============================


    def crawl(self):


        models = (
            self.fetch_model_list()
        )


        results = []

        visited = set()



        for index, model in enumerate(
            models,
            start=1,
        ):


            logging.info(
                "[%d/%d] %s %s",
                index,
                len(models),
                model.provider,
                model.name,
            )


            try:

                detail = (
                    self.fetch_detail(
                        model
                    )
                )


                if not detail:

                    continue



                key = (
                    detail.get(
                        "provider"
                    ),
                    detail.get(
                        "logical_name"
                    ),
                    detail.get(
                        "model_id"
                    ),
                )


                if key in visited:

                    continue


                visited.add(key)


                results.append(
                    detail
                )


            except Exception:

                logging.exception(
                    "model failed"
                )


            #
            # 防止频率过高
            #
            time.sleep(
                random.uniform(
                    0.3,
                    0.8,
                )
            )



        logging.info(
            "Parsed %d deployments",
            len(results),
        )


        return results



    def _deduplicate(
        self,
        items,
    ):

        result = []

        seen = set()


        for item in items:

            key = (
                item.provider,
                item.name,
                item.detail_url,
            )


            if key in seen:

                continue


            seen.add(key)

            result.append(
                item
            )


        return result




def crawl_models(
    top_k: int = 200,
):

    return FreeLLMCrawler(
        top_k=top_k
    ).crawl()



def fetch_models(
    top_k: int = 200,
):

    return crawl_models(
        top_k
    )



def fetch_all_models(
    top_k: int = 200,
):

    return crawl_models(
        top_k
    )
