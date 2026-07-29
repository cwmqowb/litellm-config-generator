"""
输出真正可直接使用的 config.generated.yaml，包括：

model_list
router_settings
litellm_settings
fallbacks
model_info
tags
capabilities
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from models import LogicalModel, ProviderModel


class LiteLLMConfigBuilder:
    """
    将 LogicalModel 转换为 LiteLLM config.yaml
    """

    def build(
        self,
        logical_models: list[LogicalModel],
        capability_map: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:

        config: dict[str, Any] = {}

        config["litellm_settings"] = {
            "drop_params": True,
            "set_verbose": False,
        }

        config["model_list"] = []

        config["router_settings"] = {
            "routing_strategy": "simple-shuffle",
            "num_retries": 3,
            "timeout": 120,
        }

        fallbacks: list[dict[str, list[str]]] = []
        dep_counters: dict[str, int] = defaultdict(int)

        for logical in logical_models:
            for provider_model in logical.providers:
                dep_key = (
                    f"{logical.name}-"
                    f"{provider_model.provider.lower().replace(' ', '-')}"
                )
                dep_counters[dep_key] += 1
                deployment_name = f"{dep_key}-{dep_counters[dep_key]}"

                config["model_list"].append(
                    self._build_model(
                        provider_model,
                        deployment_name,
                    )
                )

        if capability_map:
            for cap, target_models in capability_map.items():
                if target_models:
                    fallbacks.append({cap: target_models})

        for logical in logical_models:
            other_models = [m.name for m in logical_models if m.name != logical.name]
            if other_models:
                fallbacks.append({logical.name: other_models[:3]})

        if fallbacks:
            config["router_settings"]["fallbacks"] = fallbacks

        return config

    def save(
        self,
        config: dict,
        output: str | Path,
    ):

        output = Path(output)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as f:

            yaml.safe_dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
            )

    def _build_model(
        self,
        model: ProviderModel,
        deployment_name: str,
    ):

        tags = []

        if model.capability.chat:
            tags.append("chat")
        if model.capability.reasoning:
            tags.append("reasoning")
        if model.capability.coding:
            tags.append("coding")
        if model.capability.vision:
            tags.append("vision")
        if model.capability.embedding:
            tags.append("embedding")
        if model.capability.rerank:
            tags.append("rerank")
        if model.capability.image:
            tags.append("image")
        if model.capability.audio:
            tags.append("audio")
        if model.capability.tools:
            tags.append("tools")
        if model.capability.json_mode:
            tags.append("json")

        litellm_model = model.model_id
        if not litellm_model.startswith("openai/") and not litellm_model.startswith("openrouter/"):
            litellm_model = f"openai/{litellm_model}"

        item = {
            "model_name": model.logical_name,
            "litellm_params": {
                "model": litellm_model,
                "api_base": model.api_base,
                "api_key": f"os.environ/{model.api_key_env}",
            },
            "model_info": {
                "deployment_name": deployment_name,
                "provider": model.provider,
                "logical_model": model.logical_name,
                "context_window": model.context_window,
                "max_output_tokens": model.max_output_tokens,
                "tags": tags,
            },
        }

        return item
