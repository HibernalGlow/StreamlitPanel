import re
import hashlib
from typing import Optional, Dict

def parse_log_line(line: str) -> Optional[Dict]:
    """解析单行日志"""
    # 匹配标准日志格式: 2025-03-27 22:03:14,456 - INFO - [@hash_progress] 进度 0%
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - \[([@#])(\w+)\](.*)', line)
    
    if not match:
        return None
        
    timestamp, level, panel_type, panel_name, content = match.groups()
    
    return {
        "timestamp": timestamp,
        "level": level,
        "panel_type": panel_type,  # @ 进度条, # 普通日志
        "panel_name": panel_name,
        "content": content.strip(),
        "raw": line,
        "fingerprint": hashlib.md5(content[:4].encode()).hexdigest()  # 创建内容前4个字符的指纹
    }

def parse_progress(content: str) -> Optional[Dict]:
    """解析进度条信息"""
    # 匹配分数形式进度: 任务 (5/10) 50%
    fraction_match = re.match(r'(.*?)\s+\((\d+)/(\d+)\)\s+(\d+(?:\.\d+)?)%$', content)
    
    if fraction_match:
        prefix, current, total, percentage = fraction_match.groups()
        return {
            "prefix": prefix.strip(),
            "current": int(current),
            "total": int(total),
            "percentage": float(percentage),
            "is_complete": float(percentage) >= 100.0,
            "fraction": f"({current}/{total})"
        }
        
    # 匹配方括号形式进度: 任务 [5/10] 50%
    bracket_match = re.match(r'(.*?)\s+\[(\d+)/(\d+)\]\s+(\d+(?:\.\d+)?)%$', content)
    
    if bracket_match:
        prefix, current, total, percentage = bracket_match.groups()
        return {
            "prefix": prefix.strip(),
            "current": int(current),
            "total": int(total),
            "percentage": float(percentage),
            "is_complete": float(percentage) >= 100.0,
            "fraction": f"[{current}/{total}]"
        }
    
    # 匹配进度百分比: 进度 50%
    progress_match = re.match(r'(.*?)(\d+(?:\.\d+)?)%$', content)
    
    if progress_match:
        prefix, percentage = progress_match.groups()
        return {
            "prefix": prefix.strip(),
            "percentage": float(percentage),
            "is_complete": float(percentage) >= 100.0
        }
    
    return None 