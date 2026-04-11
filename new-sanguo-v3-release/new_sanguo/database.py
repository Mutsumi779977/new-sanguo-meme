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
新三国梗系统 - 数据库层
"""
import sqlite3
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import yaml

from .models import Genku, UserPreference
from .config import Config


class Database:
    """
    SQLite 数据库管理类
    
    提供梗数据和用户偏好的持久化存储。
    使用线程本地存储确保线程安全。
    
    Attributes:
        db_path: 数据库文件路径
        config: 配置对象
        logger: 日志对象
    """
    
    def __init__(self, config: Config, logger):
        """
        初始化数据库
        
        Args:
            config: 配置对象
            logger: 日志对象
        """
        self.config = config
        self.logger = logger
        self.db_path = Path(__file__).parent.parent / 'data' / config.get('database.filename', 'genku.db')
        self.db_path.parent.mkdir(exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取线程本地的数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path), timeout=self.config.get('database.timeout', 30))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    @contextmanager
    def _transaction(self):
        """事务上下文管理器"""
        conn = self._get_conn()
        with self._lock:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def _init_db(self):
        """初始化数据库表结构"""
        with self._transaction() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS genku (
                    genku_id TEXT PRIMARY KEY,
                    original TEXT NOT NULL,
                    person TEXT NOT NULL,
                    source TEXT,
                    context TEXT,
                    emotions TEXT,
                    intensity TEXT,
                    tags TEXT,
                    semantic_keywords TEXT,
                    weight INTEGER DEFAULT 3,
                    variant_template TEXT,
                    variable_desc TEXT,
                    usage_count INTEGER DEFAULT 0,
                    effectiveness REAL DEFAULT 0.0,
                    is_meta INTEGER DEFAULT 0,
                    fusion_targets TEXT,
                    fusion_rules TEXT,
                   录入时间 TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_prefs (
                    user_id TEXT PRIMARY KEY,
                    liked_persons TEXT,
                    liked_tags TEXT,
                    avg_intensity TEXT,
                    total_interactions INTEGER DEFAULT 0,
                    last_active TEXT,
                    feedback_stats TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    genku_id TEXT,
                    feedback_type TEXT,
                    feedback_reason TEXT,
                    conversation_context TEXT,
                    timestamp TEXT
                )
            ''')
    
    def import_from_yaml(self, yaml_path: str) -> int:
        """
        从 YAML 文件导入梗数据
        
        Args:
            yaml_path: YAML 文件路径
            
        Returns:
            导入的梗数量
        """
        yaml_file = Path(__file__).parent.parent / yaml_path
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML文件不存在: {yaml_file}")
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割多个 YAML 文档
        docs = content.split('\n---\n')
        count = 0
        
        with self._transaction() as conn:
            for doc in docs:
                doc = doc.strip()
                if not doc or doc.startswith('#'):
                    continue
                try:
                    data = yaml.safe_load(doc)
                    if data and '梗ID' in data:
                        self._insert_genku(conn, data)
                        count += 1
                except Exception as e:
                    self.logger.warning(f"导入失败: {e}")
        
        self.logger.info(f"从 YAML 导入 {count} 条梗")
        return count
    
    def _insert_genku(self, conn: sqlite3.Connection, data: Dict):
        """插入单条梗数据"""
        conn.execute('''
            INSERT OR REPLACE INTO genku VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            data.get('梗ID', ''),
            data.get('原文', ''),
            data.get('人物', '未知'),
            data.get('出处', ''),
            data.get('情境', ''),
            json.dumps(data.get('情绪', []), ensure_ascii=False),
            data.get('强度', '中'),
            json.dumps(data.get('场景标签', []), ensure_ascii=False),
            json.dumps(data.get('语义关键词', []), ensure_ascii=False),
            data.get('权重', 3),
            data.get('变体模板'),
            json.dumps(data.get('变量说明'), ensure_ascii=False) if data.get('变量说明') else None,
            data.get('引用频次', 0),
            data.get('effectiveness', 0.0),
            1 if data.get('is_meta', False) else 0,
            json.dumps(data.get('fusion_targets', []), ensure_ascii=False),
            json.dumps(data.get('融合规则'), ensure_ascii=False) if data.get('融合规则') else None,
            data.get('录入时间', '')
        ))
    
    def save_genku(self, genku: Genku) -> bool:
        """保存梗到数据库"""
        try:
            with self._transaction() as conn:
                data = {
                    '梗ID': genku.genku_id,
                    '原文': genku.original,
                    '人物': genku.person,
                    '出处': genku.source,
                    '情境': genku.context,
                    '情绪': genku.emotions,
                    '强度': genku.intensity,
                    '场景标签': genku.tags,
                    '语义关键词': genku.semantic_keywords,
                    '权重': genku.weight,
                    '变体模板': genku.variant_template,
                    '变量说明': genku.variable_desc,
                    '引用频次': genku.usage_count,
                    'effectiveness': genku.effectiveness,
                    'is_meta': genku.is_meta,
                    'fusion_targets': genku.fusion_targets,
                    '融合规则': genku.fusion_rules,
                    '录入时间': '',
                }
                self._insert_genku(conn, data)
            return True
        except Exception as e:
            self.logger.error(f"保存梗失败: {e}")
            return False
    
    def get_all_genku(self) -> List[Genku]:
        """获取所有梗"""
        conn = self._get_conn()
        cursor = conn.execute('SELECT * FROM genku')
        return [self._row_to_genku(row) for row in cursor.fetchall()]
    
    def get_genku_by_id(self, genku_id: str) -> Optional[Genku]:
        """根据 ID 获取梗"""
        conn = self._get_conn()
        row = conn.execute('SELECT * FROM genku WHERE genku_id = ?', (genku_id,)).fetchone()
        return self._row_to_genku(row) if row else None
    
    def _row_to_genku(self, row: sqlite3.Row) -> Genku:
        """将数据库行转换为 Genku 对象"""
        # 安全获取列值
        def get_col(col_name, default=None):
            try:
                return row[col_name]
            except (KeyError, IndexError):
                return default
        
        return Genku(
            genku_id=get_col('genku_id', ''),
            original=get_col('original', ''),
            person=get_col('person', '未知'),
            source=get_col('source', ''),
            context=get_col('context', ''),
            emotions=json.loads(get_col('emotions', '[]')) if get_col('emotions') else [],
            intensity=get_col('intensity', '中'),
            tags=json.loads(get_col('tags', '[]')) if get_col('tags') else [],
            semantic_keywords=json.loads(get_col('semantic_keywords', '[]')) if get_col('semantic_keywords') else [],
            weight=get_col('weight', 3),
            variant_template=get_col('variant_template'),
            variable_desc=json.loads(get_col('variable_desc')) if get_col('variable_desc') else None,
            usage_count=get_col('usage_count', 0),
            effectiveness=get_col('effectiveness', 0.0),
            is_meta=bool(get_col('is_meta', 0)),
            fusion_targets=json.loads(get_col('fusion_targets', '[]')) if get_col('fusion_targets') else [],
            fusion_rules=json.loads(get_col('fusion_rules')) if get_col('fusion_rules') else None,
        )
    
    def update_usage_count(self, genku_id: str):
        """更新梗的引用频次"""
        with self._transaction() as conn:
            conn.execute(
                'UPDATE genku SET usage_count = usage_count + 1 WHERE genku_id = ?',
                (genku_id,)
            )
    
    def save_user_preference(self, pref: UserPreference) -> bool:
        """保存用户偏好"""
        try:
            with self._transaction() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_prefs VALUES (?,?,?,?,?,?,?)
                ''', (
                    pref.user_id,
                    json.dumps(pref.liked_persons, ensure_ascii=False),
                    json.dumps(pref.liked_tags, ensure_ascii=False),
                    pref.avg_intensity,
                    pref.total_interactions,
                    pref.last_active,
                    json.dumps(pref.feedback_stats, ensure_ascii=False)
                ))
            return True
        except Exception as e:
            self.logger.error(f"保存用户偏好失败: {e}")
            return False
    
    def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        """获取用户偏好"""
        conn = self._get_conn()
        row = conn.execute('SELECT * FROM user_prefs WHERE user_id = ?', (user_id,)).fetchone()
        
        if not row:
            return None
        
        return UserPreference(
            user_id=row['user_id'],
            liked_persons=json.loads(row['liked_persons']) if row['liked_persons'] else {},
            liked_tags=json.loads(row['liked_tags']) if row['liked_tags'] else {},
            avg_intensity=row['avg_intensity'],
            total_interactions=row['total_interactions'],
            last_active=row['last_active'],
            feedback_stats=json.loads(row['feedback_stats']) if row['feedback_stats'] else {'like': 0, 'dislike': 0}
        )
    
    def add_feedback(self, user_id: str, genku_id: str, feedback_type: str,
                     reason: str = None, context: str = None) -> bool:
        """添加用户反馈"""
        try:
            with self._transaction() as conn:
                from datetime import datetime
                conn.execute('''
                    INSERT INTO user_feedback 
                    (user_id, genku_id, feedback_type, feedback_reason, conversation_context, timestamp)
                    VALUES (?,?,?,?,?,?)
                ''', (user_id, genku_id, feedback_type, reason, context, datetime.now().isoformat()))
            return True
        except Exception as e:
            self.logger.error(f"添加反馈失败: {e}")
            return False
    
    def get_genku_feedback_stats(self, genku_id: str) -> Dict[str, int]:
        """获取梗的反馈统计"""
        conn = self._get_conn()
        cursor = conn.execute('''
            SELECT feedback_type, COUNT(*) as count 
            FROM user_feedback WHERE genku_id = ? GROUP BY feedback_type
        ''', (genku_id,))
        
        stats = {'like': 0, 'dislike': 0}
        for row in cursor.fetchall():
            stats[row['feedback_type']] = row['count']
        return stats
    
    def get_user_feedback_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """获取用户反馈历史"""
        conn = self._get_conn()
        cursor = conn.execute('''
            SELECT f.*, g.original as genku_text 
            FROM user_feedback f
            JOIN genku g ON f.genku_id = g.genku_id
            WHERE f.user_id = ?
            ORDER BY f.timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return [{
            'genku_id': row['genku_id'],
            'genku_text': row['genku_text'],
            'feedback_type': row['feedback_type'],
            'timestamp': row['timestamp']
        } for row in cursor.fetchall()]
