"""
多维度梗匹配器
支持从多个维度匹配最合适的梗
"""
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import random

from .models import Genku
from .structured_search import StructuredSearchResult, EvaluationType


@dataclass
class MatchDimension:
    """匹配维度"""
    name: str           # 维度名称
    weight: float       # 维度权重
    score: float        # 该维度的得分


@dataclass
class MatchResult:
    """匹配结果"""
    genku: Genku
    total_score: float
    dimensions: List[MatchDimension]
    context: Dict[str, Any]  # 推荐的填充变量


class MultiDimensionalMatcher:
    """
    多维度梗匹配器
    
    支持以下匹配维度：
    1. 实体匹配 - 人物/战队/作品名
    2. 情感匹配 - 情感倾向和强度
    3. 场景匹配 - 标签匹配
    4. 语义匹配 - 关键词相似度
    5. 评价类型匹配 - 赞扬/批评/对比
    """
    
    # 各维度权重配置
    DIMENSION_WEIGHTS = {
        'entity': 0.30,      # 实体匹配（最重要）
        'sentiment': 0.25,   # 情感匹配
        'scene': 0.20,       # 场景标签匹配
        'semantic': 0.15,    # 语义关键词匹配
        'evaluation': 0.10,  # 评价类型匹配
    }
    
    def __init__(self, genku_list: List[Genku]):
        self.genku_list = genku_list
        
    def match(self, context: Dict[str, Any], top_n: int = 3) -> List[MatchResult]:
        """
        多维度匹配
        
        Args:
            context: 匹配上下文（来自StructuredSearchResult）
            top_n: 返回前N个结果
            
        Returns:
            按总分排序的匹配结果列表
        """
        results = []
        
        for genku in self.genku_list:
            dimensions = []
            
            # 1. 实体匹配
            entity_score = self._match_entity(genku, context)
            dimensions.append(MatchDimension('entity', self.DIMENSION_WEIGHTS['entity'], entity_score))
            
            # 2. 情感匹配
            sentiment_score = self._match_sentiment(genku, context)
            dimensions.append(MatchDimension('sentiment', self.DIMENSION_WEIGHTS['sentiment'], sentiment_score))
            
            # 3. 场景匹配
            scene_score = self._match_scene(genku, context)
            dimensions.append(MatchDimension('scene', self.DIMENSION_WEIGHTS['scene'], scene_score))
            
            # 4. 语义匹配
            semantic_score = self._match_semantic(genku, context)
            dimensions.append(MatchDimension('semantic', self.DIMENSION_WEIGHTS['semantic'], semantic_score))
            
            # 5. 评价类型匹配
            eval_score = self._match_evaluation(genku, context)
            dimensions.append(MatchDimension('evaluation', self.DIMENSION_WEIGHTS['evaluation'], eval_score))
            
            # 计算总分
            total_score = sum(d.weight * d.score for d in dimensions)
            
            # 生成交互变量
            template_vars = self._generate_template_vars(genku, context)
            
            results.append(MatchResult(
                genku=genku,
                total_score=total_score,
                dimensions=dimensions,
                context=template_vars
            ))
        
        # 按总分排序
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_n]
    
    def _match_entity(self, genku: Genku, context: Dict[str, Any]) -> float:
        """实体匹配：检查梗的人物是否与搜索实体匹配"""
        entity_name = context.get('entity_name', '')
        entity_aliases = context.get('entity_aliases', [])
        
        if not entity_name:
            return 0.5  # 无实体信息，中等分数
        
        # 直接匹配人物名
        if genku.person and any(alias in genku.person for alias in entity_aliases):
            return 1.0
        
        # 匹配语义关键词
        if any(alias in kw for alias in entity_aliases for kw in genku.semantic_keywords):
            return 0.9
        
        # 匹配标签
        if any(alias.lower() in tag.lower() for alias in entity_aliases for tag in genku.tags):
            return 0.8
        
        return 0.3
    
    def _match_sentiment(self, genku: Genku, context: Dict[str, Any]) -> float:
        """情感匹配：检查梗的情感标签是否与搜索情感匹配"""
        is_positive = context.get('is_positive', False)
        is_negative = context.get('is_negative', False)
        intensity = context.get('sentiment_intensity', '中')
        
        # 统计梗的情感倾向
        positive_emotions = ['赞叹', '得意', '嘲讽', '兴奋', '坚定']
        negative_emotions = ['无奈', '悲伤', '愤怒', '失望', '痛苦']
        
        genku_positive = any(e in genku.emotions for e in positive_emotions)
        genku_negative = any(e in genku.emotions for e in negative_emotions)
        
        # 情感方向匹配
        if is_positive and genku_positive:
            score = 1.0
        elif is_negative and genku_negative:
            score = 1.0
        elif not is_positive and not is_negative:
            score = 0.7  # 中性输入，匹配度中等
        else:
            score = 0.2  # 情感方向相反
        
        # 强度匹配
        if intensity == genku.intensity:
            score *= 1.2
        
        return min(score, 1.0)
    
    def _match_scene(self, genku: Genku, context: Dict[str, Any]) -> float:
        """场景匹配：检查梗的标签是否与推荐标签匹配"""
        recommended_tags = context.get('recommended_tags', [])
        
        if not recommended_tags:
            return 0.5
        
        matches = sum(1 for tag in recommended_tags if tag in genku.tags)
        return min(matches / max(len(recommended_tags) * 0.5, 1), 1.0)
    
    def _match_semantic(self, genku: Genku, context: Dict[str, Any]) -> float:
        """语义匹配：检查语义关键词"""
        # 使用原始查询进行匹配
        query = context.get('query', '')
        
        if not query:
            return 0.5
        
        matches = sum(1 for kw in genku.semantic_keywords if kw in query)
        return min(matches / max(len(genku.semantic_keywords) * 0.3, 1), 1.0)
    
    def _match_evaluation(self, genku: Genku, context: Dict[str, Any]) -> float:
        """评价类型匹配"""
        eval_type = context.get('evaluation_type', '未知')
        
        # 根据评价类型推荐不同标签
        eval_tag_mapping = {
            '赞扬': ['封神', '赞叹', '传奇'],
            '批评': ['吐槽', '嘲讽', '愤怒'],
            '对比': ['对比', '比较', '递进'],
            '中立': ['介绍', '科普', '说明']
        }
        
        recommended = eval_tag_mapping.get(eval_type, [])
        matches = sum(1 for tag in recommended if tag in genku.tags)
        
        return min(matches / max(len(recommended) * 0.5, 1), 1.0) if recommended else 0.5
    
    def _generate_template_vars(self, genku: Genku, context: Dict[str, Any]) -> Dict[str, str]:
        """生成模板填充变量"""
        vars = {
            '对象': context.get('entity_name', '此人'),
            '人物': genku.person,
            '原文': genku.original,
        }
        
        # 根据情感添加形容词
        if context.get('is_positive'):
            vars['形容词'] = '天下无敌'
            vars['强化描述'] = '勇猛'
        elif context.get('is_negative'):
            vars['形容词'] = '糟糕'
            vars['强化描述'] = '拉胯'
        else:
            vars['形容词'] = '厉害'
            vars['强化描述'] = '可以'
        
        # 添加属性
        vars.update(context.get('attributes', {}))
        
        return vars
