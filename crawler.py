"""
crawler.py

FreeLLM模型爬虫


职责:

获取模型列表数据


流程:

crawler
    |
    v
parser.py
    |
    v
List[dict]
    |
    v
normalizer.py
    |
    v
List[ModelInfo]


禁止:

ProviderModel
primary_model
providers
"""


from __future__ import annotations


import logging

import requests


from typing import Any, Dict, List, Optional



logger = logging.getLogger(__name__)




# ============================================================
# Config
# ============================================================


DEFAULT_URL = (

    "https://freellm.net/models/?free=1"

)



DEFAULT_TIMEOUT = 20



HEADERS = {


    "User-Agent":

        "Mozilla/5.0 "

        "(Windows NT 10.0; Win64; x64)"

}




# ============================================================
# Request
# ============================================================


def fetch_page(
    url: str = DEFAULT_URL
) -> str:
    """
    获取网页内容
    """



    try:


        response = requests.get(

            url,

            headers=HEADERS,

            timeout=DEFAULT_TIMEOUT

        )


        response.raise_for_status()



        return response.text



    except Exception as e:


        logger.error(

            "fetch page failed: %s",

            e

        )


        return ""





# ============================================================
# JSON extraction
# ============================================================


def extract_models_from_json(
    data: Any
) -> List[Dict]:


    """
    从网页JSON中寻找模型列表


    支持:

    models

    data

    items

    results

    """



    if not data:

        return []



    if isinstance(

        data,

        list

    ):


        if all(

            isinstance(

                x,

                dict

            )

            for x in data

        ):

            return data




    if isinstance(

        data,

        dict

    ):


        for key in [

            "models",

            "items",

            "data",

            "results",

        ]:


            value = data.get(

                key

            )



            if isinstance(

                value,

                list

            ):


                return value




        for value in data.values():


            result = extract_models_from_json(

                value

            )



            if result:

                return result



    return []





# ============================================================
# HTML parser
# ============================================================


def parse_html_models(
    html: str
) -> List[Dict]:


    """
    解析HTML


    当前FreeLLM使用Next.js


    __NEXT_DATA__

    """



    if not html:

        return []



    import json



    from bs4 import BeautifulSoup



    try:


        soup = BeautifulSoup(

            html,

            "html.parser"

        )



        node = soup.find(

            "script",

            id="__NEXT_DATA__"

        )



        if not node:

            return []



        data = json.loads(

            node.string

        )



        return extract_models_from_json(

            data

        )



    except Exception:


        logger.exception(

            "parse html models failed"

        )



        return []





# ============================================================
# Public API
# ============================================================


def crawl_models(
    top_k: int = 200,
    url: Optional[str] = None
) -> List[Dict]:
    """
    主入口


    返回:

    List[dict]


    """



    target_url = (

        url

        or

        DEFAULT_URL

    )



    logger.info(

        "crawl models from %s",

        target_url

    )



    html = fetch_page(

        target_url

    )



    if not html:


        return []



    models = parse_html_models(

        html

    )



    if not models:


        logger.warning(

            "no models extracted"

        )


        return []




    # 排序和截取

    result = models[:top_k]



    logger.info(

        "crawler found %s models",

        len(result)

    )



    return result