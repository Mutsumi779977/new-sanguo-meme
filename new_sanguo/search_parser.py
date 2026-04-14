"""
搜索结果解析器
将原始搜索结果转换为StructuredSearchResult
"""
from typing import List, Dict, Optional
import re

from .structured_search import (
    StructuredSearchResult, Entity, EntityType, Sentiment,
    EvaluationType, SENTIMENT_KEYWORDS, EVALUATION_PATTERNS
)


class SearchResultParser:
    """搜索结果解析器"""
    
    # 预定义的实体识别模式
    ENTITY_PATTERNS = {
        EntityType.PERSON: [
            r'(Faker|李相赫|ShowMaker|许秀|Chovy|郑志勋)',
            r'(吕布|关羽|张飞|曹操|刘备|诸葛亮|孔明)',
            r'(唐国强|陆毅|鲍国安|陈建斌)',
        ],
        EntityType.TEAM: [
            r'(T1|GEN|DK|BLG|JDG|TES|RNG|EDG|WBG|LNG)',
            r'(SKT|ROX|Samsung|KT)',
        ],
        EntityType.WORK: [
            r'(老三国|新三国|三国演义|央视版)',
            r'(英雄联盟|LOL|League of Legends)',
        ],
    }
    
    # 属性提取模式
    ATTRIBUTE_PATTERNS = {
        '成就': r'(五冠王|三冠王|冠军|FMVP|MVP|大满贯)',
        '地位': r'(GOAT|历史第一|传奇|天花板|巅峰)',
        '数据': r'(豆瓣[\d.]+|评分[\d.]+|([\d]+)分)',
        '时间': r'(S\d+|\d{4}年|\d+年)',
    }
    
    def parse(self, query: str, raw_results: List[Dict], summary: str) -> StructuredSearchResult:
        """
        解析搜索结果为结构化信息
        
        Args:
            query: 原始查询
            raw_results: 原始搜索结果列表
            summary: 摘要文本
            
        Returns:
            StructuredSearchResult
        """
        # 1. 提取实体
        entities = self._extract_entities(summary)
        main_entity = entities[0] if entities else None
        
        # 2. 分析情感
        sentiment = self._analyze_sentiment(summary)
        
        # 3. 识别评价类型
        eval_type = self._identify_evaluation_type(query)
        
        # 4. 提取属性
        attributes = self._extract_attributes(summary)
        
        # 5. 生成推荐标签
        tags = self._generate_recommended_tags(main_entity, sentiment, eval_type)
        emotions = self._generate_recommended_emotions(sentiment, eval_type)
        
        return StructuredSearchResult(
            query=query,
            raw_summary=summary,
            entities=entities,
            main_entity=main_entity,
            sentiment=sentiment,
            evaluation_type=eval_type,
            attributes=attributes,
            recommended_tags=tags,
            recommended_emotions=emotions,
            raw_results=raw_results
        )
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """从文本中提取实体"""
        entities = []
        found_names = set()
        
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1)
                    if name not in found_names:
                        found_names.add(name)
                        entities.append(Entity(
                            name=name,
                            entity_type=entity_type,
                            aliases=[name]
                        ))
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Sentiment:
        """分析情感倾向"""
        text_lower = text.lower()
        
        # 统计正负向词
        pos_count = sum(1 for word in SENTIMENT_KEYWORDS['positive'] if word in text_lower)
        neg_count = sum(1 for word in SENTIMENT_KEYWORDS['negative'] if word in text_lower)
        
        # 计算极性
        total = pos_count + neg_count
        if total == 0:
            polarity = 0.0
        else:
            polarity = (pos_count - neg_count) / total
        
        # 确定强度
        strong_count = sum(1 for word in SENTIMENT_KEYWORDS['intensity_strong'] if word in text_lower)
        weak_count = sum(1 for word in SENTIMENT_KEYWORDS['intensity_weak'] if word in text_lower)
        
        if strong_count > weak_count:
            intensity = '强'
        elif weak_count > strong_count:
            intensity = '弱'
        else:
            intensity = '中'
        
        # 提取情感关键词
        emotion_keywords = []
        for word in SENTIMENT_KEYWORDS['positive'] + SENTIMENT_KEYWORDS['negative']:
            if word in text_lower:
                emotion_keywords.append(word)
        
        return Sentiment(
            polarity=polarity,
            intensity=intensity,
            keywords=emotion_keywords[:5]  # 最多5个
        )
    
    def _identify_evaluation_type(self, query: str) -> EvaluationType:
        """识别评价类型"""
        query_lower = query.lower()
        
        for eval_type, keywords in EVALUATION_PATTERNS.items():
            if any(kw in query_lower for kw in keywords):
                return eval_type
        
        return EvaluationType.UNKNOWN
    
    def _extract_attributes(self, text: str) -> Dict[str, str]:
        """提取关键属性"""
        attributes = {}
        
        for attr_name, pattern in self.ATTRIBUTE_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                # 取第一个匹配
                attributes[attr_name] = matches[0] if isinstance(matches[0], str) else matches[0][0]
        
        return attributes
    
    def _generate_recommended_tags(self, main_entity: Optional[Entity], 
                                   sentiment: Sentiment, 
                                   eval_type: EvaluationType) -> List[str]:
        """生成推荐标签"""
        tags = []
        
        # 根据实体类型
        if main_entity:
            if main_entity.entity_type == EntityType.PERSON:
                tags.extend(['人物', '评价'])
            elif main_entity.entity_type == EntityType.TEAM:
                tags.extend(['电竞', '战队'])
            elif main_entity.entity_type == EntityType.WORK:
                tags.extend(['影视', '对比'])
        
        # 根据评价类型
        eval_tag_map = {
            EvaluationType.PRAISE: ['封神', '赞叹'],
            EvaluationType.CRITICISM: ['吐槽', '愤怒'],
            EvaluationType.COMPARISON: ['对比', '递进'],
            EvaluationType.NEUTRAL: ['介绍', '科普'],
        }
        tags.extend(eval_tag_map.get(eval_type, ['评价']))
        
        # 根据情感强度
        if sentiment:
            if sentiment.intensity == '强':
                tags.append('meta')  # 强情感用meta梗
        
        return list(set(tags))  # 去重
    
    def _generate_recommended_emotions(self, sentiment: Sentiment, 
                                       eval_type: EvaluationType) -> List[str]:
        """生成推荐情绪"""
        emotions = []
        
        if sentiment:
            if sentiment.is_positive():
                emotions.extend(['赞叹', '得意', '兴奋'])
            elif sentiment.is_negative():
                emotions.extend(['嘲讽', '愤怒', '无奈'])
            else:
                emotions.extend(['中立', '客观'])
        
        # 根据评价类型补充
        if eval_type == EvaluationType.PRAISE:
            emotions.append('赞叹')
        elif eval_type == EvaluationType.CRITICISM:
            emotions.append('嘲讽')
        
        return list(set(emotions))
