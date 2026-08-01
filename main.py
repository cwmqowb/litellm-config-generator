"""
main.py

Application entry.


Pipeline:


models.html
        |
        v
crawler.py

        |
        |
        v

raw model list


        |
        v

detail_parser.py

        |
        v

ModelInfo


        |
        v

normalizer.py


        |
        v

config_builder.py


        |
        v

config.generated.yaml



Usage:

python main.py --top 100

"""


from __future__ import annotations


import argparse
import logging

from typing import List


from crawler import crawl_models


from detail_parser import (
    parse_details as parse_detail_pages,
)


from normalizer import (
    normalize_models,
)


from config_builder import (
    build_config,
    save_config,
)

from providers import (
    get_provider,
    normalize_provider_name,
)

from models import ModelInfo


logger = logging.getLogger(__name__)


# ============================================================
# Logging
# ============================================================


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )


# ============================================================
# Arguments
# ============================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate LiteLLM config from FreeLLM models"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="number of models to crawl",
    )
    parser.add_argument(
        "--output",
        default="config.generated.yaml",
        help="output yaml file",
    )
    return parser.parse_args()


# ============================================================
# Provider filtering
# ============================================================


def filter_supported_models(raw_models: List[dict]) -> List[dict]:
    """
    Keep only models whose provider is currently supported by the
    registry in providers.py.
    """
    result = []

    for model in raw_models:
        provider_name = normalize_provider_name(model.get("provider", ""))
        if not provider_name:
            continue

        if get_provider(provider_name) is None:
            logger.info(
                "skip unsupported provider before detail fetch: %s",
                provider_name,
            )
            continue

        result.append(model)

    return result


# ============================================================
# Detail processing
# ============================================================


def parse_details(raw_models: List[dict]) -> List[ModelInfo]:
    """
    Parse detail pages using the current parser API.
    """
    return parse_detail_pages(raw_models)


# ============================================================
# Main pipeline
# ============================================================


def generate_config(top: int, output: str):
    """
    Complete generation flow.
    """

    logger.info("crawl top %s models", top)
    raw_models = crawl_models(top_k=top)
    logger.info("crawler models: %s", len(raw_models))

    if not raw_models:
        raise RuntimeError("No models extracted from models.html")

    raw_models = filter_supported_models(raw_models)
    logger.info("supported provider models after filter: %s", len(raw_models))

    if not raw_models:
        raise RuntimeError("No supported models after provider filtering")

    detail_models = parse_details(raw_models)
    logger.info("detail parsed models: %s", len(detail_models))

    if not detail_models:
        raise RuntimeError("No models parsed from detail pages")

    normalized = normalize_models(
        [model.__dict__ for model in detail_models]
    )
    logger.info("normalized models: %s", len(normalized))

    if not normalized:
        raise RuntimeError("No valid models after normalization")

    config = build_config(
        [model.__dict__ for model in normalized]
    )
    if not config.get("model_list"):
        raise RuntimeError("No models generated into config")

    save_config(config, output)
    logger.info("config generated successfully")


# ============================================================
# Entry
# ============================================================


def main():
    setup_logging()
    args = parse_args()
    generate_config(top=args.top, output=args.output)


if __name__ == "__main__":
    main()




if __name__ == "__main__":

    main()