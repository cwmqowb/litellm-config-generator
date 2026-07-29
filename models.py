from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FreeLLMModel:
    """
    freellm 首页模型记录
    """

    provider: str

    name: str

    detail_url: str



@dataclass
class ModelCapability:
    """
    模型能力描述
    """

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


        for name in (
            "chat",
            "reasoning",
            "coding",
            "vision",
            "embedding",
            "rerank",
            "image",
            "audio",
            "tools",
            "json_mode",
        ):

            if getattr(
                self,
                name,
                False,
            ):

                result.append(
                    name
                )


        return result



    def merge(
        self,
        other: "ModelCapability",
    ):

        """
        合并多个 provider capability
        """

        for field_name in vars(self):

            if getattr(
                other,
                field_name,
                False,
            ):

                setattr(
                    self,
                    field_name,
                    True,
                )



@dataclass
class ProviderModel:
    """
    一个 Provider 的一个 deployment
    """

    provider: str

    logical_name: str

    model_id: str

    api_base: str = ""

    api_format: str = ""


    #
    # 单 key 兼容
    #
    api_key_env: str = ""


    #
    # 多 key 支持
    #
    api_key_envs: List[str] = field(
        default_factory=list
    )


    deployment_name: str = ""


    context_window: Optional[int] = None


    max_output_tokens: Optional[int] = None



    capability: ModelCapability = field(
        default_factory=ModelCapability
    )


    raw_tags: List[str] = field(
        default_factory=list
    )


    metadata: Dict = field(
        default_factory=dict
    )



    def get_api_keys(self):

        """
        获取所有 API Key 环境变量
        """

        if self.api_key_envs:

            return self.api_key_envs


        if self.api_key_env:

            return [
                self.api_key_env
            ]


        return []



@dataclass
class LogicalModel:
    """
    品牌模型

    例如：

    glm-5.2

        NVIDIA
        OpenRouter
        ModelScope

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



    def add_provider(
        self,
        provider: ProviderModel,
    ):

        self.providers.append(
            provider
        )


        #
        # Context Window
        #
        if provider.context_window:

            if (
                self.context_window is None
                or
                provider.context_window
                >
                self.context_window
            ):

                self.context_window = (
                    provider.context_window
                )


        #
        # Max Output Tokens
        #
        if provider.max_output_tokens:

            if (
                self.max_output_tokens is None
                or
                provider.max_output_tokens
                >
                self.max_output_tokens
            ):

                self.max_output_tokens = (
                    provider.max_output_tokens
                )


        #
        # Capability merge
        #
        self.capability.merge(
            provider.capability
        )



@dataclass
class CapabilityGroup:
    """
    capability:

    chat
    reasoning
    coding
    vision
    """

    name: str


    models: List[str] = field(
        default_factory=list
    )



@dataclass
class BuildResult:
    """
    Builder 输出结果
    """

    logical_models: Dict[str, LogicalModel] = field(
        default_factory=dict
    )


    capability_groups: Dict[str, CapabilityGroup] = field(
        default_factory=dict
    )
