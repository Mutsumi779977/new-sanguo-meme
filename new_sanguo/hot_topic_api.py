"""
新三国梗系统 v3.0
Copyright (C) 2025 梦雨_raining (B站: https://space.bilibili.com/24250060)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

"""
热点话题API接口
支持多平台热点数据获取
"""
import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)


@dataclass
class HotTopic:
    """热点话题数据结构"""
    title: str
    heat: float  # 热度值 0-1
    platform: str  # 来源平台
    category: str  # 话题分类
    url: str = ""  # 链接
    timestamp: str = ""  # 时间戳


class HotTopicAPI:
    """热点话题API聚合"""
    
    def __init__(self, cache_duration: int = 300):
        """
        Args:
            cache_duration: 缓存时间（秒），默认5分钟
        """
        self.cache_duration = cache_duration
        self.cache: Dict[str, Tuple[List[HotTopic], datetime]] = {}
        
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        _, cached_time = self.cache[key]
        return datetime.now() - cached_time < timedelta(seconds=self.cache_duration)
    
    def _get_from_cache(self, key: str) -> Optional[List[HotTopic]]:
        """从缓存获取数据"""
        if self._is_cache_valid(key):
            return self.cache[key][0]
        return None
    
    def _set_cache(self, key: str, data: List[HotTopic]):
        """设置缓存"""
        self.cache[key] = (data, datetime.now())
    
    def fetch_weibo_hot(self) -> List[HotTopic]:
        """
        获取微博热搜
        
        来源：微博热搜榜
        """
        cache_key = 'weibo'
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            # 使用备用API
            urls_to_try = [
                "https://weibo.com/ajax/side/hotSearch",
                "https://api.vvhan.com/api/weibo",
            ]
            
            topics = []
            for url in urls_to_try:
                try:
                    req = Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://weibo.com/' if 'weibo.com' in url else ''
                    })
                    with urlopen(req, timeout=5) as response:
                        data = json.loads(response.read().decode('utf-8'))
                    
                    # 解析不同格式的数据
                    if 'data' in data and 'realtime' in data['data']:
                        # 官方格式
                        for item in data['data']['realtime'][:50]:
                            title = item.get('word', '')
                            if title:
                                topics.append(HotTopic(
                                    title=title,
                                    heat=min(item.get('raw_hot', 0) / 1000000, 1.0),
                                    platform='weibo',
                                    category=self._classify_topic(title),
                                    timestamp=datetime.now().isoformat()
                                ))
                    elif isinstance(data, list):
                        # 简单列表格式
                        for item in data[:50]:
                            if isinstance(item, dict):
                                title = item.get('title', item.get('word', ''))
                                if title:
                                    topics.append(HotTopic(
                                        title=title,
                                        heat=0.7,
                                        platform='weibo',
                                        category=self._classify_topic(title),
                                        timestamp=datetime.now().isoformat()
                                    ))
                    
                    if topics:
                        break  # 成功获取则跳出
                        
                except Exception as e:
                    continue  # 尝试下一个URL
            
            if topics:
                self._set_cache(cache_key, topics)
            return topics
            
        except Exception as e:
            print(f"[HotTopicAPI] 微博热搜获取失败: {e}")
            return []
    
    def fetch_bilibili_hot(self) -> List[HotTopic]:
        """
        获取B站热门搜索
        
        来源：B站搜索推荐
        """
        cache_key = 'bilibili'
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            # B站热门API
            url = "https://s.search.bilibili.com/main/hotword?limit=30"
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://search.bilibili.com/'
            })
            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            for item in data.get('list', []):
                title = item.get('keyword', '')
                heat_value = item.get('heat', 0) / 100  # 归一化
                
                category = self._classify_topic(title)
                
                topics.append(HotTopic(
                    title=title,
                    heat=min(heat_value, 1.0),
                    platform='bilibili',
                    category=category,
                    timestamp=datetime.now().isoformat()
                ))
            
            self._set_cache(cache_key, topics)
            return topics
            
        except Exception as e:
            print(f"[HotTopicAPI] B站热门获取失败: {e}")
            return []
    
    def fetch_zhihu_hot(self) -> List[HotTopic]:
        """
        获取知乎热榜
        
        来源：知乎热榜
        """
        cache_key = 'zhihu'
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            # 知乎热榜API
            url = "https://www.zhihu.com/api/v3/explore/guest/feeds?limit=50"
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            topics = []
            for item in data.get('data', []):
                card = item.get('card', {})
                if card.get('type') == 'HotListCard':
                    title = card.get('title', '')
                    heat_value = self._parse_heat(card.get('description', ''))
                    
                    category = self._classify_topic(title)
                    
                    topics.append(HotTopic(
                        title=title,
                        heat=heat_value,
                        platform='zhihu',
                        category=category,
                        timestamp=datetime.now().isoformat()
                    ))
            
            self._set_cache(cache_key, topics)
            return topics
            
        except Exception as e:
            logger.warning(f"知乎热榜获取失败: {e}")
            return []
    
    def fetch_all_hot(self) -> List[HotTopic]:
        """
        获取所有平台热点
        
        合并并去重，按热度排序
        """
        all_topics = []
        
        # 并行获取各平台
        all_topics.extend(self.fetch_weibo_hot())
        all_topics.extend(self.fetch_bilibili_hot())
        all_topics.extend(self.fetch_zhihu_hot())
        
        # 去重（基于标题相似度）
        unique_topics = self._deduplicate_topics(all_topics)
        
        # 按热度排序
        unique_topics.sort(key=lambda x: x.heat, reverse=True)
        
        return unique_topics[:100]  # 返回前100条
    
    def get_hot_keywords(self, top_n: int = 50) -> Dict[str, float]:
        """
        获取热点关键词映射
        
        Returns:
            {关键词: 热度值}
        """
        topics = self.fetch_all_hot()
        keywords = {}
        
        for topic in topics[:top_n]:
            # 提取关键词（去除语气词和标点）
            clean_title = re.sub(r'[！？。，、；：""''（）【】]+', '', topic.title)
            keywords[clean_title] = topic.heat
            
            # 同时提取2-4字的关键词
            for length in [4, 3, 2]:
                if len(clean_title) >= length:
                    # 取前N个字作为关键词
                    short_kw = clean_title[:length]
                    if short_kw not in keywords:
                        keywords[short_kw] = topic.heat * 0.8  # 短词权重稍降
        
        return keywords
    
    def _parse_heat(self, heat_str: str) -> float:
        """解析热度字符串为0-1的浮点数"""
        try:
            # 处理"123万"、"456.7万"等格式
            heat_str = str(heat_str).strip()
            if '万' in heat_str:
                num = float(heat_str.replace('万', ''))
                return min(num / 500, 1.0)  # 500万为满分
            elif '亿' in heat_str:
                return 1.0
            else:
                num = float(heat_str)
                return min(num / 5000000, 1.0)  # 500万为满分
        except:
            return 0.5  # 默认值
    
    def _classify_topic(self, title: str) -> str:
        """对话题进行分类"""
        title_lower = title.lower()
        
        # 分类规则
        categories = {
            '电竞': ['电竞', 'lpl', 'lck', 's赛', 'faker', 'gen', 't1', 'blg', 'tes'],
            '游戏': ['原神', '王者', '黑神话', 'steam', '游戏', '手游', '更新', '版本'],
            '科技': ['ai', 'gpt', '华为', '苹果', '小米', '发布', '手机', '科技'],
            '娱乐': ['电影', '电视剧', '综艺', '明星', '演员', '票房', '豆瓣'],
            '体育': ['足球', '篮球', 'nba', '世界杯', '国足', '比赛', '进球'],
            '社会': ['特朗普', '美国', '伊朗', '国际', '战争', '冲突'],
            '情感': ['恋爱', '分手', '结婚', '离婚', '感情', '爱情'],
        }
        
        for category, keywords in categories.items():
            if any(kw in title_lower for kw in keywords):
                return category
        
        return '其他'
    
    def _deduplicate_topics(self, topics: List[HotTopic]) -> List[HotTopic]:
        """话题去重"""
        seen = set()
        unique = []
        
        for topic in topics:
            # 使用标题前8个字作为去重键
            key = topic.title[:8]
            if key not in seen:
                seen.add(key)
                unique.append(topic)
        
        return unique


# 全局API实例
_hot_api: Optional[HotTopicAPI] = None


def get_hot_api() -> HotTopicAPI:
    """获取热点API实例"""
    global _hot_api
    if _hot_api is None:
        _hot_api = HotTopicAPI()
    return _hot_api


# 便捷函数
def get_hot_keywords(top_n: int = 50) -> Dict[str, float]:
    """获取当前热点关键词"""
    return get_hot_api().get_hot_keywords(top_n)


def is_hot_topic(text: str, threshold: float = 0.6) -> Tuple[bool, float]:
    """
    检查文本是否是当前热点话题
    
    Returns:
        (是否热点, 热度值)
    """
    hot_keywords = get_hot_keywords(50)
    text_lower = text.lower()
    
    max_heat = 0.0
    for keyword, heat in hot_keywords.items():
        if keyword in text_lower:
            max_heat = max(max_heat, heat)
    
    return max_heat >= threshold, max_heat


# 测试
if __name__ == "__main__":
    api = HotTopicAPI()
    
    print("=== 微博热搜 ===")
    weibo = api.fetch_weibo_hot()
    for t in weibo[:5]:
        print(f"  [{t.category}] {t.title} (热度: {t.heat:.2f})")
    
    print("\n=== B站热门 ===")
    bilibili = api.fetch_bilibili_hot()
    for t in bilibili[:5]:
        print(f"  [{t.category}] {t.title} (热度: {t.heat:.2f})")
    
    print("\n=== 热点关键词 ===")
    keywords = api.get_hot_keywords(20)
    for kw, heat in list(keywords.items())[:10]:
        print(f"  {kw}: {heat:.2f}")
