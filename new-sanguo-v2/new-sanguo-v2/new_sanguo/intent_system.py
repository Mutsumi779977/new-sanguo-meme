"""
新三国梗系统 - 统一意图系统 v2.8.0
整合：情感识别 + 行为识别 + 梗功能匹配
替代原 emotion_recognizer.py + intent_recognizer.py + agent.py中的分散逻辑
"""
from typing import Dict, List, Tuple, Optional
from enum import Enum, auto
from dataclasses import dataclass


class EmotionType(Enum):
    """情感类型"""
    JOY = "喜悦"
    GRATITUDE = "感激"
    AGREEMENT = "认同"
    PRAISE = "赞叹"
    EXCITEMENT = "兴奋"
    SURPRISE = "惊讶"
    SADNESS = "悲伤"
    ANGER = "愤怒"
    CONFUSION = "困惑"
    NEUTRAL = "中性"


class UserAction(Enum):
    """用户行为意图"""
    SHARE_GOOD_NEWS = "分享好消息"
    EXPRESS_THANKS = "表达感谢"
    SEEK_AGREEMENT = "寻求认同"
    SHOW_APPRECIATION = "表示赞赏"
    EXPRESS_EMOTION = "单纯表达情绪"
    ASK_QUESTION = "提问"
    SEEK_COMFORT = "寻求安慰"
    VENT_FRUSTRATION = "发泄不满"
    MAKE_JOKE = "开玩笑"
    DISCUSS_TOPIC = "讨论话题"


class GenkuFunction(Enum):
    """梗的功能用途"""
    CONGRATULATE = "祝贺"
    AGREE = "认同附和"
    PRAISE = "赞扬封神"
    COMFORT = "安慰"
    MOCK = "吐槽嘲讽"
    EXPRESS_SHOCK = "表达震惊"
    SHOW_OFF = "炫耀"
    COMPLAIN = "抱怨"
    QUESTION = "质疑"
    ENTERTAIN = "娱乐搞笑"


@dataclass
class UnifiedIntent:
    """统一意图对象"""
    emotion: EmotionType
    action: UserAction
    function_need: GenkuFunction
    suggested_genkus: List[str]
    confidence: float
    matched_keywords: List[str]


