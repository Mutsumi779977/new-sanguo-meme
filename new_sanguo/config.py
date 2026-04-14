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
新三国梗系统 - 配置管理
"""
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """
    配置管理类
    
    从 YAML 文件加载配置，提供默认值回退机制。
    支持通过点号路径访问嵌套配置，如 config.get('matching.temperature')
    """
    
    DEFAULT_CONFIG = {
        'matching': {
            'max_input_length': 2000,
            'weight_bonus_coefficient': 0.3,
            'max_freq_bonus': 0.1,
            'freq_bonus_coefficient': 0.001,
            'top_n_candidates': 5,
            'min_similarity_threshold': 0.5,
            'temperature': 1.0,  # 新增：温度参数
        },
        'scoring': {
            'weights': {
                'similarity': 0.6,
                'base_weight': 0.3,
                'frequency': 0.001,
                'frequency_max': 0.1,
                'preference_person': 0.1,
                'preference_tag': 0.05,
            },
            'normalization': {
                'weight_max': 5,
            }
        },
        'embedding': {
            'enabled': False,  # 默认关闭
            'model_name': 'paraphrase-multilingual-MiniLM-L12-v2',
            'lazy_load': True,
        },
        'database': {
            'filename': 'genku.db',
            'yaml_source': 'data/genku.yaml',
            'timeout': 30,
        },
        'logging': {
            'level': 'INFO',
            'file': '',
            'show_timestamp': True,
        },
        'fusion': {
            'enabled': True,
            'meta_prefix': 'xsg_meta_',
            'fusion_probability': 0.7,
            'max_fusion_per_output': 1,
            'templates': {  # 新增：可配置模板
                '称呼类': {
                    'patterns': ['.*爷.*', '.*哥.*', '.*姐.*'],
                    'templates': [
                        '{称呼}爷{动作}{主梗}',
                        '{称呼}爷表示{主梗}',
                        '{称呼}爷认为{主梗}',
                    ],
                    'actions': ['真是', '堪称', '可谓是', '那就是', '实乃'],
                },
                '宣告类': {
                    'patterns': ['从这一刻起.*', '历史.*'],
                    'templates': ['{meta}，{主梗}'],
                },
                '开场类': {
                    'patterns': ['列位诸公.*', '各位.*'],
                    'templates': ['{meta}，{主梗}'],
                },
                '默认': {
                    'templates': ['{meta}，{主梗}'],
                }
            }
        },
        'dialogue': {
            'context_turns': 5,
            'auto_reply_probability': 0.8,
            'fallback_replies': [
                '这句话有意思，但我还没学到对应的梗。要教教我吗？发送 /录入',
                '你说的这个场景我还不会接，试试 /玩梗 手动触发？',
                '（默默记下）你说的是：{text}...',
                '有趣，让我查查怎么接... 算了没查到😅',
            ]
        },
        'learning': {
            'enabled': True,
            'min_interactions': 3,
            'preference_decay': 0.9,
        },
        'variant': {
            'patterns': {
                'object': [
                    '不想(.*?)了',
                    '不要(.*?)了',
                    '拒绝(.*?)',
                    '别(.*?)了',
                    '今天(.*?)',
                ]
            },
            'defaults': {
                '对象': '这件事',
                '否定词': '不可能',
                '动作1': '奏乐',
                '动作2': '舞',
                '称呼': '楼主',
                '环境': '乱世',
            }
        }
    }
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径，相对于包目录
        """
        self.config_path = Path(__file__).parent.parent / config_path
        self._config = self._load()
    
    def _load(self) -> Dict:
        """从文件加载配置，失败则使用默认配置"""
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
                return self._merge_config(self.DEFAULT_CONFIG.copy(), user_config)
        except Exception:
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """递归合并配置，用户配置覆盖默认值"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_config(default[key], value)
            else:
                default[key] = value
        return default
    
    def get(self, path: str, default=None) -> Any:
        """
        通过点号路径获取配置值
        
        Args:
            path: 如 'matching.temperature' 或 'fusion.enabled'
            default: 默认值
            
        Returns:
            配置值，不存在则返回 default
        """
        keys = path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def reload(self):
        """重新加载配置"""
        self._config = self._load()
