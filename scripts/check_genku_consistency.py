#!/usr/bin/env python3
"""
Genku一致性检查脚本
检查 genku.yaml 与 genku_core_structures.py 的一致性

用法:
    python3 scripts/check_genku_consistency.py
"""
import re
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple


def extract_yaml_genku_ids(yaml_path: Path) -> Set[str]:
    """从genku.yaml中提取所有梗ID"""
    ids = set()
    with open(yaml_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('梗ID:'):
                genku_id = line.split(':', 1)[1].strip()
                ids.add(genku_id)
    return ids


def extract_structure_genku_ids(structures_path: Path) -> Set[str]:
    """从genku_core_structures.py中提取所有梗ID"""
    ids = set()
    with open(structures_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配 "xsg_xxx_xxx": 格式的键
    pattern = r'"(xsg_[a-z]+_\d{3})"\s*:'
    matches = re.findall(pattern, content)
    ids.update(matches)
    return ids


def check_consistency() -> Tuple[bool, str]:
    """执行一致性检查"""
    
    # 路径设置
    base_dir = Path(__file__).parent.parent
    yaml_path = base_dir / 'data' / 'genku.yaml'
    structures_path = base_dir / 'new_sanguo' / 'genku_core_structures.py'
    
    if not yaml_path.exists():
        return False, f"❌ 未找到文件: {yaml_path}"
    if not structures_path.exists():
        return False, f"❌ 未找到文件: {structures_path}"
    
    yaml_ids = extract_yaml_genku_ids(yaml_path)
    structure_ids = extract_structure_genku_ids(structures_path)
    
    only_in_yaml = yaml_ids - structure_ids
    only_in_structures = structure_ids - yaml_ids
    both = yaml_ids & structure_ids
    
    lines = []
    lines.append("=" * 50)
    lines.append(" Genku 一致性检查报告")
    lines.append("=" * 50)
    lines.append(f"")
    lines.append(f"genku.yaml 中的梗数:       {len(yaml_ids)}")
    lines.append(f"genku_core_structures.py 中的梗数: {len(structure_ids)}")
    lines.append(f"两边都有的梗数:            {len(both)}")
    lines.append(f"")
    
    if only_in_yaml:
        lines.append(f"⚠️  只在 genku.yaml 中存在的梗 ({len(only_in_yaml)}条):")
        for gid in sorted(only_in_yaml):
            lines.append(f"   - {gid}")
        lines.append("")
    
    if only_in_structures:
        lines.append(f"⚠️  只在 genku_core_structures.py 中存在的梗 ({len(only_in_structures)}条):")
        for gid in sorted(only_in_structures):
            lines.append(f"   - {gid}")
        lines.append("")
    
    if not only_in_yaml and not only_in_structures:
        lines.append("✅ 完全一致，没有差异！")
    else:
        lines.append(f"💡 建议: 请同步更新缺失的条目")
    
    lines.append("=" * 50)
    
    is_ok = len(only_in_yaml) == 0 and len(only_in_structures) == 0
    return is_ok, "\n".join(lines)


if __name__ == '__main__':
    ok, report = check_consistency()
    print(report)
    sys.exit(0 if ok else 1)
