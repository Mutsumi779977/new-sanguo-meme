"""
结构化搜索信息模型 - 用于多维度梗匹配
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class EvaluationType(Enum):
    """评价类型"""
    PRAISE = "赞扬"      # 正面评价
    CRITICISM = "批评"  # 负面评价  
    NEUTRAL = "中立"    # 中立评价
    COMPARISON = "对比" # 对比评价
    UNKNOWN = "未知"    # 未知


class EntityType(Enum):
    """实体类型"""
    PERSON = "人物"
    TEAM = "战队"
    EVENT = "事件"
    WORK = "作品"
    CONCEPT = "概念"


@dataclass
class Entity:
    """结构化实体"""
    name: str                    # 实体名称
    entity_type: EntityType      # 实体类型
    aliases: List[str] = field(default_factory=list)  # 别名
    attributes: Dict[str, Any] = field(default_factory=dict)  # 属性
    
    def __post_init__(self):
        if not self.aliases:
            self.aliases = [self.name]


@dataclass
class Sentiment:
    """情感分析结果"""
    polarity: float  # -1.0 ~ 1.0，负面到正面
    intensity: str   # 弱/中/强
    keywords: List[str] = field(default_factory=list)  # 情感关键词
    
    def is_positive(self) -> bool:
        return self.polarity > 0.3
    
    def is_negative(self) -> bool:
        return self.polarity < -0.3


@dataclass
class StructuredSearchResult:
    """
    结构化搜索结果
    
    用于多维度梗匹配，包含：
    - 原始查询
    - 提取的实体
    - 情感倾向
    - 评价类型
    - 关键属性
    - 推荐标签
    """
    # 基础信息
    query: str
    raw_summary: str
    
    # 实体信息
    entities: List[Entity] = field(default_factory=list)
    main_entity: Optional[Entity] = None  # 主要实体
    
    # 情感与评价
    sentiment: Optional[Sentiment] = None
    evaluation_type: EvaluationType = EvaluationType.UNKNOWN
    
    # 关键属性（用于模板填充）
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # 推荐标签（用于梗匹配）
    recommended_tags: List[str] = field(default_factory=list)
    recommended_emotions: List[str] = field(default_factory=list)
    
    # 原始搜索结果（保留）
    raw_results: List[Dict] = field(default_factory=list)
    
    def to_matching_context(self) -> Dict[str, Any]:
        """
        转换为匹配上下文，供多维度匹配使用
        
        Returns:
            包含所有维度的匹配上下文
        """
        context = {
            # 实体维度
            'entity_name': self.main_entity.name if self.main_entity else '',
            'entity_type': self.main_entity.entity_type.value if self.main_entity else '',
            'entity_aliases': [e.name for e in self.entities],
            
            # 情感维度
            'sentiment_polarity': self.sentiment.polarity if self.sentiment else 0,
            'sentiment_intensity': self.sentiment.intensity if self.sentiment else '中',
            'is_positive': self.sentiment.is_positive() if self.sentiment else False,
            'is_negative': self.sentiment.is_negative() if self.sentiment else False,
            
            # 评价维度
            'evaluation_type': self.evaluation_type.value,
            
            # 标签维度
            'recommended_tags': self.recommended_tags,
            'recommended_emotions': self.recommended_emotions,
            
            # 属性维度（用于模板填充）
            'attributes': self.attributes,
        }
        return context


# 预定义的情感关键词映射
SENTIMENT_KEYWORDS = {
    'positive': [
        '冠军', '王者', '传奇', '巅峰', '无敌', '天才', '神', 'goat', 
        '伟大', '优秀', '出色', '完美', ' masterpiece', '经典', '不朽',
        '第一', '最强', '无人能敌', '坚刚', '万念不能乱其心'
    ],
    'negative': [
        '糟糕', '烂', '垃圾', '废物', '下滑', '堕落', '失败', '输',
        '菜', '坑', '暴雷', '塌房', '差评', '难看', '无聊'
    ],
    'intensity_strong': [
        '绝对', '完全', '彻底', '极其', '非常', '最', '第一', '无敌',
        '不可能', '绝对不可能', '天下无敌'
    ],
    'intensity_weak': [
        '有点', '稍微', '还行', '一般', '凑合', '普通', '正常'
    ]
}


# 预定义的评价类型关键词
EVALUATION_PATTERNS = {
    EvaluationType.PRAISE: ['评价', '怎么看', '如何看', '觉得', '认为', '厉害', '强'],
    EvaluationType.CRITICISM: ['吐槽', '批评', '喷', '骂', '烂', '差'],
    EvaluationType.COMPARISON: ['对比', '比较', 'vs', '和', '哪个', '差距', '区别'],
    EvaluationType.NEUTRAL: ['介绍', '是什么', '谁', '科普']
}
