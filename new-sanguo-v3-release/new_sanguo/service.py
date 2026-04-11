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


# 高频梗防滥用配置（新三国事不过三定律）
HIGH_FREQUENCY_GENKU_CONFIG = {
    'weight_5_genkus': {  # 所有权重>=5的梗自动纳入
        'min_weight': 5,
        'window_seconds': 600,  # 10分钟窗口
        'max_usage_before_penalty': 3,  # 事不过三：前3次正常使用
        'penalty_per_use': 0.1,  # 第4次起每次乘以0.1（严重惩罚）
        'penalty_threshold': 0.5,  # 惩罚系数低于此值时换梗
    }
}


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

        config = HIGH_FREQUENCY_GENKU_CONFIG.get('weight_5_genkus')
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
        excess_uses = len(history) - max_before_penalty + 1  # 超出次数（从第4次开始算1）
        penalty = penalty_per_use ** excess_uses
        
        self.logger.debug(f"高频梗 {genku.genku_id} 事不过三惩罚: {penalty:.3f} (已使用{len(history)}次)")

        return penalty

    def _record_genku_usage(self, genku: Genku):
        """记录梗使用情况（仅记录高频梗）"""
        import time

        config = HIGH_FREQUENCY_GENKU_CONFIG.get('weight_5_genkus')
        if not config:
            return

        min_weight = config.get('min_weight', 5)
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
        """基于关键词的匹配（降级方案）"""
        text_lower = text.lower()
        scores = []

        coeff_weight = self.config.get('scoring.weights.base_weight', 0.3)
        weight_max = self.config.get('scoring.normalization.weight_max', 5)

        for genku in self.normal_genkus:
            score = 0

            # 原文匹配
            for word in genku.original.split('，'):
                if word and word in text:
                    score += 0.5

            # 标签匹配
            for tag in genku.tags:
                if tag in text_lower:
                    score += 0.3

            # 语义关键词匹配
            for kw in genku.semantic_keywords:
                if kw in text_lower:
                    score += 0.2

            if score > 0:
                score += (genku.weight / weight_max) * coeff_weight

                # 应用高频梗频率惩罚（静默降权）
                freq_penalty = self._get_frequency_penalty(genku)
                score *= freq_penalty

                if user_pref and self.config.get('learning.enabled'):
                    score += self._preference_bonus(genku, user_pref)
                scores.append((score, genku))

        return scores

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
        if best_quality >= 0.7:
            return best_fusion
        return None

    def _evaluate_fusion_quality(self, fused: str, meta: str, main: str) -> float:
        """
        评估融合质量，返回 0-1 的分数
        """
        score = 1.0

        # 检查1：长度合理（不能比两部分加起来长太多）
        expected_len = len(meta) + len(main)
        if len(fused) > expected_len * 1.5:
            score -= 0.3

        # 检查2：避免重复感叹词
        dup_patterns = ['！！', '？？', '。。', '!!', '??']
        for dup in dup_patterns:
            if dup in fused:
                score -= 0.2

        # 检查3：检查自然的逻辑连接
        meta_is_exclaim = meta.endswith(('！', '!', '。')) if meta else False
        main_is_exclaim = main.startswith(('不可能', '绝对', '叉出去', '星夜', '天意')) if main else False

        if meta_is_exclaim and main_is_exclaim:
            # 两句感叹句拼接，检查是否有逻辑连接
            connectors = ['表示', '就是', '堪称', '可谓是', '那是', '：']
            has_connector = any(c in fused for c in connectors)
            if not has_connector:
                score -= 0.4

        # 检查4：曹操盖饭等特殊梗需要完整语境
        if '曹操盖饭' in main and '撤回' not in fused and '这就不奇怪' not in fused:
            score -= 0.3

        # 检查5：避免连续多个梗拼接（如"天意，不可能，天下无敌"）
        comma_count = fused.count('，') + fused.count(',')
        if comma_count >= 2 and ('天意' in fused or '列位诸公' in fused):
            score -= 0.3

        return max(0.0, score)

    def _fuse_genkus(self, meta: Genku, main: Genku, user_text: str) -> Optional[str]:
        """
        融合 meta 梗和主梗

        优先使用梗自身的融合规则，否则使用全局配置模板。
        添加质量检查，避免生硬拼接。
        """
        # 生成 meta 变体
        meta_variant = self.generate_variant(meta, user_text)

        # 提取称呼变量
        entities = self._extract_entities(user_text)
        称呼 = entities.get('称呼', '折棒')

        # 优先使用梗自身的融合规则
        if meta.fusion_rules:
            result = self._apply_fusion_rules(meta.fusion_rules, meta_variant, main.original, 称呼)
            if self._check_fusion_quality(result, meta_variant, main.original):
                return result
            else:
                # 融合质量不佳，返回主梗即可
                return None

        # 否则使用全局配置的模板匹配
        templates_config = self.config.get('fusion.templates', {})

        # 根据 meta 内容匹配模板类别
        for category, rules in templates_config.items():
            if category == '默认':
                continue
            patterns = rules.get('patterns', [])
            if any(re.match(p, meta_variant) for p in patterns):
                templates = rules.get('templates', ['{meta}，{主梗}'])

                # 尝试多个模板，选择最流畅的
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

                # 所有模板都不理想，返回主梗
                return None

        # 默认：检查直接拼接是否流畅
        default_template = templates_config.get('默认', {}).get('templates', ['{meta}，{主梗}'])[0]
        result = default_template.format(meta=meta_variant, 主梗=main.original)

        if self._check_fusion_quality(result, meta_variant, main.original):
            return result
        return None

    def _check_fusion_quality(self, fused: str, meta: str, main: str) -> bool:
        """
        检查融合质量

        避免生硬拼接，确保语义连贯。
        """
        # 检查1：长度合理
        if len(fused) > len(meta) + len(main) + 5:
            # 可能有过多的连接词
            pass

        # 检查2：避免重复感叹词
        dup_exclaims = ['！!', '？？', '。。']
        for dup in dup_exclaims:
            if dup in fused:
                return False

        # 检查3：检查是否有自然的逻辑连接
        # 好的融合应该是：meta 铺垫 -> 主梗 punchline
        # 而不是：meta + 主梗 强行并置

        # 如果 meta 和 main 都是感叹句，拼接会很生硬
        meta_is_exclaim = meta.endswith(('！', '!', '。'))
        main_is_exclaim = main.startswith(('不可能', '绝对', '叉出去', '星夜'))

        if meta_is_exclaim and main_is_exclaim:
            # 两句感叹句拼接，检查是否有逻辑连接
            connectors = ['，', '：', '表示', '就是', '堪称', '可谓是', '那是']
            has_connector = any(c in fused for c in connectors)
            if not has_connector:
                return False

        # 检查4：曹操盖饭等特殊梗需要完整语境
        if '曹操盖饭' in main and '撤回' not in fused and '这就不奇怪' not in fused:
            # 曹操盖饭需要前置铺垫
            return False

        return True

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
        生成梗的变体文本

        根据变体模板和用户输入提取的实体，替换变量生成上下文相关的变体。
        """
        if not genku.variant_template:
            return genku.original

        template = genku.variant_template
        entities = self._extract_entities(user_text)

        # 替换模板变量
        if genku.variable_desc:
            for var_name in genku.variable_desc.keys():
                placeholder = f'[{var_name}]'
                if placeholder in template:
                    value = entities.get(var_name)
                    if value:
                        template = template.replace(placeholder, value)
                    else:
                        defaults = self.config.get('variant.defaults', {})
                        template = template.replace(placeholder, defaults.get(var_name, '...'))

        # 如果还有未替换的变量，返回原文
        if '[' in template and ']' in template:
            return genku.original

        return template

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
        return self._evaluate_fusion_quality(fused, meta, main) >= 0.7
