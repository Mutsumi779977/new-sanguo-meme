"""
Agent 单元测试（Mock 版）

测试范围：
- 状态机流转
- 命令路由
- 对话处理
- 响应格式化

使用 Mock 隔离所有外部依赖（数据库、Service、搜索、随机性）
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo.models import State, Genku, UserPreference


class TestNewSanguoAgentStateMachine:
    """测试状态机流转"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 依赖的 Agent"""
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            # 配置 Mock
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
                'dialogue.genku_chain.cooldown_turns': 3,
                'dialogue.genku_chain.max_chain_length': 5,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            
            mock_service = Mock()
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_initial_state_is_idle(self, mock_agent):
        """测试初始状态为 IDLE"""
        assert mock_agent.state == State.IDLE
    
    def test_reset_state_to_idle(self, mock_agent):
        """测试重置状态到 IDLE"""
        mock_agent.state = State.INPUT_WAITING
        mock_agent._reset_state()
        assert mock_agent.state == State.IDLE
    
    def test_reset_chain_clears_sequence(self, mock_agent):
        """测试重置接龙清除序列"""
        mock_agent.context['chain_state'] = {
            'active': True,
            'sequence': ['genku1', 'genku2'],
            'count': 2,
            'cooldown': 1
        }
        mock_agent._reset_chain()
        
        assert mock_agent.context['chain_state']['active'] == False
        assert mock_agent.context['chain_state']['sequence'] == []
        assert mock_agent.context['chain_state']['count'] == 0


class TestNewSanguoAgentCommandRouting:
    """测试命令路由"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 依赖的 Agent"""
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
            
            # 设置 service 的 genku_list 和 get_meta_genkus 供 _cmd_info 使用
            mock_service = Mock()
            mock_service.genku_list = []
            mock_service.get_meta_genkus.return_value = []
            mock_service.model = None
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_command_help(self, mock_agent):
        """测试 /帮助 命令"""
        result = mock_agent.handle("/帮助")
        assert "帮助" in result or "命令" in result
    
    def test_command_info(self, mock_agent):
        """测试 /新三国 命令"""
        result = mock_agent.handle("/新三国")
        # 返回格式是 v2.6 信息，包含状态、模式、梗库等
        assert "v2.6" in result or "状态" in result or "梗库" in result
    
    def test_command_cancel(self, mock_agent):
        """测试 /取消 命令重置状态"""
        mock_agent.state = State.INPUT_WAITING
        result = mock_agent.handle("/取消")
        assert mock_agent.state == State.IDLE
    
    def test_unknown_command(self, mock_agent):
        """测试未知命令返回帮助"""
        result = mock_agent.handle("/未知命令")
        assert "未知" in result or "帮助" in result
    
    def test_input_command_enters_input_state(self, mock_agent):
        """测试 /录入 命令进入输入状态"""
        result = mock_agent.handle("/录入")
        assert mock_agent.state == State.INPUT_WAITING


