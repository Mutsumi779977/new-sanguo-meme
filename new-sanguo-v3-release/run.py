"""
新三国梗系统 v3.0
Copyright (C) 2025 梦雨_raining (B站: https://space.bilibili.com/24250060)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

警告：本软件仅供学习研究使用，禁止未经授权封装为商业SaaS服务！
"""


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
