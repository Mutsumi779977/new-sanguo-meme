# 新三国梗系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-green?style=for-the-badge&logo=gnu&logoColor=white" alt="License AGPL-3.0">
  <img src="https://img.shields.io/badge/Token-0%20消耗-orange?style=for-the-badge&logo=rocket&logoColor=white" alt="Token 0 消耗">
  <img src="https://img.shields.io/badge/版本-v2.8.4-purple?style=for-the-badge&logo=github&logoColor=white" alt="Version 2.8.4">
</p>

<p align="center">
  <b>模块化架构的新三国（2010版）梗引擎</b><br>
  <sub>纯本地运行 · 零 Token 消耗 · 智能兜底机制</sub>
</p>

---

## 📋 目录

- [✨ 核心特性](#-核心特性)
- [🚀 快速开始](#-快速开始)
- [⚙️ 配置说明](#️-配置说明)
- [💡 使用示例](#-使用示例)
- [📊 Token 消耗](#-token-消耗)
- [🛡️ 底线梗机制](#️-底线梗机制)
- [📁 项目结构](#-项目结构)
- [📜 版本历史](#-版本历史)
- [👤 作者](#-作者)

---

## ✨ 核心特性

| 特性 | 说明 |
|:---:|:---|
| 🚀 **Token 零消耗** | 纯本地运行，默认不调用任何 AI 接口 |
| 🎭 **底线梗随机回退** | 匹配失败时优雅兜底，随机选择 + 智能回退 |
| ⚖️ **可配置匹配** | 权重公式、温度参数均可调整 |
| 🔗 **Meta 梗融合** | 自动融合称呼类 meta 梗 |
| 🧠 **向量匹配** | 可选（默认关闭），支持语义相似度 |
| 🎬 **视频转文字录入** | 自动提取有效梗信息 |
| 🔍 **联网搜索增强** | 遇到不理解的信息自动搜索后匹配 |
| 🏷️ **话题映射** | 识别 LCK/科技/娱乐/日常等领域话题 |
| 📊 **信息充足度检测** | 智能判断是否需要联网搜索背景知识 |
| 🔎 **显式搜索** | 用户可主动要求搜索 |
| 💬 **日常闲聊** | 支持吃什么/天气/问候等日常对话 |

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Mutsumi779977/new-sanguo-meme.git
cd new-sanguo-meme

# 安装依赖
pip install pyyaml
```

### 运行

```bash
python run.py
```

### 基础使用

```python
from new_sanguo import create_agent

# 创建 Agent
agent = create_agent("user_id")

# 玩梗
reply = agent.handle("今天不想上班")
print(reply)  # 列位诸公，如果容得下今天不想在这里肆意放肆...
```

---

## ⚙️ 配置说明

编辑 `config.yaml`:

```yaml
# 温度参数（采样随机性）
matching:
  temperature: 1.0  # <1 更确定，>1 更随机

# 权重公式系数
scoring:
  weights:
    similarity: 0.6      # 语义相似度
    base_weight: 0.3     # 基础权重

# 向量功能（默认关闭）
embedding:
  enabled: false

# 搜索增强
search:
  enabled: true
  trigger_threshold: 0.3
```

---

## 💡 使用示例

### 日常玩梗

```
用户: 今天不想上班
系统: 列位诸公，如果容得下今天不想在这里肆意放肆，那就容我新三梗agent告老还乡了。
```

### LCK 电竞赛事

```
用户: gen2:0T1
系统: 不可能，绝对不可能！

用户: T1 3:0 横扫
系统: 我原本以为吕布已经天下无敌了
```

### 科技话题

```
用户: GPT5 发布了
系统: 好方略，不过我想稍作修改
```

### 日常闲聊

```
用户: 我晚上要吃什么呢？
系统: 是啊，吃什么

用户: 你好
系统: 来者何人
```

---

## 📊 Token 消耗

<p align="center">
  <img src="https://img.shields.io/badge/本地运行-0%20Token-success?style=flat-square" alt="本地0Token">
  <img src="https://img.shields.io/badge/搜索模式-~500--1500%20Tokens-blue?style=flat-square" alt="搜索模式">
</p>

| 功能 | Token 消耗 | 说明 |
|:---:|:---:|:---|
| 梗匹配 | **0** | 本地 SQLite + YAML 查询 |
| 梗生成 | **0** | 本地模板渲染 |
| 变体生成 | **0** | 本地规则替换 |
| 底线梗机制 | **0** | 本地随机选择 + 回退机制 |
| 向量匹配 | **0** | 本地模型（默认关闭）|
| 联网搜索 | **~500-1500** | 触发搜索时才消耗 |

**参照物对比：**
- 一次普通对话：~1,000-3,000 tokens
- 一次代码审查：~5,000-15,000 tokens  
- **本系统日常玩梗**：**0 tokens**（无限畅玩）

---

## 🛡️ 底线梗机制

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
- ✅ 多样性更高
- ✅ 避免尴尬输出（如"什么什么，没听说过"）
- ✅ 无死循环风险

---

## 📁 项目结构

```
new-sanguo-meme/
├── 📁 new_sanguo/           # 核心包
│   ├── __init__.py         # 包入口
│   ├── agent.py            # Agent主类
│   ├── models.py           # 数据模型
│   ├── config.py           # 配置管理
│   ├── database.py         # 数据库层
│   ├── service.py          # 业务逻辑
│   ├── search_adapter.py   # 搜索适配器
│   ├── topic_mapper.py     # 话题映射器
│   └── utils.py            # 工具函数
├── 📁 data/
│   ├── genku.yaml          # 梗数据源
│   ├── fallback_genkus.yaml # 底线梗配置
│   └── genku.db            # SQLite 数据库
├── 📁 tests/               # 测试文件
├── config.yaml             # 配置文件
├── run.py                  # CLI 入口
└── README.md               # 本文件
```

---

## 📜 版本历史

| 版本 | 更新内容 |
|:---:|:---|
| **v2.8.4** | 🎭 底线梗随机回退机制，🚀 Token 零消耗优化 |
| v2.7.0 | 删除角色模式，统一为纯梗模式；版本号统一 |
| v2.6.0 | 版本号统一、低频功能测试、Bug修复 |
| v2.5.13 | 补充单元测试 (pytest, 102 passed) |
| v2.5.2 | 话题映射系统（LCK/科技/娱乐）|
| v2.5.1 | 联网搜索增强 |
| v2.5 | 模块化重构，可配置权重/温度 |
| v2.0 | 统一架构，SQLite 持久化 |

---

## 👤 作者

<p align="center">
  <a href="https://space.bilibili.com/24250060">
    <img src="https://img.shields.io/badge/B站-梦雨__raining-00A1D6?style=for-the-badge&logo=bilibili&logoColor=white" alt="B站">
  </a>
</p>

---

<p align="center">
  <sub>
    ⚠️ <b>重要声明</b>：本软件仅供学习研究使用，禁止未经授权封装为商业 SaaS 服务。<br>
    采用 <b>AGPL-3.0</b> 许可证，违规使用将追究法律责任。
  </sub>
</p>
