# 智能变体生成实现方案

## 目标
将模板 `[对象]，绝对[否定词]！` 根据用户输入自动替换变量。

## 用户输入分析

用户说：`"今天不想上班，太累了"`

期望输出：`"上班？不可能，绝对不可能！"`

## 实现步骤

### 1. 变量提取
从用户输入中提取关键实体：

```python
def extract_entities(user_text: str) -> Dict[str, str]:
    """从用户输入中提取可用于替换的实体"""
    
    # 使用简单的规则 + 关键词匹配
    entities = {
        '对象': None,
        '否定词': '不可能',
        '动作1': None,
        '动作2': None,
    }
    
    # 提取"不想做/不要做"的对象
    # 模式：不想 + [动词] + [名词]
    patterns = [
        r'不想(.*?)了',      # 不想上班了 → 上班
        r'不要(.*?)了',      # 不要加班了 → 加班
        r'拒绝(.*?)',        # 拒绝加班 → 加班
        r'今天(.*?)',        # 今天下雨了 → 下雨
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_text)
        if match:
            entities['对象'] = match.group(1).strip()
            break
    
    return entities
```

### 2. 模板变量映射

定义变量和提取规则的对应关系：

```python
VARIABLE_EXTRACTORS = {
    '[对象]': {
        'patterns': [
            r'不想(.*?)了',
            r'不要(.*?)了',
            r'拒绝(.*?)',
        ],
        'default': '这件事'
    },
    '[否定词]': {
        'patterns': [],  # 固定词典
        'default': '不可能'
    },
    '[动作1]': {
        'patterns': [r'(.*?)一下', r'去(.*?)'],
        'default': '奏乐'
    },
}
```

### 3. 智能替换函数

```python
def generate_variant(genku: Genku, user_text: str) -> str:
    """生成变体"""
    
    if not genku.variant_template:
        return genku.original
    
    template = genku.variant_template
    result = template
    
    # 从 variable_desc 获取变量定义
    variables = genku.variable_desc or {}
    
    # 提取用户输入中的实体
    entities = extract_entities(user_text)
    
    # 逐个替换变量
    for var_name, desc in variables.items():
        placeholder = f"[{var_name}]"
        if placeholder in result:
            # 尝试从用户输入中提取
            value = entities.get(var_name)
            
            # 如果提取失败，使用默认值
            if not value:
                # 从 desc 中解析默认值
                value = parse_default_from_desc(desc)
            
            result = result.replace(placeholder, value)
    
    return result
```

### 4. 示例

```python
# 用户输入
text = "今天不想上班了，太累了"

# 梗数据
genku = {
    '原文': '不可能，绝对不可能',
    'variant_template': '[对象]？不可能，绝对[否定词]！',
    'variable_desc': {
        '对象': '要否定的事物（加班、下雨、失败...）',
        '否定词': '不可能/不行/不存在'
    }
}

# 提取
entities = {
    '对象': '上班',
    '否定词': '不可能'
}

# 生成
variant = "上班？不可能，绝对不可能！"
```

### 5. 增强：语义理解

更高级的实现可以用向量化匹配找到最合适的替换词：

```python
def smart_extract(user_text: str, target_var: str) -> str:
    """智能提取，使用语义匹配"""
    
    # 分词
    words = jieba.lcut(user_text)
    
    # 根据目标变量类型选择候选词
    if target_var == '对象':
        # 找名词或动词短语
        candidates = [w for w in words if w.pos in ['n', 'v']]
    
    # 选择语义最相关的
    best_match = max(candidates, key=lambda w: 
        similarity(w.vector, target_var))
    
    return best_match
```

## 简化版实现（当前采用）

为了快速可用，先用规则匹配：

```python
def generate_variant_simple(genku: Genku, user_text: str) -> str:
    """简化版变体生成"""
    
    if not genku.variant_template:
        return genku.original
    
    template = genku.variant_template
    
    # 提取对象：不想/不要 + XX + 了
    match = re.search(r'不想(.*?)了|不要(.*?)了', user_text)
    if match:
        obj = match.group(1) or match.group(2)
        template = template.replace('[对象]', obj.strip())
    else:
        template = template.replace('[对象]', '这件事')
    
    # 否定词固定
    template = template.replace('[否定词]', '不可能')
    
    return template
```
