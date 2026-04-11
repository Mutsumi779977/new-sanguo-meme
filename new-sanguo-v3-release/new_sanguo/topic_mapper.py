"""
新三国梗系统 v3.0
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
新三国梗系统 - 话题映射器

识别输入所属话题领域，映射到对应的情绪/场景，
从而找到合适的新三国梗。
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum, auto


class TopicCategory(Enum):
    """话题分类"""
    ESPORTS = "电竞赛事"      # LCK, LPL, S赛等
    TECH = "科技数码"         # AI, 手机, 电脑等
    ENTERTAINMENT = "娱乐"    # 影视, 综艺, 明星
    POLITICS = "时政"         # 新闻, 政策
    SPORTS = "体育"           # 足球, 篮球等
    GAME = "游戏"             # 单机游戏, 手游
    DAILY = "日常"            # 日常闲聊（吃、天气、心情等）
    UNKNOWN = "未知"


@dataclass
class TopicMapping:
    """话题映射配置"""
    category: TopicCategory
    keywords: List[str]
    emotions: List[str]       # 映射到的情绪标签
    scenes: List[str]         # 映射到的场景标签
    default_persons: List[str]  # 默认关联人物


class TopicMapper:
    """
    话题映射器

    识别输入话题类型，映射到情绪/场景标签，
    辅助梗匹配系统找到更合适的梗。
    """

    # 话题识别关键词
    TOPIC_PATTERNS = {
        TopicCategory.ESPORTS: {
            'keywords': [
                'lck', 'lpl', 's赛', '世界赛', 'msi', 'gen', 't1', 'blg', 'tes',
                'faker', 'chovy', 'uzi', 'theshy', 'rng', 'edg', 'dk', 'kt',
                '比赛', '战绩', '比分', '零封', '让二追三', 'bo5', '决赛'
            ],
            'emotions': ['震惊', '不服输', '愤怒', '遗憾'],
            'scenes': ['竞争', '对决', '胜负'],
            'persons': ['曹操', '张飞', '袁绍']
        },
        TopicCategory.TECH: {
            'keywords': [
                'ai', 'gpt', 'claude', 'kimi', '大模型', '芯片', '显卡', 'cpu',
                '华为', '苹果', '小米', '发布会', '新品', '科技', '数码',
                'gen', 'gpt4', 'llm', '算力', '算法'
            ],
            'emotions': ['震惊', '自负', '自信', '嘲讽'],
            'scenes': ['创新', '突破', '比较'],
            'persons': ['曹操', '诸葛亮', '关羽']
        },
        TopicCategory.ENTERTAINMENT: {
            'keywords': [
                '电影', '电视剧', '综艺', '明星', '演员', '导演', '票房',
                '豆瓣', '评分', '烂片', '神作', '追剧', '更新',
                '翻唱', '歌手', '演唱会', '版权', '侵权', '授权', '歌曲'
            ],
            'emotions': ['嘲讽', '调侃', '兴奋', '失望'],
            'scenes': ['评价', '比较', '吐槽'],
            'persons': ['曹操', '刘备', '张飞']
        },
        TopicCategory.SPORTS: {
            'keywords': [
                '足球', '篮球', 'nba', '世界杯', '欧冠', '英超', '湖人', '勇士',
                '进球', '绝杀', '逆转', '平局', '夺冠'
            ],
            'emotions': ['震惊', '兴奋', '不服输', '遗憾'],
            'scenes': ['竞争', '胜负', '逆转'],
            'persons': ['曹操', '张飞', '吕布']
        },
        TopicCategory.POLITICS: {
            'keywords': [
                '特朗普', '拜登', '美国', '伊朗', '军事行动', '空袭', '战争',
                '政治', '国际', '外交', '冲突', '制裁', '核设施', '访华'
            ],
            'emotions': ['震惊', '愤怒', '嘲讽', '难以置信'],
            'scenes': ['战争', '冲突', '国际'],
            'persons': ['曹操', '刘备', '诸葛亮']
        },
        TopicCategory.GAME: {
            'keywords': [
                '原神', '星铁', '黑神话', 'steam', '单机', '手游', '版本',
                '更新', '补丁', 'bug', '掉线', '连跪', '排位'
            ],
            'emotions': ['愤怒', '无奈', '吐槽', '自嘲'],
            'scenes': ['游戏', '失败', '抱怨'],
            'persons': ['张飞', '曹操', '刘备']
        },
        TopicCategory.DAILY: {
            'keywords': [
                '吃', '晚饭', '午饭', '早餐', '吃什么', '喝什么',
                '天气', '下雨', '晴天', '冷', '热',
                '今天', '明天', '现在', '刚刚',
                '心情', '累', '困', '无聊',
                '你好', '嗨', '哈喽', '在吗',
                '谢谢', '再见', '拜拜'
            ],
            'emotions': ['轻松', '随意', '调侃', '无奈'],
            'scenes': ['闲聊', '日常', '无厘头'],
            'persons': ['曹操', '刘备', '张飞', '陈宫']
        }
    }

    # 话题知识需求配置（方案A+）
    TOPIC_KNOWLEDGE_REQUIREMENTS = {
        TopicCategory.GAME: {
            'needs_context': True,
            'keywords_that_need_search': ['剧情', '版本', '新角色', '新地图', '怎么样', '如何评价', '如何看待', '整体'],
            'local_knowledge_keywords': ['抽卡', '歪了', '保底', '掉线', '连跪', '排位'],  # 本地梗能覆盖的
        },
        TopicCategory.TECH: {
            'needs_context': True,
            'keywords_that_need_search': ['发布', '更新', '怎么样', '如何评价', '评测'],
            'local_knowledge_keywords': ['厉害', '强', '无敌', '牛', '发布了'],
        },
        TopicCategory.ENTERTAINMENT: {
            'needs_context': True,
            'keywords_that_need_search': ['最近', '最新', '新闻', '事件', '怎么样'],
            'local_knowledge_keywords': ['版权', '侵权', '翻唱', '授权'],  # 单依纯事件已录入
        },
        TopicCategory.ESPORTS: {
            'needs_context': True,  # 电竞可能涉及时效性查询
            'keywords_that_need_search': ['今天', '最近', '怎么样', '战绩', '赢了', '输了', '了吗'],
            'local_knowledge_keywords': ['比分', '零封', '2:0', '3:0', '横扫', '让二追三'],
        },
        TopicCategory.POLITICS: {
            'needs_context': True,
            'keywords_that_need_search': ['为什么', '怎么回事', '最新', '最近'],
            'local_knowledge_keywords': ['taco', '反复无常', '退缩'],
        },
        TopicCategory.SPORTS: {
            'needs_context': False,
            'keywords_that_need_search': [],
            'local_knowledge_keywords': ['进球', '绝杀', '逆转'],
        },
        TopicCategory.DAILY: {
            'needs_context': False,  # 日常闲聊本地处理
            'keywords_that_need_search': [],
            'local_knowledge_keywords': ['吃', '天气', '今天', '心情', '你好', '谢谢'],
        },
    }
    SCORE_PATTERNS = [
        r'(\d+)[：:]?(\d+)',           # 0:1, 3:2
        r'(\d+)比(\d+)',               # 0比1
        r'(\w+?)(\d+)[：:](\w+?)(\d+)', # Gen20T1
        r'(\w+?)[零](\w+?)',           # Gen零T1（被零封）
    ]

    def __init__(self):
        self._build_keyword_index()

    def _build_keyword_index(self):
        """构建关键词索引加速查找"""
        self.keyword_to_topic: Dict[str, TopicCategory] = {}
        for topic, config in self.TOPIC_PATTERNS.items():
            for kw in config['keywords']:
                self.keyword_to_topic[kw.lower()] = topic

    def identify_topic(self, text: str) -> Tuple[TopicCategory, float]:
        """
        识别文本所属话题

        Returns:
            (话题分类, 置信度 0-1)
        """
        text_lower = text.lower()
        
        # 优先检查"是啊，[动词]什么"日常模式
        import re
        daily_verb_match = re.search(r'(吃|看|听|玩|喝|学|干|说|做|追|听).*?什么', text)
        if daily_verb_match:
            # 检查是否是纯日常闲聊（没有其他强话题关键词）
            has_strong_topic = False
            for topic, config in self.TOPIC_PATTERNS.items():
                if topic in [TopicCategory.ESPORTS, TopicCategory.TECH, TopicCategory.GAME]:
                    for kw in config['keywords']:
                        if kw in text_lower and kw not in ['什么', '怎么', '呢']:
                            has_strong_topic = True
                            break
            # 娱乐话题的"电影/剧"等不应该拦截"看什么/追什么"
            if not has_strong_topic or daily_verb_match.group(1) in ['看', '追', '听']:
                return TopicCategory.DAILY, 0.8
        
        scores: Dict[TopicCategory, int] = {}

        # 关键词匹配计分
        for topic, config in self.TOPIC_PATTERNS.items():
            score = 0
            for kw in config['keywords']:
                if kw in text_lower:
                    score += 1
                    # 完全匹配加分
                    if kw == text_lower or f' {kw} ' in f' {text_lower} ':
                        score += 1
            if score > 0:
                scores[topic] = score

        if not scores:
            # 尝试比分模式匹配
            if self._is_score_pattern(text):
                return TopicCategory.ESPORTS, 0.6
            return TopicCategory.UNKNOWN, 0.0

        # 取最高分
        best_topic = max(scores, key=scores.get)
        confidence = min(scores[best_topic] / 3, 1.0)  # 最多3个关键词达到1.0

        return best_topic, confidence

    def _is_score_pattern(self, text: str) -> bool:
        """检测是否是比分/战绩格式"""
        for pattern in self.SCORE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def parse_esports_match(self, text: str) -> Optional[Dict]:
        """
        解析电竞比赛信息

        识别队伍名、比分、胜负关系
        """
        # 常见战队名映射
        team_aliases = {
            'gen': 'Gen.G', 'gen.g': 'Gen.G', 'geng': 'Gen.G',
            't1': 'T1', 'skt': 'T1',
            'blg': 'BLG', 'tes': 'TES', 'jdg': 'JDG',
            'rng': 'RNG', 'edg': 'EDG', 'fpx': 'FPX',
            'dk': 'DK', 'kt': 'KT', 'hle': 'HLE',
        }

        result = {
            'team_a': None,
            'team_b': None,
            'score_a': None,
            'score_b': None,
            'winner': None,
            'is_upset': False,  # 是否是爆冷
        }

        # 尝试各种比分格式
        # 尝试各种比分格式
        # 格式1: gen2t1 (战队名+比分+战队名) - 支持已知战队别名
        team_aliases_lower = {k.lower(): v for k, v in team_aliases.items()}
        team_pattern = '(' + '|'.join(re.escape(t) for t in team_aliases_lower.keys()) + ')'

        match = re.search(team_pattern + r'(\d+)[：:]?(\d+)' + team_pattern, text, re.IGNORECASE)
        if match:
            team_a, score_a, score_b, team_b = match.groups()
            result['team_a'] = team_aliases_lower.get(team_a.lower(), team_a)
            result['team_b'] = team_aliases_lower.get(team_b.lower(), team_b)
            result['score_a'] = int(score_a)
            result['score_b'] = int(score_b)
            result['winner'] = result['team_a'] if result['score_a'] > result['score_b'] else result['team_b']
            return result

        # 格式2: T1 3:0 BLG (带空格的标准格式)
        match = re.search(r'(\w+?)\s+(\d+)\s*[：:]\s*(\d+)\s+(\w+?)', text, re.IGNORECASE)
        if match:
            team_a, score_a, score_b, team_b = match.groups()
            result['team_a'] = team_aliases_lower.get(team_a.lower(), team_a)
            result['team_b'] = team_aliases_lower.get(team_b.lower(), team_b)
            result['score_a'] = int(score_a)
            result['score_b'] = int(score_b)
            result['winner'] = result['team_a'] if result['score_a'] > result['score_b'] else result['team_b']
            return result

        # 格式2: 0:1, 3:2
        match = re.search(r'(\d+)\s*[：:]\s*(\d+)', text)
        if match:
            score_a, score_b = map(int, match.groups())
            result['score_a'] = score_a
            result['score_b'] = score_b
            # 尝试提取队伍名（在比分前后的单词）
            words = re.findall(r'[a-zA-Z]+', text)
            if len(words) >= 2:
                result['team_a'] = team_aliases.get(words[0].lower(), words[0])
                result['team_b'] = team_aliases.get(words[1].lower(), words[1])
            return result

        # 格式3: 提取已知战队名
        found_teams = []
        for alias, full_name in team_aliases.items():
            if alias in text.lower():
                found_teams.append(full_name)

        if found_teams:
            result['team_a'] = found_teams[0] if len(found_teams) > 0 else None
            result['team_b'] = found_teams[1] if len(found_teams) > 1 else None

        return result if result['team_a'] or result['score_a'] is not None else None

    def get_mapping(self, topic: TopicCategory) -> Dict:
        """获取话题的映射配置"""
        if topic == TopicCategory.UNKNOWN:
            return {
                'emotions': [],
                'scenes': [],
                'persons': []
            }
        return self.TOPIC_PATTERNS.get(topic, {
            'emotions': [],
            'scenes': [],
            'persons': []
        })

    # 显式搜索触发词
    EXPLICIT_SEARCH_KEYWORDS = [
        '搜索', '查一下', '帮我搜', '搜一下', '查查', '查查看',
        '搜索一下', '去搜', '去查', '查一查', '找一下',
    ]

    # 清理词（搜索触发词前后常见的无意义词）
    CLEANUP_WORDS = ['一下', '看看', '帮我', '给我', '给我']

    def check_explicit_search_request(self, text: str) -> Tuple[bool, str]:
        """
        检测用户是否明确要求联网搜索

        Args:
            text: 用户输入文本

        Returns:
            (是否要求搜索: bool, 清理后的文本: str)
        """
        for kw in self.EXPLICIT_SEARCH_KEYWORDS:
            if kw in text:
                # 移除搜索触发词
                cleaned = text.replace(kw, '').strip()
                # 清理常见无意义词
                for cw in self.CLEANUP_WORDS:
                    cleaned = cleaned.replace(cw, '').strip()
                return True, cleaned if cleaned else text
        return False, text

    def check_information_sufficiency(self, text: str, topic: TopicCategory) -> Tuple[bool, str]:
        """
        检查信息充足度（方案A+核心方法）

        判断当前话题是否需要联网搜索背景信息。

        Args:
            text: 用户输入文本
            topic: 识别到的话题分类

        Returns:
            (是否充足: bool, 原因: str)
        """
        # 未知话题直接判定为不充足
        if topic == TopicCategory.UNKNOWN:
            return False, "话题未知，需要联网确认"

        req = self.TOPIC_KNOWLEDGE_REQUIREMENTS.get(topic)
        if not req:
            # 话题无特殊需求，默认充足
            return True, "话题无背景知识需求"

        # 检查是否包含需要背景知识的关键词
        need_search_keywords = req.get('keywords_that_need_search', [])
        local_keywords = req.get('local_knowledge_keywords', [])

        has_need_search_kw = any(kw in text for kw in need_search_keywords)
        has_local_kw = any(kw in text for kw in local_keywords)

        # 决策逻辑
        if has_need_search_kw and not has_local_kw:
            # 只有需要搜索的关键词，没有本地能处理的
            return False, f"话题'{topic.value}'包含'{[kw for kw in need_search_keywords if kw in text][0]}'等评价性关键词，需要背景知识"

        if has_need_search_kw and has_local_kw:
            # 混合情况，优先保守策略（需要搜索）
            return False, f"话题'{topic.value}'需要确认最新信息"

        # 只有本地能处理的关键词
        if has_local_kw:
            return True, "本地梗库可覆盖"

        # 无特殊关键词，根据needs_context默认处理
        if req.get('needs_context', False):
            return False, f"话题'{topic.value}'默认需要背景知识确认"

        return True, "信息充足"

    def suggest_genku_tags(self, text: str) -> Dict[str, List[str]]:
        """
        建议用于匹配的标签

        根据话题识别结果，返回推荐的情绪/场景/人物标签。
        同时返回推荐的特定梗（如果有明确映射）。
        """
        topic, confidence = self.identify_topic(text)
        mapping = self.get_mapping(topic)

        suggestions = {
            'topic': topic.value,
            'confidence': confidence,
            'emotions': mapping.get('emotions', []),
            'scenes': mapping.get('scenes', []),
            'persons': mapping.get('persons', []),
            'suggested_genkus': [],  # 推荐的特定梗ID
        }

        # 特殊处理：电竞比赛
        if topic == TopicCategory.ESPORTS:
            match_info = self.parse_esports_match(text)
            if match_info:
                suggestions['match_info'] = match_info

                # 根据比分推断情绪和推荐梗
                if match_info.get('score_a') is not None and match_info.get('score_b') is not None:
                    sa, sb = match_info['score_a'], match_info['score_b']
                    winner = match_info.get('winner')

                    if sa == 0 and sb > 0:
                        # 被零封/惨败 - 震惊、否认
                        suggestions['emotions'] = ['震惊', '否认', '不服输']
                        suggestions['scenes'] = ['失败', '意外', '零封']
                        suggestions['suggested_genkus'] = ['不可能绝对不可能', '叉出去']
                    elif sa < sb:
                        # 输了但没那么惨 - 遗憾、不服输
                        suggestions['emotions'] = ['遗憾', '不服输', '震惊']
                        suggestions['scenes'] = ['惜败', '意外']
                        suggestions['suggested_genkus'] = ['不可能绝对不可能']
                    elif sa > sb:
                        # 赢了 - 称赞赢家厉害（双对象：输家 vs 赢家）
                        loser_name = match_info.get('team_b') if sa > sb else match_info.get('team_a')
                        winner_name = match_info.get('team_a') if sa > sb else match_info.get('team_b')
                        suggestions['emotions'] = ['赞赏', '惊讶', '还有高手']
                        suggestions['scenes'] = ['大胜', '碾压']
                        suggestions['persons'] = ['曹操']
                        # 双对象模板：输家被赢家超越
                        default_loser = '吕布'
                        default_winner = '此人'
                        suggestions['context_template'] = f'我原本以为{loser_name or default_loser}已经天下无敌了，没想到{winner_name or default_winner}比他还勇猛，这是谁的部将？'
                    elif abs(sa - sb) >= 2:
                        # 大胜/碾压（但不知道谁赢）
                        suggestions['emotions'] = ['震惊', '赞赏', '得意']
                        suggestions['scenes'] = ['碾压', '大胜']
                        suggestions['suggested_genkus'] = ['天下无敌', '笑死']
                    else:
                        # 胶着/险胜
                        suggestions['emotions'] = ['紧张', '不服输', '兴奋']
                        suggestions['scenes'] = ['胶着', '对决']
                        suggestions['suggested_genkus'] = ['不可能绝对不可能']

        # 特殊处理：游戏话题
        elif topic == TopicCategory.GAME:
            if '歪' in text or '抽卡' in text or '保底' in text:
                # 抽卡歪了 -- 恍然大悟、无奈接受
                # 完整场景：先愤怒质疑，后"这就不奇怪了"
                suggestions['emotions'] = ['愤怒', '质疑', '恍然大悟', '无奈']
                suggestions['scenes'] = ['抽卡', '歪了', '保底', '反转']
                suggestions['persons'] = ['曹操']
                # 支持愤怒模板或反转模板
                suggestions['context_templates'] = {
                    '愤怒': '{对象}一介匹夫，他哪里来的如此胆识！',
                    '反转': '这就不奇怪了，这就不奇怪了'
                }
                suggestions['template_vars'] = {'对象': '原神'}  # 默认对象
                suggestions['suggested_genkus'] = ['曹操盖饭', '撤回盖饭']
                suggestions['suggested_genkus'] = ['曹操盖饭', '撤回盖饭', '这就不奇怪了']

        # 特殊处理：科技话题
        elif topic == TopicCategory.TECH:
            if '发布' in text or '更新' in text or '厉害' in text or '强' in text:
                suggestions['emotions'] = ['震惊', '赞赏', '还有高手']
                suggestions['scenes'] = ['发布', '更新', '突破']
                suggestions['persons'] = ['曹操']
                # 双对象模板：[对象1]被[对象2]超越
                suggestions['context_template'] = '我原本以为{对象1}已经天下无敌了，没想到{对象2}比他还勇猛，这是谁的部将？'
                suggestions['template_vars'] = {'对象1': 'Gemini', '对象2': 'GPT5'}

        # 特殊处理：娱乐话题（版权纠纷等）
        elif topic == TopicCategory.ENTERTAINMENT:
            if '版权' in text or '侵权' in text or '授权' in text or '纠纷' in text:
                # 版权纠纷场景 - 使用"我听后大惊，却不敢相信"
                suggestions['emotions'] = ['震惊', '难以置信']
                suggestions['scenes'] = ['版权', '侵权', '纠纷']
                suggestions['persons'] = ['程普']
                suggestions['context_template'] = '我听后大惊，却不敢相信'

        # 特殊处理：时政话题（国际冲突/战争）
        elif topic == TopicCategory.POLITICS:
            if 'taco' in text.lower() or '反复' in text or '退缩' in text or 'chicken' in text.lower():
                # TACO行为 - 虚张声势后退缩，像袁术称帝一样可笑
                suggestions['emotions'] = ['嘲讽', '好笑', '轻蔑']
                suggestions['scenes'] = ['威胁', '退缩', '反复']
                suggestions['persons'] = ['曹操']
                suggestions['context_template'] = '差点没把我笑死'
            elif '访华' in text or '访问中国' in text:
                # 访华推迟 - 表面理由 vs 深层原因，让人难以置信
                suggestions['emotions'] = ['震惊', '难以置信', '讽刺']
                suggestions['scenes'] = ['外交', '推迟', '借口']
                suggestions['persons'] = ['程普']
                suggestions['context_template'] = '我听后大惊，却不敢相信'
            elif '特朗普' in text or '伊朗' in text or '军事行动' in text or '空袭' in text or '战争' in text:
                # 国际冲突场景 - 美方宣称成功但伊朗否认，双方说法矛盾
                suggestions['emotions'] = ['震惊', '难以置信', '讽刺']
                suggestions['scenes'] = ['战争', '冲突', '国际']
                suggestions['persons'] = ['程普']
                suggestions['context_template'] = '我听后大惊，却不敢相信'
        
        # 特殊处理：日常闲聊
        elif topic == TopicCategory.DAILY:
            # 检测"是啊，[动词]什么"模式（吃什么/看什么/听什么/玩什么等）
            import re
            verb_pattern = re.search(r'(吃|看|听|玩|喝|学|干|说|做|听|追).*?什么', text)
            if verb_pattern:
                verb = verb_pattern.group(1)
                # "是啊，吃什么"日常使用形式，权重5+
                suggestions['emotions'] = ['无奈', '调侃', '轻松', '接龙']
                suggestions['scenes'] = ['日常', '吃饭', '闲聊', '应和']
                suggestions['persons'] = ['公孙瓒', '诸侯']  # 公孙瓒先说"吃什么"，众人应和"是啊"
                suggestions['context_template'] = f'是啊，{verb}什么'
                suggestions['suggested_genkus'] = ['你走了我们吃什么']
                suggestions['usage_note'] = '日常使用形式：是啊，[动词]什么。动词可替换：吃、看、听、玩等'
            elif '吃' in text or '晚饭' in text or '午饭' in text or '早餐' in text:
                # 兜底：纯"吃"相关但没有"吃什么"模式
                suggestions['emotions'] = ['无奈', '调侃', '轻松']
                suggestions['scenes'] = ['日常', '吃饭', '闲聊']
                suggestions['persons'] = ['曹操', '公孙瓒']
                suggestions['context_template'] = '是啊，吃什么'
                suggestions['suggested_genkus'] = ['你走了我们吃什么']
            elif '天气' in text or '下雨' in text or '晴天' in text or '冷' in text or '热' in text:
                # 天气话题
                suggestions['emotions'] = ['随意', '轻松', '调侃']
                suggestions['scenes'] = ['日常', '天气', '闲聊']
                suggestions['persons'] = ['诸葛亮']  # 诸葛亮借东风
                suggestions['context_template'] = '好火啊，比夷陵之火还好啊'
            elif '累' in text or '困' in text or '无聊' in text:
                # 状态吐槽
                suggestions['emotions'] = ['无奈', '自嘲', '疲惫']
                suggestions['scenes'] = ['日常', '状态', '吐槽']
                suggestions['persons'] = ['刘备']  # 刘备卖草鞋的疲惫感
                suggestions['context_template'] = '我不过是笼中之鸟，网中之鱼'
            elif '你好' in text or '嗨' in text or '哈喽' in text or '在吗' in text:
                # 打招呼
                suggestions['emotions'] = ['轻松', '随意']
                suggestions['scenes'] = ['日常', '招呼']
                suggestions['persons'] = ['关羽']  # 关羽的高冷
                suggestions['context_template'] = '来者何人'
            elif '谢谢' in text:
                suggestions['emotions'] = ['客气', '轻松']
                suggestions['scenes'] = ['日常', '感谢']
                suggestions['persons'] = ['刘备']
                suggestions['context_template'] = '先生大恩，备没齿难忘'
            elif '再见' in text or '拜拜' in text:
                suggestions['emotions'] = ['随意', '轻松']
                suggestions['scenes'] = ['日常', '告别']
                suggestions['persons'] = ['陈宫']
                suggestions['context_template'] = '公台，公台啊...'

        return suggestions


# 单例实例
_topic_mapper: Optional[TopicMapper] = None


def get_topic_mapper() -> TopicMapper:
    """获取话题映射器实例"""
    global _topic_mapper
    if _topic_mapper is None:
        _topic_mapper = TopicMapper()
    return _topic_mapper
