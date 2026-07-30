"""
builder.py

Logical Model Builder


输入:

List[ModelInfo]


输出:

Dict[str, LogicalModel]


架构:

ModelInfo
    |
    v
LogicalModel.models


禁止:

ProviderModel
primary_model
providers
FallbackBuilder
"""

from __future__ import annotations


from dataclasses import dataclass, field

from typing import Dict, List


from models import (
    ModelInfo,
    LogicalModel,
)



# ============================================================
# Build Result
# ============================================================


@dataclass
class BuildResult:

    logical_models: Dict[str, LogicalModel] = field(
        default_factory=dict
    )



# ============================================================
# Builder
# ============================================================


class ModelBuilder:
    """
    ModelInfo -> LogicalModel
    """



    def build(
        self,
        models: List[ModelInfo],
    ) -> BuildResult:
        """
        构建逻辑模型
        """


        groups = self.group_models(
            models
        )


        result = {}



        for logical_name, items in groups.items():


            items.sort(
                key=lambda x:
                    x.score,
                reverse=True
            )



            logical_model = LogicalModel(

                logical_name=logical_name,

                models=items,

                strategy="fallback"

            )



            result[logical_name] = logical_model



        return BuildResult(

            logical_models=result

        )



    # ========================================================
    # group
    # ========================================================


    def group_models(
        self,
        models: List[ModelInfo]
    ) -> Dict[str, List[ModelInfo]]:


        groups = {}



        for model in models:


            logical_name = (
                self.get_logical_name(
                    model
                )
            )


            if logical_name not in groups:

                groups[logical_name] = []



            groups[logical_name].append(
                model
            )



        return groups



    # ========================================================
    # logical name
    # ========================================================


    def get_logical_name(
        self,
        model: ModelInfo
    ) -> str:
        """
        生成逻辑模型名称


        优先:

        ModelInfo.logical_name


        其次:

        根据能力分类

        """



        if model.logical_name:

            return model.logical_name



        capability = model.capabilities



        if capability.vision:

            return "vision"



        if capability.reasoning:

            return "reasoning"



        if capability.coding:

            return "coding"



        if capability.embedding:

            return "embedding"



        if capability.rerank:

            return "rerank"



        return "chat"