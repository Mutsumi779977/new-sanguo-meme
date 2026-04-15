---
name: new-sanguo-v2
description: 新三国（2010年版）梗系统 v2.8.4 - 模块化架构，支持可配置权重公式、温度参数采样、可选向量功能、底线梗随机回退机制
triggers:
  - /新三国
  - /sanguo
  - /录入
  - /查询
  - /玩梗
---

# 新三国梗系统 v2.8.4

> 一个本地运行、零 Token 消耗的新三国（2010版）梗引擎

## 核心特性

### 🚀 零 Token 消耗（默认）

**纯本地运行，不调用任何 AI 接口**，所有功能基于本地代码实现：

| 功能 | Token 消耗 | 说明 |
|------|-----------|------|
| 梗匹配 | **0** | 本地 SQLite + YAML 查询 |
| 梗生成 | **0** | 本地模板渲染 |
| 变体生成 | **0** | 本地规则替换 |
| 底线梗机制 | **0** | 本地随机选择 + 回退机制 |
| 向量匹配 | **0** | 本地模型（默认关闭）|
| **联网搜索** | **~500-1500** | 仅触发 `kimi_search` 时消耗 |

**Token 消耗参照物：**
- 一次普通对话：~1,000-3,000 tokens
- 一次代码审查：~5,000-15,000 tokens  
- **本系统日常玩梗**：**0 tokens**（无限畅玩）
- 触发搜索时：~500-1500 tokens（≈ 3-5句对话）

**何时触发搜索？**
- 输入包含不认识的专有名词（如最新战队、新产品）
- 信息充足度检测判定需要外部信息
- 用户明确要求搜索

### 🎭 底线梗随机回退机制（v2.8.4）

当所有匹配都失败时，采用**随机选择 + 智能回退**策略：

```
随机选一个底线梗
    ↓
需要核心词？
    ├─ 否 → 直接输出（叉出去/拖出去斩了）
    └─ 是 → 尝试提取核心词
              ↓
         成功？ ├─ 是 → 填充输出
                └─ 否 → 重新随机选择（避免死循环）
```

**优势：**
- 多样性更高（"叉出去"和"拖出去斩了"有同等机会出场）
- 无变量梗不会硬套变量（不会出现"大胆什么，放肆什么"的尴尬）

### 📊 可配置权重公式

```yaml
# config.yaml
scoring:
  weights:
    similarity: 0.6        # 语义相似度权重
    base_weight: 0.3       # 基础权重系数
    frequency: 0.001       # 频次系数
    preference_person: 0.1 # 人物偏好权重
    preference_tag: 0.05   # 标签偏好权重
```

### 🎲 温度参数采样

```yaml
matching:
  temperature: 1.0  # T<1 更确定，T>1 更随机
```

### 🔍 向量功能（默认关闭）

```yaml
embedding:
  enabled: false  # 默认关闭，需手动开启
  model_name: "paraphrase-multilingual-MiniLM-L12-v2"
```

开启后首次使用自动下载模型（约 120MB）。

## 架构设计

```
┌─────────────────────────────────────────┐
│           new_sanguo 包                  │
├─────────────┬─────────────┬─────────────┤
│   models    │   service   │    agent    │
│   数据模型   │   业务逻辑   │   交互入口   │
├─────────────┼─────────────┼─────────────┤
│   config    │   database  │    utils    │
│   配置管理   │   数据持久化 │   工具函数   │
└─────────────┴─────────────┴─────────────┘
              ↓
        ┌─────────────┐
        │   SQLite    │
        │   YAML      │
        │   (可选)向量模型 │
        └─────────────┘
```

## 命令列表

| 命令 | 功能 | 版本 |
|------|------|------|
| `/录入` | 进入录入模式 | v2.0 |
| `/录入 视频` | 视频转文字录入 | v2.4 |
| `/查询 <关键词>` | 查询梗库 | v2.0 |
| `/玩梗 <内容>` | 手动触发玩梗 | v2.0 |
| `/称呼 <名称>` | 生成 xx 爷称呼 | v2.4 |
| `/统计` | 显示统计 | v2.0 |
| `/融合 [内容]` | 测试融合 | v2.3 |
| `/喜欢` / `/不喜欢` | 反馈 | v2.0 |

## 输出原则

**三不原则**：
- 不出现人物标注
- 不创设互动场景
- 不死板硬套原文

## 文件结构

```
new_sanguo/
├── __init__.py      # 包入口，导出主要类
├── models.py        # Genku, UserPreference, State
├── config.py        # Config 配置管理
├── database.py      # Database SQLite 操作
├── service.py       # GenkuService 业务逻辑
├── agent.py         # NewSanguoAgent 主类
└── utils.py         # setup_logger 等工具

data/
├── genku.yaml       # 梗数据源文件
├── fallback_genkus.yaml  # 底线梗配置
└── genku.db         # SQLite 数据库

config.yaml          # 用户配置文件
run.py              # CLI 入口
requirements.txt     # 依赖
```

## 数据结构

### Genku (梗)

