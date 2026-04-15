# 结构化搜索与多维度匹配系统

## 概述

新系统解决了原Agent"搜索后无法生成回复"的问题。核心改进：

1. **结构化搜索信息** - 将搜索结果解析为实体、情感、评价类型等维度
2. **多维度匹配** - 从5个维度匹配最合适的梗（实体、情感、场景、语义、评价类型）
3. **模板填充** - 使用搜索信息自动填充梗模板

## 核心组件

### 1. StructuredSearchResult (structured_search.py)
```python
@dataclass
class StructuredSearchResult:
    query: str                    # 原始查询
    entities: List[Entity]        # 提取的实体
    main_entity: Entity           # 主要实体
    sentiment: Sentiment          # 情感分析结果
    evaluation_type: EvaluationType  # 评价类型（赞扬/批评/对比）
    recommended_tags: List[str]   # 推荐标签
    recommended_emotions: List[str]  # 推荐情绪
```

### 2. SearchResultParser (search_parser.py)
将原始搜索结果转换为结构化信息：
- 实体识别（人物、战队、作品）
- 情感分析（极性、强度）
- 评价类型识别
- 属性提取

### 3. MultiDimensionalMatcher (multi_matcher.py)
5维度匹配算法：

| 维度 | 权重 | 说明 |
|------|------|------|
| entity | 0.30 | 实体匹配（最重要） |
| sentiment | 0.25 | 情感匹配 |
| scene | 0.20 | 场景标签匹配 |
| semantic | 0.15 | 语义关键词匹配 |
| evaluation | 0.10 | 评价类型匹配 |

### 4. Agent集成 (agent_structured_search.py)
新增方法 `_structured_search_and_match()`：
1. 执行搜索
2. 解析为结构化结果
3. 多维度匹配梗
4. 模板填充生成回复

## 使用示例

```python
from new_sanguo import create_agent

agent = create_agent('user_id')

# 评价类输入
result = agent.handle("如何评价faker")
# 新系统会自动：
# 1. 识别为赞扬型评价
# 2. 提取Faker实体
# 3. 匹配xsg_eval_god_001（总分0.64）
# 4. 填充模板生成：
#    "Faker？这是真·不可能，绝对不可能被超越的存在！"
```

## 新增梗

### 评价专用Meta梗
- `xsg_eval_praise_001`: 递进式赞扬模板
- `xsg_eval_god_001`: 封神级评价模板
- `xsg_eval_critic_001`: 批评解释模板
- `xsg_eval_compare_001`: 对比评价模板

### 实体专用梗
- `xsg_esports_faker_001`: Faker五冠王专用

## 测试结果

```
输入: 如何评价faker

结构化解析:
  - 主实体: Faker (人物)
  - 情感极性: 1.00 (正面)
  - 评价类型: 赞扬
  - 推荐标签: ['评价', '赞叹', '封神']

多维度匹配Top1:
  - 梗ID: xsg_eval_god_001
  - 总分: 0.640
  - 维度得分:
    - entity: 0.30
    - sentiment: 1.00
    - scene: 1.00
    - evaluation: 1.00
```

## 后续集成

要将新系统完全集成到Agent中，需要修改 `agent.py`：

```python
# 在 _search_and_retry 方法中添加调用
structured_result = self._structured_search_and_match(text)
if structured_result:
    return structured_result
```

此修改将在下一版本中完成。
