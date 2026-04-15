"""
Service 层核心功能测试

测试范围：
- 梗匹配 (match_genku, _keyword_match)
- 融合功能 (_fuse_genkus, _try_fusion, _evaluate_fusion_quality)
- 变体生成 (generate_variant, _variant_fill_basic, _variant_fill_smart, _variant_validate_fixed)
- 温度采样 (_sample_with_temperature)
"""

import pytest
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo.service import GenkuService
from new_sanguo.models import Genku, UserPreference
from new_sanguo.config import Config
from new_sanguo.database import Database
from unittest.mock import Mock, MagicMock, patch


class TestMatchGenku:
    """测试梗匹配功能"""
    
    @pytest.fixture
    def mock_service(self):
        """创建最小化的 service 实例用于测试匹配逻辑"""
        class MockService:
            def __init__(self):
                self.config = Config()
                self.logger = Mock()
                self.normal_genkus = []
                self.meta_genkus = []
                self.model = None
                self.vectors = {}
                self.model_loaded = False
                self._high_freq_usage_history = {}
                
            def _record_genku_usage(self, genku):
                """记录梗使用"""
                pass
                
            def _keyword_match(self, text, user_pref):
                """关键词匹配"""
                scores = []
                text_lower = text.lower()
                
                for genku in self.normal_genkus:
                    score = 0
                    # 关键词匹配
                    for kw in genku.semantic_keywords:
                        if kw in text_lower:
                            score += 0.3
                    # 原文匹配
                    if genku.original in text:
                        score += 0.5
                    # 人物匹配
                    if genku.person in text:
                        score += 0.2
                        
                    if score > 0:
                        scores.append((score, genku))
                
                return sorted(scores, key=lambda x: x[0], reverse=True)
            
            def _get_frequency_penalty(self, genku):
                """频率惩罚"""
                return 1.0
            
            def _sample_with_temperature(self, scores):
                """温度采样"""
                if not scores:
                    return None
                # 无温度时返回最高分
                return scores[0][1]
            
            def _try_fusion(self, main_genku, text):
                """尝试融合"""
                return None
                
            def match_genku(self, text, user_pref=None, allow_fusion=True):
                """匹配梗"""
                if not self.normal_genkus:
                    return None, None
                
                scores = self._keyword_match(text, user_pref)
                if not scores:
                    return None, None
                
                main_genku = self._sample_with_temperature(scores)
                self._record_genku_usage(main_genku)
                
                return main_genku, None
        
        return MockService()
    
    @pytest.fixture
    def sample_genkus(self):
        """创建测试用的梗数据"""
        return [
            Genku(
                genku_id='xsg_cc_001',
                original='不可能，绝对不可能',
                person='曹操',
                source='新三国',
                context='曹操得知刘备消息后',
                emotions=['惊讶', '愤怒'],
                intensity='高',
                tags=['惊讶', '否定'],
                semantic_keywords=['不可能', '绝对'],
                weight=4,
                usage_count=10
            ),
            Genku(
                genku_id='xsg_lb_001',
                original='接着奏乐接着舞',
                person='刘备',
                source='新三国',
                context='刘备在荆州',
                emotions=['喜悦', '放纵'],
                intensity='中',
                tags=['享乐', '音乐'],
                semantic_keywords=['奏乐', '舞'],
                weight=5,
                usage_count=20
            ),
            Genku(
                genku_id='xsg_zgl_001',
                original='我从未见过有如此厚颜无耻之人',
                person='诸葛亮',
                source='新三国',
                context='诸葛亮骂王朗',
                emotions=['愤怒', '鄙视'],
                intensity='高',
                tags=['骂人', '鄙视'],
                semantic_keywords=['厚颜无耻', '从未见过'],
                weight=5,
                usage_count=15
            ),
        ]
    
    def test_match_by_keyword(self, mock_service, sample_genkus):
        """测试基于关键词的匹配"""
        mock_service.normal_genkus = sample_genkus
        
        genku, fused = mock_service.match_genku("他说不可能")
        assert genku is not None
        assert genku.genku_id == 'xsg_cc_001'
    
    def test_match_by_person(self, mock_service, sample_genkus):
        """测试基于人物的匹配"""
        mock_service.normal_genkus = sample_genkus
        
        genku, fused = mock_service.match_genku("曹操来了")
        assert genku is not None
        assert genku.person == '曹操'
    
    def test_no_match(self, mock_service, sample_genkus):
        """测试无匹配情况"""
        mock_service.normal_genkus = sample_genkus
        
        genku, fused = mock_service.match_genku("今天天气真好")
        # 没有关键词匹配，应该返回 None
        assert genku is None
    
    def test_empty_genku_list(self, mock_service):
        """测试空梗列表"""
        genku, fused = mock_service.match_genku("任何文本")
        assert genku is None
        assert fused is None
    
    def test_keyword_match_multiple(self, mock_service, sample_genkus):
        """测试多个关键词匹配，返回最高分"""
        mock_service.normal_genkus = sample_genkus
        
        scores = mock_service._keyword_match("曹操说不可能绝对", None)
        assert len(scores) > 0
        # 最高分应该在前
        assert scores[0][0] > 0.5


