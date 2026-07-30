"""
freellm detail parser

HTML:

detail.html

Output:

{
    logical_name,
    model_id,
    base_url,
    api_format,
    context_window,
    max_output_tokens,
    capabilities,
    tags
}

"""

from __future__ import annotations


import json
import logging
import re

from typing import Any, Dict, List


from bs4 import BeautifulSoup



logger = logging.getLogger(__name__)




# =====================================================
# text utils
# =====================================================


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
    """
    freellm copy button pollution

    Example:

    https://xxx Copy

    """

    if not value:

        return value


    value = re.sub(
        r"\s+Copy$",
        "",
        value,
        flags=re.I
    )


    return value.strip()




def normalize_number(
    value: str
):


    if not value:

        return None



    value = (

        str(value)
        .upper()
        .replace(
            ",",
            ""
        )
        .strip()

    )


    try:


        if value.endswith(
            "M"
        ):


            return int(
                float(
                    value[:-1]
                )
                *
                1024
                *
                1024
            )


        if value.endswith(
            "K"
        ):


            return int(
                float(
                    value[:-1]
                )
                *
                1024
            )


        return int(
            float(value)
        )


    except Exception:


        return None





# =====================================================
# next data
# =====================================================


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
            {
                "id":
                    "__NEXT_DATA__"
            }
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





# =====================================================
# json search
# =====================================================


def find_json_value(
    data,
    keys
):


    if isinstance(
        data,
        dict
    ):


        for key,value in data.items():


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



    elif isinstance(
        data,
        list
    ):


        for item in data:


            result = find_json_value(
                item,
                keys
            )


            if result is not None:

                return result



    return None





# =====================================================
# capability
# =====================================================


def parse_capabilities(
    text: str
) -> List[str]:


    if not text:

        return []



    text = text.lower()


    result = set()



    mapping = {


        "chat":[

            "chat",
            "instruction",
            "conversation",

        ],


        "vision":[

            "vision",
            "multimodal",
            "image input",

        ],


        "reasoning":[

            "reasoning",
            "think",
            "cot",

        ],


        "coding":[

            "coding",
            "coder",
            "code",

        ],


        "embedding":[

            "embedding",

        ],


        "rerank":[

            "rerank",

        ],


        "image":[

            "image generation",
            "diffusion",

        ],


        "audio":[

            "audio",
            "speech",

        ],


        "tools":[

            "tools",
            "function calling",

        ],


        "json_mode":[

            "json mode",
            "structured output",

        ],


    }



    for name,words in mapping.items():


        for word in words:


            if word in text:

                result.add(
                    name
                )

                break



    return sorted(
        result
    )





# =====================================================
# html fallback
# =====================================================


def find_field_value(
    soup,
    labels
):


    for label in labels:


        node = soup.find(
            string=lambda x:
                x
                and clean_text(x).lower()
                ==
                label.lower()
        )


        if not node:

            continue



        parent=node.parent


        if not parent:

            continue



        sibling = (
            parent.find_next_sibling()
        )


        if sibling:


            value = clean_text(
                sibling.get_text(
                    " ",
                    strip=True
                )
            )


            if value:

                return value



    return ""





# =====================================================
# main
# =====================================================


def parse_model_detail(
    html: str
) -> Dict[str,Any]:


    result = {


        "logical_name":
            "",


        "model_id":
            "",


        "base_url":
            "",


        "api_format":
            "",


        "context_window":
            None,


        "max_output_tokens":
            None,


        "capabilities":
            [],


        "tags":
            [],


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



        meta_text=""


        meta=soup.find(
            "meta",
            {
                "name":
                    "description"
            }
        )


        if meta:

            meta_text=meta.get(
                "content",
                ""
            )



        combined_text = (

            page_text
            +
            " "
            +
            meta_text

        )



        #
        # next data
        #

        data = extract_next_data(
            html
        )



        if data:


            model_id=find_json_value(
                data,
                [
                    "model",
                    "modelId",
                    "model_id",
                ]
            )


            if model_id:


                model_id = remove_copy_suffix(
                    clean_text(model_id)
                )


                result["model_id"]=model_id


                result["logical_name"]=(
                    model_id.split("/")[-1]
                )




            base_url=find_json_value(
                data,
                [
                    "baseUrl",
                    "base_url",
                    "endpoint",
                ]
            )


            if base_url:


                result["base_url"]=(
                    remove_copy_suffix(
                        clean_text(base_url)
                    )
                )



            api_format=find_json_value(
                data,
                [
                    "apiFormat",
                    "api_format",
                    "protocol",
                ]
            )


            if api_format:


                result["api_format"]=(
                    remove_copy_suffix(
                        clean_text(api_format)
                    )
                )



            context=find_json_value(
                data,
                [
                    "contextWindow",
                    "context_window",
                    "contextLength",
                ]
            )


            if context:


                result["context_window"]=(
                    normalize_number(
                        context
                    )
                )



            output=find_json_value(
                data,
                [
                    "maxOutputTokens",
                    "max_output_tokens",
                    "maxTokens",
                ]
            )


            if output:


                result["max_output_tokens"]=(
                    normalize_number(
                        output
                    )
                )





        #
        # regex fallback
        #

        if not result["context_window"]:


            match=re.search(
                r"([\d,.]+[KM]?)\s*context",
                combined_text,
                re.I
            )


            if match:


                result["context_window"]=(
                    normalize_number(
                        match.group(1)
                    )
                )





        #
        # html fallback
        #

        if not result["model_id"]:


            value=find_field_value(
                soup,
                [
                    "Model ID",
                    "Model",
                    "Model Name",
                ]
            )


            value=remove_copy_suffix(
                value
            )


            if value:


                result["model_id"]=value


                result["logical_name"]=(
                    value.split("/")[-1]
                )



        if not result["base_url"]:


            value=find_field_value(
                soup,
                [
                    "Base URL",
                    "API Base",
                    "Endpoint",
                ]
            )


            result["base_url"]=(
                remove_copy_suffix(
                    value
                )
            )



        if not result["api_format"]:


            result["api_format"]=(
                remove_copy_suffix(
                    find_field_value(
                        soup,
                        [
                            "API Format",
                            "Protocol",
                        ]
                    )
                )
            )





        #
        # max output fallback
        #

        if not result["max_output_tokens"]:


            value=find_field_value(
                soup,
                [
                    "Max Output Tokens",
                    "Max Tokens",
                ]
            )


            result["max_output_tokens"]=(
                normalize_number(
                    value
                )
            )



        if (
            not result["max_output_tokens"]
            and
            result["context_window"]
        ):


            result["max_output_tokens"]=int(
                result["context_window"]
                /
                4
            )



        #
        # capability
        #

        result["capabilities"]=(
            parse_capabilities(
                combined_text
            )
        )



    except Exception:


        logger.exception(
            "parse detail failed"
        )



    return result
