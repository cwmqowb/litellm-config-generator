"""
Model data structures.

This module defines unified model information objects used by:
- crawler.py
- parser.py
- detail_parser.py
- normalizer.py
- config_builder.py

The goal is to normalize different free LLM providers
into a LiteLLM-compatible model representation.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class ModelCapability:
    """
    Model capability information.

    Example:
    - reasoning
    - vision
    - tool_calling
    - json_mode
    """

    reasoning: bool = False
    vision: bool = False
    tool_calling: bool = False
    json_mode: bool = False

    # Original capability text from provider page
    raw: List[str] = field(default_factory=list)


@dataclass
class ModelPricing:
    """
    Pricing information.

    FreeLLM may provide:
    - free tier information
    - paid pricing information

    Keep optional because many providers do not expose pricing.
    """

    input_price: Optional[float] = None
    output_price: Optional[float] = None

    currency: str = "USD"

    free: bool = False

    free_note: Optional[str] = None


@dataclass
class ModelInfo:
    """
    Unified LLM model information.

    This object is the core data model of the project.

    Data source:
        FreeLLM models.html
        FreeLLM model detail page

    Output target:
        LiteLLM config.yaml
    """

    # ==========================
    # Basic information
    # ==========================

    name: str

    provider: str

    # Provider original model ID
    # Example:
    # z-ai/glm-5.2
    model_id: Optional[str] = None


    # Detail page URL
    detail_url: Optional[str] = None


    # ==========================
    # API information
    # ==========================

    api_base: Optional[str] = None

    api_format: Optional[str] = None

    # Environment variable name
    # Example:
    # NVIDIA_API_KEY
    api_key_env: Optional[str] = None


    # ==========================
    # Model capability
    # ==========================

    capabilities: ModelCapability = field(
        default_factory=ModelCapability
    )


    input_types: List[str] = field(
        default_factory=list
    )

    output_types: List[str] = field(
        default_factory=list
    )


    # ==========================
    # Context information
    # ==========================

    context_window: Optional[int] = None

    max_output_tokens: Optional[int] = None


    # ==========================
    # Availability
    # ==========================

    free: bool = False

    verified: bool = False

    online: bool = False


    # ==========================
    # Pricing
    # ==========================

    pricing: ModelPricing = field(
        default_factory=ModelPricing
    )


    # ==========================
    # Ranking / selection
    # ==========================

    score: float = 0

    priority: int = 0


    # ==========================
    # Extra metadata
    # ==========================

    tags: List[str] = field(
        default_factory=list
    )

    metadata: Dict = field(
        default_factory=dict
    )


    def to_dict(self) -> Dict:
        """
        Convert model object into dictionary.

        Used by:
        - json export
        - debug output
        - config builder
        """

        return asdict(self)


    def add_tag(self, tag: str):
        """
        Add model tag safely.
        """

        if tag not in self.tags:
            self.tags.append(tag)


    def add_capability(self, capability: str):
        """
        Normalize capability string.
        """

        capability = capability.lower().strip()

        if capability not in self.capabilities.raw:
            self.capabilities.raw.append(capability)

        if capability in (
            "reasoning",
            "thinking",
        ):
            self.capabilities.reasoning = True


        elif capability in (
            "vision",
            "image",
            "multimodal",
        ):
            self.capabilities.vision = True


        elif capability in (
            "tool calling",
            "tool_calling",
            "function calling",
        ):
            self.capabilities.tool_calling = True


        elif capability in (
            "json",
            "json mode",
            "structured output",
        ):
            self.capabilities.json_mode = True



    def is_chat_model(self) -> bool:
        """
        Determine whether model can be used as chat model.
        """

        if not self.input_types:
            return True

        return (
            "text" in self.input_types
            or "chat" in self.input_types
        )


    def is_vision_model(self) -> bool:
        """
        Determine whether model supports vision.
        """

        return self.capabilities.vision



@dataclass
class LogicalModel:
    """
    Logical model abstraction.

    Example:

    smart-chat
        |
        +-- glm-5.2 NVIDIA
        +-- deepseek-v3 ModelScope
        +-- gpt-4o GitHub Models


    Used for LiteLLM router configuration.
    """

    name: str

    description: Optional[str] = None


    models: List[ModelInfo] = field(
        default_factory=list
    )


    strategy: str = "fallback"


    def add_model(
        self,
        model: ModelInfo
    ):
        """
        Add physical model.
        """

        self.models.append(model)


    def sort_models(self):
        """
        Sort by score descending.
        """

        self.models.sort(
            key=lambda x: x.score,
            reverse=True
        )


    def get_model_ids(self) -> List[str]:
        """
        Return provider model IDs.
        """

        return [
            m.model_id
            for m in self.models
            if m.model_id
        ]
