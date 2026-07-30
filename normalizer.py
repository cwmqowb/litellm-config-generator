"""
normalizer.py

模型标准化模块

职责：
1. 将 detail_parser 输出的 ModelInfo 列表标准化
2. 根据模型能力生成 LogicalModel
3. 不负责 LiteLLM YAML 生成

数据流：

detail_parser
        |
        v
    ModelInfo[]
        |
        v
    normalizer
        |
        v
    LogicalModel[]
        |
        v
config_builder
"""

from typing import List, Dict

from models import (
    ModelInfo,
    LogicalModel,
)


# ============================================================
# 默认能力关键词
# ============================================================

VISION_KEYWORDS = [
    "vision",
    "vl",
    "image",
    "multimodal",
    "llava",
    "qwen-vl",
    "gpt-4o",
    "gemini",
]


REASONING_KEYWORDS = [
    "reasoning",
    "think",
    "r1",
    "o1",
    "o3",
    "deepseek-r1",
    "qwq",
]


CHAT_KEYWORDS = [
    "chat",
    "instruct",
    "chatgpt",
    "assistant",
]


# ============================================================
# 基础能力判断
# ============================================================


def detect_capabilities(model: ModelInfo) -> List[str]:
    """
    根据模型名称和已有能力判断模型能力

    返回:
        [
            "chat",
            "vision",
            "reasoning"
        ]
    """

    capabilities = set()


    # --------------------------------------------------------
    # 优先使用 parser 已解析能力
    # --------------------------------------------------------

    existing = getattr(model, "capabilities", None)

    if existing:

        if isinstance(existing, list):
            capabilities.update(existing)

        elif isinstance(existing, str):
            capabilities.add(existing)



    # --------------------------------------------------------
    # 模型名称辅助判断
    # --------------------------------------------------------

    text = " ".join(
        [
            str(getattr(model, "name", "")),
            str(getattr(model, "model", "")),
        ]
    ).lower()



    for keyword in VISION_KEYWORDS:

        if keyword in text:
            capabilities.add("vision")
            break



    for keyword in REASONING_KEYWORDS:

        if keyword in text:
            capabilities.add("reasoning")
            break



    # 默认所有 LLM 至少支持 chat

    if not capabilities:

        capabilities.add("chat")

    else:

        # 非纯 embedding/rerank 模型默认加入 chat

        if (
            "embedding" not in text
            and "rerank" not in text
        ):
            capabilities.add("chat")



    return sorted(list(capabilities))



# ============================================================
# 模型标准化
# ============================================================


def normalize_models(
    models: List[ModelInfo],
) -> List[ModelInfo]:
    """
    标准化模型字段

    不创建新对象，
    只补充缺失字段
    """

    normalized = []


    for model in models:


        # ----------------------------------------------------
        # capabilities
        # ----------------------------------------------------

        capabilities = detect_capabilities(model)


        if hasattr(model, "capabilities"):

            model.capabilities = capabilities



        # ----------------------------------------------------
        # score 默认值
        # ----------------------------------------------------

        if not getattr(model, "score", None):

            model.score = 0



        normalized.append(model)



    return normalized



# ============================================================
# Logical Model 构建
# ============================================================


def build_logical_models(
    models: List[ModelInfo],
) -> List[LogicalModel]:
    """
    创建逻辑模型

    输出:

    LogicalModel(
        name="chat",
        models=[
            ModelInfo,
            ModelInfo
        ],
        strategy="fallback"
    )

    """

    models = normalize_models(models)


    groups: Dict[str, List[ModelInfo]] = {

        "chat": [],
        "vision": [],
        "reasoning": [],

    }



    for model in models:


        capabilities = getattr(
            model,
            "capabilities",
            []
        )


        for capability in capabilities:


            if capability in groups:

                groups[capability].append(model)



    logical_models = []



    # --------------------------------------------------------
    # 按 score 排序
    # --------------------------------------------------------

    for name, items in groups.items():


        if not items:
            continue



        items.sort(
            key=lambda x:
            getattr(
                x,
                "score",
                0
            ),
            reverse=True
        )



        logical_models.append(

            LogicalModel(

                name=name,

                models=items,

                strategy="fallback",

                capabilities=[
                    name
                ],

            )

        )



    return logical_models



# ============================================================
# 对外入口
# ============================================================


def normalize(
    models: List[ModelInfo],
) -> List[LogicalModel]:
    """
    normalizer 主入口

    detail_parser.py 调用：

        logical_models = normalize(models)

    """

    return build_logical_models(models)
