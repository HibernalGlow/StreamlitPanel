import os
import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import time

from src.utils.log_parser import parse_log_line

def read_log_file(log_file: str, last_position: int = 0) -> Tuple[List[Dict], int]:
    """读取日志文件并返回解析后的日志条目和新位置"""
    if not os.path.exists(log_file):
        return [], last_position
    
    try:
        log_entries = []
        new_position = last_position
        
        # 尝试不同的编码方式
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'ascii', 'latin1']
        content = None
        error_info = None
        
        for encoding in encodings:
            try:
                with open(log_file, 'r', encoding=encoding) as f:
                    # 定位到上次读取位置
                    f.seek(last_position)
                    content = f.read()
                break
            except UnicodeDecodeError as e:
                continue
            except Exception as e:
                error_info = str(e)
                continue
        
        if content is None:
            if error_info:
                st.error(f"读取日志文件出错: {error_info}")
            else:
                # 尝试二进制方式读取来检查文件是否为空
                try:
                    with open(log_file, 'rb') as f:
                        f.seek(last_position)
                        raw_content = f.read()
                    
                    if not raw_content:
                        return [], last_position  # 文件为空或已经读取到末尾
                    else:
                        st.error(f"无法使用支持的编码方式读取日志文件: {log_file}")
                except Exception as e:
                    st.error(f"读取日志文件出错: {e}")
            
            return [], last_position
            
        # 处理读取的内容
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
                
            log_entry = parse_log_line(line)
            if log_entry:
                log_entries.append(log_entry)
        
        # 更新读取位置
        new_position = last_position + len(content.encode('utf-8'))
        
        return log_entries, new_position
    except Exception as e:
        st.error(f"读取日志文件出错: {e}")
        return [], last_position

def is_script_active(script_id: str, timeout_minutes: int = 5) -> bool:
    """检测脚本是否仍然活跃"""
    script_config = st.session_state.script_configs.get(script_id)
    
    if not script_config:
        return False
    
    # 检查文件是否存在
    log_file = script_config.get("log_file")
    if not log_file or not os.path.exists(log_file):
        return False
    
    # 检查上次更新时间
    last_update = script_config.get("last_update", datetime.min)
    if (datetime.now() - last_update).total_seconds() > timeout_minutes * 60:
        return False
    
    # 检查文件修改时间
    try:
        mtime = os.path.getmtime(log_file)
        modified_time = datetime.fromtimestamp(mtime)
        if (datetime.now() - modified_time).total_seconds() > timeout_minutes * 60:
            return False
    except:
        pass
    
    return True 