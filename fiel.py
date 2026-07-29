import os
import zipfile

# 定义所有修改后的文件内容
FILES = {
    "models.py": '''from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FreeLLMModel:
    """
    freellm Top200 页面的一条模型记录
    """

    provider: str
    name: str
    detail_url: str


@dataclass
class ModelCapability:
    chat: bool = False
    vision: bool = False
    reasoning: bool = False
    coding: bool = False
    embedding: bool = False
    rerank: bool = False
    image: bool = False
    audio: bool = False
    tools: bool = False
    json_mode: bool = False


@dataclass
class ProviderModel:
    """
    一个 Provider 对某模型的配置
    """

    provider: str

    logical_name: str

    model_id: str

    api_base: str

    api_format: str

    api_key_env: str

    context_window: Optional[int] = None

    max_output_tokens: Optional[int] = None

    capability: ModelCapability = field(
        default_factory=ModelCapability
    )


@dataclass
class LogicalModel:
    """
    LiteLLM 的逻辑模型
    """

    name: str

    providers: List[ProviderModel] = field(
        default_factory=list
    )
''',

    "providers.py": '''"""Provider 配置"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProviderConfig:
    name: str

    api_base: str

    api_key_envs: List[str]

    api_format: str = "openai"

    extra_headers: Optional[dict] = None


PROVIDERS = {

    "NVIDIA NIM": ProviderConfig(
        name="NVIDIA NIM",
        api_base="https://integrate.api.nvidia.com/v1",
        api_key_envs=[
            "NVIDIA_API_KEY_1",
            "NVIDIA_API_KEY_2",
        ],
    ),

    "OpenRouter": ProviderConfig(
        name="OpenRouter",
        api_base="https://openrouter.ai/api/v1",
        api_key_envs=[
            "OPENROUTER_API_KEY",
        ],
    ),

    "GitHub Models": ProviderConfig(
        name="GitHub Models",
        api_base="https://models.github.ai/inference",
        api_key_envs=[
            "GITHUB_MODELS_API_KEY",
        ],
    ),

    "ModelScope": ProviderConfig(
        name="ModelScope",
        api_base="https://api-inference.modelscope.cn/v1",
        api_key_envs=[
            "MODELSCOPE_API_KEY",
        ],
    ),

    "SambaNova": ProviderConfig(
        name="SambaNova",
        api_base="https://api.sambanova.ai/v1",
        api_key_envs=[
            "SAMBANOVA_API_KEY",
        ],
    ),

    "Agnes AI": ProviderConfig(
        name="Agnes AI",
        api_base="https://apihub.agnes-ai.com/v1",
        api_key_envs=[
            "AGNES_API_KEY",
        ],
    ),

    "Kilo Code": ProviderConfig(
        name="Kilo Code",
        api_base="https://api.kiloai.com/v1",
        api_key_envs=[
            "KILO_API_KEY",
        ],
    ),
}


SUPPORTED_PROVIDERS = set(PROVIDERS.keys())


def get_provider(name: str) -> ProviderConfig | None:
    if not name:
        return None
    if name in PROVIDERS:
        return PROVIDERS[name]

    name_lower = name.strip().lower()
    for k, v in PROVIDERS.items():
        if k.lower() == name_lower:
            return v
    for k, v in PROVIDERS.items():
        if k.lower() in name_lower or name_lower in k.lower():
            return v
    return None
''',

    "normalizer.py": '''"""
归一化逻辑，确保同品牌模型归并为一个逻辑模型名称：
z-ai/glm-5.2 -> glm-5.2
openrouter/nvidia/nemotron-3-ultra:free -> nemotron-3-ultra
Qwen/Qwen3-235B-Instruct -> qwen3-235b
"""
from __future__ import annotations

import re


class LogicalModelNormalizer:
    """
    将 Provider 的 Model ID 或名称归一化成 Logical Model
    """

    def normalize(self, model_id: str) -> str:
        if not model_id:
            return "unknown-model"

        name = model_id.strip().lower()

        # 清除后缀 tag
        name = re.sub(r":(free|beta|extended|nitro|online|thought|thinking)$", "", name)
        name = re.sub(r"@.*$", "", name)

        # 去除 common provider 前缀
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

        changed = True
        while changed:
            changed = False
            for p in prefixes:
                if name.startswith(p):
                    name = name[len(p):]
                    changed = True

        # GLM 品牌
        m = re.search(r"glm[-_]?([0-9.]+(?:[-_]flash|[-_]air|[-_]pro|[-_]coding)?)", name)
        if m:
            v = m.group(1).replace("_", "-")
            return f"glm-{v}"

        # Gemini 品牌
        m = re.search(r"gemini[-_]?([0-9.]+(?:[-_][a-z0-9-]+)?)", name)
        if m:
            v = m.group(1).replace("_", "-")
            return f"gemini-{v}"

        # Qwen 品牌
        m = re.search(r"qwen([0-9.]*[-_]?[a-z0-9-]+)", name)
        if m:
            v = m.group(1).replace("_", "-")
            v = re.sub(r"-(instruct|chat)$", "", v)
            return f"qwen{v}"

        # DeepSeek 品牌
        m = re.search(r"deepseek[-_]?([a-z0-9.-]+)", name)
        if m:
            v = m.group(1).replace("_", "-")
            v = re.sub(r"-(instruct|chat)$", "", v)
            return f"deepseek-{v}"

        # Kimi 品牌
        m = re.search(r"kimi[-_]?([a-z0-9.-]+)", name)
        if m:
            v = m.group(1).replace("_", "-")
            return f"kimi-{v}"

        # MiniMax 品牌
        m = re.search(r"minimax[-_]?([a-z0-9.-]+)", name)
        if m:
            v = m.group(1).replace("_", "-")
            return f"minimax-{v}"

        # Llama 品牌
        m = re.search(r"llama[-_]?([0-9.]*[-_]?[a-z0-9-]+)", name)
        if m:
            v = m.group(1).replace("_", "-")
            v = re.sub(r"-(instruct|chat)$", "", v)
            return f"llama-{v}"

        # 通用清洗
        name = re.sub(r"-(instruct|it|chat)$", "", name)
        name = re.sub(r"[/\s]+", "-", name)
        name = re.sub(r"-+", "-", name).strip("-")

        return name
''',

    "parser.py": '''"""
解析每个模型详情页，提取：
Base URL
Model ID
API Format
Context Window
Max Output Tokens
Capabilities
转换为 ProviderModel 对象。
"""
from __future__ import annotations

import re
from typing import Optional

import requests
from bs4 import BeautifulSoup

from models import (
    FreeLLMModel,
    ModelCapability,
    ProviderModel,
)
from normalizer import LogicalModelNormalizer
from providers import get_provider


class ModelParser:
    """
    解析 freellm 模型详情页
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )
        self.normalizer = LogicalModelNormalizer()

    def parse(
        self,
        model: FreeLLMModel,
    ) -> Optional[ProviderModel]:

        try:
            r = self.session.get(
                model.detail_url,
                timeout=30,
            )
            r.raise_for_status()
        except Exception as e:
            print(f"    [WARN] Failed to fetch {model.detail_url}: {e}")
            return None

        soup = BeautifulSoup(
            r.text,
            "lxml",
        )

        page = soup.get_text(
            "\\n",
            strip=True,
        )

        provider = get_provider(model.provider)
        if provider is None:
            p_text = self._find_field(page, soup, ["Provider"])
            if p_text:
                provider = get_provider(p_text)
            if provider is None:
                return None

        model_id = self._find_field(
            page,
            soup,
            [
                "Model ID",
                "Model",
            ],
        )

        if not model_id:
            model_id = model.name

        api_format = self._find_field(
            page,
            soup,
            [
                "API Format",
                "Format",
            ],
        )

        if not api_format:
            api_format = provider.api_format

        context = self._to_int(
            self._find_field(
                page,
                soup,
                [
                    "Context Window",
                    "Context Size",
                    "Context",
                ],
            )
        )

        max_output = self._to_int(
            self._find_field(
                page,
                soup,
                [
                    "Max Output Tokens",
                    "Max Output",
                    "Max Tokens",
                ],
            )
        )

        capability = self._parse_capability(page, soup)
        logical_name = self.normalizer.normalize(model.name)

        primary_api_key_env = provider.api_key_envs[0] if provider.api_key_envs else ""

        return ProviderModel(
            provider=provider.name,
            logical_name=logical_name,
            model_id=model_id,
            api_base=provider.api_base,
            api_format=api_format,
            api_key_env=primary_api_key_env,
            context_window=context,
            max_output_tokens=max_output,
            capability=capability,
        )

    @staticmethod
    def _find_field(
        text: str,
        soup: BeautifulSoup,
        names: list[str],
    ) -> Optional[str]:
        for name in names:
            pattern = re.compile(rf"^\\s*{re.escape(name)}\\s*:?\\s*$", re.IGNORECASE)
            elem = soup.find(lambda tag: tag.string and pattern.match(tag.string))
            if elem:
                next_tag = elem.find_next_sibling()
                if next_tag and next_tag.get_text(strip=True):
                    return next_tag.get_text(strip=True)
                parent = elem.parent
                if parent:
                    next_parent = parent.find_next_sibling()
                    if next_parent:
                        return next_parent.get_text(strip=True)

        for field in names:
            m = re.search(
                rf"{re.escape(field)}\\s*[:\\n\\r\\-]+\\s*([^\\n\\r]+)",
                text,
                re.IGNORECASE,
            )
            if m and m.group(1).strip():
                return m.group(1).strip()

        return None

    @staticmethod
    def _to_int(v) -> Optional[int]:
        if not v:
            return None
        s = str(v).lower().replace(",", "").strip()
        m = re.search(r"(\\d+(?:\\.\\d+)?)\\s*([km])?", s)
        if not m:
            return None
        num = float(m.group(1))
        unit = m.group(2)
        if unit == "k":
            num *= 1000
        elif unit == "m":
            num *= 1000000
        return int(num)

    @staticmethod
    def _parse_capability(
        page: str,
        soup: BeautifulSoup,
    ) -> ModelCapability:

        p = page.lower()
        cap = ModelCapability()

        if "chat" in p or "conversation" in p:
            cap.chat = True
        if "vision" in p or "multimodal" in p or "image-to-text" in p:
            cap.vision = True
        if "reasoning" in p or "thought" in p or "think" in p or "r1" in p:
            cap.reasoning = True
        if "coding" in p or "code" in p:
            cap.coding = True
        if "embedding" in p or "embed" in p:
            cap.embedding = True
        if "rerank" in p or "re-rank" in p:
            cap.rerank = True
        if "text-to-image" in p or "image generation" in p or ("image" in p and "vision" not in p):
            cap.image = True
        if "audio" in p or "speech" in p or "tts" in p or "stt" in p:
            cap.audio = True
        if "tool" in p or "function calling" in p:
            cap.tools = True
        if "json" in p or "structured output" in p:
            cap.json_mode = True

        if not any([cap.chat, cap.vision, cap.reasoning, cap.coding, cap.embedding, cap.rerank, cap.image, cap.audio]):
            cap.chat = True

        return cap
''',

    "crawler.py": '''"""
抓取 https://freellm.net/models/?free=1
获取前 200 个免费模型
提取 Provider
提取模型名
提取详情页 URL
返回 List[FreeLLMModel]
"""

from __future__ import annotations

from typing import List
from urllib.parse import urljoin
import json

import requests
from bs4 import BeautifulSoup

from models import FreeLLMModel


BASE_URL = "https://freellm.net"

MODEL_LIST_URL = (
    "https://freellm.net/models/?free=1"
)


class FreeLLMCrawler:
    """
    抓取 freellm 免费模型列表
    """

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )

    def fetch_top_models(
        self,
        limit: int = 200,
    ) -> List[FreeLLMModel]:

        try:
            resp = self.session.get(
                MODEL_LIST_URL,
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"Error fetching model list: {e}")
            return []

        soup = BeautifulSoup(
            resp.text,
            "lxml",
        )

        models: List[FreeLLMModel] = []
        seen = set()

        for script in soup.find_all(
            "script",
            {
                "type": "application/ld+json"
            }
        ):
            try:
                data = json.loads(script.string or "")
            except Exception:
                continue

            if isinstance(data, dict) and data.get("@type") == "ItemList":
                items = data.get("itemListElement", [])
                for item in items:
                    model_info = item.get("item", {})
                    model_name = model_info.get("name")
                    detail_url = model_info.get("url")
                    provider_info = model_info.get("provider", {})
                    provider = provider_info.get("name") if isinstance(provider_info, dict) else None

                    if not model_name or not detail_url or not provider:
                        continue

                    full_url = urljoin(BASE_URL, detail_url)
                    if full_url in seen:
                        continue

                    seen.add(full_url)
                    models.append(
                        FreeLLMModel(
                            provider=provider,
                            name=model_name,
                            detail_url=full_url,
                        )
                    )

                    if len(models) >= limit:
                        return models

        if len(models) < limit:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/models/" in href or "/model/" in href:
                    full_url = urljoin(BASE_URL, href)
                    if full_url in seen or full_url == MODEL_LIST_URL:
                        continue
                    text = a.get_text(strip=True)
                    if text and len(text) > 1:
                        seen.add(full_url)
                        models.append(
                            FreeLLMModel(
                                provider="Unknown",
                                name=text,
                                detail_url=full_url,
                            )
                        )
                        if len(models) >= limit:
                            break

        return models
''',

    "builder.py": '''from __future__ import annotations

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


class FallbackBuilder:

    def build(self, provider_models: list[ProviderModel]) -> list[LogicalModel]:
        logical_groups = defaultdict(list)

        for model in provider_models:
            logical_groups[model.logical_name].append(model)

        logical_models = []

        for logical_name in sorted(logical_groups.keys()):
            providers = logical_groups[logical_name]

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
        logical_models: list[LogicalModel],
    ) -> list[LogicalModel]:
        expanded = []

        for logical in logical_models:
            deployments = []

            for model in logical.providers:
                provider_cfg = get_provider(model.provider)
                if provider_cfg is None or not provider_cfg.api_key_envs:
                    deployments.append(model)
                    continue

                for env in provider_cfg.api_key_envs:
                    clone = ProviderModel(
                        provider=model.provider,
                        logical_name=model.logical_name,
                        model_id=model.model_id,
                        api_base=model.api_base,
                        api_format=model.api_format,
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
        logical_models: list[LogicalModel],
    ) -> dict[str, list[str]]:
        capability_models = defaultdict(list)

        for logical in logical_models:
            if not logical.providers:
                continue

            cap = logical.providers[0].capability
            for p in logical.providers:
                if p.capability.chat: cap.chat = True
                if p.capability.vision: cap.vision = True
                if p.capability.reasoning: cap.reasoning = True
                if p.capability.coding: cap.coding = True
                if p.capability.embedding: cap.embedding = True
                if p.capability.rerank: cap.rerank = True
                if p.capability.image: cap.image = True
                if p.capability.audio: cap.audio = True

            if cap.chat and logical.name not in capability_models["chat"]:
                capability_models["chat"].append(logical.name)
            if cap.reasoning and logical.name not in capability_models["reasoning"]:
                capability_models["reasoning"].append(logical.name)
            if cap.coding and logical.name not in capability_models["coding"]:
                capability_models["coding"].append(logical.name)
            if cap.vision and logical.name not in capability_models["vision"]:
                capability_models["vision"].append(logical.name)
            if cap.embedding and logical.name not in capability_models["embedding"]:
                capability_models["embedding"].append(logical.name)
            if cap.rerank and logical.name not in capability_models["rerank"]:
                capability_models["rerank"].append(logical.name)
            if cap.image and logical.name not in capability_models["image"]:
                capability_models["image"].append(logical.name)
            if cap.audio and logical.name not in capability_models["audio"]:
                capability_models["audio"].append(logical.name)

        return dict(capability_models)
''',

    "config_builder.py": '''"""
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
''',

    "main.py": '''"""
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
'''
}


def run():
    zip_filename = "litellm_project_fixed.zip"

    print("写入并更新项目文件...")
    for filename, content in FILES.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  - 已更新: {filename}")

    print(f"\n正在打包生成 {zip_filename}...")
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in FILES.keys():
            zf.write(filename)

    print(f"\n成功！所有文件已更新，并自动打包到了当前目录下的: {zip_filename}")

if __name__ == "__main__":
    run()
