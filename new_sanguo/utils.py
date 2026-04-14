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
新三国梗系统 - 工具函数
"""
import logging
import re
from .config import Config


def setup_logger(config: Config) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        config: 配置对象
        
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger('new_sanguo')
    logger.setLevel(getattr(logging, config.get('logging.level', 'INFO')))
    
    # 清除已有处理器
    logger.handlers.clear()
    
    # 格式化
    show_ts = config.get('logging.show_timestamp', True)
    fmt = '%(asctime)s - %(levelname)s - %(message)s' if show_ts else '%(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    
    # 控制台输出
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 文件输出（可选）
    log_file = config.get('logging.file', '')
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def clean_quote(text: str) -> str:
    """
    清理引用文本中的语气词和冗余内容
    
    Args:
        text: 原始引用文本
        
    Returns:
        清理后的文本
    """
    cleaned = re.sub(r'[，。！？]{2,}', '，', text)
    cleaned = re.sub(r'[哈嘻嘿]{2,}', '', cleaned)
    cleaned = re.sub(r'\.\.\.|……', '', cleaned)
    cleaned = re.sub(r'（[^）]*）', '', cleaned)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    cleaned = cleaned.strip('，。！？ ')
    return cleaned.strip()


def add_watermark(text: str) -> str:
    """
    添加不可见水印（零宽字符）
    用于追踪非授权分发
    
    Args:
        text: 原始文本
        
    Returns:
        带水印的文本
    """
    # 零宽字符水印: \u200b (ZWSP) \u200c (ZWNJ) \u200d (ZWJ)
    # 编码 "MUT" = M(77) U(85) T(84)
    # 简化为特定模式
    watermark = '\u200b\u200c\u200d\u200b\u200c\u200d'
    return text + watermark
