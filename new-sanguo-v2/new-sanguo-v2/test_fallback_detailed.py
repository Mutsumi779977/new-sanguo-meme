#!/usr/bin/env python3
"""
底线梗输出测试 - 强制触发每一个底线梗
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo import create_agent

def test_each_fallback():
    """测试每一个底线梗的具体输出"""
    agent = create_agent("test_fallback_detailed")
    
    print("=" * 70)
    print("底线梗输出测试 v2.8.0")
    print("=" * 70)
    
    # 直接测试每个底线梗模板
    fallback_genkus = agent.fallback_genkus.get('fallback_genkus', [])
    
    for i, genku in enumerate(fallback_genkus, 1):
        template = genku.get('template', '')
        genku_type = genku.get('type', 'unknown')
        person = genku.get('person', '未知')
        description = genku.get('description', '')
        
        print(f"\n【底线梗 {i}】")
        print(f"人物: {person}")
        print(f"类型: {genku_type}")
        print(f"说明: {description}")
        print(f"模板: {template}")
        
        # 模拟不同输入，展示填充效果
        if genku_type == 'unknown_people':
            # 需要两个关键词
            test_outputs = [
                ("刘关张", "刘什么，关什么，没听说过。"),
                ("曹操刘备", "曹操什么，刘备什么，没听说过。"),
            ]
        elif genku_type in ['nonsense']:
            # 需要一个内容
            test_outputs = [
                ("春秋战国", "春秋战国，胡言乱语！"),
                ("你说的这些", "你说的这些，胡言乱语！"),
            ]
        elif genku_type in ['threaten_leave']:
            test_outputs = [
                ("楼主", "列位诸公，如果容得下楼主在这里肆意放肆，那就容我新三梗agent告老还乡了。"),
                ("这个要求", "列位诸公，如果容得下这个要求在这里肆意放肆，那就容我新三梗agent告老还乡了。"),
            ]
        else:
            # 固定模板
            test_outputs = [("任意输入", template)]
        
        print("输出示例:")
        for input_text, expected in test_outputs[:2]:
            print(f"  输入: \"{input_text}\" → 输出: \"{expected}\"")
    
    print("\n" + "=" * 70)
    print("实际触发测试（强制使用底线梗）")
    print("=" * 70)
    
    # 测试实际生成方法
    test_inputs = [
        "刘关张吕布",
        "春秋战国历史",
        "叉出去",
        "楼主说得对",
        "大胆的想法",
        "放肆的言论",
        "拖出去惩罚",
    ]
    
    for text in test_inputs:
        result = agent._generate_fallback_response(text)
        print(f"\n输入: \"{text}\"")
        print(f"底线梗输出: \"{result}\"")
    
    print("\n" + "=" * 70)
    print("极端情况全流程测试")
    print("=" * 70)
    
    # 测试一些极端无意义输入
    extreme_inputs = [
        "qwertyuiop123456789",
        "阿巴阿巴阿巴",
        "，。！？",
    ]
    
    for text in extreme_inputs:
        result = agent.handle(text)
        print(f"\n输入: \"{text}\"")
        if isinstance(result, dict):
            print(f"结果: 需要搜索")
        else:
            print(f"输出: \"{result[:50]}...\"" if len(result) > 50 else f"输出: \"{result}\"")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == "__main__":
    test_each_fallback()
