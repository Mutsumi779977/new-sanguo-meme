"""
新三国梗系统 v2.8.0
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
新三国梗系统 - 搜索适配器

提供联网搜索增强功能
"""
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """搜索结果"""
    query: str
    summary: str
    keywords: List[str]
    raw_results: List[Dict]
    error: Optional[str] = None  # 错误信息，None表示无错误


class SearchAdapter:
    """
    搜索适配器
    
    负责调用外部搜索工具，提取关键信息，
    并转换为可用于梗匹配的格式。
    """
    
    def __init__(self, enabled: bool = True, result_count: int = 3):
        self.enabled = enabled
        self.result_count = result_count
    
    def search(self, query: str) -> Optional[SearchResult]:
        """
        执行搜索并返回结果
        
        注意：这里依赖 OpenClaw 的 kimi_search 工具。
        在非 OpenClaw 环境中需要外部注入搜索实现。
        
        Args:
            query: 搜索查询
            
        Returns:
            搜索结果，或 None（搜索失败/禁用）
        """
        if not self.enabled:
            return None
        
        try:
            # 尝试导入 OpenClaw 工具
            # 注意：这行代码只在 OpenClaw 环境中有效
            from kimi_search import kimi_search
            
            results = kimi_search(query=query, limit=self.result_count)
            
            if not results:
                return SearchResult(
                    query=query,
                    summary="搜索返回空结果",
                    keywords=[],
                    raw_results=[],
                    error="no_results"
                )
            
            # 提取摘要和关键词
            summary = self._extract_summary(results)
            keywords = self._extract_keywords(results)
            
            return SearchResult(
                query=query,
                summary=summary,
                keywords=keywords,
                raw_results=results
            )
            
        except ImportError as e:
            # 非 OpenClaw 环境，使用备用方案
            return self._fallback_search(query, error=f"import_error: {e}")
        except Exception as e:
            # 记录详细错误信息，但返回结构化结果
            error_msg = f"{type(e).__name__}: {str(e)}"
            return self._fallback_search(query, error=error_msg)
    
    def _fallback_search(self, query: str, error: Optional[str] = None) -> SearchResult:
        """
        备用搜索方案
        
        在没有外部搜索工具时使用，
        基于文本分析提取可能的关键词。
        """
        # 提取查询中的关键信息
        keywords = self._extract_query_keywords(query)
        
        summary = f"从查询中提取的关键词: {', '.join(keywords[:5])}" if keywords else "未能提取关键词"
        if error:
            summary = f"[错误: {error}] {summary}"
        
        return SearchResult(
            query=query,
            summary=summary,
            keywords=keywords,
            raw_results=[],
            error=error
        )
    
    def _extract_query_keywords(self, text: str) -> List[str]:
        """从查询文本中提取关键词"""
        keywords = []
        
        # 1. 提取引号内容（匹配中英文引号）
        # 使用明确的字符类，避免引号嵌套问题
        import re
        # 匹配双引号内容
        quoted1 = re.findall(r'"([^"]+)"', text)
        keywords.extend(quoted1)
        # 匹配中文双引号内容
        quoted2 = re.findall(r'"([^"]+)"', text)
        keywords.extend(quoted2)
        # 匹配单引号内容
        quoted3 = re.findall(r"'([^']+)'", text)
        keywords.extend(quoted3)
        # 匹配中文单引号内容
        quoted4 = re.findall(r"'([^']+)'", text)
        keywords.extend(quoted4)
        
        # 2. 提取代码/术语格式（如 gen2:0T1）
        code_patterns = [
            r'\b([a-zA-Z]+\d*)[:：]([a-zA-Z0-9]+)\b',  # gen2:0T1
            r'\b([A-Z][a-z]+[A-Z][a-z]+)\b',          # CamelCase
            r'\b([a-z]+_[a-z_]+)\b',                  # snake_case
        ]
        for pattern in code_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    keywords.append(':'.join(match))
                else:
                    keywords.append(match)
        
        # 3. 提取英文+数字组合
        english_num = re.findall(r'\b([A-Za-z]+\d+)\b', text)
        keywords.extend(english_num)
        
        # 4. 提取 2-10 字的中文词组
        chinese = re.findall(r'[\u4e00-\u9fa5]{2,10}', text)
        keywords.extend(chinese)
        
        # 去重并过滤
        seen = set()
        result = []
        for k in keywords:
            k = k.strip()
            if len(k) >= 2 and k.lower() not in seen:
                seen.add(k.lower())
                result.append(k)
        
        return result[:10]  # 最多返回 10 个
    
    def _extract_summary(self, results: List[Dict]) -> str:
        """从搜索结果中提取摘要"""
        summaries = []
        for r in results[:3]:
            content = r.get('content', '') or r.get('snippet', '')
            if content:
                summaries.append(content[:200])
        return ' '.join(summaries)[:500]
    
    def _extract_keywords(self, results: List[Dict]) -> List[str]:
        """从搜索结果中提取关键词"""
        all_text = ' '.join([
            r.get('title', '') + ' ' + r.get('content', '')
            for r in results
        ])
        
        # 简单的关键词提取
        # 实际可以用更复杂的 NLP 方法
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)
        
        # 统计频率
        from collections import Counter
        freq = Counter(words)
        
        # 返回高频词
        return [word for word, _ in freq.most_common(10)]
    
    def generate_search_queries(self, text: str) -> List[str]:
        """
        生成多个搜索查询变体
        
        提高搜索覆盖率
        """
        queries = [text]
        
        # 提取核心术语
        terms = self._extract_query_keywords(text)
        
        # 添加术语组合
        if len(terms) >= 2:
            queries.append(f"{terms[0]} {terms[1]}")
        
        # 添加 "是什么" 查询
        if terms:
            queries.append(f"{terms[0]} 是什么")
        
        return list(dict.fromkeys(queries))[:3]  # 去重，最多 3 个


# 全局搜索适配器实例
_search_adapter: Optional[SearchAdapter] = None


def get_search_adapter(enabled: bool = True, result_count: int = 3, 
                       force_new: bool = False) -> SearchAdapter:
    """
    获取搜索适配器实例（单例）
    
    Args:
        enabled: 是否启用搜索
        result_count: 搜索结果数量
        force_new: 强制创建新实例（用于测试）
    """
    global _search_adapter
    if force_new or _search_adapter is None:
        _search_adapter = SearchAdapter(enabled, result_count)
    return _search_adapter


def reset_search_adapter():
    """重置搜索适配器"""
    global _search_adapter
    _search_adapter = None
