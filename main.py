"""
把整个流程串起来：

抓取 FreeLLM Top200
过滤支持的 Provider（NVIDIA、OpenRouter、GitHub Models、ModelScope、SambaNova、Agnes、KILO）
解析每个模型详情页
构建 LogicalModel
自动生成 config.yaml
"""
from __future__ import annotations

import argparse

from builder import FallbackBuilder
from config_builder import LiteLLMConfigBuilder
from crawler import FreeLLMCrawler
from parser import ModelParser
from providers import SUPPORTED_PROVIDERS


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--top",
        type=int,
        default=200,
        help="Top N models from FreeLLM",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="config.generated.yaml",
    )

    args = parser.parse_args()

    crawler = FreeLLMCrawler()

    parser_obj = ModelParser()

    builder = FallbackBuilder()

    config_builder = LiteLLMConfigBuilder()

    print("== Step1 Fetch model list ==")

    models = crawler.fetch_top_models(args.top)

    print(f"Found {len(models)} models")

    models = [
        m
        for m in models
        if m.provider in SUPPORTED_PROVIDERS or m.provider == "Unknown"
    ]

    print(f"Supported providers : {len(models)}")

    provider_models = []

    print()

    print("== Step2 Parse detail pages ==")

    for idx, model in enumerate(models, start=1):

        print(
            f"[{idx}/{len(models)}] "
            f"{model.provider} "
            f"{model.name}"
        )

        try:

            result = parser_obj.parse(model)

            if result and result.provider in SUPPORTED_PROVIDERS:

                provider_models.append(result)

        except Exception as e:

            print(f"    FAIL {e}")

    print()

    print("== Step3 Build fallback ==")

    logical_models = builder.build(provider_models)

    logical_models = builder.expand_provider_keys(logical_models)

    capability_map = builder.build_capability_models(logical_models)

    print(f"Logical models : {len(logical_models)}")

    print()

    print("== Step4 Generate LiteLLM Config ==")

    config = config_builder.build(
        logical_models,
        capability_map=capability_map,
    )

    config_builder.save(
        config,
        args.output,
    )

    print()

    print("------------------------------------")
    print("DONE")
    print("------------------------------------")
    print(f"Provider Models : {len(provider_models)}")
    print(f"Logical Models  : {len(logical_models)}")
    print(f"Capability Models: {len(capability_map)}")
    print(f"Output          : {args.output}")


if __name__ == "__main__":

    main()
