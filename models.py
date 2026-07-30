"""
models.py

统一模型数据结构

架构:

crawler/parser/detail_parser
            |
            v
        ModelInfo
            |
            v
    LogicalModel.models
            |
            v
      LiteLLM config.yaml
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# ============================================================
# Capability
# ============================================================

@dataclass
class ModelCapability:
    """
    模型能力
    """

    chat: bool = False
    vision: bool = False
    reasoning: bool = False
    coding: bool = False
    embedding: bool = False
    rerank: bool = False
    image: bool = False
    audio: bool = False
    tool_calling: bool = False
    json_mode: bool = False

    raw: List[str] = field(
        default_factory=list
    )


# ============================================================
# Pricing
# ============================================================

@dataclass
class ModelPricing:
    """
    模型价格信息
    """

    input_price: Optional[float] = None

    output_price: Optional[float] = None

    currency: str = "USD"

    free: bool = False

    note: Optional[str] = None



# ============================================================
# Availability
# ============================================================

@dataclass
class ModelAvailability:
    """
    模型可用性状态
    """

    network_ok: bool = False

    auth_ok: bool = False

    model_available: bool = False

    tested: bool = False

    error: Optional[str] = None



# ============================================================
# ModelInfo
# ============================================================

@dataclass
class ModelInfo:
    """
    单个实际模型

    示例:

    NVIDIA
        nvidia/glm-5

    ModelScope
        deepseek-ai/DeepSeek-V3
    """


    # ----------------------------
    # 基础信息
    # ----------------------------

    name: str


    logical_name: str


    provider: str


    model_id: str


    # ----------------------------
    # API信息
    # ----------------------------

    api_base: Optional[str] = None


    api_key_env: Optional[str] = None


    api_format: Optional[str] = None



    # ----------------------------
    # 能力
    # ----------------------------

    capabilities: ModelCapability = field(
        default_factory=ModelCapability
    )


    # ----------------------------
    # 上下文
    # ----------------------------

    context_window: Optional[int] = None


    max_output_tokens: Optional[int] = None



    # ----------------------------
    # 免费/价格
    # ----------------------------

    free: bool = False


    pricing: ModelPricing = field(
        default_factory=ModelPricing
    )



    # ----------------------------
    # 状态
    # ----------------------------

    availability: ModelAvailability = field(
        default_factory=ModelAvailability
    )



    # ----------------------------
    # 排序
    # ----------------------------

    score: float = 0


    priority: int = 0



    # ----------------------------
    # 扩展
    # ----------------------------

    tags: List[str] = field(
        default_factory=list
    )


    metadata: Dict = field(
        default_factory=dict
    )


    # ========================================================
    # methods
    # ========================================================

    def to_dict(self):

        return asdict(self)



    def add_tag(
        self,
        tag: str
    ):

        if tag not in self.tags:
            self.tags.append(tag)



    def add_capability(
        self,
        capability: str
    ):

        capability = (
            capability
            .lower()
            .strip()
        )


        if capability not in self.capabilities.raw:
            self.capabilities.raw.append(
                capability
            )


        mapping = {

            "chat":
                "chat",

            "conversation":
                "chat",

            "vision":
                "vision",

            "image":
                "vision",

            "multimodal":
                "vision",

            "reasoning":
                "reasoning",

            "thinking":
                "reasoning",

            "coder":
                "coding",

            "coding":
                "coding",

            "embedding":
                "embedding",

            "rerank":
                "rerank",

            "tool":
                "tool_calling",

            "function calling":
                "tool_calling",

            "json":
                "json_mode",

        }


        field_name = mapping.get(
            capability
        )


        if field_name:

            setattr(
                self.capabilities,
                field_name,
                True
            )



    def is_chat_model(self):

        return (
            self.capabilities.chat
            or
            not any(
                [
                    self.capabilities.embedding,
                    self.capabilities.rerank,
                    self.capabilities.image,
                ]
            )
        )



# ============================================================
# LogicalModel
# ============================================================

@dataclass
class LogicalModel:
    """
    LiteLLM逻辑模型

    示例:

    smart-chat

        |
        +-- qwen3 NVIDIA

        +-- glm-5 ModelScope

        +-- deepseek SambaNova
    """


    logical_name: str


    models: List[ModelInfo] = field(
        default_factory=list
    )


    strategy: str = "fallback"



    description: Optional[str] = None



    def add_model(
        self,
        model: ModelInfo
    ):

        self.models.append(
            model
        )



    def sort_models(self):

        self.models.sort(
            key=lambda x:
                x.score,
            reverse=True
        )



    def get_model_ids(self):

        return [
            model.model_id
            for model in self.models
            if model.model_id
        ]