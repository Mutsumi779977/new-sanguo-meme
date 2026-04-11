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


"""
新三国梗系统 - 数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum, auto
from datetime import datetime


class State(Enum):
    """Agent 状态机状态"""
    IDLE = auto()
    INPUT_WAITING = auto()
    VIDEO_PROCESSING = auto()
    CONFIRM = auto()
    FEEDBACK_REASON = auto()


@dataclass
class Genku:
    """
    梗数据模型
    
    Attributes:
        genku_id: 唯一标识符，如 xsg_cc_001
        original: 原文
        person: 人物
        source: 出处
        context: 情境描述
        emotions: 情绪标签列表
        intensity: 强度 (弱/中/强)
        tags: 场景标签
        semantic_keywords: 语义关键词
        weight: 权重 1-5
        variant_template: 变体模板
        variable_desc: 变量说明
        usage_count: 引用频次
        effectiveness: 有效性评分
        is_meta: 是否为 meta 梗
        fusion_targets: 可融合的目标标签
        fusion_rules: 融合规则配置
    """
    genku_id: str
    original: str
    person: str
    source: str
    context: str
    emotions: List[str]
    intensity: str
    tags: List[str]
    semantic_keywords: List[str]
    weight: int
    variant_template: Optional[str] = None
    variable_desc: Optional[Dict[str, str]] = None
    usage_count: int = 0
    effectiveness: float = 0.0
    is_meta: bool = False
    fusion_targets: List[str] = field(default_factory=list)
    fusion_rules: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_yaml(cls, data: Dict) -> 'Genku':
        """从 YAML 字典创建 Genku 实例"""
        return cls(
            genku_id=data.get('梗ID', ''),
            original=data.get('原文', ''),
            person=data.get('人物', '未知'),
            source=data.get('出处', ''),
            context=data.get('情境', ''),
            emotions=data.get('情绪', []),
            intensity=data.get('强度', '中'),
            tags=data.get('场景标签', []),
            semantic_keywords=data.get('语义关键词', []),
            weight=data.get('权重', 3),
            variant_template=data.get('变体模板'),
            variable_desc=data.get('变量说明'),
            usage_count=data.get('引用频次', 0),
            effectiveness=data.get('effectiveness', 0.0),
            is_meta=data.get('is_meta', False),
            fusion_targets=data.get('fusion_targets', []),
            fusion_rules=data.get('融合规则')
        )


@dataclass
class UserPreference:
    """
    用户偏好模型
    
    记录用户对特定人物、标签的喜好程度，
    用于个性化梗推荐。
    """
    user_id: str
    liked_persons: Dict[str, float] = field(default_factory=dict)
    liked_tags: Dict[str, float] = field(default_factory=dict)
    avg_intensity: str = '中'
    total_interactions: int = 0
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback_stats: Dict[str, int] = field(default_factory=lambda: {'like': 0, 'dislike': 0})
    
    @classmethod
    def default(cls, user_id: str) -> 'UserPreference':
        """创建默认用户偏好"""
        return cls(user_id=user_id)
    
    def update_person_score(self, person: str, delta: float, decay: float = 0.9):
        """更新人物偏好分数"""
        current = self.liked_persons.get(person, 0)
        self.liked_persons[person] = current * decay + delta
    
    def update_tag_score(self, tag: str, delta: float, decay: float = 0.9):
        """更新标签偏好分数"""
        current = self.liked_tags.get(tag, 0)
        self.liked_tags[tag] = current * decay + delta
