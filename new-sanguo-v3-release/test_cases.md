# 新三国梗系统测试用例

## 1. 基础功能测试

### 1.1 命令路由
```python
def test_commands():
    agent = NewSanguoAgent("test")
    
    # 测试 /帮助
    assert "/录入" in agent.handle("/帮助")
    
    # 测试 /统计
    assert "总计" in agent.handle("/统计")
    
    # 测试 /模式
    assert "已切换" in agent.handle("/模式 纯梗")
    assert "已切换" in agent.handle("/模式 角色")
    
    print("✅ 命令路由测试通过")
```

### 1.2 状态机 - 录入流程
```python
def test_input_flow():
    agent = NewSanguoAgent("test")
    
    # 进入录入模式
    r1 = agent.handle("/录入")
    assert agent.state == "input_waiting"
    assert "进入录入模式" in r1
    
    # 发送数据
    r2 = agent.handle("""梗：测试梗
人物：测试人物
出处：测试出处
权重：3""")
    assert agent.state == "confirm"
    assert "预览" in r2
    
    # 确认
    r3 = agent.handle("确认")
    assert agent.state == "idle"
    assert "已保存" in r3
    
    print("✅ 录入流程测试通过")
```

### 1.3 取消功能
```python
def test_cancel():
    agent = NewSanguoAgent("test")
    
    agent.handle("/录入")
    assert agent.state == "input_waiting"
    
    r = agent.handle("/取消")
    assert agent.state == "idle"
    assert "已取消" in r
    
    print("✅ 取消功能测试通过")
```

## 2. 匹配算法测试

### 2.1 关键词匹配
```python
def test_keyword_match():
    agent = NewSanguoAgent("test")
    
    # 测试否定场景
    r = agent.handle("我不想去上班")
    assert "不可能" in r or "不想" in r
    
    # 测试享受场景
    r = agent.handle("今天想放松一下")
    assert "奏乐" in r or "享受" in r or "不可能" in r
    
    print("✅ 关键词匹配测试通过")
```

### 2.2 向量化匹配（如果安装）
```python
def test_vector_match():
    agent = NewSanguoAgent("test")
    
    if not agent.model:
        print("⚠️ 向量化模型未安装，跳过")
        return
    
    # 语义相近但不完全相同
    r = agent.handle("这简直难以置信")  # 对应"不可能"
    assert "不可能" in r
    
    r = agent.handle("让我们庆祝一下")  # 对应"接着奏乐"
    assert "奏乐" in r
    
    print("✅ 向量化匹配测试通过")
```

## 3. 变体生成测试

### 3.1 模板替换
```python
def test_variant_generation():
    agent = NewSanguoAgent("test")
    
    # 测试变量提取
    entities = extract_entities("不想上班了")
    assert entities['对象'] == '上班'
    
    entities = extract_entities("今天不想下雨")
    assert entities['对象'] == '下雨'
    
    print("✅ 变量提取测试通过")
```

## 4. 边界情况测试

### 4.1 超长输入
```python
def test_long_input():
    agent = NewSanguoAgent("test")
    
    long_text = "测试" * 1000  # 2000字
    r = agent.handle(long_text)
    assert "限制2000字" in r
    
    print("✅ 超长输入测试通过")
```

### 4.2 无匹配情况
```python
def test_no_match():
    agent = NewSanguoAgent("test")
    
    r = agent.handle("abcdefg无关内容")
    assert "还没学到" in r or "不会接" in r
    
    print("✅ 无匹配情况测试通过")
```

### 4.3 错误处理
```python
def test_error_handling():
    agent = NewSanguoAgent("test")
    
    # 未知命令
    r = agent.handle("/未知命令")
    assert "未知命令" in r
    
    print("✅ 错误处理测试通过")
```

## 5. 数据持久化测试

### 5.1 频次更新
```python
def test_usage_count():
    agent = NewSanguoAgent("test")
    
    # 记录初始频次
    initial = agent.genku_list[0].usage_count
    
    # 使用一次
    agent.handle("不可能")
    
    # 重新加载
    agent2 = NewSanguoAgent("test")
    after = agent2.genku_list[0].usage_count
    
    assert after == initial + 1
    
    print("✅ 频次更新测试通过")
```

## 运行测试

```bash
cd ~/.openclaw/workspace/skills/new-sanguo-v2
source venv/bin/activate
python3 test_agent.py
```
