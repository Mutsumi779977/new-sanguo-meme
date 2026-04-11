#!/usr/bin/env python3
"""
新三国梗系统 CLI 入口
"""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

from new_sanguo import create_agent


def main():
    """主函数"""
    print("🎭 新三国梗系统 v3.0")
    print("输入 /帮助 查看命令，/退出 退出")
    print()
    
    agent = create_agent("cli_user")
    print(f"加载了 {len(agent.service.genku_list)} 条梗")
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            if not user_input or user_input in ['/退出', '/quit', 'exit', 'quit']:
                break
            
            reply = agent.handle(user_input)
            print(f"\n🎭 {reply}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n⚠️ 错误: {e}")
    
    print("\n再见！")


if __name__ == "__main__":
    main()
