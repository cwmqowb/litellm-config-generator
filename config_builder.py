"""
config_builder.py

Build LiteLLM configuration.

Responsibility:

ModelInfo
    |
    v
LiteLLM yaml


Responsible for:

- logical model grouping
- provider model naming
- metadata generation
- yaml output


Not responsible for:

- html parsing
- model crawling
- provider discovery
- validation
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

import yaml

from providers import get_provider, normalize_provider_name

logger = logging.getLogger(__name__)


# ============================================================
# Logical Model Detection
# ============================================================

def detect_logical_models(model: Dict[str, Any]) -> List[str]:
    """
    Detect the logical model names that a provider model should be
    registered under.

    Rule:
    - every model is at least chat-capable
    - reasoning adds reasoning
    - vision/image/multimodal adds vision
    """

    capability = model.get("capability", [])
    if not capability:
        capability = []
    capability = [str(x).lower() for x in capability]

    best_for = model.get("best_for", [])
    best_for = [str(x).lower() for x in best_for]

    logical_names = ["chat"]

    vision_keywords = [
        "vision",
        "image",
        "file attachments",
        "multimodal",
    ]
    if any(item in vision_keywords for item in capability + best_for):
        logical_names.append("vision")

    if any(item == "reasoning" for item in capability):
        logical_names.append("reasoning")

    unique = []
    for name in logical_names:
        if name not in unique:
            unique.append(name)
    return unique


# ============================================================
# LiteLLM model name
# ============================================================

def build_litellm_model_name(model: Dict[str, Any]) -> str:
    """
    Preserve the provider-side model ID exactly as it appears in the detail page.
    """

    name = model.get("model_id") or model.get("name") or ""
    if not name:
        return ""
    return str(name)


def normalize_specific_model_name(model: Dict[str, Any]) -> str:
    """
    Normalize provider-side model IDs into a stable concrete alias that can be
    used as a direct LiteLLM routing name.

    Example:
        z-ai/glm-5.2 -> glm-5.2
        minimax/minimax-m3 -> minimax-m3
    """

    name = model.get("model_id") or model.get("name") or ""
    if not name:
        return ""

    name = str(name).strip().lower()
    name = re.sub(r":(free|beta|extended|nitro|online|thought|thinking)$", "", name)
    name = re.sub(r"@.*$", "", name)

    prefixes = [
        "nvidia/",
        "google/",
        "meta/",
        "meta-llama/",
        "qwen/",
        "moonshotai/",
        "z-ai/",
        "zai/",
        "deepseek-ai/",
        "deepseek/",
        "mistralai/",
        "cohere/",
        "openai/",
        "openrouter/",
        "microsoft/",
        "writer/",
        "ibm/",
        "baai/",
        "bytedance/",
        "01-ai/",
        "baichuan-inc/",
    ]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    parts = [part for part in name.split("/") if part]
    if parts:
        name = parts[-1]

    return name


# ============================================================
# Metadata
# ============================================================

def build_metadata(model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preserve model information.
    """

    metadata = {
        "provider": model.get("provider"),
        "score": model.get("score", 0.0),
        "capability": model.get("capability", []),
        "context": model.get("context"),
        "best_for": model.get("best_for", []),
    }

    extra = model.get("extra")
    if extra:
        metadata["extra"] = extra

    return metadata


# ============================================================
# Build Config
# ============================================================

def build_config(models: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build the final three-layer LiteLLM routing structure:

    1. concrete aliases such as glm-5.2 / minimax-m3
    2. provider-key deployment entries nested under each concrete alias
    3. capability aliases such as chat / reasoning with fallback order
    """

    alias_groups: Dict[str, List[Dict[str, Any]]] = {}

    for model in models:
        provider = normalize_provider_name(model.get("provider", ""))
        provider_info = get_provider(provider)
        if not provider_info:
            logger.warning("skip unsupported provider: %s", provider)
            continue

        litellm_model = build_litellm_model_name(model)
        if not litellm_model:
            logger.warning("skip model without id: %s", model)
            continue

        alias = normalize_specific_model_name(model)
        if not alias:
            continue

        extra = model.get("extra") or {}
        position = extra.get("position") if isinstance(extra, dict) else None
        if position is None:
            position = len(alias_groups.get(alias, [])) + 1

        alias_groups.setdefault(alias, []).append(
            {
                "provider": provider,
                "provider_info": provider_info,
                "position": position,
                "model": model,
                "litellm_model": litellm_model,
            }
        )

    alias_order = sorted(
        alias_groups.keys(),
        key=lambda alias: min(item["position"] for item in alias_groups[alias]),
    )

    model_list = []
    for alias in alias_order:
        group = alias_groups[alias]
        group.sort(
            key=lambda item: (
                item["position"],
                item["provider"],
                item["provider_info"].api_key_envs,
            )
        )

        for item in group:
            provider_info = item["provider_info"]
            api_key_envs = provider_info.api_key_envs or [provider_info.api_key_env]
            for api_key_env in api_key_envs:
                entry = {
                    "model_name": alias,
                    "litellm_params": {
                        "model": item["litellm_model"],
                        "api_base": provider_info.api_base,
                    },
                    "metadata": build_metadata(item["model"]),
                }
                if api_key_env:
                    entry["litellm_params"]["api_key"] = f"os.environ/{api_key_env}"
                model_list.append(entry)

    capability_fallbacks = []
    if alias_order:
        capability_fallbacks.append({"chat": alias_order})

    reasoning_aliases = []
    for model in models:
        if "reasoning" in [str(x).lower() for x in model.get("capability", [])]:
            alias = normalize_specific_model_name(model)
            if alias and alias not in reasoning_aliases:
                reasoning_aliases.append(alias)
    if reasoning_aliases:
        capability_fallbacks.append({"reasoning": ["chat"]})

    # Capability aliases are exposed as logical route names, but the actual
    # provider model target inside litellm_params.model must remain the real
    # provider-side model ID to preserve direct provider-model semantics.
    chat_target_model = None
    reasoning_target_model = None
    if alias_order:
        first_alias = alias_order[0]
        first_group = alias_groups[first_alias]
        if first_group:
            chat_target_model = first_group[0]["litellm_model"]

    if alias_order and chat_target_model:
        model_list.append(
            {
                "model_name": "chat",
                "litellm_params": {
                    "model": chat_target_model,
                },
                "metadata": {},
            }
        )

    if reasoning_aliases:
        reasoning_target_alias = reasoning_aliases[0]
        reasoning_target_group = alias_groups.get(reasoning_target_alias, [])
        if reasoning_target_group:
            reasoning_target_model = reasoning_target_group[0]["litellm_model"]

    if reasoning_aliases and reasoning_target_model:
        model_list.append(
            {
                "model_name": "reasoning",
                "litellm_params": {
                    "model": reasoning_target_model,
                },
                "metadata": {},
            }
        )

    return {
        "router_settings": {
            "routing_strategy": "simple-shuffle",
            "num_retries": 2,
            "timeout": 60,
            "fallbacks": capability_fallbacks,
        },
        "litellm_settings": {
            "drop_params": True,
        },
        "model_list": model_list,
    }


# ============================================================
# Save YAML
# ============================================================

def save_config(config: Dict[str, Any], output: str):
    """
    Save yaml file.
    """

    with open(output, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    logger.info("saved config: %s", output)
