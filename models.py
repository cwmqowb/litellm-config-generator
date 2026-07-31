"""
models.py

Unified model data structure.

All modules MUST use ModelInfo.

Pipeline:

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


Important:

LiteLLM model name MUST always use:

    model_id


model_id source:

    detail.html
        |
        v
    API Details
        |
        v
    Model ID


Never use:

- name
- title
- display_name

as LiteLLM model identifier.
"""

from __future__ import annotations


from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional



@dataclass
class ModelInfo:
    """
    Unified model information.

    This is the only model structure
    passed through the project.
    """


    # Provider name

    provider: str



    # Real provider model id

    # Example:
    # z-ai/glm-5.2

    model_id: str



    # Provider API endpoint

    api_base: Optional[str] = None



    # Ranking score

    # Note:
    # freellm models.html currently
    # does not expose score.
    #
    # Default 0.

    score: float = 0.0



    # Context window

    # Example:
    # 1.0M

    context: Optional[str] = None



    # Model capabilities

    # Example:
    # [
    #   "reasoning",
    #   "tool calling"
    # ]

    capability: List[str] = field(
        default_factory=list
    )



    # Input / output modality

    # Example:
    # [
    #   "text",
    #   "image"
    # ]

    modality: List[str] = field(
        default_factory=list
    )



    # Detail page url

    detail_url: str = ""



    # Recommended scenarios

    best_for: List[str] = field(
        default_factory=list
    )



    # Additional fields collected
    # from html pages.
    #
    # Examples:
    #
    # {
    #   "display_name":
    #       "z-ai/glm-5.2",
    #
    #   "released":
    #       "2026-01-15",
    #
    #   "status":
    #       "active",
    #
    #   "max_output":
    #       "8192"
    # }

    extra: Dict[str, Any] = field(
        default_factory=dict
    )



    def is_valid(self) -> bool:
        """
        Validate model.

        Required:

        provider
        model_id
        """

        return bool(
            self.provider
            and self.model_id
        )



    def metadata(self) -> Dict[str, Any]:
        """
        Metadata for LiteLLM config.
        """

        return {

            "provider":
                self.provider,


            "score":
                self.score,


            "capability":
                self.capability,


            "context":
                self.context,


            "best_for":
                self.best_for,


            "extra":
                self.extra,

        }



    def add_extra(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add extra metadata.
        """

        if value is not None:

            self.extra[key] = value