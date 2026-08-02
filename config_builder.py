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
# Metadata Helpers
# ============================================================

def _parse_context_tokens(value: Any) -> int | None:
    """
    Convert context strings such as 128K / 262K / 1.0M / 1.0G into token counts.
    The expected conversion keeps the same semantics as the examples:
        128K -> 131072
        262K -> 268288
        1.0M -> 1048576
    """

    if value in (None, ""):
        return None

    text = str(value).strip().lower()
    if not text:
        return None

    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([kmg])", text)
    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2)
    scale = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}[unit]
    return int(number * scale)


def _normalize_numeric(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    if not text:
        return value

    text_lower = text.lower()
    if text_lower.endswith("tok/s"):
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
        if not match:
            return value
        number = float(match.group(1))
        return int(number) if number.is_integer() else number

    if "/100" in text_lower:
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
        if not match:
            return value
        return float(match.group(1))

    if text_lower.endswith("k") or text_lower.endswith("m") or text_lower.endswith("g"):
        return _parse_context_tokens(text)

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if not match:
        return value
    number = float(match.group(1))
    return int(number) if number.is_integer() else number


def _normalize_benchmark(extra: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(extra, dict):
        return None

    benchmark = extra.get("benchmark")
    if not benchmark:
        return None

    normalized: Dict[str, Any] = {}

    if isinstance(benchmark, dict):
        raw_items = benchmark.items()
    else:
        raw_items = []
        for item in benchmark:
            if not isinstance(item, dict):
                continue
            raw_items.append((str(item.get("name", "")).strip().lower(), item.get("value")))

    for name, value in raw_items:
        if not name:
            continue
        if name == "context":
            normalized["context_tokens"] = _parse_context_tokens(value)
            continue

        normalized[name] = _normalize_numeric(value)

    if not normalized:
        return None

    return normalized


def _normalize_extra(extra: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not isinstance(extra, dict):
        return extra

    normalized = dict(extra)
    source = normalized.get("source")
    if source is not None:
        source_text = str(source).strip().lower()
        if source_text.endswith("models.html"):
            normalized["source"] = "freellm"

    benchmark = _normalize_benchmark(normalized)
    if benchmark:
        normalized["benchmark"] = benchmark

    return normalized


def _build_capability_type(model: Dict[str, Any], benchmark: Dict[str, Any] | None = None) -> List[str]:
    """
    Auto-classify capability_type from the model's capability metadata,
    benchmark, and context.
    """

    capability = [str(item).lower() for item in model.get("capability", [])]
    best_for = [str(item).lower() for item in model.get("best_for", [])]

    capability_types: List[str] = []

    def add_capability(name: str) -> None:
        if name not in capability_types:
            capability_types.append(name)

    add_capability("chat")

    if any(item == "reasoning" for item in capability):
        add_capability("reasoning")

    if any(item in {"tool calling", "tool-calling", "tools"} for item in capability):
        add_capability("agent")

    if any(item in {"vision", "image", "file attachments", "multimodal"} for item in capability + best_for):
        add_capability("vision")

    if benchmark and benchmark.get("coding", 0) >= 60:
        add_capability("coding")

    context_tokens = _parse_context_tokens(model.get("context"))
    if context_tokens is not None and context_tokens >= 500000:
        add_capability("long-context")

    ordered = ["chat", "reasoning", "coding", "agent", "vision", "long-context"]
    return [item for item in ordered if item in capability_types]


def build_metadata(model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preserve model information while enriching it with normalized display fields.
    """

    extra = _normalize_extra(model.get("extra"))
    benchmark = _normalize_benchmark(extra) if isinstance(extra, dict) else None
    context_tokens = _parse_context_tokens(model.get("context"))

    metadata = {
        "provider": model.get("provider"),
        "score": model.get("score", 0.0),
        "capability": model.get("capability", []),
        "capability_type": _build_capability_type(model, benchmark),
        "context": model.get("context"),
        "context_tokens": context_tokens,
        "best_for": model.get("best_for", []),
    }

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

    discovered_capability_types = []
    for model in models:
        for capability_type in _build_capability_type(model, _normalize_benchmark(model.get("extra")) if isinstance(model.get("extra"), dict) else None):
            if capability_type not in discovered_capability_types:
                discovered_capability_types.append(capability_type)

    for capability_type in discovered_capability_types:
        if capability_type == "chat":
            continue
        capability_fallbacks.append({capability_type: ["chat"]})

    # Capability aliases are exposed as logical route names, but the actual
    # provider model target inside litellm_params.model must remain the real
    # provider-side model ID to preserve direct provider-model semantics.
    capability_targets: Dict[str, str] = {}

    if alias_order:
        first_alias = alias_order[0]
        first_group = alias_groups[first_alias]
        if first_group:
            capability_targets["chat"] = first_group[0]["litellm_model"]

    for capability_type in discovered_capability_types:
        if capability_type in capability_targets:
            continue

        for alias in alias_order:
            group = alias_groups.get(alias, [])
            for item in group:
                model = item["model"]
                if capability_type in _build_capability_type(model, _normalize_benchmark(model.get("extra")) if isinstance(model.get("extra"), dict) else None):
                    capability_targets[capability_type] = item["litellm_model"]
                    break
            if capability_type in capability_targets:
                break

    for capability_type in discovered_capability_types:
        target_model = capability_targets.get(capability_type)
        if not target_model:
            continue
        model_list.append(
            {
                "model_name": capability_type,
                "litellm_params": {
                    "model": target_model,
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
