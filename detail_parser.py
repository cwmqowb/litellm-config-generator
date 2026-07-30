"""
detail_parser.py

FreeLLM模型详情页解析


输入:

HTML detail page


输出:

dict

后续由 normalizer.py 转换:

dict
 |
 v
ModelInfo


禁止:

ProviderModel
primary_model
providers
"""


from __future__ import annotations


import json

import logging

import re


from typing import Any, Dict, List



from bs4 import BeautifulSoup



logger = logging.getLogger(__name__)




# ============================================================
# utils
# ============================================================


def clean_text(
    value: Any
) -> str:


    if value is None:

        return ""


    return re.sub(

        r"\s+",

        " ",

        str(value)

    ).strip()




def remove_copy_suffix(
    value: str
) -> str:


    if not value:

        return value



    return re.sub(

        r"\s+Copy$",

        "",

        value,

        flags=re.I

    ).strip()




# ============================================================
# next data
# ============================================================


def extract_next_data(
    html: str
):


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

            return {}



        if not node.string:

            return {}



        return json.loads(

            node.string

        )



    except Exception:


        return {}





# ============================================================
# recursive json search
# ============================================================


def find_json_value(
    data,
    keys: List[str]
):


    if isinstance(data, dict):


        for key, value in data.items():


            if key.lower() in [

                x.lower()

                for x in keys

            ]:

                return value



            result = find_json_value(

                value,

                keys

            )


            if result is not None:

                return result



    elif isinstance(data, list):


        for item in data:


            result = find_json_value(

                item,

                keys

            )


            if result is not None:

                return result



    return None




# ============================================================
# capability
# ============================================================


def parse_capabilities(
    text: str
) -> List[str]:


    if not text:

        return []



    text = text.lower()



    result = []



    rules = {


        "chat":

        [

            "chat",

            "instruction",

            "conversation",

        ],



        "vision":

        [

            "vision",

            "multimodal",

            "image input",

        ],



        "reasoning":

        [

            "reasoning",

            "thinking",

            "cot",

        ],



        "coding":

        [

            "coding",

            "coder",

            "code",

        ],



        "embedding":

        [

            "embedding",

        ],



        "rerank":

        [

            "rerank",

        ],



        "tool_calling":

        [

            "tool",

            "function calling",

        ],



        "json_mode":

        [

            "json",

            "structured",

        ],

    }




    for name, words in rules.items():


        for word in words:


            if word in text:


                result.append(

                    name

                )

                break




    return sorted(

        list(set(result))

    )





# ============================================================
# number
# ============================================================


def normalize_number(
    value
):


    if value is None:

        return None



    try:


        value = str(value)

        value = value.upper()

        value = value.replace(

            ",",

            ""

        )



        if value.endswith("K"):


            return int(

                float(

                    value[:-1]

                )

                * 1024

            )



        if value.endswith("M"):


            return int(

                float(

                    value[:-1]

                )

                * 1024

                * 1024

            )



        return int(

            float(value)

        )



    except Exception:


        return None




# ============================================================
# main parser
# ============================================================


def parse_model_detail(
    html: str
) -> Dict[str, Any]:


    result = {


        "name":

            "",


        "model_id":

            "",


        "provider":

            "",



        "api_base":

            "",



        "api_format":

            "",



        "api_key_env":

            "",



        "capabilities":

            [],



        "context_window":

            None,



        "max_output_tokens":

            None,



        "free":

            False,



        "score":

            0,



        "metadata":

            {},


    }



    if not html:

        return result




    try:


        soup = BeautifulSoup(

            html,

            "html.parser"

        )



        page_text = clean_text(

            soup.get_text(

                " ",

                strip=True

            )

        )



        data = extract_next_data(

            html

        )



        # ----------------------------
        # model id
        # ----------------------------


        model_id = find_json_value(

            data,

            [

                "model",

                "modelId",

                "model_id",

            ]

        )



        if model_id:


            model_id = remove_copy_suffix(

                clean_text(

                    model_id

                )

            )


            result["model_id"] = model_id


            result["name"] = (

                model_id.split("/")[-1]

            )



        # ----------------------------
        # api
        # ----------------------------


        base_url = find_json_value(

            data,

            [

                "baseUrl",

                "base_url",

                "endpoint",

            ]

        )



        if base_url:


            result["api_base"] = (

                remove_copy_suffix(

                    clean_text(

                        base_url

                    )

                )

            )




        api_format = find_json_value(

            data,

            [

                "apiFormat",

                "api_format",

                "protocol",

            ]

        )



        if api_format:


            result["api_format"] = (

                clean_text(

                    api_format

                )

            )



        # ----------------------------
        # context
        # ----------------------------


        context = find_json_value(

            data,

            [

                "contextWindow",

                "context_window",

                "contextLength",

            ]

        )



        if context:


            result["context_window"] = (

                normalize_number(

                    context

                )

            )




        output = find_json_value(

            data,

            [

                "maxOutputTokens",

                "max_output_tokens",

                "maxTokens",

            ]

        )



        if output:


            result["max_output_tokens"] = (

                normalize_number(

                    output

                )

            )




        # ----------------------------
        # capability
        # ----------------------------


        result["capabilities"] = (

            parse_capabilities(

                page_text

            )

        )



        result["metadata"] = {


            "source":

                "freellm",


        }



    except Exception:


        logger.exception(

            "parse detail failed"

        )



    return result