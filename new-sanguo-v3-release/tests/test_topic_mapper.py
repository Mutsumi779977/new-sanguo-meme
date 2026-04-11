"""
话题映射器单元测试

测试范围：
- 话题识别 (identify_topic)
- 信息充足度检测 (check_information_sufficiency)
- 日常闲聊模式匹配
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from new_sanguo.topic_mapper import TopicMapper, TopicCategory


class TestTopicIdentification:
    """测试话题识别功能"""
    
    @pytest.fixture
    def mapper(self):
        """创建TopicMapper实例"""
        return TopicMapper()
    
    def test_identify_esports_topic(self, mapper):
        """测试电竞话题识别"""
        test_cases = [
            ("gen2:0T1", TopicCategory.ESPORTS),
            ("LPL春季赛", TopicCategory.ESPORTS),
            ("T1 vs Gen.G", TopicCategory.ESPORTS),
            ("英雄联盟比赛", TopicCategory.ESPORTS),
        ]
        for text, expected in test_cases:
            topic, confidence = mapper.identify_topic(text)
            assert topic == expected, f"'{text}' 应识别为 {expected.value}, 实际是 {topic.value}"
            assert confidence > 0.3, f"'{text}' 置信度应 > 0.3, 实际是 {confidence}"
    
    def test_identify_tech_topic(self, mapper):
        """测试科技话题识别"""
        test_cases = [
            ("GPT5发布了", TopicCategory.TECH),
            ("华为新芯片", TopicCategory.TECH),
            ("AI大模型", TopicCategory.TECH),
            ("显卡价格", TopicCategory.TECH),
        ]
        for text, expected in test_cases:
            topic, confidence = mapper.identify_topic(text)
            assert topic == expected, f"'{text}' 应识别为 {expected.value}"
    
    def test_identify_daily_topic(self, mapper):
        """测试日常闲聊话题识别 - '[动词]什么'模式"""
        test_cases = [
            ("吃什么", TopicCategory.DAILY),
            ("看什么电影", TopicCategory.DAILY),
            ("听什么歌", TopicCategory.DAILY),
            ("玩什么游戏", TopicCategory.DAILY),
            ("喝什么奶茶", TopicCategory.DAILY),
        ]
        for text, expected in test_cases:
            topic, confidence = mapper.identify_topic(text)
            assert topic == expected, f"'{text}' 应识别为 {expected.value}"
            assert confidence >= 0.6, f"'{text}' 日常话题置信度应 >= 0.6"
    
    def test_identify_game_topic(self, mapper):
        """测试游戏话题识别"""
        test_cases = [
            ("原神抽卡歪了", TopicCategory.GAME),
            ("星铁剧情", TopicCategory.GAME),
            ("黑神话悟空", TopicCategory.GAME),
        ]
        for text, expected in test_cases:
            topic, confidence = mapper.identify_topic(text)
            assert topic == expected, f"'{text}' 应识别为 {expected.value}"
    
    def test_identify_unknown_topic(self, mapper):
        """测试未知话题识别"""
        # 使用不含数字和英文的纯乱码字符串
        topic, confidence = mapper.identify_topic("混沌虚无无极")
        assert topic == TopicCategory.UNKNOWN
        assert confidence == 0.0


class TestInformationSufficiency:
    """测试信息充足度检测功能"""
    
    @pytest.fixture
    def mapper(self):
        return TopicMapper()
    
    def test_sufficient_esports_score(self, mapper):
        """测试电竞比分信息充足"""
        # 纯比分信息充足
        is_sufficient, reason = mapper.check_information_sufficiency("gen2:0T1", TopicCategory.ESPORTS)
        assert is_sufficient == True, f"纯比分应判定为充足，实际是: {reason}"
    
    def test_insufficient_esports_query(self, mapper):
        """测试电竞询问类信息不充足"""
        # 询问类需要搜索
        is_sufficient, reason = mapper.check_information_sufficiency(
            "Gen.G今天赢了吗", TopicCategory.ESPORTS
        )
        assert is_sufficient == False, "询问类应判定为不充足"
        assert "今天" in reason or "时效" in reason or "背景知识" in reason
    
    def test_sufficient_game_gacha(self, mapper):
        """测试游戏抽卡信息充足"""
        is_sufficient, reason = mapper.check_information_sufficiency("原神又歪了", TopicCategory.GAME)
        assert is_sufficient == True, f"抽卡吐槽应判定为充足，实际是: {reason}"
    
    def test_insufficient_game_story(self, mapper):
        """测试游戏剧情信息不充足"""
        is_sufficient, reason = mapper.check_information_sufficiency(
            "原神诺德卡莱剧情怎么样", TopicCategory.GAME
        )
        assert is_sufficient == False, "剧情评价应判定为不充足"
    
    def test_sufficient_daily_chat(self, mapper):
        """测试日常闲聊信息充足"""
        is_sufficient, reason = mapper.check_information_sufficiency(
            "我晚上要吃什么呢？", TopicCategory.DAILY
        )
        assert is_sufficient == True, "日常闲聊应判定为充足"
    
    def test_unknown_topic_insufficient(self, mapper):
        """测试未知话题默认不充足"""
        is_sufficient, reason = mapper.check_information_sufficiency(
            "一些不认识的词", TopicCategory.UNKNOWN
        )
        assert is_sufficient == False, "未知话题应判定为不充足"


class TestDailyChatPatterns:
    """测试日常闲聊模式匹配"""
    
    @pytest.fixture
    def mapper(self):
        return TopicMapper()
    
    def test_shi_a_pattern_variations(self, mapper):
        """测试'是啊，[动词]什么'各种动词变体"""
        verbs = ['吃', '看', '听', '玩', '喝', '学', '干', '说', '做', '追']
        for verb in verbs:
            text = f"{verb}什么呢？"
            topic, confidence = mapper.identify_topic(text)
            assert topic == TopicCategory.DAILY, f"'{text}' 应识别为日常话题"
    
    def test_greeting_patterns(self, mapper):
        """测试问候语识别"""
        greetings = ["你好", "嗨", "哈喽"]
        for text in greetings:
            topic, confidence = mapper.identify_topic(text)
            assert topic == TopicCategory.DAILY, f"'{text}' 应识别为日常话题"
    
    def test_farewell_patterns(self, mapper):
        """测试告别语识别"""
        farewells = ["再见", "拜拜"]
        for text in farewells:
            topic, confidence = mapper.identify_topic(text)
            assert topic == TopicCategory.DAILY, f"'{text}' 应识别为日常话题"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
