#!/usr/bin/env python3
"""
底线梗功能测试 v2.8.0
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo import create_agent

def test_fallback_genkus():
    """测试底线梗功能"""
    print("=" * 60)
    print("底线梗功能测试 v2.8.0")
    print("=" * 60)
    
    agent = create_agent("test_fallback")
    
    # 检查自我认知
    print(f"\n🎭 自我认知: {agent.identity}")
    
    # 检查底线梗配置
    print(f"📦 底线梗数量: {len(agent.fallback_genkus.get('fallback_genkus', []))}")
    
    # 测试极端情况输入（应该触发底线梗）
    test_cases = [
        "这是一段完全无法匹配的内容",  # 应该触发底线梗
        "xyz123456789",  # 无意义字符串
        "今天天气真好啊但是我不知道该说什么",  # 闲聊但无匹配
    ]
    
    print("\n" + "=" * 60)
    print("极端情况测试（应触发底线梗）")
    print("=" * 60)
    
    for text in test_cases:
        result = agent.handle(text)
        print(f"\n输入: {text}")
        if isinstance(result, dict):
            print(f"结果: 需要搜索 - {result.get('reason', '未知')}")
        else:
            print(f"输出: {result}")
            # 检查是否是底线梗
            fallback_keywords = ['没听说过', '胡言乱语', '叉出去', '告老还乡', '大胆', '放肆']
            is_fallback = any(kw in result for kw in fallback_keywords)
            if is_fallback:
                print("✅ 触发了底线梗")
            else:
                print("ℹ️ 正常回复")
    
    # 测试 _cmd_info 显示自我认知
    print("\n" + "=" * 60)
    print("信息命令测试")
    print("=" * 60)
    info = agent.handle("/新三国")
    print(info)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_fallback_genkus()
