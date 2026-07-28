from __future__ import annotations

from collections import defaultdict

from providers import get_provider
from models import LogicalModel, ProviderModel


PROVIDER_PRIORITY = {
    "NVIDIA NIM": 10,
    "OpenRouter": 20,
    "GitHub Models": 30,
    "ModelScope": 40,
    "SambaNova": 50,
    "Agnes AI": 60,
    "Kilo Code": 70,
}


CAPABILITY_PRIORITY = [
    "reasoning",
    "coding",
    "chat",
    "vision",
    "image",
    "embedding",
    "rerank",
]


class FallbackBuilder:

    def build(self, provider_models):

        logical_groups = defaultdict(list)

        #
        # 品牌模型归组
        #
        for model in provider_models:
            logical_groups[model.logical_name].append(model)

        logical_models = []

        for logical_name in sorted(logical_groups.keys()):

            providers = logical_groups[logical_name]

            #
            # Provider 排序
            #
            providers.sort(
                key=lambda x: PROVIDER_PRIORITY.get(
                    x.provider,
                    999,
                )
            )

            logical_models.append(
                LogicalModel(
                    name=logical_name,
                    providers=providers,
                )
            )

        return logical_models

    def expand_provider_keys(
        self,
        logical_models,
    ):
        """
        NVIDIA_API_KEY_1
        NVIDIA_API_KEY_2

        展开为两个 deployment
        """

        expanded = []

        for logical in logical_models:

            deployments = []

            for model in logical.providers:

                provider = get_provider(
                    model.provider,
                )

                if provider is None:
                    continue

                for env in provider.api_key_envs:

                    clone = ProviderModel(
                        provider=model.provider,
                        model_id=model.model_id,
                        logical_name=model.logical_name,
                        api_base=model.api_base,
                        api_key_env=env,
                        capability=model.capability,
                        context_window=model.context_window,
                        max_output_tokens=model.max_output_tokens,
                    )

                    deployments.append(clone)

            logical.providers = deployments

            expanded.append(logical)

        return expanded

    def build_capability_models(
        self,
        logical_models,
    ):
        """
        自动生成：

        chat
        reasoning
        coding
        vision
        embedding

        """

        capability_models = defaultdict(list)

        for logical in logical_models:

            if not logical.providers:
                continue

            p = logical.providers[0]

            cap = p.capability

            if cap.chat:
                capability_models["chat"].append(logical.name)

            if cap.reasoning:
                capability_models["reasoning"].append(logical.name)

            if cap.coding:
                capability_models["coding"].append(logical.name)

            if cap.vision:
                capability_models["vision"].append(logical.name)

            if cap.embedding:
                capability_models["embedding"].append(logical.name)

            if getattr(cap, "rerank", False):
                capability_models["rerank"].append(logical.name)

        #
        # 排序
        #

        result = {}

        for capability, models in capability_models.items():

            result[capability] = sorted(
                models,
            )

        return result