class TestNewSanguoAgentChatHandling:
    """测试对话处理"""
    
    @pytest.fixture
    def mock_agent_with_genku(self):
        """创建带有返回梗能力的 Agent"""
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger, \
             patch('new_sanguo.agent.get_topic_mapper') as MockTopicMapper:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
                'dialogue.genku_chain.cooldown_turns': 3,
                'dialogue.genku_chain.max_chain_length': 5,
                'fusion.enabled': False,
                'matching.temperature': 1.0,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            mock_db.record_genku_usage.return_value = None
            MockDatabase.return_value = mock_db
            
            # 创建模拟 Genku
            mock_genku = Mock(spec=Genku)
            mock_genku.genku_id = "test_genku_001"
            mock_genku.original = "不可能，绝对不可能"
            mock_genku.person = "曹操"
            mock_genku.emotions = ["惊讶"]
            mock_genku.tags = ["经典"]
            mock_genku.weight = 5
            mock_genku.variant_template = None
            
            mock_service = Mock()
            mock_service.match_genku.return_value = (mock_genku, None)
            mock_service.sample_with_temperature.return_value = mock_genku
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            # Mock topic mapper
            mock_topic_mapper = Mock()
            mock_topic_mapper.identify_topic.return_value = (Mock(), 0.8)
            mock_topic_mapper.check_information_sufficiency.return_value = (True, "")
            mock_topic_mapper.check_explicit_search_request.return_value = (False, "")
            MockTopicMapper.return_value = mock_topic_mapper
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent, mock_service, mock_genku
    
    def test_chat_returns_genku(self, mock_agent_with_genku):
        """测试普通对话返回梗"""
        agent, mock_service, mock_genku = mock_agent_with_genku
        
        # Mock _output_genku 避免复杂渲染逻辑
        agent._output_genku = Mock(return_value="不可能，绝对不可能")
        
        result = agent.handle("这也太离谱了吧")
        
        assert "不可能" in result
        mock_service.match_genku.assert_called_once()
    
    def test_chat_updates_context(self, mock_agent_with_genku):
        """测试对话更新上下文"""
        agent, mock_service, mock_genku = mock_agent_with_genku
        
        # Mock _output_genku
        agent._output_genku = Mock(return_value="测试输出")
        
        agent.handle("测试输入")
        
        assert agent.context['last_input'] == "测试输入"
    
    def test_input_length_check(self, mock_agent_with_genku):
        """测试输入长度检查"""
        agent, mock_service, mock_genku = mock_agent_with_genku
        
        long_input = "x" * 3000
        result = agent.handle(long_input)
        
        assert "太长" in result
        mock_service.match_genku.assert_not_called()


class TestNewSanguoAgentOutputFormatting:
    """测试响应格式化"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 依赖的 Agent"""
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
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
class TestNewSanguoAgentChainLogic:
    """测试接龙逻辑"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 依赖的 Agent"""
        with patch('new_sanguo.agent.Config') as MockConfig, \
             patch('new_sanguo.agent.Database') as MockDatabase, \
             patch('new_sanguo.agent.GenkuService') as MockService, \
             patch('new_sanguo.agent.setup_logger') as MockLogger:
            
            mock_config = Mock()
            mock_config.get.side_effect = lambda key, default=None: {
                'dialogue.context_memory.max_history': 10,
                'matching.max_input_length': 2000,
                'dialogue.genku_chain.cooldown_turns': 3,
                'dialogue.genku_chain.max_chain_length': 5,
            }.get(key, default)
            MockConfig.return_value = mock_config
            
            mock_db = Mock()
            mock_db.get_user_preference.return_value = None
            MockDatabase.return_value = mock_db
            
            mock_service = Mock()
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_chain_cooldown_set_to_config_value(self, mock_agent):
        """测试接龙冷却设置为配置值"""
        mock_agent._reset_chain()
        
        expected_cooldown = mock_agent.config.get('dialogue.genku_chain.cooldown_turns', 3)
        assert mock_agent.context['chain_state']['cooldown'] == expected_cooldown
        assert mock_agent.context['chain_state']['active'] == False
        assert mock_agent.context['chain_state']['sequence'] == []
    
    def test_conversation_history_limit(self, mock_agent):
        """测试对话历史限制"""
        # 填充超过限制的历史
        for i in range(15):
            mock_agent._update_conversation_history(f"输入{i}", f"输出{i}", f"genku_{i}")
        
        max_history = mock_agent.config.get('dialogue.context_memory.max_history', 10)
        assert len(mock_agent.context['conversation_history']) <= max_history


class TestNewSanguoAgentErrorHandling:
    """测试错误处理"""
    
    @pytest.fixture
    def mock_agent(self):
        """创建带 Mock 依赖的 Agent"""
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
            MockService.return_value = mock_service
            
            mock_logger = Mock()
            MockLogger.return_value = mock_logger
            
            from new_sanguo.agent import NewSanguoAgent
            agent = NewSanguoAgent("test_user")
            yield agent
    
    def test_exception_returns_error_message(self, mock_agent):
        """测试异常返回错误消息"""
        # 制造一个异常条件
        mock_agent._route_command = Mock(side_effect=Exception("测试异常"))
        
        result = mock_agent.handle("/帮助")
        
        assert "⚠️" in result or "错误" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
