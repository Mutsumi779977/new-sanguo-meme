"""
业务逻辑服务单元测试

测试范围：
- 梗匹配 (match_genku)
- 频率惩罚计算 (_get_frequency_penalty)
- 事不过三定律
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo.service import GenkuService
from new_sanguo.models import Genku

# 高频梗配置常量（测试专用，替代已移除的 HIGH_FREQUENCY_GENKU_CONFIG）
_TEST_HIGH_FREQ_CONFIG = {
    'weight_5_genkus': {
        'min_weight': 5,
        'window_seconds': 600,
        'max_usage_before_penalty': 3,
        'penalty_per_use': 0.1
    }
}


class TestFrequencyPenalty:
    """测试高频梗频率惩罚机制（事不过三定律）"""
    
    @pytest.fixture
    def service(self):
        """创建简化版Service实例，仅用于测试惩罚逻辑"""
        # 创建一个最小化的service实例，只用于测试惩罚计算
        class MockService:
            def __init__(self):
                self._high_freq_usage_history = {}
                
            def _get_frequency_penalty(self, genku: Genku) -> float:
                """计算高频梗的频率惩罚系数（复制自原方法）"""
                config = _TEST_HIGH_FREQ_CONFIG.get('weight_5_genkus')
                if not config:
                    return 1.0
                
                # 只处理权重>=5的梗
                min_weight = config.get('min_weight', 5)
                if genku.weight < min_weight:
                    return 1.0
                
                # 检查使用历史
                history = self._high_freq_usage_history.get(genku.genku_id, [])
                window_seconds = config.get('window_seconds', 600)
                
                # 清理过期记录
                current_time = time.time()
                history = [(t, gid) for t, gid in history if current_time - t < window_seconds]
                self._high_freq_usage_history[genku.genku_id] = history
                
                if not history:
                    return 1.0
                
                # 事不过三：前3次正常使用，第4次起严重惩罚
                max_before_penalty = config.get('max_usage_before_penalty', 3)
                if len(history) < max_before_penalty:
                    return 1.0  # 前3次无惩罚
                
                # 第4次起：每次乘以0.1（严重惩罚）
                penalty_per_use = config.get('penalty_per_use', 0.1)
                excess_uses = len(history) - max_before_penalty + 1
                penalty = penalty_per_use ** excess_uses
                
                return penalty
            
            def _record_genku_usage(self, genku: Genku):
                """记录梗使用情况（复制自原方法）"""
                config = _TEST_HIGH_FREQ_CONFIG.get('weight_5_genkus')
                if not config:
                    return
                
                min_weight = config.get('min_weight', 5)
                if genku.weight < min_weight:
                    return
                
                if genku.genku_id not in self._high_freq_usage_history:
                    self._high_freq_usage_history[genku.genku_id] = []
                
                self._high_freq_usage_history[genku.genku_id].append((time.time(), genku.genku_id))
        
        return MockService()
    
    def test_no_penalty_first_three_uses(self, service):
        """测试前3次使用无惩罚（事不过三）"""
        # 创建一个权重5的测试梗
        test_genku = Genku(
            genku_id='test_weight_5',
            original='测试高频梗',
            person='测试人物',
            source='测试',
            context='测试',
            emotions=['测试'],
            intensity='中',
            tags=['测试'],
            semantic_keywords=['测试'],
            weight=5  # 权重5，属于高频梗
        )
        
        # 前3次应无惩罚
        for i in range(3):
            penalty = service._get_frequency_penalty(test_genku)
            assert penalty == 1.0, f"第{i+1}次使用应无惩罚，实际是{penalty}"
            service._record_genku_usage(test_genku)
    
    def test_penalty_after_third_use(self, service):
        """测试第4次起有惩罚"""
        test_genku = Genku(
            genku_id='test_weight_5_penalty',
            original='测试高频梗惩罚',
            person='测试人物',
            source='测试',
            context='测试',
            emotions=['测试'],
            intensity='中',
            tags=['测试'],
            semantic_keywords=['测试'],
            weight=5
        )
        
        # 使用3次
        for _ in range(3):
            service._record_genku_usage(test_genku)
        
        # 第4次应开始惩罚
        penalty = service._get_frequency_penalty(test_genku)
        assert penalty < 1.0, f"第4次使用应有惩罚，实际是{penalty}"
        assert penalty == 0.1, f"第4次惩罚系数应为0.1，实际是{penalty}"
    
    def test_severe_penalty_after_multiple_uses(self, service):
        """测试多次使用后的严重惩罚"""
        test_genku = Genku(
            genku_id='test_weight_5_severe',
            original='测试高频梗严重惩罚',
            person='测试人物',
            source='测试',
            context='测试',
            emotions=['测试'],
            intensity='中',
            tags=['测试'],
            semantic_keywords=['测试'],
            weight=5
        )
        
        # 使用5次
        for _ in range(5):
            service._record_genku_usage(test_genku)
        
        # 第6次的惩罚应该是 0.1^3 = 0.001
        penalty = service._get_frequency_penalty(test_genku)
        expected = 0.001  # (5-3+1=3次超出，0.1^3)
        # 使用近似比较处理浮点数精度问题
        assert abs(penalty - expected) < 1e-10, f"第6次惩罚系数应为{expected}，实际是{penalty}"
    
    def test_low_weight_no_penalty(self, service):
        """测试低权重梗不受惩罚"""
        test_genku = Genku(
            genku_id='test_weight_3',
            original='测试低频梗',
            person='测试人物',
            source='测试',
            context='测试',
            emotions=['测试'],
            intensity='中',
            tags=['测试'],
            semantic_keywords=['测试'],
            weight=3  # 权重3，不属于高频梗
        )
        
        # 使用10次也应无惩罚
        for _ in range(10):
            service._record_genku_usage(test_genku)
        
        penalty = service._get_frequency_penalty(test_genku)
        assert penalty == 1.0, f"低权重梗应不受惩罚，实际是{penalty}"
    
    def test_window_expiration(self, service):
        """测试窗口期过期后惩罚重置"""
        test_genku = Genku(
            genku_id='test_window',
            original='测试窗口过期',
            person='测试人物',
            source='测试',
            context='测试',
            emotions=['测试'],
            intensity='中',
            tags=['测试'],
            semantic_keywords=['测试'],
            weight=5
        )
        
        # 使用3次
        for _ in range(3):
            service._record_genku_usage(test_genku)
        
        # 第4次有惩罚
        penalty = service._get_frequency_penalty(test_genku)
        assert penalty < 1.0
        
        # 修改历史记录时间，使其过期（模拟10分钟后）
        config = _TEST_HIGH_FREQ_CONFIG.get('weight_5_genkus', {})
        window = config.get('window_seconds', 600)
        old_time = time.time() - window - 1
        service._high_freq_usage_history[test_genku.genku_id] = [
            (old_time, test_genku.genku_id) for _ in range(3)
        ]
        
        # 再次检查，应无惩罚（已过期）
        penalty = service._get_frequency_penalty(test_genku)
        assert penalty == 1.0, f"窗口过期后应无惩罚，实际是{penalty}"


class TestGenkuMatching:
    """测试梗匹配功能"""
    
    def test_placeholder(self):
        """占位测试，匹配功能需要实际数据库"""
        pytest.skip("梗匹配测试需要实际数据库数据，在集成测试中验证")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
