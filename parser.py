"""
解析每个模型详情页，提取：
Base URL
Model ID
API Format
Context Window
Max Output Tokens
Capabilities（chat / vision / coding / reasoning / image / embedding / audio / tools）
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

    def parse(
        self,
        model: FreeLLMModel,
    ) -> Optional[ProviderModel]:

        provider = get_provider(model.provider)

        if provider is None:
            return None

        r = self.session.get(
            model.detail_url,
            timeout=30,
        )

        r.raise_for_status()

        soup = BeautifulSoup(
            r.text,
            "lxml",
        )

        page = soup.get_text(
            "\n",
            strip=True,
        )

        model_id = self._find_field(
            page,
            [
                "Model ID",
                "Model",
            ],
        )

        if not model_id:
            model_id = model.name

        api_format = self._find_field(
            page,
            [
                "API Format",
            ],
        )

        if not api_format:
            api_format = provider.api_format

        context = self._to_int(
            self._find_field(
                page,
                [
                    "Context Window",
                    "Context",
                ],
            )
        )

        max_output = self._to_int(
            self._find_field(
                page,
                [
                    "Max Output",
                    "Max Tokens",
                ],
            )
        )

        capability = self._parse_capability(page)

        logical_name = self._normalize_name(model.name)

        return ProviderModel(
            provider=model.provider,
            logical_name=logical_name,
            model_id=model_id,
            api_base=provider.api_base,
            api_format=api_format,
            api_key_env=provider.api_key_env,
            context_window=context,
            max_output_tokens=max_output,
            capability=capability,
        )

    @staticmethod
    def _normalize_name(name: str) -> str:

        return (
            name.lower()
            .replace(" ", "-")
            .replace("/", "-")
        )

    @staticmethod
    def _find_field(
        text: str,
        names,
    ):

        for field in names:

            m = re.search(
                rf"{re.escape(field)}\s*:?\s*(.+)",
                text,
                re.IGNORECASE,
            )

            if m:
                return m.group(1).strip()

        return None

    @staticmethod
    def _to_int(v):

        if not v:
            return None

        m = re.search(
            r"(\d[\d,]*)",
            str(v),
        )

        if not m:
            return None

        return int(
            m.group(1).replace(",", "")
        )

    @staticmethod
    def _parse_capability(
        page: str,
    ) -> ModelCapability:

        p = page.lower()

        cap = ModelCapability()

        if "chat" in p:
            cap.chat = True

        if "vision" in p:
            cap.vision = True

        if "reasoning" in p:
            cap.reasoning = True

        if "coding" in p or "code" in p:
            cap.coding = True

        if "embedding" in p:
            cap.embedding = True

        if "image" in p:
            cap.image = True

        if "audio" in p:
            cap.audio = True

        if "tool" in p:
            cap.tools = True

        if "json" in p:
            cap.json_mode = True

        return cap
