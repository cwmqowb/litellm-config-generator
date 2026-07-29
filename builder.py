"""
Builder

职责：

1. 品牌模型聚合
2. Provider Fallback 排序
3. 多 API Key Deployment 展开
4. 自动生成 Capability Logical Model
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from models import (
    BuildResult,
    CapabilityGroup,
    LogicalModel,
    ProviderModel,
)

from providers import (
    PROVIDERS,
    provider_priority,
)


class FallbackBuilder:
    """
    构建 Logical Model

    输入：

        ProviderModel

    输出：

        LogicalModel

    例如：

        glm-5.2

            NVIDIA

            OpenRouter

            GitHub Models

    """

    def __init__(self):

        self.capability_groups: Dict[
            str,
            CapabilityGroup,
        ] = {}

    # -------------------------------------------------
    # Logical Model
    # -------------------------------------------------

    def _group_models(
        self,
        provider_models: List[ProviderModel],
    ) -> Dict[str, List[ProviderModel]]:

        groups = defaultdict(list)

        for model in provider_models:

            groups[
                model.logical_name
            ].append(model)

        return groups

    # -------------------------------------------------
    # Provider 排序
    # -------------------------------------------------

    def _sort_provider_models(
        self,
        provider_models: List[ProviderModel],
    ):

        provider_models.sort(
            key=lambda x: provider_priority(
                x.provider,
            )
        )

    # -------------------------------------------------
    # 多 API Key 展开
    # -------------------------------------------------

    def _expand_api_keys(
        self,
        provider_models: List[ProviderModel],
    ) -> List[ProviderModel]:

        expanded = []

        for model in provider_models:

            provider_cfg = PROVIDERS.get(
                model.provider,
            )

            #
            # Provider 未配置
            #

            if provider_cfg is None:

                expanded.append(model)

                continue

            api_keys = provider_cfg.api_key_envs

            #
            # 未配置多个 Key
            #

            if not api_keys:

                expanded.append(model)

                continue

            #
            # 每个 API Key 一个 Deployment
            #

            for idx, env in enumerate(api_keys):

                deployment = ProviderModel(

                    provider=model.provider,

                    logical_name=model.logical_name,

                    model_id=model.model_id,

                    api_base=model.api_base,

                    api_format=model.api_format,

                    api_key_env=env,

                    deployment_name=(
                        f"{model.logical_name}"
                        f"__"
                        f"{model.provider.lower().replace(' ','_')}"
                        f"_{idx+1}"
                    ),

                    context_window=model.context_window,

                    max_output_tokens=model.max_output_tokens,

                    capability=model.capability,

                    raw_tags=list(model.raw_tags),
                )

                expanded.append(
                    deployment
                )

        return expanded

    # -------------------------------------------------
    # Build
    # -------------------------------------------------

    def build(
        self,
        provider_models: List[
            ProviderModel
        ],
    ) -> BuildResult:

        #
        # Deployment 展开
        #

        provider_models = self._expand_api_keys(
            provider_models,
        )

        #
        # 品牌模型聚合
        #

        groups = self._group_models(
            provider_models,
        )

        result = BuildResult()

        for logical_name in sorted(
            groups.keys()
        ):

            deployments = groups[
                logical_name
            ]

            self._sort_provider_models(
                deployments,
            )

            logical = LogicalModel(
                name=logical_name,
            )

            #
            # Provider Fallback
            #

            for deployment in deployments:

                logical.add_provider(
                    deployment
                )

            result.logical_models[
                logical_name
            ] = logical

            #
            # Capability Group
            #

            capability = logical.capability

            enabled = capability.enabled()

            for capability_name in enabled:

                group = result.capability_groups.get(
                    capability_name,
                )

                if group is None:

                    group = CapabilityGroup(
                        name=capability_name,
                    )

                    result.capability_groups[
                        capability_name
                    ] = group

                if (
                    logical.name
                    not in group.models
                ):

                    group.models.append(
                        logical.name
                    )

        #
        # 每个 Capability 按名称排序，保证输出稳定
        #

        for group in result.capability_groups.values():

            group.models.sort()

        return result


#
# ---------------------------------------------------------
# 兼容旧 Builder 接口
# ---------------------------------------------------------
#

def build(
    provider_models: List[ProviderModel],
) -> BuildResult:

    """
    历史接口

    builder.build(...)
    """

    return FallbackBuilder().build(
        provider_models,
    )


def build_logical_models(
    provider_models: List[
        ProviderModel
    ],
) -> Dict[str, LogicalModel]:

    """
    兼容旧版本调用。

    返回：

        {
            "glm-5.2": LogicalModel(...),
            "kimi-k2": LogicalModel(...)
        }
    """

    result = build(
        provider_models,
    )

    return result.logical_models


def build_capability_groups(
    provider_models: List[
        ProviderModel
    ],
) -> Dict[str, CapabilityGroup]:

    """
    返回：

        chat
            glm-5.2
            kimi-k2

        reasoning
            glm-5.2
            qwen3

        coding
            kimi-k2
            qwen3-coder
    """

    result = build(
        provider_models,
    )

    return result.capability_groups


#
# ---------------------------------------------------------
# 调试入口
# ---------------------------------------------------------
#

if __name__ == "__main__":

    from crawler import crawl_models
    from models import ProviderModel

    raw_models = crawl_models()

    provider_models = []

    for item in raw_models:

        provider_models.append(

            ProviderModel(

                provider=item.get(
                    "provider",
                    "",
                ),

                logical_name=item.get(
                    "logical_name",
                    "",
                ),

                model_id=item.get(
                    "model_id",
                    "",
                ),

                api_base=item.get(
                    "base_url",
                    "",
                ),

                api_format=item.get(
                    "api_format",
                    "openai",
                ),

                #
                # build() 会自动展开多个 API Key
                #
                api_key_env="",

                deployment_name="",

                context_window=item.get(
                    "context_window",
                ),

                max_output_tokens=item.get(
                    "max_output_tokens",
                ),

                capability=item.get(
                    "capability",
                ),

                raw_tags=item.get(
                    "raw_tags",
                    [],
                ),
            )
        )

    result = build(
        provider_models,
    )

    print()

    print("=" * 80)

    print("Logical Models")

    print("=" * 80)

    for logical in result.logical_models.values():

        print()

        print(logical.name)

        for deployment in logical.providers:

            print(
                "   ",
                deployment.provider,
                deployment.model_id,
                deployment.api_key_env,
            )

    print()

    print("=" * 80)

    print("Capability Groups")

    print("=" * 80)

    for name in sorted(
        result.capability_groups.keys()
    ):

        print()

        print(name)

        for model in result.capability_groups[
            name
        ].models:

            print(
                "   ",
                model,
            )