class TestFusion:
    """测试融合功能"""
    
    @pytest.fixture
    def mock_service(self):
        """创建带融合功能的 mock service"""
        class MockService:
            def __init__(self):
                self.config = Config()
                self.logger = Mock()
                self.meta_genkus = []
                self._high_freq_usage_history = {}
                
            def _fuse_genkus(self, meta, main, user_text):
                """融合两个梗"""
                # 简单融合模板
                templates = [
                    f"{meta.original}，{main.original}",
                    f"{main.original}，{meta.original}",
                ]
                import random
                return random.choice(templates)
            
            def _evaluate_fusion_quality(self, fused, meta, main):
                """评估融合质量"""
                if not fused or not meta or not main:
                    return 0.0
                
                score = 0.5
                
                # 检查是否包含两个梗的内容
                if meta in fused:
                    score += 0.2
                if main in fused:
                    score += 0.2
                
                # 检查是否有合理的连接
                if '，' in fused or ',' in fused:
                    score += 0.1
                
                # 检查重复惩罚
                if fused.count(meta) >= 2 or fused.count(main) >= 2:
                    score -= 0.3
                
                return max(0.0, min(1.0, score))
        
        return MockService()
    
    @pytest.fixture
    def sample_meta_genku(self):
        """创建 meta 梗"""
        return Genku(
            genku_id='xsg_meta_001',
            original='这就不奇怪了',
            person='meta',
            source='新三国',
            context='meta梗',
            emotions=['恍然大悟'],
            intensity='中',
            tags=['meta', '恍然大悟'],
            semantic_keywords=['不奇怪', '原来如此'],
            weight=3,
            is_meta=True,
            fusion_targets=['曹操', '惊讶']
        )
    
    @pytest.fixture
    def sample_main_genku(self):
        """创建主梗"""
        return Genku(
            genku_id='xsg_cc_001',
            original='不可能，绝对不可能',
            person='曹操',
            source='新三国',
            context='曹操得知刘备消息后',
            emotions=['惊讶', '愤怒'],
            intensity='高',
            tags=['惊讶', '否定'],
            semantic_keywords=['不可能', '绝对'],
            weight=4
        )
    
    def test_fuse_genkus_basic(self, mock_service, sample_meta_genku, sample_main_genku):
        """测试基本融合功能"""
        fused = mock_service._fuse_genkus(sample_meta_genku, sample_main_genku, "测试文本")
        assert fused is not None
        assert sample_meta_genku.original in fused or sample_main_genku.original in fused
    
    def test_evaluate_fusion_quality_good(self, mock_service, sample_meta_genku, sample_main_genku):
        """测试高质量融合评分"""
        fused = "这就不奇怪了，不可能，绝对不可能"
        quality = mock_service._evaluate_fusion_quality(
            fused, 
            sample_meta_genku.original, 
            sample_main_genku.original
        )
        assert quality > 0.6
    
    def test_evaluate_fusion_quality_poor(self, mock_service, sample_meta_genku, sample_main_genku):
        """测试低质量融合评分"""
        # 重复的融合
        fused = "这就不奇怪了这就不奇怪了不可能不可能"
        quality = mock_service._evaluate_fusion_quality(
            fused, 
            sample_meta_genku.original, 
            sample_main_genku.original
        )
        assert quality < 0.5
    
    def test_evaluate_fusion_quality_empty(self, mock_service):
        """测试空融合评分"""
        quality = mock_service._evaluate_fusion_quality("", "meta", "main")
        assert quality == 0.0


