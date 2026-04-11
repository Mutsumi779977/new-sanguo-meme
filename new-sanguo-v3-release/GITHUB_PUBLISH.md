# GitHub 开源发布指南

## 步骤 1: 准备仓库

### 1.1 创建必要的文件

```bash
cd /root/.openclaw/workspace/skills/new-sanguo-v2

# 创建 LICENSE 文件（MIT 许可证）
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 [你的名字]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 创建 .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 数据库（可从 YAML 重新生成）
data/genku.db

# 旧版本备份
*.old

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 测试
.pytest_cache/
.coverage
htmlcov/

# 日志
*.log
EOF
```

### 1.2 整理项目结构

```bash
# 确保没有不需要的文件
rm -f agent.py.old
cd data && rm -f genku.db && cd ..
```

## 步骤 2: 创建 GitHub 仓库

### 2.1 在 GitHub 上创建新仓库

1. 访问 https://github.com/new
2. 填写信息：
   - **Repository name**: `new-sanguo-genku` (或你喜欢的名字)
   - **Description**: 新三国梗系统 - 基于2010版新三国的中文玩梗Agent
   - **Public** (公开) 或 **Private** (私有)
   - **Add a README**: ❌ 不勾选 (我们已有 README.md)
   - **Add .gitignore**: ❌ 不勾选 (我们已有 .gitignore)
   - **Choose a license**: ❌ 不勾选 (我们已有 LICENSE)
3. 点击 **Create repository**

### 2.2 推送代码到 GitHub

```bash
cd /root/.openclaw/workspace/skills/new-sanguo-v2

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 新三国梗系统 v2.5.12

- 模块化架构 (9个核心模块)
- 话题映射系统 (8大话题类别)
- 信息充足度检测 (方案A+)
- 显式搜索功能
- 日常闲聊支持
- 高频梗防滥用机制
- 完整 API 文档
- 单元测试 (19个测试用例)"

# 关联远程仓库（替换为你的用户名）
git remote add origin https://github.com/你的用户名/new-sanguo-genku.git

# 推送
git push -u origin master
# 或如果是 main 分支：
git push -u origin main
```

## 步骤 3: 创建 Release（推荐）

### 3.1 在 GitHub 上创建 Release

1. 访问你的仓库页面
2. 点击右侧 **Releases** → **Create a new release**
3. 填写信息：
   - **Choose a tag**: 输入 `v2.5.12`，点击 "Create new tag"
   - **Release title**: `新三国梗系统 v2.5.12`
   - **Description**:
```markdown
## 新三国梗系统 v2.5.12

### 核心特性
- 🎭 **双模式输出**: 纯梗模式 / 角色模式
- 🧠 **话题映射**: 自动识别 8 大话题类别
- 🔍 **智能搜索**: 信息充足度检测 + 显式搜索
- 💬 **日常闲聊**: 吃什么/天气/问候等场景
- ⚖️ **防滥用机制**: 高频梗自动降权

### 快速开始
```bash
pip install pyyaml
python run.py
```

### 文档
- [API文档](API.md)
- [使用说明](README.md)

### 完整更新日志
详见 [版本历史](#版本历史)
```

4. 上传发布包：
   - 点击 **Attach binaries** 
   - 上传 `new-sanguo-v2-release.tar.gz`

5. 点击 **Publish release**

## 步骤 4: 可选 - 添加到 PyPI（Python 包索引）

如果你想让别人可以用 `pip install new-sanguo-genku` 安装：

### 4.1 创建 setup.py

```bash
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="new-sanguo-genku",
    version="2.5.12",
    author="你的名字",
    author_email="你的邮箱",
    description="新三国梗系统 - 基于2010版新三国的中文玩梗Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/你的用户名/new-sanguo-genku",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
        "vector": ["sentence-transformers>=2.2.0", "numpy>=1.24.0"],
    },
    package_data={
        "new_sanguo": ["../data/*.yaml", "../config.yaml"],
    },
    include_package_data=True,
)
EOF
```

### 4.2 发布到 PyPI

```bash
# 安装工具
pip install twine build

# 构建
cd /root/.openclaw/workspace/skills/new-sanguo-v2
python -m build

# 上传到 PyPI（需要账号）
python -m twine upload dist/*
```

## 步骤 5: 分享和推广

### 5.1 完善仓库信息

在 GitHub 仓库页面：
1. 点击 **About** 右侧的 ⚙️ 齿轮
2. 添加 **Topics**: `python`, `agent`, `meme`, `new-sanguo`, `chatbot`, `chinese-nlp`
3. 勾选 **Releases** 和 **Packages**

### 5.2 分享到社区

- V2EX: https://www.v2ex.com/t/create
- 知乎: 写一篇文章介绍
- Twitter/X: 发推 @ 相关账号
- Discord/微信群: 分享给感兴趣的朋友

## 常见问题

### Q: 代码里有我的个人信息怎么办？
```bash
# 检查是否有邮箱、姓名等
grep -r "你的邮箱\|你的名字\|@qq.com\|@gmail.com" new_sanguo/

# 清理后重新提交
git add .
git commit --amend --no-edit
git push -f
```

### Q: 如何更新 Release？
1. 修改代码
2. `git add . && git commit -m "v2.5.13: 修复xxx"`
3. `git push`
4. 在 GitHub 创建新的 Release (v2.5.13)

### Q: 别人怎么用我的项目？
在你的 README 顶部加上：
```markdown
## 安装

```bash
# 方式1: 直接下载
git clone https://github.com/你的用户名/new-sanguo-genku.git
cd new-sanguo-genku
pip install pyyaml
python run.py

# 方式2: 如果发布了PyPI
pip install new-sanguo-genku
```
```

---

需要我帮你执行其中哪些步骤吗？
