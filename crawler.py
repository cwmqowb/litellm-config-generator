"""
抓取 https://freellm.net/models/?free=1
获取前 200 个免费模型
提取 Provider
提取模型名
提取详情页 URL
返回 List[FreeLLMModel]
"""

from __future__ import annotations

from typing import List
from urllib.parse import urljoin
import json

import requests
from bs4 import BeautifulSoup

from models import FreeLLMModel


BASE_URL = "https://freellm.net"

MODEL_LIST_URL = (
    "https://freellm.net/models/?free=1"
)


class FreeLLMCrawler:
    """
    抓取 freellm 免费模型列表
    """

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )


    def fetch_top_models(
        self,
        limit: int = 200,
    ) -> List[FreeLLMModel]:

        resp = self.session.get(
            MODEL_LIST_URL,
            timeout=30,
        )

        resp.raise_for_status()


        soup = BeautifulSoup(
            resp.text,
            "lxml",
        )


        models: List[FreeLLMModel] = []

        seen = set()


        #
        # freellm 页面通过 JSON-LD
        # 提供完整模型列表
        #

        for script in soup.find_all(
            "script",
            {
                "type": "application/ld+json"
            }
        ):

            try:
                data = json.loads(
                    script.string
                )

            except Exception:
                continue


            if data.get("@type") != "ItemList":
                continue


            items = data.get(
                "itemListElement",
                []
            )


            for item in items:

                model_info = item.get(
                    "item",
                    {}
                )


                model_name = model_info.get(
                    "name"
                )


                detail_url = model_info.get(
                    "url"
                )


                provider_info = model_info.get(
                    "provider",
                    {}
                )


                provider = provider_info.get(
                    "name"
                )


                if not model_name or not detail_url or not provider:
                    continue


                #
                # Provider 白名单过滤
                #
                #
                # if not self._is_supported_provider(
                #     provider
                # ):
                #     continue


                detail_url = urljoin(
                    BASE_URL,
                    detail_url,
                )


                if detail_url in seen:
                    continue


                models.append(
                    FreeLLMModel(
                        provider=provider,
                        name=model_name,
                        detail_url=detail_url,
                    )
                )


                seen.add(detail_url)


                if len(models) >= limit:
                    return models


        return models



    # @staticmethod
    # def _is_supported_provider(
    #     provider: str,
    # ) -> bool:
    #     """
    #     Provider 白名单过滤
    #     """
    #
    #     supported_providers = {
    #
    #         "NVIDIA NIM",
    #
    #         "OpenRouter",
    #
    #         "GitHub Models",
    #
    #         "ModelScope",
    #
    #         "SambaNova",
    #
    #         "Agnes AI",
    #
    #         "Kilo Code",
    #
    #     }
    #
    #
    #     return provider in supported_providers