```yaml
梗ID: xsg_cc_001
原文: "不可能，绝对不可能！"
人物: "曹操"
出处: "第X集-场景"
情境: "..."
情绪: [震惊, 自负]
场景标签: [否认, 经典]
语义关键词: [拒绝, 不可能]
权重: 5
变体模板: "[对象]，绝对[否定词]！"
is_meta: false
fusion_rules:  # 可选，meta 梗的融合规则
  模板: "{称呼}爷{动作}{主梗}"
  变量:
    动作: ["真是", "堪称"]
```

### 配置示例

```yaml
# 匹配算法
matching:
  max_input_length: 2000
  temperature: 1.0
  top_n_candidates: 5

# 评分权重
scoring:
  weights:
    similarity: 0.6
    base_weight: 0.3
    frequency: 0.001
    preference_person: 0.1
    preference_tag: 0.05

# 融合模板
fusion:
  enabled: true
  fusion_probability: 0.7
  templates:
    称呼类:
      patterns: [".*爷.*"]
      templates: ["{称呼}爷{动作}{主梗}"]
      actions: ["真是", "堪称"]

# 向量功能（默认关闭）
embedding:
  enabled: false
  model_name: "paraphrase-multilingual-MiniLM-L12-v2"
  lazy_load: true
```

## 使用方式

### 作为包导入

```python
from new_sanguo import create_agent

agent = create_agent("user_id")
reply = agent.handle("今天不想上班")
print(reply)
```

### CLI 运行

```bash
python run.py
```

## 依赖

**必需**:
- Python 3.7+
- pyyaml

**可选**:
- numpy (推荐)
- sentence-transformers (向量功能)

## 联网搜索增强（v2.5.1）

当遇到不理解的信息时，系统自动搜索并尝试匹配梗。

### 工作流程

```
用户输入: "你怎么看待 gen2:0T1"
        ↓
    首次匹配: 无结果
        ↓
    触发搜索: 🔍 搜索 "gen2:0T1"
        ↓
    提取关键词: ["gen2", "0T1", "生成式AI"]
        ↓
    重试匹配: 用关键词再次匹配
        ↓
    输出: 🔍 搜索后匹配 + 梗
```

### 配置

```yaml
search:
  enabled: true              # 启用搜索
  trigger_threshold: 0.3     # 匹配分数低于此值时触发
  result_count: 3            # 搜索结果数量
  retry_match_after_search: true  # 搜索后重试匹配
```

### 实现方式

- **OpenClaw 环境**: 自动调用 `kimi_search` 工具
- **其他环境**: 使用备用关键词提取方案

## 话题映射系统（v2.5.2）

自动识别输入所属话题领域，映射到对应的情绪/场景，辅助梗匹配。

### 支持的话题

| 话题 | 关键词示例 | 映射情绪 | 默认人物 |
|:---|:---|:---|:---|
| **电竞赛事** | LCK, LPL, Gen.G, T1, 比分 | 震惊, 不服输, 遗憾 | 曹操, 张飞, 袁绍 |
| **科技数码** | AI, GPT, 芯片, 发布会 | 震惊, 自负, 嘲讽 | 曹操, 诸葛亮, 关羽 |
| **娱乐** | 电影, 综艺, 明星, 评分 | 嘲讽, 调侃, 失望 | 曹操, 刘备, 张飞 |
| **体育** | 足球, 篮球, NBA, 世界杯 | 震惊, 兴奋, 不服输 | 曹操, 张飞, 吕布 |
| **游戏** | 原神, 星铁, Steam, 连跪 | 愤怒, 无奈, 吐槽 | 张飞, 曹操, 刘备 |

### 电竞比赛解析

自动识别战队名和比分，映射到对应情绪：

```
输入: "gen2:0T1"
识别: Gen.G 0:1 T1 (LCK赛事)
映射: 被零封/惨败 → 震惊、否认情绪
匹配: "不可能，绝对不可能！"

输入: "T1 3:0 横扫"
识别: T1 大胜
映射: 碾压 → 得意、嘲讽情绪
匹配: "我原本以为吕布已经天下无敌了"
```

## 版本历史

- **v2.8.4**: 底线梗随机回退机制，Token 消耗优化（纯本地零消耗）
- v2.8.0: 底线梗机制引入
- v2.5.2: 话题映射系统，自动识别 LCK/科技/娱乐等领域话题
- v2.5.1: 联网搜索增强功能
- v2.5: 模块化重构，可配置权重/温度，向量默认关闭
- v2.4: 视频转文字录入，称呼生成，双模式渲染
- v2.3: meta 梗融合功能
- v2.0: 统一架构，SQLite 持久化，向量化匹配

## 开发规范

### Git 提交规范

**每次功能更新后必须提交**，便于回退和管理：

```bash
# 添加所有更改
git add -A

# 提交（使用规范格式）
git commit -m "type(scope): 简短描述

详细说明（可选）

Closes: 相关issue"
```

**提交类型**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `chore`: 杂项

**重要**：每个有意义的更新都应独立提交，不要累积大量修改后再提交。

---

**许可证**: AGPL-3.0 | **作者**: 梦雨_raining | **B站**: https://space.bilibili.com/24250060
