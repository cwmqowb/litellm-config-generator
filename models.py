"""
models.py

Unified data model definition.

All modules MUST use ModelInfo.

Architecture:

crawler.py
    |
    v
detail_parser.py
    |
    v
ModelInfo
    |
    v
config_builder.py


禁止:
- name
- display_name
- title

LiteLLM model name MUST use model_id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModelInfo:
    """
    Unified model information.

    This is the only model structure used
    inside the project.
    """

    # -----------------------------
    # Provider information
    # -----------------------------

    provider: str


    # -----------------------------
    # Real LiteLLM model id
    #
    # MUST come from detail page:
    # API Details -> Model ID
    # -----------------------------

    model_id: str


    # -----------------------------
    # Provider endpoint
    # -----------------------------

    api_base: Optional[str] = None


    # -----------------------------
    # Ranking score from crawler
    # -----------------------------

    score: float = 0.0


    # -----------------------------
    # Context window
    #
    # Example:
    # "128K"
    # -----------------------------

    context: Optional[str] = None


    # -----------------------------
    # Model capability
    #
    # Example:
    # [
    #   "chat",
    #   "reasoning",
    #   "coding"
    # ]
    # -----------------------------

    capability: List[str] = field(
        default_factory=list
    )


    # -----------------------------
    # Input/output modality
    #
    # Example:
    # [
    #   "text",
    #   "image"
    # ]
    # -----------------------------

    modality: List[str] = field(
        default_factory=list
    )


    # -----------------------------
    # FreeLLM detail page
    # -----------------------------

    detail_url: str = ""


    # -----------------------------
    # Recommended usage
    #
    # Example:
    # [
    #   "coding",
    #   "reasoning"
    # ]
    # -----------------------------

    best_for: List[str] = field(
        default_factory=list
    )


    def is_valid(self) -> bool:
        """
        Validate model.

        A valid model MUST have:
        - provider
        - model_id
        """

        return bool(
            self.provider
            and self.model_id
        )


    def normalized_provider(self) -> str:
        """
        Normalized provider name.
        """

        return (
            self.provider
            .strip()
            .lower()
        )


    def metadata(self) -> dict:
        """
        Metadata used by LiteLLM config.
        """

        return {
            "provider": self.provider,
            "score": self.score,
            "capability": self.capability,
            "context": self.context,
        }