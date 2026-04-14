"""
新三国梗系统 v2.7.0
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



"""
新三国梗系统 v2.5.13

模块化架构，支持：
- 可配置权重公式
- 温度参数采样
- 可配置融合策略
- 向量功能可选（默认关闭）
- 快速/深度回复区分（方案A+信息充足度检测）

Usage:
    from new_sanguo import create_agent
    agent = create_agent("user_id")
    result = agent.handle("用户输入")
    
    # result可以是字符串（快速回复）或字典（需要搜索）
    if isinstance(result, dict) and result.get('type') == 'need_search':
        # 执行搜索后再调用agent
        search_results = kimi_search(result['query'])
        reply = agent.handle_with_search(result['query'], search_results)
    else:
        reply = result
"""

from .models import Genku, UserPreference, State
from .config import Config
from .database import Database
from .service import GenkuService
from .search_adapter import SearchAdapter, SearchResult, get_search_adapter
from .topic_mapper import TopicMapper, TopicCategory, get_topic_mapper
from .agent import NewSanguoAgent, create_agent
from .utils import setup_logger
from .intent_system import IntentSystem, UnifiedIntent, GenkuFunction

# 结构化搜索组件（新增）
from .structured_search import (
    StructuredSearchResult, Entity, EntityType, 
    Sentiment, EvaluationType
)
from .search_parser import SearchResultParser
from .multi_matcher import MultiDimensionalMatcher, MatchResult

__version__ = "2.6.0"
__all__ = [
    'Genku',
    'UserPreference',
    'State',
    'Config',
    'Database',
    'GenkuService',
    'SearchAdapter',
    'SearchResult',
    'get_search_adapter',
    'TopicMapper',
    'TopicCategory',
    'get_topic_mapper',
    'NewSanguoAgent',
    'create_agent',
    'setup_logger',
    'IntentSystem',
    'UnifiedIntent',
    'GenkuFunction',
    # 新增结构化搜索组件
    'StructuredSearchResult',
    'Entity',
    'EntityType',
    'Sentiment',
    'EvaluationType',
    'SearchResultParser',
    'MultiDimensionalMatcher',
    'MatchResult',
]
