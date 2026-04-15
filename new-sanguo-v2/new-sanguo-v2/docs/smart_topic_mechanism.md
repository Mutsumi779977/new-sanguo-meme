# 智能话题识别器 - 运行机制详解

## 一、核心架构

### 1. 三层识别体系

```
┌─────────────────────────────────────────────────────────────┐
│  第一层：精确匹配层 (关键词 + 正则)                            │
│  ├── 精确关键词：完全匹配，非子串                             │
│  ├── 正则模式：复杂格式识别 (比分、型号等)                     │
│  └── 排除词：反向过滤，避免误判                              │
├─────────────────────────────────────────────────────────────┤
│  第二层：语义扩展层 (同义词 + 上下文)                          │
│  ├── 语义提示词：相关概念扩展                                │
│  ├── 上下文记忆：上一轮话题继承                              │
│  └── 语义向量：embedding相似度 (可选)                        │
├─────────────────────────────────────────────────────────────┤
│  第三层：混合决策层 (加权投票)                                │
│  ├── 多方法评分加权                                          │
│  ├── 置信度归一化                                            │
│  └── 阈值判断                                                │
└─────────────────────────────────────────────────────────────┘
```

## 二、详细运行机制

### 1. 特征定义 (TopicFeature)

```python
@dataclass
class TopicFeature:
    exact_keywords: Set[str]      # 精确匹配词（不能是子串）
    patterns: List[re.Pattern]    # 正则模式
    semantic_hints: Set[str]      # 语义提示词
    exclusion_words: Set[str]     # 排除词（出现则扣分）
    context_preference: Set[str]  # 上下文偏好
```

**示例配置：**
```python
TopicFeature(
    exact_keywords={'lck', 't1', 'faker', '比赛', '战绩'},
    patterns=[
        re.compile(r'\b(gen\.?g?|t1|blg)\b', re.I),  # 战队名
        re.compile(r'\d+\s*[:：]\s*\d+'),             # 比分
    ],
    semantic_hints={'战队', '选手', 'bp', '团战'},
    exclusion_words={'agent', '智能体', 'ai助手'},  # 关键！避免误判
    context_preference={'ESPORTS', 'GAME'}
)
```

### 2. 识别流程

```
输入文本
    ↓
[Step 1] 精确关键词匹配
    ├── 使用单词边界匹配（不是子串！）
    ├── "gen" in "agent" → False ✅
    ├── "gen" in "gen 2:0 t1" → True ✅
    └── 匹配成功 +2分
    ↓
[Step 2] 正则模式匹配
    ├── 战队名模式: "T1", "Gen.G" → +1.5分
    ├── 比分模式: "2:0", "3:1" → +1.5分
    └── 匹配成功 +1.5分
    ↓
[Step 3] 语义提示词
    ├── "战队"、"选手"、"bp" → +0.5分
    └── 匹配成功 +0.5分
    ↓
[Step 4] 排除词惩罚（关键！）
    ├── 如果包含"agent" → -3分（强惩罚）
    ├── 如果包含"智能体" → -3分
    └── 避免"agent"被误判为电竞
    ↓
[Step 5] 上下文加成
    ├── 上一轮话题是TECH → TECH+1分
    ├── 上一轮话题是ESPORTS → ESPORTS+1分
    └── 连续话题加分
    ↓
[Step 6] 归一化输出
    ├── 总分 / 5.0 → 置信度0-1
    └── 返回 (话题, 置信度)
```

### 3. 精确匹配 vs 子串匹配

```python
# 旧方案（问题）
"gen" in "agent" → True ❌  # 子串匹配，误判！

# 新方案（修复）
_exact_word_match("gen", "agent") → False ✅
_exact_word_match("gen", "gen 2:0 t1") → True ✅

# 实现：单词边界正则
pattern = r'(?:^|[^a-z])' + re.escape("gen") + r'(?:[^a-z]|$)'
```

### 4. 排除词机制

```python
# 当用户说"这个agent怎么用"
ESPORTS 话题特征:
    exclusion_words = {'agent', '智能体', 'ai助手'}

识别过程:
    精确关键词: [] → 0分
    正则模式: [] → 0分
    语义提示: [] → 0分
    排除词惩罚: "agent"匹配 → -3分
    
    总分: -3分 → 被排除
```

### 5. 上下文记忆

```python
class SmartTopicRecognizer:
    def __init__(self):
        self.last_topic = None  # 上一轮话题
        self.topic_history = []  # 历史记录
    
    def recognize(self, text, context=None):
        # 上下文加成
        if self.last_topic == current_topic:
            score += 1.0  # 连续话题加分
```

**示例：**
```
第一轮: "GPT4发布了" → 识别为TECH，last_topic = TECH
第二轮: "agent怎么用" → 
    TECH 上下文加成 +1分
    ESPORTS 无加成
    → 更倾向TECH，避免误判为ESPORTS
```

## 三、混合识别器 (Hybrid)

```python
class HybridTopicRecognizer:
    def recognize(self, text, history=None):
        # 多方法并行
        votes = {
            'keyword': (kw_topic, kw_conf),      # 关键词方法
            'semantic': (sem_topic, sem_conf),    # 语义方法
            'context': (ctx_topic, ctx_conf),     # 上下文方法
        }
        
        # 加权投票
        weights = {
            'keyword': 0.4,
            'semantic': 0.4,
            'context': 0.2
        }
        
        # 最终决策
        best_topic = weighted_vote(votes, weights)
        return best_topic
```

## 四、与传统方案对比

| 场景 | 旧方案 | 新方案 | 结果 |
|:---|:---|:---|:---|
| "agent怎么用" | "gen" in → ESPORTS | 排除词惩罚 + 无电竞词 | TECH ✅ |
| "gen2:0T1" | ESPORTS | ESPORTS (模式匹配) | ESPORTS ✅ |
| "AI Agent" | 可能误判 | 精确匹配 + 上下文 | TECH ✅ |
| "今天吃什么" | DAILY | DAILY + 上下文继承 | DAILY ✅ |
| "T1又输了" | ESPORTS (需要搜索) | ESPORTS + 语义理解 | ESPORTS ✅ |

## 五、关键优势

1. **精确匹配**：避免子串误伤（agent ≠ gen）
2. **排除机制**：主动排除易混淆词
3. **上下文感知**：连续对话保持话题一致性
4. **多维度评分**：不依赖单一特征
5. **可配置权重**：不同场景调整策略
6. **语义向量**：支持embedding相似度（可选）

## 六、待优化点

1. **语义向量需要embedding模型**（120MB）
2. **排除词列表需要维护**
3. **上下文窗口大小可调**
4. **不同话题的权重可配置**
