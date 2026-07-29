from __future__ import annotations

import re
from typing import Dict, List

from bs4 import BeautifulSoup


# ==================================================
# 通用清洗
# ==================================================

def clean_text(value: str) -> str:
    if not value:
        return ""

    value = value.replace(
        "\xa0",
        " ",
    )

    value = " ".join(
        value.split()
    )

    return value.strip()



# ==================================================
# 数字解析
# ==================================================

def parse_number(
    value: str,
):
    """
    解析：

    128K
    128k tokens
    128,000

    """

    if not value:
        return None


    value = (
        value
        .lower()
        .replace(",", "")
        .strip()
    )


    match = re.search(
        r"(\d+(?:\.\d+)?)",
        value,
    )


    if not match:
        return None


    number = float(
        match.group(1)
    )


    if "k" in value:

        number *= 1000


    if "m" in value:

        number *= 1000000


    return int(number)



# ==================================================
# 标签提取
# ==================================================

def extract_section_values(
    soup,
    keywords: List[str],
):

    results = []


    #
    # 查找包含关键词节点
    #
    for node in soup.find_all(
        string=True
    ):

        text = clean_text(
            str(node)
        )


        if not text:
            continue


        lower = text.lower()


        if any(
            k.lower() in lower
            for k in keywords
        ):

            parent = node.parent


            if parent:

                #
                # 同级元素
                #
                for item in parent.find_all(
                    [
                        "span",
                        "li",
                        "div",
                        "p",
                    ]
                ):

                    value = clean_text(
                        item.get_text(
                            " ",
                            strip=True,
                        )
                    )


                    if value:

                        results.append(
                            value
                        )


    return list(
        dict.fromkeys(
            results
        )
    )



# ==================================================
# Capability
# ==================================================

def parse_capabilities(
    soup,
):

    values = []


    values.extend(
        extract_section_values(
            soup,
            [
                "Capabilities",
                "Capability",
                "Features",
                "Modalities",
            ],
        )
    )


    #
    # 全文兜底
    #
    text = clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )


    values.append(
        text
    )


    result = []


    for value in values:

        value = (
            value
            .replace(
                "✓",
                "",
            )
        )


        parts = re.split(
            r"[,|/•\n]",
            value,
        )


        for part in parts:

            part = clean_text(
                part
            )


            if part:

                result.append(
                    part
                )


    return list(
        dict.fromkeys(
            result
        )
    )



# ==================================================
# Key Value 提取
# ==================================================

def find_value(
    soup,
    labels,
):

    for label in labels:

        #
        # 文本节点
        #
        node = soup.find(
            string=re.compile(
                label,
                re.I,
            )
        )


        if not node:
            continue


        parent = node.parent


        if not parent:
            continue


        text = clean_text(
            parent.get_text(
                " ",
                strip=True,
            )
        )


        #
        # 去掉 label
        #
        text = re.sub(
            label,
            "",
            text,
            flags=re.I,
        )


        text = clean_text(
            text
        )


        if text:

            return text


        #
        # 下一个兄弟节点
        #
        sibling = parent.find_next()


        if sibling:

            value = clean_text(
                sibling.get_text(
                    " ",
                    strip=True,
                )
            )

            if value:

                return value


    return ""



# ==================================================
# URL
# ==================================================

def parse_model_detail(
    html: str,
) -> Dict:


    soup = BeautifulSoup(
        html,
        "html.parser",
    )


    data = {}



    #
    # Model ID
    #
    data["model_id"] = clean_text(
        find_value(
            soup,
            [
                "Model ID",
                "Model",
                "Model Name",
            ],
        )
    )



    #
    # Base URL
    #
    data["base_url"] = clean_text(
        find_value(
            soup,
            [
                "Base URL",
                "API Base",
                "Endpoint",
            ],
        )
    )



    #
    # API Format
    #
    data["api_format"] = clean_text(
        find_value(
            soup,
            [
                "API Format",
                "Format",
            ],
        )
    )



    #
    # Context Window
    #
    context = find_value(
        soup,
        [
            "Context Window",
            "Context Length",
            "Context Size",
        ],
    )


    data["context_window"] = parse_number(
        context
    )



    #
    # Max Output Tokens
    #
    output = find_value(
        soup,
        [
            "Max Output Tokens",
            "Maximum Output",
            "Output Tokens",
        ],
    )


    data["max_output_tokens"] = parse_number(
        output
    )



    #
    # Capability
    #
    data["capabilities"] = parse_capabilities(
        soup
    )


    #
    # Tags
    #
    data["tags"] = extract_section_values(
        soup,
        [
            "Tags",
            "Tag",
        ],
    )


    #
    # logical name
    #
    data["logical_name"] = clean_text(
        find_value(
            soup,
            [
                "Model Name",
                "Model",
            ],
        )
    )



    return data
