from __future__ import annotations

import logging
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import FreeLLMModel
from parser import parse_model_detail
from providers import SUPPORTED_PROVIDERS

BASE_URL = "https://freellm.net"
MODEL_LIST_URL = "https://freellm.net/models/?free=1"

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
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

    # -------------------------------------
    # HTTP
    # -------------------------------------

    def _get(
        self,
        url: str,
    ) -> Optional[str]:

        try:

            r = self.session.get(
                url,
                timeout=self.timeout,
            )

            r.raise_for_status()

            return r.text

        except Exception as e:

            logging.warning(
                "GET failed %s : %s",
                url,
                e,
            )

            return None

    # -------------------------------------
    # 首页
    # -------------------------------------

    def fetch_model_list(
        self,
    ) -> List[FreeLLMModel]:

        html = self._get(MODEL_LIST_URL)

        if html is None:
            return []

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        results: List[FreeLLMModel] = []

        #
        # freellm 页面结构可能调整，因此采用多个 selector
        #

        cards = []

        cards.extend(
            soup.select("a[href*='/model/']")
        )

        cards.extend(
            soup.select("a[href*='/models/']")
        )

        visited = set()

        for card in cards:

            href = card.get("href")

            if not href:
                continue

            if href in visited:
                continue

            visited.add(href)

            provider = self._guess_provider(card)

            if provider not in SUPPORTED_PROVIDERS:
                continue

            name = self._guess_name(card)

            if not name:
                continue

            if href.startswith("/"):

                href = BASE_URL + href

            results.append(
                FreeLLMModel(
                    provider=provider,
                    name=name,
                    detail_url=href,
                )
            )

            if len(results) >= self.top_k:
                break

        logging.info(
            "Fetched %d models",
            len(results),
        )

        return results

    # -------------------------------------
    # Provider
    # -------------------------------------

    def _guess_provider(
        self,
        card,
    ) -> str:

        text = card.get_text(
            " ",
            strip=True,
        )

        for provider in SUPPORTED_PROVIDERS:

            if provider.lower() in text.lower():
                return provider

        #
        # 再尝试父节点
        #

        p = card.parent

        if p:

            text = p.get_text(
                " ",
                strip=True,
            )

            for provider in SUPPORTED_PROVIDERS:

                if provider.lower() in text.lower():
                    return provider

        return ""

    # -------------------------------------
    # Name
    # -------------------------------------

    def _guess_name(
        self,
        card,
    ) -> str:

        text = card.get_text(
            " ",
            strip=True,
        )

        text = " ".join(text.split())

        if not text:
            return ""

        #
        # provider 名称去掉
        #

        for provider in SUPPORTED_PROVIDERS:

            text = text.replace(
                provider,
                "",
            )

        return text.strip()

    # -------------------------------------
    # 详情页
    # -------------------------------------

    def fetch_detail(
        self,
        model: FreeLLMModel,
    ):

        html = self._get(
            model.detail_url,
        )

        if html is None:
            return None

        try:

            data = parse_model_detail(
                html,
            )

        except Exception as e:

            logging.exception(e)

            return None

        #
        # Provider 信息来自列表
        #

        data["provider"] = model.provider

        #
        # 名称优先采用详情页
        #

        if not data.get("logical_name"):

            data["logical_name"] = model.name

        return data

    # -------------------------------------
    # Crawl
    # -------------------------------------

    def crawl(self):
        """
        抓取 freellm Top 模型，并解析详情页。

        返回:
            List[dict]
        """

        model_list = self.fetch_model_list()

        results = []

        #
        # 用于避免同一 Provider + Model ID 重复
        #
        visited = set()

        total = len(model_list)

        for index, model in enumerate(model_list, start=1):

            logging.info(
                "[%d/%d] %s | %s",
                index,
                total,
                model.provider,
                model.name,
            )

            try:

                detail = self.fetch_detail(model)

                if detail is None:
                    continue

                #
                # Provider
                #
                provider = detail.get("provider", "")

                #
                # logical model
                #
                logical_name = detail.get(
                    "logical_name",
                    model.name,
                )

                #
                # model id
                #
                model_id = detail.get(
                    "model_id",
                    "",
                )

                #
                # 去重
                #
                dedup_key = (
                    provider,
                    logical_name,
                    model_id,
                )

                if dedup_key in visited:
                    continue

                visited.add(dedup_key)

                results.append(detail)

            except Exception:

                logging.exception(
                    "parse model failed: %s",
                    model.detail_url,
                )

            #
            # 避免请求过快
            #
            time.sleep(0.2)

        #
        # Provider 优先级排序
        #
        try:

            from providers import provider_priority

            results.sort(
                key=lambda x: (
                    x.get("logical_name", ""),
                    provider_priority(
                        x.get("provider", "")
                    ),
                )
            )

        except Exception:
            pass

        logging.info(
            "Parsed %d deployments",
            len(results),
        )

        return results


#
# 对外兼容旧接口
#

def crawl_models(
    top_k: int = 200,
):
    """
    兼容旧 builder.py 调用方式
    """

    crawler = FreeLLMCrawler(
        top_k=top_k,
    )

    return crawler.crawl()


def fetch_models(
    top_k: int = 200,
):
    """
    兼容部分旧版本 main.py
    """

    return crawl_models(
        top_k=top_k,
    )


def fetch_all_models(
    top_k: int = 200,
):
    """
    保留历史接口，避免修改其它文件。
    """

    return crawl_models(
        top_k=top_k,
    )


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )

    items = crawl_models()

    print()

    print("=" * 80)

    print(
        "Total deployments:",
        len(items),
    )

    print("=" * 80)

    for item in items[:10]:

        print()

        print(
            item.get("logical_name"),
        )

        print(
            " Provider:",
            item.get("provider"),
        )

        print(
            " Model:",
            item.get("model_id"),
        )

        print(
            " Context:",
            item.get("context_window"),
        )

        print(
            " Output:",
            item.get("max_output_tokens"),
        )

        print(
            " Base:",
            item.get("base_url"),
        )

        print(
            " Capability:",
            item.get("capability").enabled()
            if item.get("capability")
            else [],
        )
