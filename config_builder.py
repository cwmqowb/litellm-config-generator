"""
LiteLLM Config Builder

职责：

1. Logical Model 输出
2. Provider Deployment 输出
3. Router 配置生成
4. Capability / Metadata 输出

生成：

config.generated.yaml

可直接用于 LiteLLM Proxy
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import yaml

from models import LogicalModel, ProviderModel


class LiteLLMConfigBuilder:
    """
    将 LogicalModel 转换为 LiteLLM config.yaml
    """


    def build(
        self,
        logical_models: List[LogicalModel],
        capability_map: Dict[str, List[str]] | None = None,
    ) -> dict[str, Any]:

        config: dict[str, Any] = {}

        #
        # LiteLLM 全局配置
        #
        config["litellm_settings"] = {
            "drop_params": True,
            "set_verbose": False,
        }


        #
        # Router 配置
        #
        config["router_settings"] = {
            "routing_strategy": "simple-shuffle",
            "num_retries": 3,
            "timeout": 120,
        }


        config["model_list"] = []


        #
        # deployment 计数
        #
        deployment_counter = defaultdict(int)


        #
        # 记录同 logical model 的 deployment
        #
        logical_deployments = {}


        for logical in logical_models:

            deployments = []

            for provider_model in logical.providers:

                provider_key = (
                    provider_model.provider
                    .lower()
                    .replace(" ", "_")
                )

                counter_key = (
                    f"{logical.name}"
                    f"__{provider_key}"
                )

                deployment_counter[counter_key] += 1


                deployment_name = (
                    f"{logical.name}"
                    f"__{provider_key}"
                    f"_{deployment_counter[counter_key]}"
                )


                deployments.append(
                    deployment_name
                )


                config["model_list"].append(
                    self._build_model(
                        provider_model,
                        deployment_name,
                    )
                )


            logical_deployments[
                logical.name
            ] = deployments



        #
        # Router fallback
        #
        #
        # LiteLLM 推荐：
        #
        # 同一个 model_name 多 deployment
        #
        # 不创建 provider 污染模型名
        #
        fallbacks = []


        for logical_name in logical_deployments:

            #
            # 只有一个 deployment
            # 不需要 fallback
            #
            if (
                len(
                    logical_deployments[
                        logical_name
                    ]
                )
                <= 1
            ):
                continue


            #
            # 同 logical model fallback
            #
            fallbacks.append(
                {
                    logical_name:
                    [
                        logical_name
                    ]
                }
            )


        if fallbacks:
            config[
                "router_settings"
            ][
                "fallbacks"
            ] = fallbacks



        #
        # Capability 信息
        #
        if capability_map:

            config[
                "model_groups"
            ] = capability_map



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


        capability = model.capability


        if capability.chat:
            tags.append("chat")

        if capability.reasoning:
            tags.append("reasoning")

        if capability.coding:
            tags.append("coding")

        if capability.vision:
            tags.append("vision")

        if capability.embedding:
            tags.append("embedding")

        if capability.rerank:
            tags.append("rerank")

        if capability.image:
            tags.append("image")

        if capability.audio:
            tags.append("audio")

        if capability.tools:
            tags.append("tools")

        if capability.json_mode:
            tags.append("json")



        #
        # LiteLLM model 标准化
        #
        litellm_model = model.model_id


        if not (
            litellm_model.startswith(
                "openai/"
            )
            or litellm_model.startswith(
                "openrouter/"
            )
        ):

            litellm_model = (
                f"openai/{litellm_model}"
            )



        return {

            #
            # 关键：
            #
            # logical model 名称
            #
            "model_name":
                model.logical_name,


            "litellm_params": {

                "model":
                    litellm_model,

                "api_base":
                    model.api_base,

                "api_key":
                    (
                        f"os.environ/"
                        f"{model.api_key_env}"
                    ),

            },


            "model_info": {

                "deployment_name":
                    deployment_name,


                "provider":
                    model.provider,


                "logical_model":
                    model.logical_name,


                "context_window":
                    model.context_window,


                "max_output_tokens":
                    model.max_output_tokens,


                "tags":
                    tags,


            },

        }
