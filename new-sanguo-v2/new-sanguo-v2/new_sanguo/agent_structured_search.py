"""
Agent扩展 - 结构化搜索与多维度匹配集成
添加到 agent.py 中
"""

# 新增导入（添加到 agent.py 顶部）
# from .structured_search import StructuredSearchResult
# from .search_parser import SearchResultParser
# from .multi_matcher import MultiDimensionalMatcher, MatchResult


class StructuredSearchMixin:
    """
    结构化搜索混入类
    为Agent添加结构化搜索和多维度匹配能力
    """
    
    def _structured_search_and_match(self, text: str) -> Optional[str]:
        """
        结构化搜索 + 多维度匹配
        
        流程：
        1. 执行搜索
        2. 解析为结构化结果
        3. 多维度匹配梗
        4. 使用模板生成回复
        
        Returns:
            生成的回复文本，或None（匹配失败）
        """
        try:
            # 导入（延迟导入避免循环依赖）
            from .search_adapter import get_search_adapter, SearchResult
            from .search_parser import SearchResultParser
            from .multi_matcher import MultiDimensionalMatcher
            
            # 1. 执行搜索
            adapter = get_search_adapter(
                enabled=self.config.get('search.enabled', False),
                result_count=self.config.get('search.result_count', 3)
            )
            
            raw_result = adapter.search(text)
            if not raw_result:
                return None
            
            # 2. 解析为结构化结果
            parser = SearchResultParser()
            structured = parser.parse(
                query=text,
                raw_results=raw_result.raw_results,
                summary=raw_result.summary
            )
            
            self.logger.info(f"结构化搜索: 实体={structured.main_entity.name if structured.main_entity else 'None'}, "
                           f"情感={structured.sentiment.polarity if structured.sentiment else 0:.2f}, "
                           f"评价={structured.evaluation_type.value}")
            
            # 3. 多维度匹配梗
            matcher = MultiDimensionalMatcher(self.service.get_all_genkus())
            context = structured.to_matching_context()
            context['query'] = text  # 保留原始查询
            
            match_results = matcher.match(context, top_n=3)
            
            if not match_results or match_results[0].total_score < 0.4:
                self.logger.debug(f"多维度匹配分数过低: {match_results[0].total_score if match_results else 0}")
                return None
            
            # 4. 选择最佳匹配并生成回复
            best_match = match_results[0]
            
            # 使用模板变量填充
            output = self._fill_template(best_match.genku, best_match.context)
            
            # 记录匹配详情（调试用）
            dims_str = ", ".join([f"{d.name}:{d.score:.2f}" for d in best_match.dimensions])
            self.logger.info(f"多维度匹配成功: {best_match.genku.genku_id}, 总分={best_match.total_score:.2f}, 维度=[{dims_str}]")
            
            return output
            
        except Exception as e:
            self.logger.error(f"结构化搜索失败: {e}", exc_info=True)
            return None
    
    def _fill_template(self, genku: Genku, template_vars: dict) -> str:
        """
        使用变量填充梗模板
        
        支持：
        - 变体模板填充
        - 融合模板填充
        - 原始文本返回
        """
        output = genku.original
        
        # 如果有变体模板，尝试填充
        if genku.variant_template:
            try:
                output = genku.variant_template.format(**template_vars)
            except (KeyError, IndexError) as e:
                self.logger.debug(f"模板填充失败: {e}，使用原文")
                output = genku.original
        
        # 如果有融合规则，尝试融合meta梗
        if genku.fusion_rules and genku.is_meta:
            output = self._apply_fusion_if_needed(genku, output, template_vars)
        
        return output
    
    def _apply_fusion_if_needed(self, genku: Genku, base_output: str, 
                                template_vars: dict) -> str:
        """根据需要应用融合"""
        import random
        
        # 检查是否需要融合
        fusion_prob = genku.fusion_rules.get('probability', 0.3)
        if random.random() > fusion_prob:
            return base_output
        
        # 查找可融合的meta梗
        compatible_meta = []
        for g in self.service.get_meta_genkus():
            if g.genku_id != genku.genku_id:
                compatible_meta.append(g)
        
        if not compatible_meta:
            return base_output
        
        # 随机选择一个融合
        meta = random.choice(compatible_meta)
        fused = self.service._fuse_genkus(meta, genku, template_vars.get('query', ''))
        
        if fused and self.service.check_fusion_quality(fused, meta.original, genku.original):
            return fused
        
        return base_output


# 修改建议：在 _search_and_retry 方法中添加调用
"""
def _search_and_retry(self, text: str) -> Optional[str]:
    # 先尝试结构化搜索（新）
    structured_result = self._structured_search_and_match(text)
    if structured_result:
        return structured_result
    
    # 回退到旧逻辑
    ...（原有代码）
"""
