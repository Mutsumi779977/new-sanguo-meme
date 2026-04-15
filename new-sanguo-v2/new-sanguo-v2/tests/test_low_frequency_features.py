"""
低频功能综合测试
测试平时较少使用的功能，确保它们工作正常
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEmbeddingFeature:
    """测试向量匹配功能（默认关闭）"""
    
    def test_embedding_disabled_by_default(self):
        """测试向量功能默认关闭"""
        from new_sanguo.config import Config
        config = Config()
        assert config.get('embedding.enabled') == False
    
    def test_service_without_embedding(self):
        """测试无向量模型时 Service 正常工作"""
        with patch('new_sanguo.service.EMBEDDING_AVAILABLE', False):
            from new_sanguo import create_agent
            agent = create_agent("test_user")
            # 应该使用关键词匹配
            result = agent.handle("测试")
            assert isinstance(result, str) or isinstance(result, dict)


class TestSearchAdapter:
    """测试搜索适配器（联网搜索增强）"""
    
    def test_fallback_search_without_kimi(self):
        """测试无 kimi_search 时的备用方案"""
        from new_sanguo.search_adapter import SearchAdapter, SearchResult
        
        adapter = SearchAdapter(enabled=True)
        
        # 模拟非 OpenClaw 环境
        with patch.dict('sys.modules', {'kimi_search': None}):
            result = adapter.search("测试查询")
            
        assert isinstance(result, SearchResult)
        assert result.query == "测试查询"
        assert len(result.keywords) > 0
    
    def test_extract_keywords_from_text(self):
        """测试关键词提取功能"""
        from new_sanguo.search_adapter import SearchAdapter
        
        adapter = SearchAdapter()
        text = '如何评价 gen2:0T1 的比赛'
        keywords = adapter._extract_query_keywords(text)
        
        assert 'gen2:0T1' in keywords or any('gen' in k.lower() for k in keywords)
    
    def test_search_disabled(self):
        """测试搜索禁用时返回 None"""
        from new_sanguo.search_adapter import SearchAdapter
        
        adapter = SearchAdapter(enabled=False)
        result = adapter.search("任何查询")
        
        assert result is None


class TestVideoInputMode:
    """测试视频转文字录入模式"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 的 Agent"""
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            
            MockService.return_value = Mock()
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_video_mode_enters_correct_state(self, mock_agent):
        """测试视频模式进入正确状态"""
        result = mock_agent.handle('/录入 视频')
        
        assert '视频转文字录入模式' in result
        from new_sanguo.models import State
        assert mock_agent.state == State.VIDEO_PROCESSING
    
    def test_video_mode_cancel(self, mock_agent):
        """测试视频模式取消"""
        mock_agent.handle('/录入 视频')
        result = mock_agent.handle('/取消')
        
        assert '已取消' in result
        from new_sanguo.models import State
        assert mock_agent.state == State.IDLE


class TestFusionCommand:
    """测试融合测试命令"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            
            mock_service = Mock()
            # 模拟返回一个梗
            mock_genku = Mock()
            mock_genku.genku_id = 'xsg_cc_001'
            mock_genku.original = '不可能，绝对不可能！'
            mock_service.match_genku.return_value = (mock_genku, None)
            mock_service.get_meta_genkus.return_value = []
            MockService.return_value = mock_service
            
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            agent.service = mock_service
            yield agent
    
    def test_fusion_command_basic(self, mock_agent):
        """测试融合命令基本功能"""
        result = mock_agent.handle('/融合 测试内容')
        
        assert '融合测试' in result
        assert '不可能，绝对不可能' in result


class TestTitleGeneration:
    """测试称呼生成功能"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            MockService.return_value = Mock()
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_title_generation_basic(self, mock_agent):
        """测试称呼生成基本功能"""
        result = mock_agent.handle('/称呼 折棒')
        
        assert '折棒爷' in result
        assert '张飞' in result  # 来源说明
    
    def test_title_generation_already_title(self, mock_agent):
        """测试输入已经是称呼的情况"""
        result = mock_agent.handle('/称呼 折棒爷')
        
        assert '已是标准格式' in result


