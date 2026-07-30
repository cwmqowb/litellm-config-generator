"""
models.py

核心数据模型定义


架构:

ModelInfo
    |
    v
LogicalModel.models
    |
    v
LiteLLM config


禁止:

ProviderModel
primary_model
providers
provider_models
"""

from __future__ import annotations


from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional



# ============================================================
# Capability
# ============================================================


@dataclass
class ModelCapability:
    """
    模型能力标签
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



    def primary_type(self) -> str:
        """
        返回主要能力类型
        """

        if self.embedding:

            return "embedding"


        if self.rerank:

            return "rerank"



        if self.vision:

            return "vision"



        if self.coding:

            return "coding"



        if self.reasoning:

            return "reasoning"



        return "chat"





# ============================================================
# Pricing
# ============================================================


@dataclass
class ModelPricing:


    input_price: Optional[float] = None


    output_price: Optional[float] = None


    free: bool = True





# ============================================================
# ModelInfo
# ============================================================


@dataclass
class ModelInfo:
    """
    单个真实模型


    示例:

    nvidia/nemotron-3-ultra-550b-a55b:free

    """



    name: str


    model_id: str


    provider: str



    logical_name: str = ""



    api_base: Optional[str] = None


    api_key_env: Optional[str] = None


    api_format: str = "openai"



    capability: ModelCapability = field(
        default_factory=ModelCapability
    )



    context_window: Optional[int] = None



    max_output_tokens: Optional[int] = None



    free: bool = True



    pricing: ModelPricing = field(
        default_factory=ModelPricing
    )



    score: float = 0.0



    tags: List[str] = field(
        default_factory=list
    )



    metadata: Dict[str, Any] = field(
        default_factory=dict
    )





# ============================================================
# LogicalModel
# ============================================================


@dataclass
class LogicalModel:
    """
    逻辑模型


    一个逻辑入口对应多个真实模型


    示例:


    LogicalModel(chat)


        models:

            nvidia/nemotron

            openai/gpt-oss

            deepseek


    """



    logical_name: str



    models: List[ModelInfo] = field(
        default_factory=list
    )



    strategy: str = "simple-shuffle"