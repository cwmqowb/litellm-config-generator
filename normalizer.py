import re

from models import ModelCapability


# 一些 Provider 会附加这些后缀
_SUFFIXES = [
    ":free",
    ":beta",
    ":latest",
]


_PROVIDER_SUFFIX = re.compile(
    r"(__.*)$",
    re.IGNORECASE,
)


_MULTI_SPACE = re.compile(r"\s+")


def normalize_model_name(name: str) -> str:
    """
    将 freellm/OpenRouter 等各种名字统一成品牌模型名称

    glm-5.2:free
        ↓
    glm-5.2

    glm-5.2__github
        ↓
    glm-5.2

    DeepSeek-V4-Flash
        ↓
    deepseek-v4-flash
    """

    if not name:
        return ""

    name = name.strip()

    name = _PROVIDER_SUFFIX.sub("", name)

    for suffix in _SUFFIXES:
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]

    name = name.replace("_", "-")

    name = _MULTI_SPACE.sub("-", name)

    name = name.strip("- ")

    return name.lower()


def parse_capabilities(capabilities, tags):
    """
    freellm Capability + Tags
    →

    LiteLLM Capability
    """

    result = ModelCapability()

    words = []

    if capabilities:
        words.extend(capabilities)

    if tags:
        words.extend(tags)

    words = [x.lower() for x in words]

    text = " ".join(words)

    if "chat" in text:
        result.chat = True

    if "vision" in text:
        result.vision = True

    if "image" in text:
        result.image = True

    if "audio" in text:
        result.audio = True

    if "embedding" in text:
        result.embedding = True

    if "rerank" in text:
        result.rerank = True

    if "reason" in text:
        result.reasoning = True

    if "thinking" in text:
        result.reasoning = True

    if "reasoning" in text:
        result.reasoning = True

    if "code" in text:
        result.coding = True

    if "coder" in text:
        result.coding = True

    if "tool" in text:
        result.tools = True

    if "function calling" in text:
        result.tools = True

    if "json" in text:
        result.json_mode = True

    # 默认都是 chat
    if not (
        result.embedding
        or result.rerank
    ):
        result.chat = True

    return result
