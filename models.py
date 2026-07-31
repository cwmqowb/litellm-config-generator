"""
models.py

Core data models for LiteLLM Config Generator V2.

Architecture:

crawler.py
    |
    v
RawModel
    |
    v
detail_parser.py
    |
    v
ProviderModel
    |
    v
config_builder.py
    |
    v
LiteLLM config.yaml
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# ============================================================
# Raw model from freellm model list page
# ============================================================

@dataclass
class RawModel:
    """
    Model information collected from models listing page.

    This object is temporary.
    It should NOT directly generate LiteLLM config.
    """

    name: str

    provider: str

    score: float = 0

    detail_url: Optional[str] = None

    context: Optional[str] = None

    modality: List[str] = field(default_factory=list)

    verified: bool = False

    description: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Provider model after detail page parsing
# ============================================================

@dataclass
class ProviderModel:
    """
    Normalized provider model.

    This is the single source of truth
    for LiteLLM configuration generation.
    """

    # ----------------------------
    # Basic information
    # ----------------------------

    provider: str

    model_id: str

    display_name: str


    # ----------------------------
    # API information
    # ----------------------------

    api_base: Optional[str] = None

    api_format: Optional[str] = None


    # ----------------------------
    # Ranking
    # ----------------------------

    score: float = 0


    # ----------------------------
    # Model capability
    # ----------------------------

    capabilities: List[str] = field(
        default_factory=list
    )

    input_modalities: List[str] = field(
        default_factory=list
    )

    output_modalities: List[str] = field(
        default_factory=list
    )


    # ----------------------------
    # Context
    # ----------------------------

    context_tokens: Optional[int] = None

    max_output_tokens: Optional[int] = None


    # ----------------------------
    # Usage classification
    # ----------------------------

    best_for: List[str] = field(
        default_factory=list
    )


    # ----------------------------
    # Provider limitation
    # ----------------------------

    rate_limit: Optional[str] = None


    # ----------------------------
    # Status
    # ----------------------------

    verified: bool = False

    online: bool = False


    # ----------------------------
    # Source
    # ----------------------------

    detail_url: Optional[str] = None


    # ----------------------------
    # Extra metadata
    # ----------------------------

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


    # ========================================================
    # helper methods
    # ========================================================

    def supports(self, capability: str) -> bool:
        """
        Check capability support.

        Example:

            model.supports("vision")
        """

        capability = capability.lower()

        return any(
            capability in item.lower()
            for item in self.capabilities
        )


    def is_chat_model(self) -> bool:
        """
        Whether model can be used for chat.
        """

        chat_keywords = {
            "chat",
            "text",
            "reasoning",
            "code"
        }

        values = set(
            x.lower()
            for x in self.best_for
        )

        return bool(
            values.intersection(chat_keywords)
        )


    def is_vision_model(self) -> bool:
        """
        Whether model supports vision.
        """

        values = (
            self.input_modalities
            +
            self.capabilities
        )

        return any(
            "vision" in x.lower()
            or "image" in x.lower()
            for x in values
        )


    def is_embedding_model(self) -> bool:
        """
        Whether model is embedding model.
        """

        values = (
            self.best_for
            +
            self.capabilities
        )

        return any(
            "embedding" in x.lower()
            for x in values
        )


    def model_type(self) -> str:
        """
        Return logical model category.

        Used by config_builder.
        """

        if self.is_embedding_model():
            return "embedding"

        if self.is_vision_model():
            return "vision"

        if self.is_chat_model():
            return "chat"

        return "unknown"


    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        """

        return asdict(self)



# ============================================================
# LiteLLM configuration model
# ============================================================

@dataclass
class LiteLLMModel:
    """
    Internal representation of one LiteLLM model entry.
    """

    model_name: str

    litellm_model: str

    api_base: Optional[str]

    api_key_env: Optional[str]

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


    def to_yaml_dict(self) -> Dict[str, Any]:
        """
        Convert to LiteLLM yaml structure.
        """

        result = {

            "model_name": self.model_name,

            "litellm_params": {

                "model": self.litellm_model

            }

        }


        if self.api_base:
            result["litellm_params"][
                "api_base"
            ] = self.api_base


        if self.api_key_env:
            result["litellm_params"][
                "api_key"
            ] = (
                f"os.environ/{self.api_key_env}"
            )


        if self.metadata:
            result["metadata"] = self.metadata


        return result



# ============================================================
# Config container
# ============================================================

@dataclass
class GeneratedConfig:

    models: List[LiteLLMModel] = field(
        default_factory=list
    )


    def to_yaml_dict(self) -> Dict[str, Any]:

        return {

            "model_list": [

                item.to_yaml_dict()

                for item in self.models

            ]

        }
