"""
加入归一化逻辑，例如：

z-ai/glm-5.2
glm-5.2
ZAI GLM-5.2

全部归并为：

glm-5.2
"""
from __future__ import annotations

import re


class LogicalModelNormalizer:
    """
    将 Provider 的 Model ID 归一化成 Logical Model

    例如：

    nvidia/nemotron-3-ultra-550b-a55b
    openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
    ==> nemotron-3-ultra-550b-a55b

    z-ai/glm-5.2
    glm-5.2
    ==> glm-5.2

    Qwen/Qwen3-235B-A22B-Instruct
    ==> qwen3-235b
    """

    def normalize(self, model_id: str) -> str:

        name = model_id.lower()

        #
        # OpenRouter
        #

        name = name.replace(":free", "")
        name = name.replace(":beta", "")

        #
        # 去 provider 前缀
        #

        prefixes = [
            "nvidia/",
            "google/",
            "meta/",
            "qwen/",
            "moonshotai/",
            "z-ai/",
            "deepseek-ai/",
            "mistralai/",
            "cohere/",
            "openai/",
            "openrouter/",
            "microsoft/",
            "writer/",
            "ibm/",
            "baai/",
            "bytedance/",
        ]

        changed = True

        while changed:

            changed = False

            for p in prefixes:

                if name.startswith(p):

                    name = name[len(p):]

                    changed = True

        #
        # glm
        #

        m = re.search(
            r"glm[-_]?([0-9.]+)",
            name,
        )

        if m:
            return f"glm-{m.group(1)}"

        #
        # gemini
        #

        m = re.search(
            r"gemini[-_]?([0-9.]+)-(.*)",
            name,
        )

        if m:
            return f"gemini-{m.group(1)}-{m.group(2)}"

        #
        # qwen3
        #

        m = re.search(
            r"qwen3(?:\.5)?[-_]?([0-9]+)b",
            name,
        )

        if m:
            return f"qwen3-{m.group(1)}b"

        #
        # deepseek
        #

        if "deepseek-v4-flash" in name:
            return "deepseek-v4-flash"

        if "deepseek-v4" in name:
            return "deepseek-v4"

        if "deepseek-v3.2" in name:
            return "deepseek-v3.2"

        if "deepseek-v3" in name:
            return "deepseek-v3"

        #
        # kimi
        #

        if "kimi-k2.6" in name:
            return "kimi-k2.6"

        if "kimi-k2.5" in name:
            return "kimi-k2.5"

        if "kimi-k2" in name:
            return "kimi-k2"

        #
        # minimax
        #

        if "minimax-m3" in name:
            return "minimax-m3"

        if "minimax-m2.7" in name:
            return "minimax-m2.7"

        #
        # GPT OSS
        #

        if "gpt-oss-120b" in name:
            return "gpt-oss-120b"

        if "gpt-oss-20b" in name:
            return "gpt-oss-20b"

        #
        # Nemotron
        #

        if "nemotron" in name:

            name = re.sub(
                r"^(llama[-_]3\.[0-9][-_]?)",
                "",
                name,
            )

            name = name.replace(
                "-instruct",
                "",
            )

            return name

        #
        # Gemma
        #

        if "gemma" in name:

            name = name.replace(
                "-it",
                "",
            )

            return name

        #
        # Llama
        #

        if "llama" in name:

            name = name.replace(
                "-instruct",
                "",
            )

            return name

        #
        # Mistral
        #

        if "mistral" in name:

            name = name.replace(
                "-instruct",
                "",
            )

            return name

        return name
