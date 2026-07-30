"""
LiteLLM Config Builder

职责:

1. Logical Model 输出
2. Provider Model Deployment 输出
3. Router fallback 配置生成
4. Capability / Metadata 输出

输入:

LogicalModel
    |
    └── models: List[ModelInfo]


输出:

config.generated.yaml

可直接用于 LiteLLM Proxy
"""

from __future__ import annotations


from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


import yaml


from models import (
    LogicalModel,
    ModelInfo,
)



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

            "routing_strategy":
                "simple-shuffle",

            "num_retries":
                3,

            "timeout":
                120,

        }



        config["model_list"] = []



        #
        # 保存 logical model 对应 deployment
        #
        logical_deployments: dict[
            str,
            list[str]
        ] = {}


        deployment_counter = defaultdict(int)



        #
        # 生成 deployment
        #
        for logical in logical_models:


            deployments = []


            #
            # 当前 LogicalModel 下
            # 的物理模型列表
            #
            models = sorted(

                logical.models,

                key=lambda x:
                    getattr(
                        x,
                        "score",
                        0
                    ),

                reverse=True,

            )



            for model in models:


                provider_key = (

                    model.provider

                    .lower()

                    .replace(
                        " ",
                        "_"
                    )

                )



                counter_key = (

                    f"{logical.name}"

                    f"__{provider_key}"

                )



                deployment_counter[counter_key] += 1



                deployment_name = (

                    f"{logical.name}"

                    f"__{provider_key}"

                    f"_"
                    f"{deployment_counter[counter_key]}"

                )



                deployments.append(
                    deployment_name
                )



                config["model_list"].append(

                    self._build_model(

                        logical,

                        model,

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
            # score最高作为主模型
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
        logical: LogicalModel,
        model: ModelInfo,
        deployment_name: str,
    ) -> dict[str, Any]:


        tags = []



        capability = (
            model.capabilities
        )



        #
        # capability tags
        #
        if capability.chat:

            tags.append(
                "chat"
            )


        if capability.reasoning:

            tags.append(
                "reasoning"
            )


        if capability.coding:

            tags.append(
                "coding"
            )


        if capability.vision:

            tags.append(
                "vision"
            )


        if capability.embedding:

            tags.append(
                "embedding"
            )


        if capability.rerank:

            tags.append(
                "rerank"
            )


        if capability.image:

            tags.append(
                "image"
            )


        if capability.audio:

            tags.append(
                "audio"
            )


        if capability.tools:

            tags.append(
                "tools"
            )


        if capability.json_mode:

            tags.append(
                "json"
            )




        litellm_model = (

            self._normalize_model_name(

                model

            )

        )



        return {


            #
            # LiteLLM logical model
            #
            "model_name":

                logical.name,



            "litellm_params": {


                "model":

                    litellm_model,



                "api_base":

                    model.api_base,



                "api_key":

                    (

                        f"os.environ/"

                        f"{model.api_key_env}"

                    )

                    if model.api_key_env

                    else None,

            },



            "model_info": {


                "deployment_name":

                    deployment_name,



                "provider":

                    model.provider,



                "logical_model":

                    logical.name,



                "original_model":

                    model.model_id,



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
        model: ModelInfo,
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
        # NVIDIA
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
        # ModelScope
        #
        if "modelscope" in provider:


            return (

                f"modelscope/{model_id}"

            )



        #
        # GitHub Models
        #
        if "github" in provider:


            return (

                f"github/{model_id}"

            )



        #
        # 默认 OpenAI Compatible
        #
        return (

            f"openai/{model_id}"

        )
