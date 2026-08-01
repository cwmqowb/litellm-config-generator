# LiteLLM Config Generator

一个从 FreeLLM 模型站点抓取模型元数据，并自动生成 LiteLLM 可直接使用的 YAML 配置的脚本项目。

## 项目目标

该项目的核心目标是：

1. 从 FreeLLM 的公开模型列表页面中发现可用模型；
2. 进入每个模型的详情页，提取真正的 `Model ID`、API Base、上下文窗口、能力标签等字段；
3. 统一规范化这些数据结构；
4. 将模型按能力归类，生成带有 provider / api_base / api_key 引用的 LiteLLM 配置文件。

最终产物是一个 `config.generated.yaml`，可被 LiteLLM 直接作为 `model_list` 配置输入。

---

## 设计思路

这个项目的设计非常偏“数据管线式”架构：

- `crawler.py` 只负责抓取页面列表；
- `detail_parser.py` 只负责解析模型详情页；
- `normalizer.py` 负责统一结构和清洗字段；
- `builder.py` 和 `config_builder.py` 负责逻辑分组与配置生成；
- `providers.py` 负责维护 provider 与 API 信息的注册表。

这种分层的好处是：

- 每个模块职责明确，便于维护；
- 解析器不会混杂生成配置逻辑；
- 新增 provider 或新字段不会影响已有主流程；
- 配置输出可以在不修改抓取逻辑的前提下快速迭代。

---

## 总体流程

项目主流程如下：

1. 读取 `https://freellm.net/models/?free=1` 模型列表页；
2. 抽取模型的 provider、详情页 URL、slug、display_name 等基础信息；
3. 再访问每个模型的详情页，解析出 `Model ID`、`Base URL`、能力标签、上下文窗口等真实信息；
4. 将这些信息转成统一的 `ModelInfo` 数据模型；
5. 对模型进行 provider 规范化、去重、字段标准化；
6. 依据能力类型生成 LiteLLM 的逻辑模型名；
7. 生成 YAML 配置文件并保存到目标路径。

主入口位于 `main.py`，实现了完整管线调用。

---

## 核心模块说明

### 1. `main.py`

项目入口脚本。

职责：

- 解析命令行参数；
- 调用抓取、详情解析、归一化、配置生成等步骤；
- 最终保存 YAML。

提供的参数：

- `--top`：抓取前多少个模型；
- `--output`：输出 YAML 文件路径；

示例：

```bash
python main.py --top 50 --output config.generated.yaml
```

### 2. `crawler.py`

只负责抓取 FreeLLM 的“模型列表页”。

它会提取以下关键信息：

- provider
- detail_url
- slug
- display_name
- extra

注意：它不负责最终的 `model_id` 生成，也不负责构建 LiteLLM YAML。

### 3. `detail_parser.py`

负责解析模型详情页中的真实信息。

它会抓取页面中的：

- `API Details` 下的 `Model ID`
- `Base URL`
- `Context window`
- `Capabilities`
- `Input`
- `Best For`
- benchmark 等补充字段

这里非常重要的一点是：

> 项目严格要求使用页面中的 `Model ID` 作为 LiteLLM 标识，而不是使用 `display_name` / `slug`。

### 4. `models.py`

定义统一的数据模型 `ModelInfo`。

它集中表示一个模型的核心字段：

- `provider`
- `model_id`
- `api_base`
- `score`
- `context`
- `capability`
- `modality`
- `detail_url`
- `best_for`
- `extra`

这个模型在整个项目中承担“数据传递单元”的角色。

### 5. `normalizer.py`

负责把不同来源的数据标准化成一致格式。

主要处理：

- provider 名称标准化；
- 字段列表拆分；
- 图片/文本等能力字段统一；
- 去重；
- 缺失 `model_id` 的数据过滤。

### 6. `builder.py`

负责根据模型能力产生“逻辑模型”。

它会把模型分成：

- `chat`
- `reasoning`
- `coding`
- `vision`
- `embedding`
- `rerank`

算法上会按能力优先级和模型分数进行排序，最终形成一个逻辑模型组。

### 7. `config_builder.py`

真正的配置生成器。

它负责把标准化后的模型转换成 LiteLLM 的 YAML 结构，主要内容包括：

- 逻辑模型名确定；
- provider 前缀拼装；
- `api_base` 注入；
- `api_key` 通过环境变量引用；
- metadata 保留原始模型信息。

输出结构大致如下：

```yaml
model_list:
  - model_name: chat
    litellm_params:
      model: provider/model-id
      api_base: https://...
      api_key: os.environ/OPENROUTER_API_KEY
    metadata:
      provider: openrouter
      score: 0.0
      capability: []
      context: ...
      best_for: []
```

### 8. `providers.py`

维护 provider 注册表。

当前支持的 provider 主要包括：

- `nvidia`
- `openrouter`
- `github`
- `modelscope`
- `sambanova`
- `agnes`
- `kilo`

它同时保存了各 provider 的：

- `api_base`
- `api_key_env`
- `api_format`

这意味着最终生成的 LiteLLM YAML 可以直接依赖环境变量来配置授权信息。

---

## 输出内容特点

生成的配置文件并不是简单的“原型模型列表”，而是更贴近 LiteLLM 运行需求的结构：

- `model_list` 统一命名；
- 逻辑模型聚合；
- provider 信息透明可审计；
- metadata 中保留模型能力、上下文窗口、benchmark 和推荐场景等信息。

这使得生成的配置文件既能用于部署，也可以作为后续筛选与排错的基础。

---

## 运行方式

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 运行生成：

```bash
python main.py --top 50 --output config.generated.yaml
```

3. 生成结果会写入指定 YAML 文件。

---

## 依赖说明

项目依赖包括：

- `requests`：抓取网络页面；
- `beautifulsoup4`：解析 HTML；
- `PyYAML`：生成 YAML；
- `python-dotenv`：环境变量支持；
- `pytest`：可选测试依赖。

---

## 项目限制与注意事项

1. 当前抓取站点是外部公开页面，网络可用性与页面结构变化会影响抓取结果；
2. 如果目标页面结构发生变更，`detail_parser.py` 也需要同步更新；
3. `Model ID` 是最终 LiteLLM 识别字段，项目明确避免把 `display_name`、`slug` 误用为 model 名；
4. provider 的 `api_key` 为环境变量引用方式，因此部署时需要提前设置对应环境变量；
5. 当前逻辑模型仍然偏简单聚合，不包含更复杂的 fallback、路由与负载均衡策略。

---

## 总结

这个项目本质上是一个“从公开模型目录中转成 LiteLLM 配置”的数据工程脚本。

它的价值在于：

- 自动化收集模型元数据；
- 统一 provider 与能力信息；
- 生成适配 LiteLLM 的 YAML 模板；
- 为后续扩展到更多 provider、更多路由策略提供基础设施。

如果你要继续迭代它，最值得补强的方向通常有两块：

- 增强 model 名与 provider 的精准映射；
- 加上更强的过滤、排序、路由策略，以支持更稳定的生产级配置生成。
