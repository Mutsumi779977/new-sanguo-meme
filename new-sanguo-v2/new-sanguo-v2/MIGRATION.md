# 新三国梗系统 v2.0 迁移说明

## 主要改进

### 1. 架构统一
- **旧版**: 4个独立 Skill（new-sanguo/tianyi/luanshi/liewei）
- **新版**: 1个统一 Agent，内部路由+状态机管理

### 2. 数据层升级
- **旧版**: 纯 YAML，运行时全量加载
- **新版**: YAML（源文件）+ SQLite（运行时）
  - 启动时自动导入 YAML 到 SQLite
  - 运行时读写 SQLite（有索引、事务安全）
  - 支持增量更新和持久化

### 3. 匹配算法
- **旧版**: 简单关键词匹配 + random.choice
- **新版**: 
  - 向量化语义匹配（Sentence-Transformer）
  - 权重加成（基础权重1-5 + 引用频次）
  - 温度采样选择（保持一定随机性）

### 4. 状态机
- **旧版**: 无状态，每轮独立
- **新版**: 
  - `/录入` 进入多轮交互模式
  - 支持确认/取消/修改
  - 短期上下文记忆（当前会话）

### 5. 错误处理
- **旧版**: 基本无错误处理
- **新版**:
  - 输入验证（聊天阶段限制2000字）
  - 具体错误信息展示
  - 优雅降级策略

## 命令对照

| 旧命令 | 新命令 | 说明 |
|--------|--------|------|
| /天意 | /录入 | 进入录入模式 |
| /乱世 查询 | /查询 | 查询梗库 |
| /乱世 统计 | /统计 | 显示统计 |
| /列位诸公 | /玩梗 | 手动触发 |
| /纯梗 /角色 | /模式 纯梗/角色 | 切换模式 |

## 数据迁移

启动时会自动从 `../new-sanguo/data/genku.yaml` 导入数据。

如需手动导入：
```python
from agent import Database
db = Database()
count = db.import_from_yaml("../new-sanguo/data/genku.yaml")
print(f"导入 {count} 条梗")
```

## 待实现功能

- [ ] 智能变体生成（模板变量替换）
- [ ] 用户偏好学习（长期记忆）
- [ ] 使用反馈收集（点赞/点踩）
- [ ] 向量增量更新
- [ ] 测试用例

## 安装依赖

```bash
pip install sentence-transformers numpy pyyaml
```

如果使用 CPU 运行模型：
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```
