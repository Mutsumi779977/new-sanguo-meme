"""
非梗内容观察记录器
用于观察和分析Agent生成的非梗内容，为后续决策提供数据支持
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class NonGenkuRecord:
    """非梗内容记录"""
    timestamp: str
    user_input: str
    output_text: str
    source: str  # 'topic_default', 'fusion_explanation', 'template_addon', 'agent_creation'
    topic: Optional[str]
    matched_genku_id: Optional[str]
    confidence: float
    user_feedback: Optional[str] = None  # 'like', 'dislike', None


class NonGenkuObserver:
    """
    非梗内容观察器
    
    功能：
    1. 记录所有非梗输出
    2. 分类统计
    3. 支持用户反馈关联
    4. 定期生成观察报告
    """
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.expanduser("~/.openclaw/workspace/memory/non_genku_logs")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.records: List[NonGenkuRecord] = []
        
        # 加载今日已有记录
        self._load_today_records()
    
    def _get_log_file(self) -> Path:
        """获取今日日志文件路径"""
        return self.log_dir / f"non_genku_{self.current_date}.jsonl"
    
    def _load_today_records(self):
        """加载今日记录"""
        log_file = self._get_log_file()
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.records.append(NonGenkuRecord(**data))
                        except:
                            pass
    
    def record(self, 
               user_input: str,
               output_text: str,
               source: str,
               topic: Optional[str] = None,
               matched_genku_id: Optional[str] = None,
               confidence: float = 0.0):
        """
        记录非梗输出
        
        Args:
            user_input: 用户输入
            output_text: Agent输出（非梗部分）
            source: 来源类型
                - 'topic_default': 话题默认回复
                - 'fusion_explanation': 融合时的解释性附加
                - 'template_addon': 模板附加说明
                - 'agent_creation': Agent自创内容
            topic: 识别到的话题（如有）
            matched_genku_id: 匹配到的梗ID（如有）
            confidence: 置信度
        """
        record = NonGenkuRecord(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            output_text=output_text,
            source=source,
            topic=topic,
            matched_genku_id=matched_genku_id,
            confidence=confidence
        )
        
        self.records.append(record)
        
        # 追加写入文件
        log_file = self._get_log_file()
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
    
    def add_feedback(self, output_text: str, feedback: str):
        """
        添加用户反馈
        
        Args:
            output_text: 输出文本（用于匹配）
            feedback: 'like' 或 'dislike'
        """
        # 更新内存中的记录
        for record in self.records:
            if record.output_text == output_text and record.user_feedback is None:
                record.user_feedback = feedback
                break
        
        # 重写文件（简化处理，实际可优化为增量更新）
        log_file = self._get_log_file()
        with open(log_file, 'w', encoding='utf-8') as f:
            for record in self.records:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        if not self.records:
            return {"total": 0}
        
        stats = {
            "total": len(self.records),
            "by_source": {},
            "by_topic": {},
            "feedback": {"like": 0, "dislike": 0, "none": 0}
        }
        
        for record in self.records:
            # 按来源统计
            stats["by_source"][record.source] = stats["by_source"].get(record.source, 0) + 1
            
            # 按话题统计
            topic = record.topic or "unknown"
            stats["by_topic"][topic] = stats["by_topic"].get(topic, 0) + 1
            
            # 反馈统计
            if record.user_feedback == 'like':
                stats["feedback"]["like"] += 1
            elif record.user_feedback == 'dislike':
                stats["feedback"]["dislike"] += 1
            else:
                stats["feedback"]["none"] += 1
        
        return stats
    
    def generate_report(self) -> str:
        """生成观察报告"""
        stats = self.get_statistics()
        
        if stats["total"] == 0:
            return "暂无非梗内容记录"
        
        report = f"""
=== 非梗内容观察报告 ({self.current_date}) ===
总记录数: {stats['total']}

【按来源分布】
"""
        for source, count in sorted(stats["by_source"].items(), key=lambda x: -x[1]):
            report += f"  {source}: {count}\n"
        
        report += "\n【按话题分布】\n"
        for topic, count in sorted(stats["by_topic"].items(), key=lambda x: -x[1])[:5]:
            report += f"  {topic}: {count}\n"
        
        report += f"""
【用户反馈】
  👍 点赞: {stats['feedback']['like']}
  👎 点踩: {stats['feedback']['dislike']}
  📝 未反馈: {stats['feedback']['none']}

【建议】
"""
        # 基于数据给出建议
        total_feedback = stats['feedback']['like'] + stats['feedback']['dislike']
        if total_feedback > 0:
            like_ratio = stats['feedback']['like'] / total_feedback
            if like_ratio > 0.7:
                report += "- 非梗内容用户接受度较高，可考虑保留部分自然过渡\n"
            elif like_ratio < 0.3:
                report += "- 非梗内容用户接受度较低，建议收紧输出限制\n"
            else:
                report += "- 非梗内容反馈分化，建议分类讨论\n"
        
        # 检查主要来源
        if stats["by_source"].get('topic_default', 0) > stats["total"] * 0.5:
            report += "- 话题默认回复占比过高，建议优化话题匹配\n"
        
        if stats["by_source"].get('fusion_explanation', 0) > stats["total"] * 0.3:
            report += "- 融合解释性内容较多，建议优化融合策略\n"
        
        return report
    
    def get_recent_records(self, limit: int = 10) -> List[NonGenkuRecord]:
        """获取最近记录"""
        return self.records[-limit:]


# 全局观察器实例（单例模式）
_observer_instance: Optional[NonGenkuObserver] = None


def get_observer() -> NonGenkuObserver:
    """获取全局观察器实例"""
    global _observer_instance
    if _observer_instance is None:
        _observer_instance = NonGenkuObserver()
    return _observer_instance


def record_non_genku(user_input: str, output_text: str, source: str, **kwargs):
    """便捷记录函数"""
    observer = get_observer()
    observer.record(user_input, output_text, source, **kwargs)
