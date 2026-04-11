#!/usr/bin/env python3
import os
os.environ['DISABLE_EMBEDDING'] = '1'

from agent import NewSanguoAgent

print('🎭 新三国梗系统 v2.1 - 测试')
print('='*60)

a = NewSanguoAgent('test_user')
print(f'✅ 加载 {len(a.service.genku_list)} 条梗')

# 测试1: 玩梗
print('\n1️⃣ /玩梗 不可能')
result = a.handle('/玩梗 不可能')
print(f'结果: {result}')

# 测试2: 反馈（多轮对话）
print('\n2️⃣ /喜欢（进入多轮原因收集）')
print(a.handle('/喜欢'))

print('\n   输入原因: 很经典')
print(a.handle('很经典'))

# 测试3: 偏好
print('\n3️⃣ /偏好（显示学习结果）')
print(a.handle('/偏好'))

# 测试4: 统计
print('\n4️⃣ /统计')
print(a.handle('/统计'))

# 测试5: 查询
print('\n5️⃣ /查询 曹操')
result = a.handle('/查询 曹操')
print(result)

# 测试6: 录入
print('\n6️⃣ 录入流程测试')
a.handle('/录入')
print(a.handle('''梗：测试新梗123
人物：测试员
出处：测试场景
情境：测试用
权重：3'''))
print(a.handle('确认'))

print('\n✅ 测试完成')
