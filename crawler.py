"""
crawler.py

FreeLLM模型列表爬虫


职责:

1. 请求 freellm 模型列表页面

2. 解码 HTML entity

3. 提取页面中的模型 JSON

4. 输出原始模型 dict


输出:

List[dict]


后续:

parser.py
    |
normalizer.py
    |
List[ModelInfo]


禁止:

ProviderModel
LogicalModel
"""


from __future__ import annotations


import html

import json

import logging

import re


from typing import Any, Dict, List



import requests



logger = logging.getLogger(__name__)





# ============================================================
# Config
# ============================================================


DEFAULT_URL = (

    "https://freellm.net/models/?free=1"

)



HEADERS = {


    "User-Agent":

        "Mozilla/5.0 "

        "(Windows NT 10.0; Win64; x64)"

}



TIMEOUT = 30





# ============================================================
# HTTP
# ============================================================


def fetch_page(
    url: str = DEFAULT_URL
) -> str:
    """
    获取网页
    """

    try:


        response = requests.get(

            url,

            headers=HEADERS,

            timeout=TIMEOUT

        )


        response.raise_for_status()



        return response.text



    except Exception as e:


        logger.error(

            "fetch freellm failed: %s",

            e

        )


        return ""





# ============================================================
# Decode
# ============================================================


def decode_html(
    content: str
) -> str:
    """
    HTML entity解码


    示例:

    &#34;models&#34;

        |

        v

    "models"

    """

    return html.unescape(
        content
    )





# ============================================================
# Extract JSON
# ============================================================


def extract_json_objects(
    source: str
) -> List[Any]:
    """
    提取页面script中的JSON

    """

    result = []



    scripts = re.findall(

        r"<script[^>]*>(.*?)</script>",

        source,

        re.S

    )



    for script in scripts:


        text = script.strip()



        if not text:

            continue



        # 尝试完整JSON

        if (

            text.startswith("{")

            or

            text.startswith("[")

        ):


            try:


                result.append(

                    json.loads(

                        text

                    )

                )


            except Exception:


                pass



        # 查找包含models片段

        for match in re.finditer(

            r'\{.*?"models"\s*:\s*\[.*?\].*?\}',

            text,

            re.S

        ):


            try:


                result.append(

                    json.loads(

                        match.group()

                    )

                )


            except Exception:


                pass



    return result





# ============================================================
# Find models
# ============================================================


def find_models(
    data: Any
) -> List[Dict]:


    result = []



    if isinstance(

        data,

        dict

    ):



        for key, value in data.items():



            if key.lower() == "models":



                if isinstance(

                    value,

                    list

                ):


                    result.extend(

                        [

                            x

                            for x in value

                            if isinstance(

                                x,

                                dict

                            )

                        ]

                    )




            else:


                result.extend(

                    find_models(

                        value

                    )

                )




    elif isinstance(

        data,

        list

    ):


        for item in data:


            result.extend(

                find_models(

                    item

                )

            )



    return result





# ============================================================
# Model normalize
# ============================================================


def normalize_raw_model(
    item: Dict
) -> Dict:


    model_id = (

        item.get(

            "id"

        )

        or

        item.get(

            "model"

        )

        or

        ""

    )



    name = (

        item.get(

            "name"

        )

        or

        model_id

    )



    provider = ""



    if "/" in model_id:


        provider = (

            model_id

            .split("/")[0]

        )



    return {


        "name":

            name,



        "model_id":

            model_id,



        "provider":

            provider,



        "metadata":

            item,

    }





# ============================================================
# Public API
# ============================================================


def crawl_models(
    top_k: int = 200
) -> List[Dict]:
    """
    主入口


    返回:

    List[dict]

    """



    logger.info(

        "crawl models from %s",

        DEFAULT_URL

    )



    page = fetch_page()



    if not page:


        return []



    decoded = decode_html(

        page

    )



    json_objects = extract_json_objects(

        decoded

    )



    models = []



    for obj in json_objects:


        models.extend(

            find_models(

                obj

            )

        )



    if not models:


        logger.warning(

            "no json models found"

        )


        return []



    result = []



    seen = set()



    for item in models:


        model = normalize_raw_model(

            item

        )



        model_id = model.get(

            "model_id"

        )



        if not model_id:


            continue



        if model_id in seen:


            continue



        seen.add(

            model_id

        )



        result.append(

            model

        )



        if len(result) >= top_k:


            break



    logger.info(

        "crawler result: %s",

        len(result)

    )



    return result