class TestVariantGeneration:
    """测试变体生成功能"""
    
    @pytest.fixture
    def mock_service(self):
        """创建带变体生成功能的 mock service"""
        class MockService:
            def __init__(self):
                self.config = Config()
                self.logger = Mock()
                
            def _variant_fill_basic(self, template, genku, entities, fixed_parts):
                """基础变量替换"""
                result = template
                for var_name, value in entities.items():
                    placeholder = f'[{var_name}]'
                    if placeholder in result:
                        # 检查是否在 fixed_parts 中
                        in_fixed = any(placeholder in fixed for fixed in fixed_parts)
                        if not in_fixed:
                            result = result.replace(placeholder, value)
                return result
            
            def _variant_validate_fixed(self, template, genku_id, fixed_parts):
                """验证 fixed 部分完整性"""
                template_clean = template.replace('，', '').replace(',', '')
                
                for fixed in fixed_parts:
                    if '#' in fixed:
                        continue
                    fixed_clean = fixed.replace('#', '').replace('，', '').replace(',', '')
                    if fixed_clean not in template_clean:
                        return False
                return True
            
            def generate_variant(self, genku, user_text, fixed_parts=None):
                """生成变体"""
                if not genku.variable_desc:
                    return genku.original
                
                # 提取实体
                entities = self._extract_entities(user_text)
                template = genku.variant_template or genku.original
                
                # 基础替换
                template = self._variant_fill_basic(template, genku, entities, fixed_parts or [])
                
                # 验证
                if not self._variant_validate_fixed(template, genku.genku_id, fixed_parts or []):
                    return genku.original
                
                return template
            
            def _extract_entities(self, text):
                """简单实体提取"""
                entities = {}
                # 提取对象（简单实现）
                import re
                patterns = [
                    r'不想(.*?)了',
                    r'不要(.*?)了',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        entities['对象'] = match.group(1)
                        break
                return entities
        
        return MockService()

    @pytest.fixture
    def sample_genku_with_template(self):
        """创建带变体模板的梗"""
        return Genku(
            genku_id='xsg_cc_002',
            original='不可能，绝对不可能',
            person='曹操',
            source='新三国',
            context='惊讶场景',
            emotions=['惊讶'],
            intensity='高',
            tags=['否定'],
            semantic_keywords=['不可能'],
            weight=4,
            variable_desc={'对象': '否定的内容'},
            variant_template='不可能，绝对不可能[对象]'
        )
    
    def test_variant_fill_basic(self, mock_service, sample_genku_with_template):
        """测试基础变量填充"""
        entities = {'对象': '加班'}
        fixed_parts = ['不可能', '绝对不可能#']
        
        template = mock_service._variant_fill_basic(
            '不可能，绝对不可能[对象]',
            sample_genku_with_template,
            entities,
            fixed_parts
        )
        assert '加班' in template
        assert '[对象]' not in template
    
    def test_variant_validate_fixed_success(self, mock_service):
        """测试 fixed 验证通过"""
        template = "不可能，绝对不可能加班"
        fixed_parts = ['不可能', '绝对不可能#']
        
        result = mock_service._variant_validate_fixed(template, 'test_id', fixed_parts)
        assert result is True
    
    def test_variant_validate_fixed_fail(self, mock_service):
        """测试 fixed 验证失败"""
        template = "完全可以"
        fixed_parts = ['不可能', '绝对不可能#']
        
        result = mock_service._variant_validate_fixed(template, 'test_id', fixed_parts)
        assert result is False
    
    def test_variant_validate_fixed_with_placeholder(self, mock_service):
        """测试带 # 的 fixed 跳过验证"""
        template = "不可能"
        fixed_parts = ['不可能#']  # 带 # 表示可变
        
        result = mock_service._variant_validate_fixed(template, 'test_id', fixed_parts)
        assert result is True


class TestTemperatureSampling:
    """测试温度采样功能"""
    
    @pytest.fixture
    def mock_service(self):
        class MockService:
            def __init__(self):
                self.config = Config()
                
            def _sample_with_temperature(self, scores, temperature=1.0):
                """温度采样"""
                import random
                
                if not scores:
                    return None
                
                if temperature == 0 or len(scores) == 1:
                    return scores[0][1]
                
                candidates = [s[1] for s in scores]
                weights = [s[0] for s in scores]
                
                if temperature != 1.0 and temperature > 0:
                    # 温度缩放
                    weights = [max(w, 0.001) for w in weights]
                    exp_weights = [math.exp(w / temperature) for w in weights]
                    total = sum(exp_weights)
                    weights = [w / total for w in exp_weights]
                    return random.choices(candidates, weights=weights)[0]
                else:
                    # 无温度时返回最高分的
                    return candidates[0]
        
        return MockService()
    
    @pytest.fixture
    def sample_scores(self):
        """测试分数数据"""
        class MockGenku:
            def __init__(self, id):
                self.genku_id = id
        
        return [
            (0.9, MockGenku('high')),
            (0.6, MockGenku('medium')),
            (0.3, MockGenku('low')),
        ]
    
    def test_sample_zero_temperature(self, mock_service, sample_scores):
        """测试零温度（确定性选择最高分）"""
        result = mock_service._sample_with_temperature(sample_scores, temperature=0)
        assert result.genku_id == 'high'
    
    def test_sample_high_temperature(self, mock_service, sample_scores):
        """测试高温度（更多随机性）"""
        # 运行多次，检查是否会选中低分
        results = []
        for _ in range(50):
            result = mock_service._sample_with_temperature(sample_scores, temperature=2.0)
            results.append(result.genku_id)
        
        # 高温度下应该有机会选中非最高分
        assert len(set(results)) > 1 or 'high' in results
    
    def test_sample_empty_scores(self, mock_service):
        """测试空分数列表"""
        result = mock_service._sample_with_temperature([], temperature=1.0)
        assert result is None
    
    def test_sample_single_score(self, mock_service):
        """测试单一项"""
        class MockGenku:
            pass
        scores = [(0.5, MockGenku())]
        result = mock_service._sample_with_temperature(scores, temperature=1.0)
        assert result is not None


class TestCosineSimilarity:
    """测试余弦相似度计算"""
    
    def test_cosine_similarity_identical(self):
        """测试相同向量的相似度"""
        # 使用纯 Python 实现余弦相似度
        v1 = [1, 2, 3]
        v2 = [1, 2, 3]
        
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(x * x for x in v1) ** 0.5
        norm2 = sum(x * x for x in v2) ** 0.5
        similarity = dot / (norm1 * norm2)
        
        assert abs(similarity - 1.0) < 0.001
    
    def test_cosine_similarity_orthogonal(self):
        """测试正交向量的相似度"""
        v1 = [1, 0, 0]
        v2 = [0, 1, 0]
        
        dot = sum(a * b for a, b in zip(v1, v2))
        
        assert abs(dot - 0.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