class TestFeedbackSystem:
    """测试反馈系统"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
                'learning.preference_decay': 0.9,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            mock_db.add_feedback.return_value = True
            mock_db.get_genku_feedback_stats.return_value = {'like': 5, 'dislike': 1}
            MockDatabase.return_value = mock_db
            
            mock_service = Mock()
            mock_genku = Mock()
            mock_genku.genku_id = 'xsg_cc_001'
            mock_genku.person = '曹操'
            mock_genku.tags = ['经典']
            mock_service.get_normal_genkus.return_value = [mock_genku]
            mock_service.match_genku.return_value = (mock_genku, None)
            MockService.return_value = mock_service
            
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            agent.service = mock_service
            agent.db = mock_db
            # 先设置一个 last_genku
            agent.context['last_genku'] = 'xsg_cc_001'
            yield agent
    
    def test_like_without_context(self, mock_agent):
        """测试无上下文时喜欢命令"""
        mock_agent.context['last_genku'] = None
        result = mock_agent.handle('/喜欢')
        
        assert '还没有使用任何梗' in result
    
    def test_dislike_without_reason(self, mock_agent):
        """测试不喜欢命令（无原因）"""
        result = mock_agent.handle('/不喜欢')
        
        # 应该进入反馈原因状态
        from new_sanguo.models import State
        assert mock_agent.state == State.FEEDBACK_REASON
        assert '说明原因' in result


class TestPreferenceCommand:
    """测试偏好查看功能"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            MockService.return_value = Mock()
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            from new_sanguo.models import UserPreference
            agent = NewSanguoAgent("test_user")
            # 设置有数据的偏好
            agent.user_pref = UserPreference(
                user_id="test_user",
                liked_persons={'曹操': 0.8, '张飞': 0.5},
                liked_tags={'经典': 0.6},
                total_interactions=10
            )
            yield agent
    
    def test_preference_command_with_data(self, mock_agent):
        """测试有数据时的偏好查看"""
        result = mock_agent.handle('/偏好')
        
        assert '曹操' in result
        assert '10次' in result


class TestResetCommand:
    """测试重置会话功能"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            MockService.return_value = Mock()
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_reset_command(self, mock_agent):
        """测试重置命令"""
        # 先设置一个非空闲状态
        from new_sanguo.models import State
        mock_agent.state = State.INPUT_WAITING
        mock_agent.state_data = {'some_data': 'test'}
        
        result = mock_agent.handle('/重置')
        
        assert '已重置' in result
        assert mock_agent.state == State.IDLE
        assert mock_agent.state_data == {}


class TestGenkuChain:
    """测试接龙功能"""
    
    @pytest.fixture
    def mock_agent(self):
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
                'dialogue.genku_chain.enabled': True,
                'dialogue.genku_chain.trigger_probability': 1.0,  # 100%触发
                'dialogue.genku_chain.max_chain_length': 3,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            
            mock_service = Mock()
            mock_genku = Mock()
            mock_genku.genku_id = 'xsg_cc_002'
            mock_genku.original = '不可能'
            mock_genku.person = '曹操'
            mock_service.get_normal_genkus.return_value = [mock_genku]
            mock_service.match_genku.return_value = (mock_genku, None)
            MockService.return_value = mock_service
            
            MockLogger.return_value = Mock()
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            agent.service = mock_service
            yield agent
    
    def test_chain_state_initialization(self, mock_agent):
        """测试接龙状态初始化"""
        chain_state = mock_agent.context['chain_state']
        
        assert chain_state['active'] == False
        assert chain_state['count'] == 0
        assert chain_state['sequence'] == []
    
    def test_chain_cooldown_after_reset(self, mock_agent):
        """测试接龙重置后的冷却"""
        from new_sanguo.models import State
        mock_agent._reset_chain()
        
        assert mock_agent.context['chain_state']['cooldown'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
