"""
builder.py

Logical Model Builder

输入:

    List[ModelInfo]


输出:

    BuildResult

其中:

    logical_models:
        Dict[str, LogicalModel]


当前架构:

ModelInfo
    |
    |
    v

LogicalModel

    name

    models: List[ModelInfo]

    strategy
"""


from dataclasses import dataclass, field

from typing import (
    Dict,
    List,
)


from models import (
    ModelInfo,
    LogicalModel,
)



# ============================================================
# Build Result
# ============================================================


@dataclass
class BuildResult:

    """
    Builder输出结果
    """

    logical_models: Dict[
        str,
        LogicalModel
    ] = field(
        default_factory=dict
    )



# ============================================================
# Builder
# ============================================================


class ModelBuilder:


    """
    ModelInfo -> LogicalModel

    不再存在:

        ProviderModel

        primary_model

        providers

    """



    def build(
        self,

        models: List[ModelInfo],

    ) -> BuildResult:



        groups = self.group_models(
            models
        )


        logical_models = {}



        for name, items in groups.items():


            # 按评分排序

            items.sort(

                key=lambda x:

                    getattr(
                        x,
                        "score",
                        0,
                    )
                    or 0,

                reverse=True,

            )


            logical_model = LogicalModel(

                name=name,

                models=items,

                strategy="fallback",

            )


            logical_models[name] = (
                logical_model
            )



        return BuildResult(

            logical_models=logical_models

        )



    # ========================================================
    # Group
    # ========================================================


    def group_models(

        self,

        models: List[ModelInfo],

    ) -> Dict[str, List[ModelInfo]]:


        result = {}



        for model in models:


            name = (
                self.get_logical_name(
                    model
                )
            )



            if name not in result:

                result[name] = []



            result[name].append(
                model
            )



        return result



    # ========================================================
    # Logical name
    # ========================================================


    def get_logical_name(

        self,

        model: ModelInfo,

    ) -> str:


        """
        将实际模型归类

        示例:

        qwen3-235b
            ->
        qwen3


        deepseek-v3
            ->
        deepseek

        """



        raw_name = (

            getattr(
                model,
                "name",
                None,
            )

            or

            getattr(
                model,
                "model_id",
                None,
            )

            or

            "unknown"

        )



        raw_name = (
            raw_name
            .lower()
            .replace(
                "/",
                "-"
            )
        )



        keywords = [

            "qwen",

            "deepseek",

            "kimi",

            "glm",

            "llama",

            "gemma",

            "mistral",

            "nemotron",

        ]



        for keyword in keywords:


            if keyword in raw_name:

                return keyword



        return raw_name.split(
            "-"
        )[0]



# ============================================================
# 兼容旧调用入口
# ============================================================


class FallbackBuilder(ModelBuilder):


    """
    保留旧类名兼容 main.py

    但内部已经完全使用:

        LogicalModel.models

    """

    pass
