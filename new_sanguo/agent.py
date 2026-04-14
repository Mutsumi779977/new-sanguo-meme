"""
新三国梗系统 v2.7.0
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
新三国梗系统 Agent v2.5
- 模块化架构
- 可配置权重公式
- 温度参数采样
- 可配置融合策略
- 向量功能可选
"""
import random
import re
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path

from .models import State, Genku, UserPreference
from .config import Config
from .database import Database
from .service import GenkuService
from .search_adapter import get_search_adapter, SearchResult
from .topic_mapper import get_topic_mapper, TopicCategory
from .utils import setup_logger, clean_quote, add_watermark


class NewSanguoAgent:
    """
    新三国梗系统主 Agent

    负责命令路由、状态管理、用户交互。
    将业务逻辑委托给 Service 层。
    """

    def __init__(self, user_id: str = "default") -> None:
        """
        初始化 Agent

        Args:
            user_id: 用户唯一标识
        """
        self.user_id = user_id
        self.config = Config()
        self.logger = setup_logger(self.config)
        self.db = Database(self.config, self.logger)
        self.service = GenkuService(self.db, self.config, self.logger)

        self.state = State.IDLE
        self.state_data: Dict[str, Any] = {}
        
        # 增强上下文记忆
        max_history = self.config.get('dialogue.context_memory.max_history', 10)
        self.context = {
            'last_genku': None,
            'mentioned_persons': [],
            'last_input': '',
            'conversation_history': [],  # 对话历史 [(input, output, genku_id), ...]
            'recent_genku_ids': [],  # 最近使用的梗ID（去重）
            'chain_state': {  # 接龙状态
                'active': False,
                'sequence': [],  # 当前接龙序列
                'count': 0,      # 当前接龙长度
                'cooldown': 0,   # 冷却轮数
            }
        }
        self.user_pref = self.db.get_user_preference(user_id) or UserPreference.default(user_id)

        self.logger.info(f"Agent 初始化完成: {user_id}")

    def handle(self, text: str) -> Union[str, Dict]:
        """
        处理用户输入

        Args:
            text: 用户输入文本

        Returns:
            回复文本，或包含type='need_search'的字典表示需要搜索
        """
        try:
            # 长度检查
            max_len = self.config.get('matching.max_input_length', 2000)
            if len(text) > max_len:
                return f"⚠️ 输入太长（限制{max_len}字）"

            self.context['last_input'] = text

            # 命令路由（优先处理，即使在特定状态中）
            # 例外：CONFIRM 和 FEEDBACK_REASON 状态需要处理特定关键词
            if text.startswith('/'):
                if self.state in [State.CONFIRM, State.FEEDBACK_REASON]:
                    # 这些状态下只处理 /取消 命令
                    if text == '/取消':
                        return self._route_command(text)
                else:
                    return self._route_command(text)

            # 状态机处理
            if self.state == State.INPUT_WAITING:
                return self._handle_input_mode(text)
            elif self.state == State.VIDEO_PROCESSING:
                return self._handle_video_mode(text)
            elif self.state == State.CONFIRM:
                return self._handle_confirm_mode(text)
            elif self.state == State.FEEDBACK_REASON:
                return self._handle_feedback_reason(text)

            # 普通聊天
            return self._handle_chat(text)

        except Exception as e:
            self.logger.exception("处理消息时出错")
            return f"⚠️ 系统错误: {str(e)[:50]}"

    def _route_command(self, text: str) -> str:
        """命令路由"""
        parts = text.split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        routes = {
            '/录入': self._cmd_input,
            '/查询': self._cmd_query,
            '/玩梗': self._cmd_play,
            '/统计': self._cmd_stats,
            '/帮助': self._cmd_help,
            '/取消': self._cmd_cancel,
            '/新三国': self._cmd_info,
            '/sanguo': self._cmd_info,
            '/喜欢': self._cmd_feedback_like,
            '/不喜欢': self._cmd_feedback_dislike,
            '/反馈': self._cmd_feedback_history,
            '/偏好': self._cmd_show_preference,
            '/重置': self._cmd_reset_session,
            '/融合': self._cmd_fusion_test,
            '/称呼': self._cmd_generate_title,
        }

        handler = routes.get(cmd)
        if handler:
            return handler(args)
        return f"❓ 未知命令: {cmd}"

    def _handle_input_mode(self, text: str) -> str:
        """处理标准录入模式"""
        if text == '/取消':
            self._reset_state()
            return "✅ 已取消"

        try:
            parsed = self._parse_input(text)
            self.state_data['pending_genku'] = parsed
            self.state = State.CONFIRM

            return f"""📋 解析预览：
梗ID: {parsed.get('梗ID', '自动生成')}
原文: {parsed.get('原文', '')}
人物: {parsed.get('人物', '未知')}
权重: {parsed.get('权重', 3)}/5
meta: {'是' if parsed.get('is_meta') else '否'}

发送「确认」保存，或「修改」重新输入"""
        except Exception as e:
            return f"❌ 解析失败: {str(e)}"

    def _handle_video_mode(self, text: str) -> str:
        """处理视频转文字录入模式"""
        if text == '/取消':
            self._reset_state()
            return "✅ 已取消"

        try:
            parsed_list = self._parse_video_text(text)
            if not parsed_list:
                return "📭 未识别到可提取的梗，请检查内容或重新输入。\n\n发送 /取消 退出"

            self.state_data['pending_genku_list'] = parsed_list
            self.state = State.CONFIRM

            reply = f"📋 解析完成，识别到 {len(parsed_list)} 条潜在梗：\n"
            for i, parsed in enumerate(parsed_list[:3], 1):
                reply += f"\n{i}. [{parsed.get('人物', '未知')}] {parsed.get('原文', '')[:30]}..."
            if len(parsed_list) > 3:
                reply += f"\n... 还有 {len(parsed_list)-3} 条"

            self.state_data['pending_genku'] = parsed_list[0]
            reply += "\n\n发送「确认」保存第一条，或发送编号选择，或「修改」重新输入"
            return reply

        except Exception as e:
            return f"❌ 解析失败: {str(e)}"

    def _handle_confirm_mode(self, text: str) -> str:
        """处理确认模式"""
        if text == '确认':
            parsed = self.state_data.get('pending_genku')
            if not parsed:
                self._reset_state()
                return "❌ 数据丢失"

            genku = Genku.from_yaml(parsed)
            if self.db.save_genku(genku):
                self.service.reload_data()
                self._reset_state()
                return f"✅ 已保存: {genku.original[:30]}...\n共 {len(self.service.genku_list)} 条"
            return "❌ 保存失败"

        elif text == '修改':
            self.state = State.INPUT_WAITING
            return "📝 请重新输入"

        elif text == '/取消':
            self._reset_state()
            return "✅ 已取消"

        # 处理编号选择
        if text.isdigit():
            idx = int(text) - 1
            pending_list = self.state_data.get('pending_genku_list', [])
            if 0 <= idx < len(pending_list):
                self.state_data['pending_genku'] = pending_list[idx]
                return f"已选择第 {text} 条，发送「确认」保存"
            return "编号无效"

        return "❓ 发送「确认」「修改」或 /取消"

    def _handle_feedback_reason(self, text: str) -> str:
        """处理反馈原因输入"""
        feedback_data = self.state_data.get('feedback_data', {})
        feedback_type = feedback_data.get('type')
        genku_id = feedback_data.get('genku_id')

        reason = None if text == '/跳过' else text

        if self.db.add_feedback(self.user_id, genku_id, feedback_type, reason, self.context.get('last_input')):
            genku = self.service.get_normal_genkus()
            genku = next((g for g in genku if g.genku_id == genku_id), None)
            if genku:
                self.service.update_user_preference(self.user_pref, genku, feedback_type)
                self.db.save_user_preference(self.user_pref)

            stats = self.db.get_genku_feedback_stats(genku_id)
            emoji = '👍' if feedback_type == 'like' else '👎'
            self._reset_state()
            return f"{emoji} 已记录（👍{stats['like']} 👎{stats['dislike']}）"

        self._reset_state()
        return "❌ 反馈失败"

    def _reset_state(self) -> None:
        """重置状态"""
        self.state = State.IDLE
        self.state_data = {}

    # ========== 上下文记忆与接龙功能 ==========
    
    def _update_conversation_history(self, user_input: str, output: str, genku_id: Optional[str] = None) -> None:
        """更新对话历史"""
        max_history = self.config.get('dialogue.context_memory.max_history', 10)
        
        self.context['conversation_history'].append({
            'input': user_input,
            'output': output,
            'genku_id': genku_id,
            'timestamp': __import__('time').time()
        })
        
        # 保持历史在限制范围内
        if len(self.context['conversation_history']) > max_history:
            self.context['conversation_history'] = self.context['conversation_history'][-max_history:]
        
        # 记录最近使用的梗ID（用于去重）
        if genku_id:
            avoid_window = self.config.get('dialogue.context_memory.avoid_repeat_window', 5)
            self.context['recent_genku_ids'].append(genku_id)
            if len(self.context['recent_genku_ids']) > avoid_window:
                self.context['recent_genku_ids'] = self.context['recent_genku_ids'][-avoid_window:]
    
    def _is_recently_used(self, genku_id: str) -> bool:
        """检查梗是否最近使用过"""
        return genku_id in self.context['recent_genku_ids']
    
    def _check_genku_chain(self, text: str) -> Optional[Dict]:
        """
        检查是否可以触发多轮梗接龙
        
        Returns:
            接龙配置或None
        """
        chain_config = self.config.get('dialogue.genku_chain', {})
        if not chain_config.get('enabled', True):
            return None
        
        chain_state = self.context['chain_state']
        
        # 检查冷却期
        if chain_state['cooldown'] > 0:
            chain_state['cooldown'] -= 1
            return None
        
        # 检查最大长度
        max_length = chain_config.get('max_chain_length', 3)
        if chain_state['count'] >= max_length:
            self._reset_chain()
            return None
        
        # 检查渐进式接龙（如"不可能"->"绝对不可能"）
        progressive = chain_config.get('patterns', {}).get('progressive', {})
        if progressive.get('enabled', True):
            keywords = progressive.get('keywords', [])
            # 如果用户输入包含递进关键词，可能触发接龙
            if any(kw in text for kw in keywords):
                last_genku_id = self.context.get('last_genku')
                if last_genku_id:
                    return {'type': 'progressive', 'last_genku_id': last_genku_id}
        
        return None
    
    def _try_chain_response(self, text: str) -> Optional[str]:
        """
        尝试生成接龙回复
        
        Returns:
            接龙回复或None
        """
        chain_config = self.config.get('dialogue.genku_chain', {})
        trigger_prob = chain_config.get('trigger_probability', 0.6)
        
        # 概率触发
        if __import__('random').random() > trigger_prob:
            return None
        
        chain_info = self._check_genku_chain(text)
        if not chain_info:
            return None
        
        # 递进式接龙
        if chain_info['type'] == 'progressive':
            return self._generate_progressive_chain(chain_info['last_genku_id'], text)
        
        return None
    
    def _generate_progressive_chain(self, last_genku_id: str, text: str) -> Optional[str]:
        """生成递进式接龙回复"""
        # 获取上一个梗
        last_genku = None
        for g in self.service.get_normal_genkus():
            if g.genku_id == last_genku_id:
                last_genku = g
                break
        
        if not last_genku:
            return None
        
        # 根据上一个梗选择递进梗
        progressive_pairs = {
            '不可能': ['不可能，绝对不可能！'],
            '叉出去': ['叉出去！', '匹夫！'],
            '曹操盖饭': ['这就不奇怪了'],
            '列位诸公': ['告老还乡'],
        }
        
        # 查找匹配的递进梗
        for key, follow_ups in progressive_pairs.items():
            if key in last_genku.original:
                # 随机选择一个递进回复
                follow_up = random.choice(follow_ups)
                
                # 更新接龙状态
                self.context['chain_state']['count'] += 1
                self.context['chain_state']['sequence'].append(follow_up)
                
                return follow_up
        
        return None
    
    def _reset_chain(self) -> None:
        """重置接龙状态"""
        cooldown = self.config.get('dialogue.genku_chain.cooldown_turns', 3)
        self.context['chain_state'] = {
            'active': False,
            'sequence': [],
            'count': 0,
            'cooldown': cooldown,
        }

    def _cmd_input(self, args: str) -> str:
        """录入命令"""
        if args.strip().lower() in ['视频', 'video']:
            self.state = State.VIDEO_PROCESSING
            return "🎬 视频转文字录入模式\n请发送视频转文字后的原始内容\n\n发送 /取消 退出"
        self.state = State.INPUT_WAITING
        return "📝 录入模式\n格式：\n梗：原文\n人物：xxx\n权重：1-5\n\n发送 /取消 退出"

    def _cmd_query(self, args: str) -> str:
        """查询命令"""
        if not args:
            return "❓ /查询 <关键词>"

        results = []
        for genku in self.service.get_normal_genkus():
            if args in genku.person or args in genku.original or args in genku.tags:
                results.append(genku)

        if not results:
            return f"📭 未找到「{args}」"

        reply = f"📚 找到 {len(results)} 条:\n"
        for i, g in enumerate(results[:5], 1):
            meta_mark = "[M]" if g.is_meta else ""
            reply += f"\n{i}. {meta_mark}[{g.person}] {g.original[:25]}..."
        return reply

    def _cmd_play(self, args: str) -> str:
        """手动玩梗"""
        if not args:
            return "❓ /玩梗 <内容>"

        genku, fused = self.service.match_genku(args, self.user_pref, allow_fusion=True)
        if not genku:
            return "📭 没找到合适的梗"

        output = fused if fused else self.service.generate_variant(genku, args)
        return output

    def _cmd_stats(self, args: str) -> str:
        """统计命令"""
        total = len(self.service.genku_list)
        meta_count = len(self.service.get_meta_genkus())
        normal_count = len(self.service.get_normal_genkus())

        by_person = {}
        for g in self.service.get_normal_genkus():
            by_person[g.person] = by_person.get(g.person, 0) + 1

        reply = f"📊 统计\n{'='*30}\n总计: {total} 条\n"
        reply += f"  - 普通梗: {normal_count}\n"
        reply += f"  - meta梗: {meta_count}\n\n"
        reply += "按人物:\n"
        for person, count in sorted(by_person.items(), key=lambda x: -x[1])[:8]:
            reply += f"  {person}: {count}条\n"

        if self.user_pref.total_interactions > 0:
            reply += f"\n📈 你的交互: {self.user_pref.total_interactions}次"

        return reply

    def _cmd_help(self, args: str) -> str:
        """帮助命令"""
        return """🎭 新三国梗系统 v2.5

【基础】/录入 [视频] | /查询 | /玩梗 | /统计 | /称呼
【反馈】/喜欢 | /不喜欢 | /反馈 | /偏好
【测试】/融合 [内容] - 测试meta梗融合
【其他】/重置 | /取消 | /帮助

📋 三不原则：
• 不出现人物标注
• 不创设互动场景
• 不死板硬套原文"""

    def _cmd_cancel(self, args: str) -> str:
        """取消命令"""
        self._reset_state()
        return "✅ 已取消"

    def _cmd_info(self, args: str) -> str:
        """信息命令"""
        vector_status = '✅' if self.service.model else '❌（默认关闭）'
        return f"""🎭 v2.7
状态: {self.state.name}
梗库: {len(self.service.genku_list)} 条（meta: {len(self.service.get_meta_genkus())}）
融合: {'✅' if self.config.get('fusion.enabled') else '❌'}
向量: {vector_status}
温度: {self.config.get('matching.temperature', 1.0)}"""

    def _cmd_feedback_like(self, args: str) -> str:
        return self._handle_feedback('like', args)

    def _cmd_feedback_dislike(self, args: str) -> str:
        return self._handle_feedback('dislike', args)

    def _handle_feedback(self, feedback_type: str, reason: str) -> str:
        """处理反馈"""
        last_genku_id = self.context.get('last_genku')
        if not last_genku_id:
            return "❓ 还没有使用任何梗"

        if reason:
            return self._submit_feedback(feedback_type, last_genku_id, reason)
        else:
            self.state = State.FEEDBACK_REASON
            self.state_data['feedback_data'] = {'type': feedback_type, 'genku_id': last_genku_id}
            return "💬 请说明原因（或 /跳过）："

    def _submit_feedback(self, feedback_type: str, genku_id: str, reason: str) -> str:
        """提交反馈"""
        if self.db.add_feedback(self.user_id, genku_id, feedback_type, reason, self.context.get('last_input')):
            genku = next((g for g in self.service.get_normal_genkus() if g.genku_id == genku_id), None)
            if genku:
                self.service.update_user_preference(self.user_pref, genku, feedback_type)
                self.db.save_user_preference(self.user_pref)

            stats = self.db.get_genku_feedback_stats(genku_id)
            emoji = '👍' if feedback_type == 'like' else '👎'
            return f"{emoji} 已记录（👍{stats['like']} 👎{stats['dislike']}）"
        return "❌ 反馈失败"

    def _cmd_feedback_history(self, args: str) -> str:
        """反馈历史"""
        history = self.db.get_user_feedback_history(self.user_id, limit=5)
        if not history:
            return "📭 无反馈记录"

        lines = ["📊 反馈历史："]
        for h in history:
            emoji = '👍' if h['feedback_type'] == 'like' else '👎'
            text = h['genku_text'][:15] + '...' if len(h['genku_text']) > 15 else h['genku_text']
            lines.append(f"{emoji} {h['genku_id']} - {text}")
        return '\n'.join(lines)

    def _cmd_show_preference(self, args: str) -> str:
        """显示偏好"""
        pref = self.user_pref
        reply = f"📊 偏好画像\n{'='*30}\n"
        reply += f"交互: {pref.total_interactions}次\n"

        if pref.liked_persons:
            reply += "\n偏好人物:\n"
            for person, score in sorted(pref.liked_persons.items(), key=lambda x: -x[1])[:5]:
                reply += f"  {person}: {score:.2f}\n"

        if pref.liked_tags:
            reply += "\n偏好标签:\n"
            for tag, score in sorted(pref.liked_tags.items(), key=lambda x: -x[1])[:5]:
                reply += f"  {tag}: {score:.2f}\n"

        return reply or "📭 暂无数据"

    def _cmd_reset_session(self, args: str) -> str:
        """重置会话"""
        self._reset_state()
        return "✅ 已重置"

    def _cmd_fusion_test(self, args: str) -> str:
        """测试融合"""
        if not args:
            args = "如何评价折棒"

        genku, fused = self.service.match_genku(args, self.user_pref, allow_fusion=True)

        if not genku:
            return "📭 无匹配"

        result = f"""🧪 融合测试
输入: {args}
主梗: [{genku.genku_id}] {genku.original}
融合: {'✅ ' + fused if fused else '❌ 未触发'}

meta梗库: {len(self.service.get_meta_genkus())} 条"""

        return result

    def _cmd_generate_title(self, args: str) -> str:
        """生成称呼"""
        if not args:
            return "❓ /称呼 <名称>\n\n示例：\n/称呼 折棒 → 折棒爷\n/称呼 R9 → R9爷"

        name = args.strip()
        if name.endswith('爷'):
            return f"🎭 称呼：{name}（已是标准格式）"

        titles = [f"{name}爷"]
        if len(name) >= 2:
            titles.append(f"{name[:2]}爷")

        reply = f"🎭 为「{name}」生成的称呼：\n"
        for i, title in enumerate(titles, 1):
            reply += f"\n{i}. {title}"

        reply += "\n\n来源：张飞「主子爷，先帝爷」"
        return reply

    def _handle_chat(self, text: str) -> Union[str, Dict]:
        """
        处理普通聊天（优化版：先匹配，后话题检测）

        调整后的流程：
        1. 显式搜索检查
        2. 梗接龙
        3. **直接梗匹配**（不依赖话题，优先尝试）
        4. 话题识别 + 信息充足度检测
        5. 搜索增强
        6. 默认回复

        Returns:
            回复文本，或 dict{'type': 'need_search', 'query': str, 'reason': str}
        """
        # 0. 检查用户是否明确要求搜索（显式搜索优先）
        topic_mapper = get_topic_mapper()
        is_explicit_search, cleaned_text = topic_mapper.check_explicit_search_request(text)

        if is_explicit_search:
            return {
                'type': 'need_search',
                'query': cleaned_text,
                'reason': '用户明确要求联网搜索',
                'topic': 'explicit',
                'confidence': 1.0
            }

        # 1. 尝试多轮梗接龙（最高优先级）
        chain_response = self._try_chain_response(text)
        if chain_response:
            return chain_response

        # 2. **优先尝试直接梗匹配**（不依赖话题识别）
        # 这是关键调整：不管话题是什么，先尝试匹配梗
        genku, fused = self.service.match_genku(text, self.user_pref, allow_fusion=True)
        if genku:
            return self._output_genku(genku, fused, text)

        # 2.5. 关键词匹配失败，尝试**意图匹配**（新增 v2.0）
        # 识别用户意图（情感+行为），匹配梗的"功能用途"
        intent_match = self._try_intent_match(text)
        if intent_match:
            return intent_match

        # 3. 直接匹配失败，再识别话题
        topic, confidence = topic_mapper.identify_topic(text)

        # 4. 信息充足度检测（现在只在匹配失败后执行）
        is_sufficient, reason = topic_mapper.check_information_sufficiency(text, topic)

        if not is_sufficient:
            # 本地无匹配 + 信息不充足，需要搜索
            return {
                'type': 'need_search',
                'query': text,
                'reason': f'本地梗库无匹配，{reason}',
                'topic': topic.value,
                'confidence': confidence
            }

        # 5. 信息充足，尝试话题增强匹配
        confidence_threshold = self.config.get('scoring.thresholds.topic_confidence', 0.3)
        if confidence > confidence_threshold and topic != TopicCategory.UNKNOWN:
            suggestions = topic_mapper.suggest_genku_tags(text)
            genku, fused = self._match_with_topic(text, suggestions)
            if genku:
                return self._output_genku(genku, fused, text)

        # 6. 尝试搜索增强
        if self.config.get('search.enabled', False):
            search_result = self._search_and_retry(text)
            if search_result:
                return search_result

        # 7. 有话题但无匹配，使用话题默认回复
        high_confidence_threshold = self.config.get('scoring.thresholds.topic_confidence_high', 0.5)
        if confidence > high_confidence_threshold:
            return self._generate_topic_response(topic, text)

        # 8. 完全无法匹配，建议搜索
        return {
            'type': 'need_search',
            'query': text,
            'reason': '本地梗库无匹配，需要联网搜索相关信息',
            'topic': topic.value,
            'confidence': confidence
        }

    def _match_with_topic(self, text: str, suggestions: Dict) -> Tuple[Optional[Genku], Optional[str]]:
        """使用话题标签增强匹配"""
        # 优先使用推荐的特定梗（不融合，直接输出）
        suggested_genkus = suggestions.get('suggested_genkus', [])
        if suggested_genkus:
            for keyword in suggested_genkus:
                for genku in self.service.get_normal_genkus():
                    if keyword in genku.original or keyword in genku.tags:
                        # 找到推荐的梗，直接使用
                        output = genku.original

                        # 如果有场景模板，使用模板包装
                        context_templates = suggestions.get('context_templates')
                        context_template = suggestions.get('context_template')
                        if context_templates:
                            # 多模板选择（如愤怒/反转）
                            template_vars = suggestions.get('template_vars', {})
                            selected_key = random.choice(list(context_templates.keys()))
                            selected_template = context_templates[selected_key]
                            try:
                                output = selected_template.format(**template_vars)
                            except (KeyError, IndexError):
                                output = selected_template
                        elif context_template:
                            # 单模板
                            template_vars = suggestions.get('template_vars', {})
                            try:
                                if '{' in context_template and template_vars:
                                    output = context_template.format(**template_vars)
                                else:
                                    output = context_template
                            except (KeyError, IndexError):
                                pass

                        # 检查高频梗惩罚（事不过三）
                        if not self._check_high_freq_penalty(genku):
                            return None, None
                        
                        # 推荐梗直接输出，不融合（避免滥用meta梗）
                        return genku, output

        # 有模板但没有匹配到具体梗，直接使用模板
        context_template = suggestions.get('context_template')
        if context_template and '{对象}' not in context_template:
            template_vars = suggestions.get('template_vars', {})
            try:
                output = context_template.format(**template_vars)
            except (KeyError, IndexError):
                output = context_template

            # 检查高频梗惩罚（如"列位诸公"）
            temp_genku = self.service.db.get_genku_by_id('xsg_meta_001')  # 列位诸公
            if temp_genku and not self._check_high_freq_penalty(temp_genku):
                return None, None  # 惩罚严重，让系统选其他梗

            # 创建一个临时Genku对象返回
            from .models import Genku
            temp_genku = Genku(
                genku_id="template",
                original=output,
                person=suggestions.get('persons', [''])[0] if suggestions.get('persons') else '',
                source="话题模板",
                context="模板生成",
                emotions=suggestions.get('emotions', []),
                intensity="中",
                tags=suggestions.get('scenes', []),
                semantic_keywords=[],
                weight=4
            )
            return temp_genku, output
        elif context_template and '{对象}' in context_template:
            # 有{对象}变量的模板，尝试替换
            template_vars = suggestions.get('template_vars', {})
            output = context_template.format(**template_vars) if template_vars else context_template

            # 检查高频梗惩罚（如"是啊，吃什么"）
            if '是啊，' in output and '什么' in output:
                temp_genku = self.service.db.get_genku_by_id('xsg_cc_017')  # 你走了我们吃什么
                if temp_genku and not self._check_high_freq_penalty(temp_genku):
                    return None, None  # 惩罚严重，让系统选其他梗

            from .models import Genku
            temp_genku = Genku(
                genku_id="template",
                original=output,
                person=suggestions.get('persons', [''])[0] if suggestions.get('persons') else '',
                source="话题模板",
                context="模板生成",
                emotions=suggestions.get('emotions', []),
                intensity="中",
                tags=suggestions.get('scenes', []),
                semantic_keywords=[],
                weight=4
            )
            return temp_genku, output

        # 没有推荐梗，构建增强查询进行匹配
        enhanced_query = text

        # 添加场景标签到查询
        for scene in suggestions.get('scenes', [])[:2]:
            enhanced_query += f" {scene}"

        # 添加情绪标签到查询
        for emotion in suggestions.get('emotions', [])[:2]:
            enhanced_query += f" {emotion}"

        # 使用增强查询匹配（允许融合，但融合概率已降低）
        genku, fused = self.service.match_genku(enhanced_query, self.user_pref, allow_fusion=True)

        # 如果没匹配到，尝试用推荐的人物过滤
        if not genku and suggestions.get('persons'):
            for person in suggestions['persons']:
                person_genkus = [g for g in self.service.get_normal_genkus() if g.person == person]
                if person_genkus:
                    # 随机选一个该人物的梗
                    genku = random.choice(person_genkus)
                    break

        return genku, fused

    def _generate_topic_response(self, topic: TopicCategory, text: str) -> str:
        """根据话题生成默认回复"""
        # 电竞赛事话题
        if topic == TopicCategory.ESPORTS:
            topic_mapper = get_topic_mapper()
            match_info = topic_mapper.parse_esports_match(text)

            if match_info and match_info.get('score_a') is not None:
                sa, sb = match_info['score_a'], match_info['score_b']

                # 找对应情境的梗
                if sa == 0 and sb > 0:
                    # 被零封/惨败
                    genku = self._find_genku_by_emotion('震惊', '否认')
                    if genku:
                        return self._output_genku(genku, None, text)
                elif sa < sb:
                    # 输了但没那么惨
                    genku = self._find_genku_by_emotion('不服输')
                    if genku:
                        return self._output_genku(genku, None, text)

        return "📡 识别到话题但暂无匹配梗，教教我？发送 /录入"

    def _find_genku_by_emotion(self, *emotions: str) -> Optional[Genku]:
        """根据情绪标签查找梗"""
        candidates = []

        for genku in self.service.get_normal_genkus():
            for emotion in emotions:
                if emotion in genku.emotions or emotion in genku.tags:
                    candidates.append(genku)
                    break

        return random.choice(candidates) if candidates else None

    def _try_emotion_match(self, text: str) -> Optional[str]:
        """
        尝试情感匹配
        
        当关键词匹配失败时，识别用户情感，用对应情绪的梗回应。
        这是兜底策略，让Agent对情感表达有基本回应能力。
        
        Returns:
            回应文本，或None（无法匹配）
        """
        try:
            from .emotion_recognizer import EmotionRecognizer, EmotionType
            
            recognizer = EmotionRecognizer()
            emotion, confidence, keywords = recognizer.recognize(text)
            
            # 置信度太低，不处理
            if confidence < 0.3:
                return None
            
            # 获取对应的梗情绪标签
            genku_tags = recognizer.get_genku_emotion_tags(emotion)
            
            # 查找对应情绪的梗
            genku = self._find_genku_by_emotion(*genku_tags)
            
            if genku:
                self.logger.info(f"情感匹配: {emotion.value} (置信度{confidence:.2f}), 关键词{keywords}, 匹配梗{genku.genku_id}")
                
                # 特殊处理：喜悦/治愈类 → 用袁术祝贺模板
                if emotion == EmotionType.JOY:
                    return "恭喜贴主可以痊愈了"
                
                # 特殊处理：认同类 → 用"痛切"模板
                if emotion == EmotionType.AGREEMENT:
                    return "贴主说得痛切，当浮一大白"
                
                # 其他情感直接输出原文
                return genku.original
            
            return None
            
        except Exception as e:
            self.logger.debug(f"情感匹配失败: {e}")
            return None

    def _try_intent_match(self, text: str) -> Optional[str]:
        """
        意图匹配 v2.0（基于情感+行为+梗功能）
        
        当关键词匹配失败时，识别用户意图，匹配梗的"功能用途"。
        不再只看情感，而是看"情感+行为"的组合意图。
        
        Returns:
            回应文本，或None（无法匹配）
        """
        try:
            from .intent_recognizer import IntentRecognizer, UserAction, UserEmotion
            from .genku_functions import get_genku_functions
            
            recognizer = IntentRecognizer()
            intent = recognizer.recognize(text)
            
            # 置信度太低，不处理
            if intent.confidence < 0.3:
                return None
            
            # 映射到梗功能
            target_functions = recognizer.map_to_genku_function(intent)
            
            self.logger.info(f"意图识别: 情感={intent.emotion.value}, 行为={intent.action.value}, "
                           f"置信度={intent.confidence:.2f}, 推荐功能={[f.value for f in target_functions]}")
            
            # 根据意图直接生成回应（不需要搜索）
            # 分享好消息 -> 祝贺
            if intent.action == UserAction.SHARE_GOOD_NEWS:
                return "恭喜贴主可以撑地了"
            
            # 表达感谢 -> 认同
            if intent.action == UserAction.EXPRESS_THANKS:
                return "贴主说得痛切，当浮一大白"
            
            # 寻求认同 -> 附和
            if intent.action == UserAction.SEEK_AGREEMENT:
                return "俺也一样"
            
            # 表示赞赏 -> 赞扬
            if intent.action == UserAction.SHOW_APPRECIATION:
                # 找赞扬封神的梗
                genku = self._find_genku_by_function("赞扬封神")
                if genku:
                    return genku.original
                return "贴主真是神人也"
            
            # 寻求安慰 -> 安慰
            if intent.action == UserAction.SEEK_COMFORT:
                genku = self._find_genku_by_function("安慰")
                if genku:
                    return genku.original
                return "知我者谓我心忧，不知我者谓我何求"
            
            # 发泄不满 -> 吐槽
            if intent.action == UserAction.VENT_FRUSTRATION:
                genku = self._find_genku_by_function("吐槽嘲讽")
                if genku:
                    return genku.original
                return "放肆！叉出去！"
            
            # 提问但困惑 -> 用质疑类梗
            if intent.action == UserAction.ASK_QUESTION and intent.emotion == UserEmotion.CONFUSION:
                genku = self._find_genku_by_function("质疑")
                if genku:
                    return genku.original
            
            # 其他情况，尝试按功能找梗
            for func in target_functions:
                genku = self._find_genku_by_function(func.value)
                if genku:
                    return genku.original
            
            return None
            
        except Exception as e:
            self.logger.debug(f"意图匹配失败: {e}")
            return None
    
    def _find_genku_by_function(self, function_tag: str) -> Optional[Genku]:
        """根据功能标签查找梗"""
        from .genku_functions import get_genku_functions
        
        candidates = []
        
        for genku in self.service.get_normal_genkus():
            functions = get_genku_functions(genku.genku_id)
            if function_tag in functions:
                candidates.append(genku)
        
        return random.choice(candidates) if candidates else None

    def _check_high_freq_penalty(self, genku: Genku) -> bool:
        """
        检查高频梗惩罚，如果惩罚严重返回 False

        Returns:
            bool: True 表示可以使用，False 表示惩罚严重应换梗
        """
        freq_penalty = self.service._get_frequency_penalty(genku)
        threshold = self.service.config.get('scoring.high_freq_penalty_threshold', 0.5)
        if freq_penalty < threshold:
            self.logger.debug(f"高频梗 {genku.genku_id} 惩罚系数 {freq_penalty:.3f}，尝试其他梗")
            return False
        self.service._record_genku_usage(genku)
        return True

    def _search_and_retry(self, text: str) -> Optional[str]:
        """
        搜索不理解的信息，基于意图推理后重试匹配

        **改进：搜索后不再直接搜内容匹配，而是识别意图（情感+行为）**
        
        工作流程：
        1. 执行搜索获取关键词
        2. 识别用户意图（情感+行为）
        3. 基于意图匹配梗的功能用途
        4. 返回最合适的梗

        Returns:
            匹配到的梗文本，或 None
        """
        try:
            # 获取搜索适配器
            adapter = get_search_adapter(
                enabled=self.config.get('search.enabled', False),
                result_count=self.config.get('search.result_count', 3)
            )

            # 执行搜索
            search_result = adapter.search(text)

            if not search_result:
                # 搜索失败，使用备用关键词提取
                keywords = adapter._extract_query_keywords(text)
                search_result = SearchResult(
                    query=text,
                    summary=f"提取关键词: {', '.join(keywords[:5])}",
                    keywords=keywords,
                    raw_results=[]
                )

            # ========== 新增：搜索后意图推理 ==========
            # 不再直接用关键词匹配梗，而是识别意图
            intent_match = self._try_intent_match(text)
            if intent_match:
                self.logger.info(f"搜索后意图匹配成功: {intent_match[:30]}...")
                return f"🔍 搜索后匹配\n{intent_match}"

            # 意图匹配失败，退回到关键词匹配
            self.logger.info("意图匹配失败，退回到关键词匹配")
            
            # 用搜索关键词重试匹配
            all_keywords = search_result.keywords + [search_result.query]

            for keyword in all_keywords:
                if len(keyword) < 2:
                    continue

                genku, fused = self.service.match_genku(keyword, self.user_pref, allow_fusion=True)
                if genku:
                    # 找到匹配，包装输出
                    output = self._output_genku(genku, fused, keyword, silent=True)
                    return f"🔍 搜索后匹配\n{output}"

            return None

        except Exception as e:
            self.logger.debug(f"搜索增强失败: {e}")
            return None

    def _extract_search_keywords(self, text: str) -> List[str]:
        """从文本中提取可能的关键词用于搜索"""
        adapter = get_search_adapter()
        return adapter._extract_query_keywords(text)

    def _output_genku(self, genku: Genku, fused: Optional[str], user_text: str, silent: bool = False) -> str:
        """输出梗"""
        self.context['last_genku'] = genku.genku_id
        self.context['mentioned_persons'].append(genku.person)
        self.db.update_usage_count(genku.genku_id)

        output = fused if fused else self.service.generate_variant(genku, user_text)
        
        # 更新对话历史
        if not silent:
            self._update_conversation_history(user_text, output, genku.genku_id)

        # 清理人物标注
        cleaned = output.replace(f"【{genku.person}】", "")
        cleaned = cleaned.replace(f"[{genku.person}]", "")
        return cleaned.strip()

    def _parse_input(self, text: str) -> Dict[str, Any]:
        """解析标准录入输入"""
        result = {}

        for line in text.strip().split('\n'):
            if '：' in line:
                key, value = line.split('：', 1)
                key, value = key.strip(), value.strip()

                mapping = {
                    '梗': '原文', '梗ID': '梗ID', '人物': '人物',
                    '出处': '出处', '情境': '情境', '情绪': '情绪',
                    '场景标签': '场景标签', '语义关键词': '语义关键词',
                    '权重': '权重', '变体模板': '变体模板',
                    'is_meta': 'is_meta', 'meta': 'is_meta',
                }

                yaml_key = mapping.get(key)
                if yaml_key:
                    if key in ['情绪', '场景标签', '语义关键词']:
                        result[yaml_key] = [e.strip() for e in value.split('、')]
                    elif key == '权重':
                        result[yaml_key] = int(value)
                    elif key in ['is_meta', 'meta']:
                        result[yaml_key] = value.lower() in ['true', '是', 'yes', '1']
                    else:
                        result[yaml_key] = value

        # 自动生成 ID
        if '梗ID' not in result and '人物' in result:
            person = result['人物']
            is_meta = result.get('is_meta', False)

            if is_meta:
                prefix = 'xsg_meta_'
                count = len(self.service.get_meta_genkus())
                result['梗ID'] = f"{prefix}{count+1:03d}"
            else:
                prefix_map = {
                    '曹操': 'xsg_cc', '刘备': 'xsg_lb', '张飞': 'xsg_zf',
                    '关羽': 'xsg_gy', '诸葛亮': 'xsg_zgl',
                }
                prefix = prefix_map.get(person, f"xsg_{person[:2]}")
                count = sum(1 for g in self.service.get_normal_genkus() if g.person == person)
                result['梗ID'] = f"{prefix}_{count+1:03d}"

        if '原文' not in result:
            raise ValueError("必须提供「梗：原文内容」")

        return result

    def _parse_video_text(self, text: str) -> list:
        """解析视频转文字内容"""
        results = []
        lines = text.strip().split('\n')

        current_person = None
        current_quote = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            person_match = re.match(r'^(\S+?)[：:\s]+', line)
            if person_match:
                if current_person and current_quote:
                    quote_text = ' '.join(current_quote)
                    cleaned = clean_quote(quote_text)
                    if cleaned and len(cleaned) >= 5:
                        results.append({
                            '原文': cleaned,
                            '人物': current_person,
                            '出处': '视频转文字提取',
                            '情境': '原剧情场景',
                            '情绪': ['搞笑'],
                            '权重': 3
                        })

                current_person = person_match.group(1).replace('说', '').replace('道', '').strip()
                content = line[person_match.end():].strip()
                current_quote = [content] if content else []
            elif current_person:
                current_quote.append(line)

        if current_person and current_quote:
            quote_text = ' '.join(current_quote)
            cleaned = clean_quote(quote_text)
            if cleaned and len(cleaned) >= 5:
                results.append({
                    '原文': cleaned,
                    '人物': current_person,
                    '出处': '视频转文字提取',
                    '情境': '原剧情场景',
                    '情绪': ['搞笑'],
                    '权重': 3
                })

        return results


def create_agent(user_id: str = "default") -> NewSanguoAgent:
    """工厂函数创建 Agent"""
    return NewSanguoAgent(user_id)

def create_agent(user_id: str = "default") -> NewSanguoAgent:
    """工厂函数创建 Agent"""
    return NewSanguoAgent(user_id)
