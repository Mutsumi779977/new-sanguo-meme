"""
新三国梗系统 - 工具函数
"""
import logging
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
