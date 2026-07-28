"""
输出真正可直接使用的 config.yaml，包括：

model_list
router_settings
fallbacks
model_info
tags
capabilities
"""
from __future__ import annotations

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
    ) -> dict[str, Any]:

        config: dict[str, Any] = {}

        config["model_list"] = []

        #
        # router_settings
        #
        config["router_settings"] = {
            "routing_strategy": "simple-shuffle",
            "num_retries": 0,
            "timeout": 120,
        }

        #
        # fallbacks
        #
        fallbacks: list[dict] = []

        for logical in logical_models:

            aliases = []

            for provider_model in logical.providers:

                alias = self._deployment_name(
                    provider_model
                )

                aliases.append(alias)

                config["model_list"].append(
                    self._build_model(
                        provider_model,
                        alias,
                    )
                )

            if len(aliases) > 1:

                fallbacks.append(
                    {
                        logical.name: aliases
                    }
                )

        if fallbacks:
            config["router_settings"][
                "fallbacks"
            ] = fallbacks

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

    def _deployment_name(
        self,
        model: ProviderModel,
    ):

        return (
            f"{model.logical_name}"
            f"__"
            f"{model.provider.lower().replace(' ','_')}"
        )

    def _build_model(
        self,
        model: ProviderModel,
        alias: str,
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

        if model.capability.image:
            tags.append("image")

        if model.capability.audio:
            tags.append("audio")

        if model.capability.tools:
            tags.append("tools")

        if model.capability.json_mode:
            tags.append("json")

        item = {

            "model_name": alias,

            "litellm_params": {

                "model": model.model_id,

                "api_base": model.api_base,

                "api_key": f"os.environ/{model.api_key_env}",

            },

            "model_info": {

                "provider": model.provider,

                "logical_model": model.logical_name,

                "context_window": model.context_window,

                "max_output_tokens": model.max_output_tokens,

                "tags": tags,

            },

        }

        return item
