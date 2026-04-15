"""
新三国梗系统 v2.8.0
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
新三国梗系统 - 业务逻辑层
"""
import re
import math
import random
import logging
from typing import Optional, List, Dict, Any, Tuple

# numpy 是可选依赖
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

from .models import Genku, UserPreference
from .database import Database
from .config import Config


class GenkuService:
    """
    梗业务逻辑服务

    负责梗的匹配、融合、变体生成等核心业务逻辑。
    支持向量匹配和关键词匹配两种模式。

    Attributes:
        db: 数据库实例
        config: 配置实例
        logger: 日志实例
        genku_list: 所有梗列表
        meta_genkus: meta 梗列表
        normal_genkus: 普通梗列表
        model: 向量化模型
        vectors: 预计算的向量字典
    """

    def __init__(self, db: Database, config: Config, logger: logging.Logger):
        """
        初始化服务

        Args:
            db: 数据库实例
            config: 配置实例
            logger: 日志实例
        """
        self.db = db
        self.config = config
        self.logger = logger
        self.genku_list: List[Genku] = []
        self.meta_genkus: List[Genku] = []
        self.normal_genkus: List[Genku] = []
        self.model = None
        self.vectors: Dict[str, Any] = {}
        self.model_loaded = False
        # 高频梗使用历史 {pattern_type: [(timestamp, output_text), ...]}
        self._high_freq_usage_history: Dict[str, List[Tuple[float, str]]] = {}
        self._load_data()

    def _load_data(self):
        """从数据库加载梗数据"""
        cursor = self.db._get_conn().execute("SELECT COUNT(*) FROM genku")
        if cursor.fetchone()[0] == 0:
            yaml_path = self.config.get('database.yaml_source', 'data/genku.yaml')
            try:
                imported = self.db.import_from_yaml(yaml_path)
                self.logger.info(f"从 YAML 导入 {imported} 条梗")
            except FileNotFoundError:
                self.logger.warning(f"未找到 YAML: {yaml_path}")

        self.genku_list = self.db.get_all_genku()
        self._separate_genkus()
        self.logger.info(f"加载 {len(self.genku_list)} 条梗（meta: {len(self.meta_genkus)}）")

    def _separate_genkus(self):
        """分离 meta 梗和普通梗"""
        meta_prefix = self.config.get('fusion.meta_prefix', 'xsg_meta_')
        self.meta_genkus = [g for g in self.genku_list if g.genku_id.startswith(meta_prefix)]
        self.normal_genkus = [g for g in self.genku_list if not g.genku_id.startswith(meta_prefix)]

    def reload_data(self):
        """重新加载数据（供外部调用）"""
        self._load_data()

    def _load_model(self):
        """加载向量化模型"""
        if not EMBEDDING_AVAILABLE or not self.config.get('embedding.enabled'):
            return
        try:
            model_name = self.config.get('embedding.model_name')
            self.logger.info(f"加载模型: {model_name}")
            self.model = SentenceTransformer(model_name)
            self._precompute_vectors()
            self.model_loaded = True
        except Exception as e:
            self.logger.error(f"模型加载失败: {e}")
            self.model = None

    def _precompute_vectors(self):
        """预计算所有梗的向量"""
        if not self.model or not self.genku_list:
            return
        texts = [g.original for g in self.genku_list]
        vectors = self.model.encode(texts)
        for genku, vec in zip(self.genku_list, vectors):
            self.vectors[genku.genku_id] = vec

    def _get_frequency_penalty(self, genku: Genku) -> float:
        """
        计算高频梗的频率惩罚系数

        对于短期内多次使用的高频梗（权重>=5），降低其得分权重
        实现静默降权，不提示用户，让系统自动选择其他梗

        Returns:
            惩罚系数 (0.0-1.0)，1.0表示无惩罚
        """
        import time
        current_time = time.time()

        # 从配置获取高频梗设置
        min_weight = self.config.get('scoring.high_freq_config.min_weight', 5)
        window_seconds = self.config.get('scoring.high_freq_config.window_seconds', 600)
        max_before_penalty = self.config.get('scoring.high_freq_config.max_usage_before_penalty', 3)
        penalty_per_use = self.config.get('scoring.high_freq_config.penalty_per_use', 0.1)

        # 只处理权重>=5的梗
        if genku.weight < min_weight:
            return 1.0

        # 获取并清理过期记录
        history = self._high_freq_usage_history.get(genku.genku_id, [])
        history = [(t, gid) for t, gid in history if current_time - t < window_seconds]
        self._high_freq_usage_history[genku.genku_id] = history

        if not history:
            return 1.0
        
        # 事不过三：前N次正常使用，之后严重惩罚
        if len(history) < max_before_penalty:
            return 1.0  # 前N次无惩罚
        
        # 第N+1次起：每次乘以惩罚系数（严重惩罚）
        excess_uses = len(history) - max_before_penalty + 1  # 超出次数
        penalty = penalty_per_use ** excess_uses
        
        self.logger.debug(f"高频梗 {genku.genku_id} 事不过三惩罚: {penalty:.3f} (已使用{len(history)}次)")

        return penalty

    def _record_genku_usage(self, genku: Genku):
        """记录梗使用情况（仅记录高频梗）"""
        import time

        min_weight = self.config.get('scoring.high_freq_config.min_weight', 5)
        if genku.weight < min_weight:
            return

        if genku.genku_id not in self._high_freq_usage_history:
            self._high_freq_usage_history[genku.genku_id] = []

        self._high_freq_usage_history[genku.genku_id].append((time.time(), genku.genku_id))
        self.logger.debug(f"记录高频梗使用: {genku.genku_id}, 窗口内次数: {len(self._high_freq_usage_history[genku.genku_id])}")

    def _check_high_frequency_usage(self, genku_id: str = None, output_text: str = None) -> Tuple[bool, str]:
        """
        检查高频梗是否应被限制使用 (旧方法，保留兼容性)

        Returns:
            (是否应该限制: bool, 原因: str)
        """
        return False, ""  # 新机制下不强制限制，只降权

    def _record_high_frequency_usage(self, genku_id: str = None, output_text: str = None):
        """记录高频梗使用情况 (旧方法，保留兼容性)"""
        pass  # 新机制使用 _record_genku_usage

    def match_genku(self, text: str, user_pref: Optional[UserPreference] = None,
                    allow_fusion: bool = True) -> Tuple[Optional[Genku], Optional[str]]:
        """
        匹配最合适的梗

        Args:
            text: 用户输入文本
            user_pref: 用户偏好（可选）
            allow_fusion: 是否允许融合 meta 梗

        Returns:
            (匹配到的梗, 融合后的文本)
        """
        if not self.normal_genkus:
            return None, None

        # 按需加载模型
        if self.config.get('embedding.enabled') and not self.model_loaded:
            self._load_model()

        # 匹配主梗（频率惩罚已在匹配过程中应用）
        scores = []
        if self.model and self.vectors:
            scores = self._vector_match(text, user_pref)
        else:
            scores = self._keyword_match(text, user_pref)

        if not scores:
            return None, None

        # 应用温度参数采样
        main_genku = self._sample_with_temperature(scores)

        # 尝试融合 meta 梗
        fused_text = None
        if allow_fusion and self.config.get('fusion.enabled', True) and self.meta_genkus:
            fused_text = self._try_fusion(main_genku, text)

        # 记录高频梗使用（用于后续降权）
        self._record_genku_usage(main_genku)

        return main_genku, fused_text

    def _vector_match(self, text: str, user_pref: Optional[UserPreference]) -> List[Tuple[float, Genku]]:
        """
        基于向量相似度的匹配

        使用余弦相似度计算用户输入与梗的语义相似度，
        结合权重、频次、用户偏好计算最终得分。
        """
        user_vec = self.model.encode([text])[0]
        scores = []

        # 从配置获取系数
        coeff_sim = self.config.get('scoring.weights.similarity', 0.6)
        coeff_weight = self.config.get('scoring.weights.base_weight', 0.3)
        coeff_freq = self.config.get('scoring.weights.frequency', 0.001)
        max_freq = self.config.get('scoring.weights.frequency_max', 0.1)
        threshold = self.config.get('matching.min_similarity_threshold', 0.5)
        weight_max = self.config.get('scoring.normalization.weight_max', 5)

        for genku in self.normal_genkus:
            vec = self.vectors.get(genku.genku_id)
            if vec is None:
                continue

            similarity = self._cosine_similarity(user_vec, vec)
            if similarity < threshold:
                continue

            # 可配置的得分计算
            score = similarity * coeff_sim
            score += (genku.weight / weight_max) * coeff_weight
            score += min(genku.usage_count * coeff_freq, max_freq)

            # 应用高频梗频率惩罚（静默降权）
            freq_penalty = self._get_frequency_penalty(genku)
            score *= freq_penalty

            if user_pref and self.config.get('learning.enabled'):
                score += self._preference_bonus(genku, user_pref)

            scores.append((score, genku))

        return scores

    def _keyword_match(self, text: str, user_pref: Optional[UserPreference]) -> List[Tuple[float, Genku]]:
        """
        基于关键词的匹配（增强版）
        
        **新增功能：**
        - 核心结构保护：确保匹配的梗符合核心结构
        - 特殊规则处理：如 gy_001 的 long 音匹配
        """
        from .genku_core_structures import GENKU_CORE_STRUCTURES, get_genku_core
        
        text_lower = text.lower()
        scores = []

        coeff_weight = self.config.get('scoring.weights.base_weight', 0.3)
        weight_max = self.config.get('scoring.normalization.weight_max', 5)

        for genku in self.normal_genkus:
            score = 0
            matched_keywords = []

            # 1. 原文匹配（关键词在原文中）
            for word in genku.original.split('，'):
                if word and word in text:
                    score += 0.5
                    matched_keywords.append(word)

            # 2. 标签匹配
            for tag in genku.tags:
                if tag in text_lower:
                    score += 0.3
                    matched_keywords.append(tag)

            # 3. 语义关键词匹配
            for kw in genku.semantic_keywords:
                if kw in text_lower:
                    score += 0.2
                    matched_keywords.append(kw)

            # 4. 核心结构匹配（新增）
            core_structure_score = self._match_core_structure(genku.genku_id, text, matched_keywords)
            score += core_structure_score

            if score > 0:
                score += (genku.weight / weight_max) * coeff_weight

                # 应用高频梗频率惩罚（静默降权）
                freq_penalty = self._get_frequency_penalty(genku)
                score *= freq_penalty

                if user_pref and self.config.get('learning.enabled'):
                    score += self._preference_bonus(genku, user_pref)
                scores.append((score, genku))

        return scores

    def _match_core_structure(self, genku_id: str, text: str, matched_keywords: List[str]) -> float:
        """
        基于核心结构的匹配评分
        
        - 检查文本是否包含核心结构的 fixed 部分
        - 特殊规则处理（如 gy_001 的 long 音匹配）
        
        Returns:
            额外的匹配分数（0-1.0）
        """
        from .genku_core_structures import get_genku_core
        
        core = get_genku_core(genku_id)
        if not core or core.get('structure') == '未标注':
            return 0.0
        
        fixed_parts = core.get('fixed', [])
        if not fixed_parts:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        # 检查每个 fixed 部分是否在文本中
        for fixed in fixed_parts:
            # 处理 ## 通配符
            if '##' in fixed:
                # 可替换部分，检查核心词
                core_words = fixed.replace('##', '').split('，')
                for word in core_words:
                    if word and word in text:
                        score += 0.3
            elif '#' in fixed:
                # 单字通配符，检查核心词
                core_words = fixed.replace('#', '').split('，')
                for word in core_words:
                    if word and len(word) >= 2 and word in text:
                        score += 0.25
            else:
                # 完全匹配
                if fixed in text:
                    score += 0.4
        
        # ========== 特殊规则处理 ==========
        
        # 规则1: gy_001 - long 音匹配
        if genku_id == 'xsg_gy_001':
            # 检查前文是否有 lb_005（扎聋）
            has_deaf_context = '扎聋' in text or '聋' in matched_keywords
            
            # long 音字列表
            long_sound_words = ['聋', '笼', '龙', '隆', '垄']
            
            if has_deaf_context:
                # 前文有聋，优先匹配聋
                if '聋' in text:
                    score += 0.5
            else:
                # 找其他 long 音字
                for word in long_sound_words:
                    if word in text:
                        score += 0.3
                        break
        
        # 规则2: gs_001 - 数量对偶匹配
        if genku_id == 'xsg_gs_001':
            # 检查是否有"一对X，两头Y"模式
            if re.search(r'一对.+?，.+?两[头个只]', text):
                score += 0.5
            elif re.search(r'一[对双个].+?，两[头个条]', text):
                score += 0.4
        
        # 规则3: wr_001 - 好坏不明推理
        if genku_id == 'xsg_wr_001':
            # 检查是否有"好坏不明/生死不明"类表达
            if re.search(r'[好坏生死]不[好清明]', text):
                score += 0.5
        
        return min(score, 1.0)  # 最高加1分

    def _apply_special_rules(self, genku_id: str, text: str, base_output: str) -> str:
        """
        应用特殊规则处理输出
        
        Returns:
            处理后的输出文本
        """
        # gy_001: long 音替换
        if genku_id == 'xsg_gy_001':
            has_deaf_context = '扎聋' in text
            
            # 找出文本中的 long 音字
            long_words = ['笼', '龙', '隆', '垄', '聋']
            found_word = None
            
            for word in long_words:
                if word in text:
                    found_word = word
                    break
            
            if found_word and not has_deaf_context:
                # 替换输出中的"聋"为找到的long音字
                return base_output.replace('聋', found_word)
        
        return base_output

    def _preference_bonus(self, genku: Genku, pref: UserPreference) -> float:
        """计算用户偏好加成"""
        coeff_person = self.config.get('scoring.weights.preference_person', 0.1)
        coeff_tag = self.config.get('scoring.weights.preference_tag', 0.05)

        bonus = 0.0
        person_score = pref.liked_persons.get(genku.person, 0)
        bonus += person_score * coeff_person

        for tag in genku.tags:
            tag_score = pref.liked_tags.get(tag, 0)
            bonus += tag_score * coeff_tag

        return bonus

    def _cosine_similarity(self, a, b) -> float:
        """计算余弦相似度"""
        if NUMPY_AVAILABLE:
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
        else:
            # 简单的回退实现
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            return dot / (norm_a * norm_b + 1e-8)

    def _sample_with_temperature(self, scores: List[Tuple[float, Genku]]) -> Genku:
        """
        应用温度参数进行采样

        温度 T < 1: 更确定，偏向高分
        温度 T = 1: 正常分布
        温度 T > 1: 更随机，探索性强
        """
        temperature = self.config.get('matching.temperature', 1.0)
        top_n = self.config.get('matching.top_n_candidates', 5)

        # 取 Top N
        scores.sort(reverse=True, key=lambda x: x[0])
        top_candidates = scores[:top_n]

        weights = [s[0] for s in top_candidates]
        candidates = [s[1] for s in top_candidates]

        # 应用温度缩放
        if temperature != 1.0 and temperature > 0:
            # 防止除零，添加小值
            weights = [max(w, 0.001) for w in weights]
            exp_weights = [math.exp(w / temperature) for w in weights]
            total = sum(exp_weights)
            weights = [w / total for w in exp_weights]

        return random.choices(candidates, weights=weights)[0]

    def _try_fusion(self, main_genku: Genku, user_text: str) -> Optional[str]:
        """
        尝试将 meta 梗与主梗融合

        根据 meta 梗的融合规则配置，选择合适的模板生成融合文本。
        严格质量控制，避免生硬拼接。
        """
        fusion_prob = self.config.get('fusion.fusion_probability', 0.7)
        if random.random() > fusion_prob:
            return None

        # 找出可融合的 meta 梗
        compatible_meta = []
        for meta in self.meta_genkus:
            if not meta.fusion_targets:
                compatible_meta.append(meta)
            else:
                for target in meta.fusion_targets:
                    if target in main_genku.tags or target in main_genku.person:
                        compatible_meta.append(meta)
                        break

        if not compatible_meta:
            return None

        # 尝试多个 meta 梗，选择融合质量最好的
        best_fusion = None
        best_quality = 0

        for meta in random.sample(compatible_meta, min(3, len(compatible_meta))):
            fused = self._fuse_genkus(meta, main_genku, user_text)
            if fused:
                quality = self._evaluate_fusion_quality(fused, meta.original, main_genku.original)
                if quality > best_quality:
                    best_quality = quality
                    best_fusion = fused

        # 只有质量足够高才返回融合结果
        threshold = self.config.get('scoring.thresholds.fusion_quality', 0.7)
        if best_quality >= threshold:
            return best_fusion
        return None

    def _evaluate_fusion_quality(self, fused: str, meta: str, main: str) -> float:
        """
        评估融合质量，返回 0-1 的分数（规则引擎增强版）
        
        优化内容：
        1. 高质量融合模式库（正向匹配）
        2. 低质量模式库（负向惩罚）
        3. 语义连贯性检查
        4. 梗类型冲突检测
        """
        import re
        score = 0.5  # 基础分

        # ========== 前置质量过滤（新增）==========
        # 检测meta或main文本在融合结果中是否真的重复出现
        # 注意：如果main本身包含meta（如meta="不可能", main="绝对不可能"），
        # 则需要排除这种自然包含导致的"伪重复"
        def _count_real_occurrences(text: str, substring: str) -> int:
            """计算子串在文本中的真实出现次数，排除main对meta的自然包含"""
            if not substring:
                return 0
            count = text.count(substring)
            # 如果main本身包含meta，减去main自带的一次
            if substring != main and main and substring in main:
                count -= 1
            return max(1, count) if substring in text else 0
        
        meta_count = _count_real_occurrences(fused, meta) if meta else 0
        main_count = fused.count(main) if main else 0
        is_repetitive = meta_count >= 2 or main_count >= 2
        
        if is_repetitive:
            score -= 0.45  # 重复堆叠惩罚
        
        # ========== 高质量模式（加分）==========
        # 只有非重复时才匹配高质量模式
        if not is_repetitive:
            good_patterns = [
                (r'^.+，这就不奇怪了[，。！]*$', 0.25),  # "X，这就不奇怪了"
                (r'^.+？.+！$', 0.2),  # 问句+感叹句
                (r'^不可能，.+！$', 0.2),  # "不可能，X！"
                (r'^.+，这才是.+！$', 0.15),  # "X，这才是Y！"
                (r'^.+：.+！*$', 0.15),  # 冒号连接
            ]
            
            for pattern, bonus in good_patterns:
                if re.match(pattern, fused):
                    score += bonus
                    break  # 只匹配一个最高分模式

        # ========== 低质量模式（减分）==========
        bad_patterns = [
            (r'[！？。，]{2,}', 0.3),  # 重复标点
            (r'^.+，.+，.+，.*$', 0.25),  # 三个以上分句
            (r'^.+，.+，.+。.*$', 0.25),  # 三个以上分句（句号结尾）
            (r'(天意|不可能|天下无敌).*(天意|不可能|天下无敌)', 0.4),  # 同类型梗重复
            (r'^(是|这就是|这才是).+(是|这就是|这才是)', 0.3),  # 判断词重复
            (r'.+罢了.+罢了', 0.25),  # 重复语气词
        ]
        
        for pattern, penalty in bad_patterns:
            if re.search(pattern, fused):
                score -= penalty

        # ========== 长度合理性检查 ==========
        expected_len = len(meta) + len(main)
        actual_len = len(fused)
        
        if actual_len > expected_len * 1.5:
            score -= 0.2
        elif actual_len < expected_len * 0.8:
            score -= 0.15  # 过度压缩也不好
        
        # 最佳长度：比原句之和长0-20%
        if expected_len <= actual_len <= expected_len * 1.2:
            score += 0.1

        # ========== 语义连贯性检查 ==========
        # meta梗与main梗的语义关联加分
        coherence_keywords = {
            '这就不奇怪了': ['曹操盖饭', '撤回', '失败', '输', '败', '奇怪', '难怪'],
            '不可能': ['赢', '强', '胜利', '无敌', '勇猛', '天下无敌'],
            '叉出去': ['放肆', '无礼', '大胆', '匹夫', '狂妄'],
            '天意': ['胜败', '命运', '历史', '剧变', '结局'],
            '列位诸公': ['告老还乡', '放肆', '容不下', '容我'],
        }
        
        # 检查meta是否在关键词映射中
        for meta_keyword, related_words in coherence_keywords.items():
            if meta_keyword in meta:
                # 检查main或fused中是否有相关词
                has_related = any(w in main or w in fused for w in related_words)
                if has_related:
                    score += 0.15
                break

        # ========== 自然连接词检查 ==========
        natural_connectors = ['表示', '就是', '堪称', '可谓是', '那是', '：', '，', '——']
        has_connector = any(c in fused for c in natural_connectors)
        
        # 检查是否有生硬拼接（两个完整句子无连接）
        both_exclaim = (meta.endswith(('！', '!')) and 
                       main.startswith(('不可能', '绝对', '叉出去', '天意', '列位')))
        
        if both_exclaim and not has_connector:
            score -= 0.25
        elif has_connector:
            score += 0.1

        # ========== 特殊梗保护 ==========
        # 曹操盖饭需要完整语境
        if '曹操盖饭' in main or '盖饭' in main:
            if '撤回' not in fused and '这就不奇怪' not in fused:
                score -= 0.2
            else:
                score += 0.1

        # ========== 多样性保护 ==========
        # 避免连续使用相同结构
        if '，' in fused and ('。' in fused or '！' in fused):
            # 检查是否是"X，Y。"结构（推荐）
            if fused.count('，') == 1 and fused.count('。') + fused.count('！') == 1:
                score += 0.05

        return max(0.0, min(1.0, score))

    def _fuse_genkus(self, meta: Genku, main: Genku, user_text: str) -> Optional[str]:
        """
        融合 meta 梗和主梗

        公共入口，保持接口不变。内部委托给子方法：
        1. 使用梗自身融合规则
        2. 使用全局配置模板
        3. 默认直接拼接
        """
        meta_variant = self.generate_variant(meta, user_text)
        entities = self._extract_entities(user_text)
        称呼 = entities.get('称呼', '折棒')

        # 步骤1: 梗自身融合规则
        result = self._fuse_by_custom_rules(meta, main, meta_variant, 称呼, user_text)
        if result:
            return result

        # 步骤2: 全局模板匹配
        result = self._fuse_by_templates(meta, main, meta_variant, 称呼, user_text)
        if result:
            return result

        # 步骤3: 默认直接拼接
        result = f"{meta_variant}，{main.original}"
        if self._check_fusion_quality(result, meta_variant, main.original):
            return result
        return None

    def _fuse_by_custom_rules(self, meta: Genku, main: Genku,
                                meta_variant: str, 称呼: str, user_text: str) -> Optional[str]:
        """使用梗自身的融合规则进行融合"""
        if not meta.fusion_rules:
            return None

        result = self._apply_fusion_rules(meta.fusion_rules, meta_variant, main.original, 称呼)
        if self._check_fusion_quality(result, meta_variant, main.original):
            return result
        return None

    def _fuse_by_templates(self, meta: Genku, main: Genku,
                           meta_variant: str, 称呼: str, user_text: str) -> Optional[str]:
        """使用全局配置模板进行融合"""
        templates_config = self.config.get('fusion.templates', {})

        for category, rules in templates_config.items():
            if category == '默认':
                continue
            patterns = rules.get('patterns', [])
            if not any(re.match(p, meta_variant) for p in patterns):
                continue

            templates = rules.get('templates', ['{meta}，{主梗}'])
            for template in templates:
                actions = rules.get('actions', [''])
                action = random.choice(actions) if actions else ''
                result = template.format(
                    meta=meta_variant,
                    主梗=main.original,
                    称呼=称呼,
                    动作=action
                )
                if self._check_fusion_quality(result, meta_variant, main.original):
                    return result

            # 该类别所有模板都不理想
            return None

        return None

    def _check_fusion_quality(self, fused: str, meta: str, main: str) -> bool:
        """
        检查融合质量（使用评分方法的包装）

        避免生硬拼接，确保语义连贯。
        """
        threshold = self.config.get('scoring.thresholds.fusion_quality', 0.7)
        return self._evaluate_fusion_quality(fused, meta, main) >= threshold

    def _apply_fusion_rules(self, rules: Dict, meta_variant: str, main_text: str, 称呼: str) -> str:
        """应用梗自身的融合规则"""
        template = rules.get('模板', '{meta}，{主梗}')

        # 替换变量
        result = template.replace('{meta}', meta_variant)
        result = result.replace('{主梗}', main_text)
        result = result.replace('{称呼}', 称呼)

        # 处理动作变量
        if '{动作}' in result:
            actions = rules.get('变量', {}).get('动作', [''])
            result = result.replace('{动作}', random.choice(actions))

        return result

    def generate_variant(self, genku: Genku, user_text: str) -> str:
        """
        生成梗的变体文本（基于核心结构保护）

        公共入口，保持接口不变。内部按步骤委托给子方法：
        1. 基础变量替换
        2. 智能填充未匹配变量
        3. 验证 fixed 部分完整性
        4. 应用特殊规则
        """
        from .genku_core_structures import get_genku_core

        core = get_genku_core(genku.genku_id)
        fixed_parts = core.get('fixed', [])

        if not genku.variant_template:
            return genku.original

        entities = self._extract_entities(user_text)
        template = genku.variant_template

        # 步骤1: 基础变量替换
        template = self._variant_fill_basic(template, genku, entities, fixed_parts)

        # 步骤2: 智能填充未匹配变量
        template = self._variant_fill_smart(template, genku, user_text, fixed_parts)
        if template is None:
            return genku.original

        # 步骤3: 验证 fixed 部分完整性
        if not self._variant_validate_fixed(template, genku.genku_id, fixed_parts):
            return genku.original

        # 步骤4: 应用特殊规则
        template = self._apply_special_rules(genku.genku_id, user_text, template)

        return template

    def _variant_fill_basic(self, template: str, genku: Genku,
                            entities: dict, fixed_parts: list) -> str:
        """基础变量替换（保护 fixed 部分）"""
        if not genku.variable_desc:
            return template

        for var_name in genku.variable_desc.keys():
            placeholder = f'[{var_name}]'
            if placeholder not in template:
                continue

            value = entities.get(var_name)
            if not value:
                defaults = self.config.get('variant.defaults', {})
                value = defaults.get(var_name, '')

            if not value:
                continue

            placeholder_in_fixed = any(placeholder in fixed for fixed in fixed_parts)
            if placeholder_in_fixed:
                self.logger.debug(f"变量 {placeholder} 在fixed部分中，跳过替换")
                continue

            template = template.replace(placeholder, value)

        return template

    def _variant_fill_smart(self, template: str, genku: Genku,
                            user_text: str, fixed_parts: list) -> Optional[str]:
        """智能填充未匹配变量，失败时返回 None"""
        if '[' not in template or ']' not in template:
            return template

        unmatched_vars = []
        for match in re.finditer(r'\[([^\]]+)\]', template):
            var_name = match.group(1)
            extracted = self._smart_extract(user_text, var_name)
            if extracted:
                template = template.replace(f'[{var_name}]', extracted)
            else:
                unmatched_vars.append((match.group(0), var_name))

        # 智能降级策略
        for placeholder, var_name in unmatched_vars:
            if placeholder == '[内容]' or var_name == '内容':
                fallback = self._extract_last_noun(user_text)
                if fallback:
                    template = template.replace(placeholder, fallback)
                    continue

            found_in_fixed = False
            for fixed in fixed_parts:
                if '#' in fixed and var_name in fixed.replace('#', ''):
                    keyword = self._extract_keyword(user_text)
                    if keyword:
                        template = template.replace(placeholder, keyword)
                        found_in_fixed = True
                        break
            if found_in_fixed:
                continue

            self.logger.debug(f"无法提取变量 {var_name}，返回原文")
            return None

        return template

    def _variant_validate_fixed(self, template: str, genku_id: str, fixed_parts: list) -> bool:
        """验证生成的变体是否包含所有 fixed 部分"""
        template_clean = template.replace('，', '').replace(',', '')

        for fixed in fixed_parts:
            if '#' in fixed:
                continue
            fixed_clean = fixed.replace('#', '').replace('，', '').replace(',', '')
            if fixed_clean not in template_clean:
                self.logger.warning(f"变体破坏了核心结构: {genku_id}, missing fixed: {fixed}")
                return False

        return True

    def _smart_extract(self, text: str, var_name: str) -> Optional[str]:
        """
        智能提取变量值 - 改进版
        
        支持更多提取模式，当无法精确匹配时尝试模糊提取
        """
        # 扩展的提取器配置
        extractors = {
            '对象': [
                r'(\S+?)[这那]个',
                r'[关于是](\S+?)[的,]',
                r'(\S+?)的',
                r'(?:讨论|议论|提到|说)(\S+?)',
            ],
            '动作': [
                r'(\S+?)[了过]',
                r'(\S+?)一下',
                r'(?:要|想|准备|去)(\S+?)(?:了|的)',
            ],
            '人物': [
                r'(\S+?)[爷哥姐]',
                r'(\S+?)老师',
                r'(\S+?)(?:先生|女士)',
            ],
            '物品': [
                r'(\S+?)[东西]',
                r'[个件条](\S+?)',
                r'(?:买|拿|带|吃)(\S+?)',
            ],
            '内容': [
                r'(?:不怕|怕)(\S+?)(?:，|！|!|$)',
                r'不怕(\S+?)',
            ],
            '时间': [
                r'(\d+[天周月年])',
                r'(明天|后天|今天|现在|立刻)',
            ],
            '地点': [
                r'(?:在|去|到)(\S+?)(?:的|了|啊)',
                r'(\S+?)(?:那边|这里|那里)',
            ],
        }

        patterns = extractors.get(var_name, [])
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                extracted = match.group(1).strip()
                # 过滤掉过短的提取结果
                if len(extracted) >= 1:
                    return extracted

        # 如果标准模式都失败，尝试通用提取
        # 对于短文本，尝试提取关键词
        if var_name == '内容' and len(text) <= 20:
            # 直接返回文本中最后一个词
            words = text.replace('，', ',').replace('。', '.').replace('！', '!').split()
            if words:
                last_word = words[-1].strip('，。！.,!')
                if len(last_word) >= 1:
                    return last_word

        return None

    def _extract_last_noun(self, text: str) -> Optional[str]:
        """
        从文本中提取最后一个名词/关键词
        用于降级策略时的备用提取
        """
        # 清理文本
        clean = text.replace('，', ' ').replace('。', ' ').replace('！', ' ').replace('?', ' ')
        words = clean.split()
        
        # 从后往前找，跳过语气词和短词
        skip_words = {'了', '的', '吗', '呢', '吧', '啊', '我', '你', '他', '她', '它', '是', '有', '在', '就'}
        
        for word in reversed(words):
            word = word.strip('，。！？.,!?')
            if len(word) >= 2 and word not in skip_words:
                return word
            elif len(word) == 1 and word not in skip_words:
                # 单字也接受，但优先返回多字
                if not any(w for w in reversed(words) if len(w.strip('，。！？.,!?')) >= 2 and w.strip('，。！？.,!?') not in skip_words):
                    return word
        
        # 如果都没找到，返回最后一个词
        if words:
            return words[-1].strip('，。！？.,!?')
        return None
    
    def _extract_keyword(self, text: str) -> Optional[str]:
        """
        从文本中提取关键词（通用方法）
        优先提取动词/名词组合
        """
        # 常见动词后的名词
        patterns = [
            r'(?:要|想|准备|去|做|搞|弄|处理|解决|完成|学习|研究)(\S+?)(?:了|的|一下|吧|$)',
            r'(?:买|卖|拿|带|吃|喝|玩|看|听|写|画)(\S+?)(?:了|的|吗|$)',
            r'(?:很|太|非常|特别|有点|比较)(\S+?)(?:的|了|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                extracted = match.group(1).strip()
                if len(extracted) >= 1:
                    return extracted
        
        # 回退到最后名词提取
        return self._extract_last_noun(text)

    def _extract_entities(self, user_text: str) -> Dict[str, str]:
        """
        从用户文本中提取实体

        提取对象、称呼等变量用于模板替换。
        """
        entities = {}
        patterns = self.config.get('variant.patterns', {})

        # 提取对象
        for pattern in patterns.get('object', []):
            match = re.search(pattern, user_text)
            if match:
                entities['对象'] = match.group(1).strip()
                break

        # 提取称呼
        称呼_match = re.search(r'(\S+?)(?:爷|哥|姐|老师)', user_text)
        if 称呼_match:
            entities['称呼'] = 称呼_match.group(1)

        return entities

    def update_user_preference(self, user_pref: UserPreference, genku: Genku, feedback_type: str):
        """
        根据用户反馈更新偏好

        Args:
            user_pref: 用户偏好对象
            genku: 被反馈的梗
            feedback_type: 'like' 或 'dislike'
        """
        decay = self.config.get('learning.preference_decay', 0.9)

        if feedback_type == 'like':
            user_pref.update_person_score(genku.person, 0.1, decay)
            for tag in genku.tags:
                user_pref.update_tag_score(tag, 0.05, decay)
        else:
            user_pref.update_person_score(genku.person, -0.05, decay)
            for tag in genku.tags:
                user_pref.update_tag_score(tag, -0.02, decay)

        user_pref.feedback_stats[feedback_type] = user_pref.feedback_stats.get(feedback_type, 0) + 1
        user_pref.total_interactions += 1
        from datetime import datetime
        user_pref.last_active = datetime.now().isoformat()

    def get_meta_genkus(self) -> List[Genku]:
        """获取 meta 梗列表（返回副本防止外部修改）"""
        return self.meta_genkus.copy()

    def get_normal_genkus(self) -> List[Genku]:
        """获取普通梗列表（返回副本防止外部修改）"""
        return self.normal_genkus.copy()

    # ========== 公开接口 ==========

    def try_fusion(self, main_genku: Genku, user_text: str) -> Optional[str]:
        """
        尝试将 meta 梗与主梗融合（公开接口）

        Returns:
            融合后的文本，或 None（融合失败/不触发）
        """
        return self._try_fusion(main_genku, user_text)

    def check_fusion_quality(self, fused: str, meta: str, main: str) -> bool:
        """检查融合质量（公开接口）"""
        threshold = self.config.get('scoring.thresholds.fusion_quality', 0.7)
        return self._evaluate_fusion_quality(fused, meta, main) >= threshold
