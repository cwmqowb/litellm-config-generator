from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FreeLLMModel:
    """
    freellm Top200 页面的一条模型记录
    """

    provider: str
    name: str
    detail_url: str


@dataclass
class ModelCapability:
    chat: bool = False
    vision: bool = False
    reasoning: bool = False
    coding: bool = False
    embedding: bool = False
    image: bool = False
    audio: bool = False
    tools: bool = False
    json_mode: bool = False


@dataclass
class ProviderModel:
    """
    一个 Provider 对某模型的配置
    """

    provider: str

    logical_name: str

    model_id: str

    api_base: str

    api_format: str

    api_key_env: str

    context_window: Optional[int] = None

    max_output_tokens: Optional[int] = None

    capability: ModelCapability = field(
        default_factory=ModelCapability
    )


@dataclass
class LogicalModel:
    """
    LiteLLM 的逻辑模型
    """

    name: str

    providers: List[ProviderModel] = field(
        default_factory=list
    )
