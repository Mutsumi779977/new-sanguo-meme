"""
梗的完整数据模型 v3.0

核心原则：
1. 核心结构不可动（保持辨识度）
2. 可变部分明确标注（用于模板填充）
3. 双情景系统：剧中情景 + 使用情景
4. 双情感系统：剧中情感 + 使用情感
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class DramaticContext(Enum):
    """剧中原始情景（剧情）"""
    # 按人物分类
    CAOCAO_ANGRY = "曹操发怒"      # 叉出去、放肆
    CAOCAO_SUSPICIOUS = "曹操多疑"  # 这是谁的部将
    CAOCAO_SHOCKED = "曹操震惊"    # 不可能绝对不可能
    YUANSHU_ARROGANT = "袁术称帝"   # 恭喜可以撑地了
    YUANSHU_THREATEN = "袁术威胁"  # 列位诸公
    LIUBEI_DRUNK = "刘备醉酒"      # 接着奏乐接着舞
    GUANYU_DRUNK = "关羽醉酒"      # 三弟说得痛切
    GONGSUNZAN_SARCASTIC = "公孙瓒吐槽"  # 笑面虎乌角鲨
    # ... 更多


class UsageContext(Enum):
    """梗使用情景（用户行为）"""
    # 回应类
    RESPOND_TO_ANGER = "回应愤怒"      # 对方生气时
    RESPOND_TO_ARROGANCE = "回应傲慢"  # 对方装逼时
    RESPOND_TO_SURPRISE = "回应震惊"   # 对方惊讶时
    RESPOND_TO_COMPLAINT = "回应抱怨"  # 对方吐槽时
    
    # 表达类
    EXPRESS_ANGER = "表达愤怒"         # 自己生气
    EXPRESS_AGREEMENT = "表达认同"     # 表示同意
    EXPRESS_SHOCK = "表达震惊"         # 表示惊讶
    EXPRESS_SARCASM = "表达讽刺"       # 阴阳怪气
    EXPRESS_REJECTION = "表达拒绝"     # 不想理人
    
    # 互动类
    SEEK_ATTENTION = "寻求关注"        # 想被注意到
    SHOW_OFF = "炫耀"                  # 显摆
    MAKE_JOKE = "开玩笑"               # 幽默


class DramaticEmotion(Enum):
    """剧中情感（角色当时的情绪）"""
    ANGRY = "愤怒"
    SHOCKED = "震惊"
    ARROGANT = "傲慢"
    DRUNK = "醉态"
    SARCASTIC = "讽刺"
    SERIOUS = "严肃"
    COMFORTABLE = "惬意"


class UsageEmotion(Enum):
    """使用情感（用户用梗时的情绪）"""
    PLAYFUL = "玩味"       # 开玩笑
    GENUINE = "真诚"       # 真这么觉得
    SARCASTIC = "讽刺"     # 阴阳怪气
    DEFENSIVE = "防御"     # 保护自己
    AGGRESSIVE = "进攻"    # 主动出击
    NEUTRAL = "中性"       # 无特别情感


@dataclass
class GenkuCore:
    """
    梗的核心结构（不可变动部分）
    
    这些是保持辨识度的关键，不能替换。
    例如：
    - "我再听到" + "扎聋" 是"再听扎聋"的核心
    - "不可能" + "绝对不可能" 是递进的核心
    """
    fixed_parts: List[str]  # 固定部分，如 ["我再听到", "扎聋"]
    variable_slots: List[str]  # 可变槽位，如 ["对象"]
    structure_type: str  # 结构类型：递进、反问、感叹、命令...


@dataclass
class GenkuV3:
    """
    梗完整数据模型 v3.0
    
    从"情感+行为"两维度定义梗的用途
    """
    # 基础信息
    genku_id: str
    original: str
    person: str
    source: str
    
    # 核心结构（不可动）
    core: GenkuCore
    
    # 剧中维度（原始语境）
    dramatic_context: DramaticContext  # 剧中情景
    dramatic_emotion: DramaticEmotion  # 剧中情感
    
    # 使用维度（用户怎么用）
    usage_contexts: List[UsageContext]  # 适用情景
    usage_emotions: List[UsageEmotion]  # 使用时的情感色彩
    
    # 功能标签（用于快速匹配）
    functions: List[str]  # ["祝贺", "吐槽", "认同"]
    
    # 变体模板
    template: Optional[str] = None  # "我再听到{对象}，我就扎聋我自己的耳朵！"
    
    # 示例用法（从帖子中学习）
    examples: List[Dict] = field(default_factory=list)
    # 如：{"user_situation": "被惹生气", "usage": "自我克制"}


# 从帖子中提取的具体用法示例
GENKU_USAGE_EXAMPLES = {
    "xsg_xw_001": [  # 不要愤怒
        {
            "user_situation": "被惹生气了",
            "usage": "自我克制，劝自己冷静",
            "usage_emotion": "DEFENSIVE",
            "dramatic_context": "荀彧劝曹操"
        }
    ],
    "xsg_ys_001": [  # 恭喜可以撑地了
        {
            "user_situation": "对方装逼/傲慢",
            "usage": "讽刺祝贺",
            "usage_emotion": "SARCASTIC",
            "dramatic_context": "袁术称帝"
        }
    ],
    "xsg_ys_002": [  # 叉出去
        {
            "user_situation": "不想理某人",
            "usage": "驱逐/拒绝",
            "usage_emotion": "AGGRESSIVE",
            "dramatic_context": "曹操发怒"
        }
    ],
    "xsg_meta_003": [  # 放肆
        {
            "user_situation": "对方无礼",
            "usage": "警告/威慑",
            "usage_emotion": "AGGRESSIVE",
            "dramatic_context": "曹操发怒"
        }
    ],
    "xsg_gs_001": [  # 一对笑面虎
        {
            "user_situation": "某人表里不一",
            "usage": "讽刺揭露",
            "usage_emotion": "SARCASTIC",
            "dramatic_context": "公孙瓒吐槽"
        }
    ],
    "xsg_meta_004": [  # 不可能绝对不可能
        {
            "user_situation": "事情变化太快",
            "usage": "表达震惊",
            "usage_emotion": "SHOCKED",
            "dramatic_context": "曹操震惊"
        }
    ],
}
