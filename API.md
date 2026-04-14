# API 文档

本文档详细介绍新三国梗系统的 Python API。

## 目录

- [快速开始](#快速开始)
- [核心类](#核心类)
  - [Agent](#agent)
  - [TopicMapper](#topicmapper)
  - [GenkuService](#genkuservice)
- [数据模型](#数据模型)
  - [Genku](#genku)
  - [UserPreference](#userpreference)
- [配置选项](#配置选项)
- [话题类别](#话题类别)
- [异常处理](#异常处理)

---

## 快速开始

```python
from new_sanguo import create_agent

# 创建 Agent 实例
agent = create_agent("user_001")

# 处理用户输入
result = agent.handle("gen2:0T1")

# result 可以是字符串或字典
if isinstance(result, dict):
    if result.get('type') == 'need_search':
        print(f"需要搜索: {result['reason']}")
        # 执行搜索后重新调用
    elif result.get('type') == 'quick_reply':
        print(f"快速回复: {result['text']}")
else:
    print(f"回复: {result}")
```

---

## 核心类

### Agent

主入口类，协调话题识别、梗匹配和输出生成。

```python
from new_sanguo.agent import Agent

agent = Agent(
    user_id="user_001",
    db_path="data/genku.db",
    config_path="config.yaml",
    mode="纯梗"  # 或 "角色"
)
```

#### 主要方法

##### `handle(text: str) -> Union[str, Dict]`

处理用户输入，返回梗回复或搜索请求。

**参数：**
- `text` (str): 用户输入文本

**返回：**
- `str`: 直接回复的梗文本
- `Dict`: 需要进一步处理的结果
  - `{'type': 'need_search', 'query': str, 'reason': str}`: 需要搜索
  - `{'type': 'quick_reply', 'text': str, 'topic': str}`: 快速回复

**示例：**
```python
# 本地可处理的输入
result = agent.handle("原神又歪了")
# 返回: "这就不奇怪了，这就不奇怪了..."

# 需要搜索的输入
result = agent.handle("Gen.G今天赢了吗")
# 返回: {'type': 'need_search', 'query': 'Gen.G今天赢了吗', 'reason': '...'}
```

##### `switch_mode(mode: str)`

切换输出模式。

**参数：**
- `mode` (str): `"纯梗"` 或 `"角色"`

---

### TopicMapper

识别输入文本的话题类别，判断信息充足度。

```python
from new_sanguo.topic_mapper import TopicMapper, TopicCategory

mapper = TopicMapper()
```

#### 主要方法

##### `identify_topic(text: str) -> Tuple[TopicCategory, float]`

识别文本所属话题。

**参数：**
- `text` (str): 输入文本

**返回：**
- `Tuple[TopicCategory, float]`: (话题类别, 置信度 0-1)

**示例：**
```python
topic, confidence = mapper.identify_topic("gen2:0T1")
# 返回: (TopicCategory.ESPORTS, 0.8)

topic, confidence = mapper.identify_topic("吃什么")
# 返回: (TopicCategory.DAILY, 0.8)
```

##### `check_information_sufficiency(text: str, topic: TopicCategory) -> Tuple[bool, str]`

检查信息是否充足（方案A+）。

**参数：**
- `text` (str): 输入文本
- `topic` (TopicCategory): 识别到的话题

**返回：**
- `Tuple[bool, str]`: (是否充足, 原因说明)

**示例：**
```python
# 电竞比分 - 信息充足
sufficient, reason = mapper.check_information_sufficiency("gen2:0T1", TopicCategory.ESPORTS)
# 返回: (True, "本地知识可处理")

# 电竞询问 - 信息不充足
sufficient, reason = mapper.check_information_sufficiency("Gen.G今天赢了吗", TopicCategory.ESPORTS)
# 返回: (False, "话题'电竞赛事'包含'今天'等时效性关键词")
```

##### `suggest_genku_tags(text: str) -> Dict`

为输入生成推荐的标签和模板。

**返回字段：**
- `topic` (str): 话题名称
- `confidence` (float): 置信度
- `emotions` (List[str]): 推荐情绪
- `scenes` (List[str]): 推荐场景
- `persons` (List[str]): 推荐人物
- `context_template` (str): 上下文模板（可选）
- `template_vars` (Dict): 模板变量（可选）

---

### GenkuService

核心匹配服务，负责梗的检索、评分和频率控制。

```python
from new_sanguo.service import GenkuService
from new_sanguo.database import Database
from new_sanguo.config import Config
import logging

config = Config("config.yaml")
db = Database("data/genku.db", logging.getLogger())
service = GenkuService(db, config, logging.getLogger())
```

#### 主要方法

##### `match_genku(text: str, user_pref=None, allow_fusion=True) -> Tuple[Optional[Genku], Optional[str]]`

匹配最合适的梗。

**参数：**
- `text` (str): 输入文本
- `user_pref` (UserPreference, optional): 用户偏好
- `allow_fusion` (bool): 是否允许融合 meta 梗

**返回：**
- `Tuple[Genku, str]`: (匹配的梗, 融合后的文本)
- `Tuple[None, None]`: 未匹配到

**示例：**
```python
genku, fused_text = service.match_genku("gen2:0T1")
if genku:
    print(f"匹配: {genku.original}")
    if fused_text:
        print(f"融合: {fused_text}")
```

---

## 数据模型

### Genku

梗的数据模型。

```python
from new_sanguo.models import Genku

genku = Genku(
    genku_id="xsg_cc_001",
    original="不可能，绝对不可能！",
    person="曹操",
    source="得知刘备得徐州后",
    context="曹操听说刘备得到徐州后的反应",
    emotions=["震惊", "否认", "不服输"],
    intensity="高",
    tags=["震惊", "否认", "经典"],
    semantic_keywords=["不可能", "绝对"],
    weight=5,  # 权重 1-5
)
```

**字段说明：**

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `genku_id` | str | 唯一标识符 |
| `original` | str | 原文 |
| `person` | str | 人物 |
| `source` | str | 出处 |
| `context` | str | 情境 |
| `emotions` | List[str] | 情绪标签 |
| `intensity` | str | 强度 (高/中/低) |
| `tags` | List[str] | 场景标签 |
| `semantic_keywords` | List[str] | 语义关键词 |
| `weight` | int | 权重 1-5，5为高频梗 |

---

## 配置选项

### config.yaml 完整配置

```yaml
# 匹配参数
matching:
  max_input_length: 2000        # 最大输入长度
  weight_bonus_coefficient: 0.3 # 权重加成系数
  max_freq_bonus: 0.1          # 最大频次加成
  freq_bonus_coefficient: 0.001 # 频次加成系数
  top_n_candidates: 5          # 候选梗数量
  min_similarity_threshold: 0.5 # 最小相似度阈值
  temperature: 1.0             # 温度参数 (0.1-2.0)

# 评分权重
scoring:
  weights:
    similarity: 0.6        # 语义相似度权重
    base_weight: 0.3       # 基础权重
    frequency: 0.001       # 频次权重
    frequency_max: 0.1     # 最大频次加成
    preference_person: 0.1 # 人物偏好权重
    preference_tag: 0.05   # 标签偏好权重
  normalization:
    weight_max: 5          # 权重最大值（用于归一化）

# 向量功能（默认关闭）
embedding:
  enabled: false
  model_name: 'paraphrase-multilingual-MiniLM-L12-v2'
  lazy_load: true  # 延迟加载

# 数据库
database:
  filename: 'genku.db'
  yaml_source: 'data/genku.yaml'
  timeout: 30

# 日志
logging:
  level: 'INFO'
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 搜索增强
search:
  enabled: true
  trigger_threshold: 0.3
```

### 高频梗防滥用配置

```python
from new_sanguo.service import HIGH_FREQUENCY_GENKU_CONFIG

# 默认配置
HIGH_FREQUENCY_GENKU_CONFIG = {
    'weight_5_genkus': {
        'window_seconds': 600,         # 10分钟窗口
        'max_usage_before_penalty': 3,  # 事不过三
        'penalty_per_use': 0.1,         # 惩罚系数 0.1^n
        'penalty_threshold': 0.5,       # 低于此值换梗
        'min_weight': 5,                # 最小权重阈值
    }
}
```

---

## 话题类别

### TopicCategory 枚举

| 类别 | 说明 | 典型关键词 |
|:---|:---|:---|
| `ESPORTS` | 电竞赛事 | gen, t1, lck, 2:0, 比赛 |
| `TECH` | 科技数码 | AI, GPT, 芯片, 发布会 |
| `GAME` | 游戏 | 原神, 星铁, 抽卡, 歪了 |
| `ENTERTAINMENT` | 娱乐 | 电影, 歌手, 演唱会, 翻唱 |
| `SPORTS` | 体育 | 足球, NBA, 世界杯 |
| `POLITICS` | 时政 | 特朗普, 伊朗, 军事行动 |
| `DAILY` | 日常闲聊 | 吃什么, 天气, 你好, 再见 |
| `UNKNOWN` | 未知 | - |

### 日常闲聊模板

| 场景 | 输入示例 | 输出模板 |
|:---|:---|:---|
| 吃什么 | "晚上吃什么" | "是啊，吃什么" |
| 看什么 | "看什么电影" | "是啊，看什么" |
| 天气 | "今天天气" | "好火啊，比夷陵之火还好啊" |
| 问候 | "你好" | "来者何人" |
| 告别 | "再见" | "公台，公台啊..." |
| 累了 | "好累" | "我不过是笼中之鸟，网中之鱼" |

---

## 异常处理

```python
from new_sanguo import create_agent

try:
    agent = create_agent("user_001")
    result = agent.handle("用户输入")
except FileNotFoundError as e:
    print(f"配置文件缺失: {e}")
except ValueError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 完整示例

```python
from new_sanguo import create_agent

def main():
    # 创建 Agent
    agent = create_agent("user_001", mode="纯梗")
    
    # 示例对话
    inputs = [
        "gen2:0T1",              # 电竞比分
        "原神又歪了",             # 游戏
        "吃什么",                # 日常
        "Gen.G今天赢了吗",        # 需要搜索
    ]
    
    for text in inputs:
        print(f"\n用户: {text}")
        result = agent.handle(text)
        
        if isinstance(result, dict):
            if result.get('type') == 'need_search':
                print(f"系统: [需要搜索] {result['reason']}")
                # 实际应用中执行搜索后重新调用
            else:
                print(f"系统: {result.get('text', '未知')}")
        else:
            print(f"系统: {result}")

if __name__ == "__main__":
    main()
```

---

## 版本信息

- **当前版本**: v3.0
- **Python**: >= 3.8
- **主要依赖**: PyYAML, numpy（可选，用于向量功能）

## 更多资源

- [项目README](README.md)
- [单元测试](tests/)
- [梗数据库](data/genku.yaml)
