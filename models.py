from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    rerank: bool = False
    image: bool = False
    audio: bool = False
    tools: bool = False
    json_mode: bool = False

    def enabled(self) -> List[str]:
        result = []

        if self.chat:
            result.append("chat")

        if self.reasoning:
            result.append("reasoning")

        if self.coding:
            result.append("coding")

        if self.vision:
            result.append("vision")

        if self.embedding:
            result.append("embedding")

        if self.rerank:
            result.append("rerank")

        if self.image:
            result.append("image")

        if self.audio:
            result.append("audio")

        return result


@dataclass
class ProviderModel:
    """
    一个 Provider 的一个 Deployment
    """

    provider: str

    logical_name: str

    model_id: str

    api_base: str

    api_format: str

    api_key_env: str

    deployment_name: str = ""

    context_window: Optional[int] = None

    max_output_tokens: Optional[int] = None

    capability: ModelCapability = field(
        default_factory=ModelCapability
    )

    raw_tags: List[str] = field(
        default_factory=list
    )


@dataclass
class LogicalModel:
    """
    一个品牌模型（LiteLLM Logical Model）
    """

    name: str

    providers: List[ProviderModel] = field(
        default_factory=list
    )

    context_window: Optional[int] = None

    max_output_tokens: Optional[int] = None

    capability: ModelCapability = field(
        default_factory=ModelCapability
    )

    def add_provider(self, provider: ProviderModel):

        self.providers.append(provider)

        if self.context_window is None:
            self.context_window = provider.context_window

        if self.max_output_tokens is None:
            self.max_output_tokens = provider.max_output_tokens

        for field_name in vars(self.capability):

            if getattr(provider.capability, field_name):

                setattr(self.capability, field_name, True)


@dataclass
class CapabilityGroup:
    """
    chat / reasoning / coding ...
    """

    name: str

    models: List[str] = field(
        default_factory=list
    )


@dataclass
class BuildResult:
    """
    Builder 最终中间结果
    """

    logical_models: Dict[str, LogicalModel] = field(
        default_factory=dict
    )

    capability_groups: Dict[str, CapabilityGroup] = field(
        default_factory=dict
    )
