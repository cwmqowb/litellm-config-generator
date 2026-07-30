from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List


from models import (
    LogicalModel,
    ModelInfo,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)


@dataclass
class CapabilityGroup:
    """
    按能力分类的模型组

    例如：

    chat:
        qwen3
        deepseek-v3

    vision:
        qwen3-vl
    """

    name: str

    models: List[LogicalModel] = field(
        default_factory=list
    )



@dataclass
class BuildResult:
    """
    Builder 输出结果
    """

    logical_models: Dict[str, LogicalModel] = field(
        default_factory=dict
    )


    capability_groups: Dict[str, CapabilityGroup] = field(
        default_factory=dict
    )



class FallbackBuilder:
    """
    Logical Model 构建器


    输入:

        ModelInfo


    输出:

        LogicalModel(
            models=[
                model1,
                model2
            ]
        )


    LiteLLM:

        logical-model
              |
              |
              +-- provider model A
              |
              +-- provider model B

    """



    def build(
        self,
        models: List[ModelInfo],
    ) -> BuildResult:


        result = BuildResult()



        for model in models:

            try:

                logical_name = (
                    model.logical_name
                    or
                    model.model_id
                )


                if not logical_name:

                    logging.warning(
                        "skip model without name: %s",
                        model,
                    )

                    continue



                #
                # 创建 LogicalModel
                #
                logical_model = (
                    result.logical_models
                    .get(logical_name)
                )



                if logical_model is None:


                    logical_model = LogicalModel(

                        logical_name=logical_name,

                        models=[],

                    )


                    result.logical_models[
                        logical_name
                    ] = logical_model



                #
                # 添加模型
                #
                logical_model.models.append(
                    model
                )



                #
                # 能力分组
                #
                self._add_capability_group(
                    result,
                    logical_model,
                    model,
                )


            except Exception:

                logging.exception(
                    "build logical model failed: %s",
                    model,
                )



        return result



    def _add_capability_group(
        self,
        result: BuildResult,
        logical_model: LogicalModel,
        model: ModelInfo,
    ):


        capability = (
            model.capability
        )


        groups = []



        if capability.chat:

            groups.append(
                "chat"
            )


        if capability.vision:

            groups.append(
                "vision"
            )


        if capability.embedding:

            groups.append(
                "embedding"
            )


        if capability.audio:

            groups.append(
                "audio"
            )



        #
        # 没有能力标签
        #
        if not groups:

            groups.append(
                "unknown"
            )



        for group_name in groups:


            group = (
                result.capability_groups
                .get(group_name)
            )


            if group is None:


                group = CapabilityGroup(
                    name=group_name
                )


                result.capability_groups[
                    group_name
                ] = group



            if logical_model not in group.models:


                group.models.append(
                    logical_model
                )
