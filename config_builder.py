"""
LiteLLM Config Builder

职责:

1. Logical Model 输出
2. Provider Deployment 输出
3. Router 配置生成
4. Capability / Metadata 输出

生成:

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
        # 记录 logical model deployment
        #
        logical_deployments: dict[str, list[str]] = {}

        deployment_counter = defaultdict(int)


        #
        # 生成 deployment
        #
        for logical in logical_models:

            deployments = []


            #
            # 按 score 排序
            #
            providers = sorted(
                logical.providers,
                key=lambda x: getattr(
                    x,
                    "score",
                    0
                ),
                reverse=True,
            )


            for provider_model in providers:


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
        # fallback 配置
        #
        fallbacks = []


        for logical_name, deployments in logical_deployments.items():


            if len(deployments) <= 1:
                continue


            #
            # 第一个为主模型
            # 后续为备用
            #
            primary = deployments[0]

            backups = deployments[1:]


            fallbacks.append(
                {
                    primary:
                    backups
                }
            )


        if fallbacks:

            config[
                "router_settings"
            ][
                "fallbacks"
            ] = fallbacks



        #
        # capability 信息
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
    ) -> dict[str, Any]:


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
        # LiteLLM model name
        #
        litellm_model = self._normalize_model_name(
            model
        )


        return {


            #
            # logical model
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


                "original_model":
                    model.model_id,


                #
                # 排序评分
                #
                "score":
                    getattr(
                        model,
                        "score",
                        0
                    ),


                "context_window":
                    getattr(
                        model,
                        "context_window",
                        None
                    ),


                "max_output_tokens":
                    getattr(
                        model,
                        "max_output_tokens",
                        None
                    ),


                "tags":
                    tags,

            },

        }



    def _normalize_model_name(
        self,
        model: ProviderModel,
    ) -> str:


        model_id = model.model_id


        #
        # 已经有 provider 前缀
        #
        if "/" in model_id:

            return model_id



        provider = (
            model.provider
            .lower()
        )


        #
        # NVIDIA NIM
        #
        if "nvidia" in provider:

            return (
                f"nvidia/{model_id}"
            )


        #
        # OpenRouter
        #
        if "openrouter" in provider:

            return (
                f"openrouter/{model_id}"
            )


        #
        # 其他 OpenAI Compatible provider
        #
        return (
            f"openai/{model_id}"
        )