class IntentSystem:
    """
    统一意图系统
    单一入口处理所有意图相关逻辑
    """

    # 情感关键词映射（整合自原emotion_recognizer）
    EMOTION_PATTERNS = {
        EmotionType.JOY: ['开心', '高兴', '快乐', '治愈', '好了', '痊愈', '棒', '赞', '好',
                         '爽', '舒服', '喜欢', '爱', '哈哈哈', '笑得', '太棒了'],
        EmotionType.GRATITUDE: ['感谢', '谢谢', '多亏', '幸亏', '感恩', '托您的福', '治好了'],
        EmotionType.AGREEMENT: ['同意', '认同', '没错', '确实', '对', '是', '说得好', '所言极是',
                               '痛切', '有道理', '支持', '附议', '我也是'],
        EmotionType.PRAISE: ['厉害', '牛逼', '神', '天才', '完美', '封神', '绝了', '无敌',
                            '佩服', '牛', '强', '伟大', '传奇'],
        EmotionType.EXCITEMENT: ['激动', '期待', '等不及', '迫不及待', '终于', '要来了', '啊啊啊'],
        EmotionType.SURPRISE: ['震惊', '惊讶', '没想到', '居然', '竟然', '不可能', '真的吗', 'wtf'],
        EmotionType.SADNESS: ['难过', '伤心', '悲伤', '哭', '泪', '难受', '抑郁', '失落', '痛苦', '遗憾'],
        EmotionType.ANGER: ['生气', '愤怒', '讨厌', '恨', '烦', '垃圾', '烂', '恶心', '气死'],
        EmotionType.CONFUSION: ['不懂', '不明白', '疑惑', '疑问', '为什么', '怎么', '什么'],
    }

    # 行为识别模式（整合自原intent_recognizer）
    ACTION_PATTERNS = {
        UserAction.SHARE_GOOD_NEWS: {
            'keywords': ['治好了', '痊愈', '成功了', '考上了', '中了', '发财', '脱单', '升职加薪'],
            'emotions': [EmotionType.JOY, EmotionType.GRATITUDE, EmotionType.EXCITEMENT],
            'indicators': ['我', '终于', '了']
        },
        UserAction.EXPRESS_THANKS: {
            'keywords': ['感谢', '谢谢', '多亏', '托', '福', '没有你就', '幸亏'],
            'emotions': [EmotionType.GRATITUDE, EmotionType.JOY],
            'indicators': ['你', '贴主', 'up主']
        },
        UserAction.SEEK_AGREEMENT: {
            'keywords': ['是不是', '对吧', '应该', '我觉得', '我认为', '难道不'],
            'emotions': [EmotionType.AGREEMENT, EmotionType.NEUTRAL],
            'indicators': ['?', '？']
        },
        UserAction.SHOW_APPRECIATION: {
            'keywords': ['牛逼', '厉害', '神作', '封神', '绝了'],
            'emotions': [EmotionType.PRAISE, EmotionType.JOY],
            'indicators': ['太', '真的', '确实']
        },
        UserAction.VENT_FRUSTRATION: {
            'keywords': ['气死', '受不了', '无语', '离谱', '什么鬼', '醉了'],
            'emotions': [EmotionType.ANGER, EmotionType.SURPRISE],
            'indicators': ['真的', '太']
        },
        UserAction.MAKE_JOKE: {
            'keywords': ['哈哈哈', '笑死', '地狱笑话', '蚌埠住', '绷不住'],
            'emotions': [EmotionType.JOY, EmotionType.SURPRISE],
            'indicators': ['doge', '[doge]', '（']
        },
        UserAction.ASK_QUESTION: {
            'keywords': ['怎么', '为什么', '什么', '谁', '哪里', '如何', '吗'],
            'emotions': [EmotionType.CONFUSION, EmotionType.NEUTRAL],
            'indicators': []
        },
    }

    # 意图 → 梗功能 映射
    EMOTION_ACTION_TO_FUNCTION = {
        (EmotionType.SURPRISE, UserAction.EXPRESS_EMOTION): GenkuFunction.EXPRESS_SHOCK,
        (EmotionType.SURPRISE, UserAction.ASK_QUESTION): GenkuFunction.EXPRESS_SHOCK,
        (EmotionType.AGREEMENT, UserAction.SHOW_APPRECIATION): GenkuFunction.AGREE,
        (EmotionType.AGREEMENT, UserAction.SEEK_AGREEMENT): GenkuFunction.AGREE,
        (EmotionType.PRAISE, UserAction.SHOW_APPRECIATION): GenkuFunction.PRAISE,
        (EmotionType.PRAISE, UserAction.SHARE_GOOD_NEWS): GenkuFunction.PRAISE,
        (EmotionType.ANGER, UserAction.VENT_FRUSTRATION): GenkuFunction.MOCK,
        (EmotionType.ANGER, UserAction.EXPRESS_EMOTION): GenkuFunction.MOCK,
        (EmotionType.JOY, UserAction.MAKE_JOKE): GenkuFunction.ENTERTAIN,
        (EmotionType.JOY, UserAction.SHARE_GOOD_NEWS): GenkuFunction.CONGRATULATE,
        (EmotionType.SADNESS, UserAction.SEEK_COMFORT): GenkuFunction.COMFORT,
        (EmotionType.SADNESS, UserAction.EXPRESS_EMOTION): GenkuFunction.COMPLAIN,
        (EmotionType.CONFUSION, UserAction.ASK_QUESTION): GenkuFunction.QUESTION,
    }

    # 功能 → 推荐梗ID 映射（集中管理）
    FUNCTION_TO_GENKU_IDS = {
        GenkuFunction.EXPRESS_SHOCK: ['xsg_cc_002', 'xsg_cc_018', 'xsg_cc_019'],
        GenkuFunction.AGREE: ['xsg_cp_001', 'xsg_gy_002', 'xsg_cc_024'],
        GenkuFunction.PRAISE: ['xsg_cc_019', 'xsg_cc_009'],
        GenkuFunction.MOCK: ['xsg_cc_013', 'xsg_zf_001', 'xsg_cc_023'],
        GenkuFunction.ENTERTAIN: ['xsg_cc_023', 'xsg_lb_001', 'xsg_pf_001'],
        GenkuFunction.CONGRATULATE: ['xsg_cc_009', 'xsg_xy_004'],
        GenkuFunction.COMFORT: ['xsg_cc_003', 'xsg_cc_005'],
        GenkuFunction.COMPLAIN: ['xsg_cc_003', 'xsg_xy_001'],
        GenkuFunction.QUESTION: ['xsg_wr_001', 'xsg_cc_002'],
    }

    def analyze(self, text: str, context: Dict = None) -> UnifiedIntent:
        """
        统一分析入口

        Args:
            text: 用户输入文本
            context: 可选上下文

        Returns:
            UnifiedIntent 包含完整意图信息
        """
        text_lower = text.lower()

        # 1. 情感识别
        emotion, emotion_conf, emotion_kw = self._recognize_emotion(text_lower)

        # 2. 行为识别
        action, action_conf, action_kw = self._recognize_action(text_lower, emotion)

        # 3. 功能需求映射
        function = self._map_to_function(emotion, action)

        # 4. 推荐梗
        suggested_genkus = self._suggest_by_function(function)

        # 5. 计算综合置信度
        confidence = min(emotion_conf, action_conf) * 0.8 + 0.2  # 基础分0.2

        return UnifiedIntent(
            emotion=emotion,
            action=action,
            function_need=function,
            suggested_genkus=suggested_genkus,
            confidence=confidence,
            matched_keywords=emotion_kw + action_kw
        )

    def _recognize_emotion(self, text: str) -> Tuple[EmotionType, float, List[str]]:
        """识别情感"""
        scores = {}
        matched_keywords = {}

        for emotion, keywords in self.EMOTION_PATTERNS.items():
            matched = [kw for kw in keywords if kw in text]
            if matched:
                scores[emotion] = len(matched)
                matched_keywords[emotion] = matched

        if not scores:
            return EmotionType.NEUTRAL, 0.3, []

        best_emotion = max(scores, key=scores.get)
        confidence = min(scores[best_emotion] * 0.3, 1.0)

        return best_emotion, confidence, matched_keywords.get(best_emotion, [])

    def _recognize_action(self, text: str, emotion: EmotionType) -> Tuple[UserAction, float, List[str]]:
        """识别行为"""
        scores = {}
        matched_keywords = {}

        for action, pattern in self.ACTION_PATTERNS.items():
            score = 0
            matched = []

            # 情感匹配
            if emotion in pattern['emotions']:
                score += 2

            # 关键词匹配
            for kw in pattern['keywords']:
                if kw in text:
                    score += 1
                    matched.append(kw)

            # 指示词匹配
            for indicator in pattern['indicators']:
                if indicator in text:
                    score += 0.5

            if score > 0:
                scores[action] = score
                matched_keywords[action] = matched

        if not scores:
            return UserAction.EXPRESS_EMOTION, 0.3, []

        best_action = max(scores, key=scores.get)
        confidence = min(scores[best_action] * 0.2, 1.0)

        return best_action, confidence, matched_keywords.get(best_action, [])

    def _map_to_function(self, emotion: EmotionType, action: UserAction) -> GenkuFunction:
        """映射到梗功能"""
        key = (emotion, action)
        if key in self.EMOTION_ACTION_TO_FUNCTION:
            return self.EMOTION_ACTION_TO_FUNCTION[key]

        #  fallback：仅根据情感
        emotion_only_map = {
            EmotionType.SURPRISE: GenkuFunction.EXPRESS_SHOCK,
            EmotionType.ANGER: GenkuFunction.MOCK,
            EmotionType.JOY: GenkuFunction.ENTERTAIN,
            EmotionType.SADNESS: GenkuFunction.COMPLAIN,
            EmotionType.PRAISE: GenkuFunction.PRAISE,
            EmotionType.AGREEMENT: GenkuFunction.AGREE,
        }

        return emotion_only_map.get(emotion, GenkuFunction.ENTERTAIN)

    def _suggest_by_function(self, function: GenkuFunction) -> List[str]:
        """根据功能推荐梗"""
        return self.FUNCTION_TO_GENKU_IDS.get(function, [])

    def get_function_name(self, function: GenkuFunction) -> str:
        """获取功能中文名"""
        return function.value


# 向后兼容：保留原EmotionRecognizer接口
class EmotionRecognizer:
    """兼容旧接口的情感识别器"""

    def __init__(self):
        self.system = IntentSystem()

    def recognize(self, text: str) -> Tuple[EmotionType, float, List[str]]:
        intent = self.system.analyze(text)
        return intent.emotion, intent.confidence, intent.matched_keywords


# 向后兼容：保留原IntentRecognizer接口
class IntentRecognizer:
    """兼容旧接口的意图识别器"""

    def __init__(self):
        self.system = IntentSystem()

    def recognize(self, text: str) -> 'Intent':
        """返回兼容格式"""
        intent = self.system.analyze(text)

        # 构造兼容对象
        class CompatibleIntent:
            def __init__(self, emotion, action, confidence, keywords):
                self.emotion = emotion
                self.action = action
                self.confidence = confidence
                self.keywords = keywords
                self.context = {}

        return CompatibleIntent(
            emotion=intent.emotion,
            action=intent.action,
            confidence=intent.confidence,
            keywords=intent.matched_keywords
        )
