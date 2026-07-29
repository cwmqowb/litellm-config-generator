"""
Model name normalizer

负责：

1. 品牌模型名称统一
2. Provider 后缀清理
3. free 标识清理
4. 厂商 namespace 清理

例如：

z-ai/glm-5.2
        |
        v
glm-5.2


deepseek-ai/deepseek-v4-flash
        |
        v
deepseek-v4-flash
"""

from __future__ import annotations

import re



# 厂商 namespace

VENDOR_PREFIXES = {

    "z-ai",
    "zhipuai",
    "glm",

    "deepseek-ai",
    "deepseek",

    "moonshotai",
    "moonshot",

    "qwen",
    "alibaba",

    "google",
    "gemini",

    "meta",
    "meta-llama",

    "mistralai",

}



# 不影响语义的后缀

REMOVE_SUFFIX = [

    ":free",

    "-free",

    "_free",

    "(free)",

    "[free]",

]



# provider 污染

PROVIDER_SUFFIX = [

    "__nvidia",

    "__nvidia_nim",

    "__openrouter",

    "__github",

    "__github_models",

    "__modelscope",

    "__sambanova",

    "__agnes",

    "__kilo",

]



def clean_text(
    value: str,
) -> str:

    if not value:

        return ""

    value = value.strip()

    value = value.lower()

    value = value.replace(
        " ",
        "-",
    )

    return value



def remove_vendor_prefix(
    name: str,
) -> str:


    if "/" not in name:

        return name


    parts = name.split(
        "/"
    )


    if len(parts) != 2:

        return name


    prefix, model = parts


    if (
        prefix.lower()
        in VENDOR_PREFIXES
    ):

        return model


    #
    # 默认保留最后一段
    #
    return model



def remove_free_tag(
    name: str,
) -> str:


    for suffix in REMOVE_SUFFIX:

        name = name.replace(
            suffix,
            "",
        )


    name = re.sub(
        r"\s*\(free\)",
        "",
        name,
        flags=re.I,
    )


    return name



def remove_provider_suffix(
    name: str,
) -> str:


    for suffix in PROVIDER_SUFFIX:

        name = name.replace(
            suffix,
            "",
        )


    return name



def normalize_model_name(
    name: str,
) -> str:


    if not name:

        return ""


    name = clean_text(
        name
    )


    #
    # 去 namespace
    #
    name = remove_vendor_prefix(
        name
    )


    #
    # 去 provider
    #
    name = remove_provider_suffix(
        name
    )


    #
    # 去 free
    #
    name = remove_free_tag(
        name
    )


    #
    # 清理连续符号
    #
    name = re.sub(
        r"[_]+",
        "-",
        name,
    )


    name = re.sub(
        r"-+",
        "-",
        name,
    )


    return name.strip("-")



def normalize_brand(
    name: str,
) -> str:

    """
    alias

    保留兼容旧调用
    """

    return normalize_model_name(
        name
    )
