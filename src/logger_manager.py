import streamlit as st
import os
import time
from datetime import datetime
import json
from typing import Dict, List, Optional
import psutil

from src.components.script_dashboard import ScriptDashboard
from src.utils.file_utils import read_log_file, is_script_active
from src.utils.log_parser import parse_progress

class StreamlitLoggerManager:
    """Streamlit日志管理器"""
    
    _default_layout = {
        "status": {"title": "📊 总体进度", "style": "lightyellow", "icon": "✅"},
        "progress": {"title": "🔄 当前进度", "style": "lightcyan", "icon": "🔄"},
        "performance": {"title": "⚡ 性能配置", "style": "lightgreen", "icon": "⚡"},
        "image_convert": {"title": "🖼️ 图片转换", "style": "lightorange", "icon": "🖼️"},
        "archive_ops": {"title": "📦 压缩包处理", "style": "lightmagenta", "icon": "📦"},
        "file_ops": {"title": "📁 文件操作", "style": "lightblue", "icon": "📁"}
    }
    
    _running_scripts = {}
    _config_dir = None
    _dashboards = {}
    
    @staticmethod
    def set_layout(layout_config=None, log_file=None):
        """设置日志布局并初始化"""
        script_id = os.path.basename(os.path.dirname(log_file))
        script_name = os.path.basename(log_file).split('.')[0]
        
        # 创建脚本仪表板
        if script_id not in StreamlitLoggerManager._dashboards:
            dashboard = ScriptDashboard(script_name)
            StreamlitLoggerManager._dashboards[script_id] = dashboard
            
            # 添加默认面板
            for panel_id, config in (layout_config or StreamlitLoggerManager._default_layout).items():
                dashboard.add_log_panel(
                    panel_id,
                    config["title"],
                    config["icon"],
                    config["style"]
                )
        
        # 保存配置到session_state
        if not hasattr(st.session_state, "script_configs"):
            st.session_state.script_configs = {}
        
        # 使用默认布局或自定义布局
        final_layout = layout_config or StreamlitLoggerManager._default_layout
        
        # 保存脚本配置
        st.session_state.script_configs[script_id] = {
            "layout": final_layout,
            "log_file": log_file,
            "script_name": script_name,
            "last_position": 0,
            "last_update": datetime.now(),
            "start_time": datetime.now()
        }
        
        # 记录运行中的脚本
        StreamlitLoggerManager._running_scripts[script_id] = {
            "log_file": log_file,
            "last_check": datetime.now()
        }
        
        return log_file

    @staticmethod
    def _update_dashboard(script_id: str, log_entries: List[dict]):
        """更新仪表板内容"""
        if script_id not in StreamlitLoggerManager._dashboards:
            return
            
        dashboard = StreamlitLoggerManager._dashboards[script_id]
        
        # 更新系统状态
        try:
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            dashboard.system_panel.update_stats(
                cpu=cpu_usage,
                memory=memory.percent,
                disk_io={
                    "read": disk_io.read_bytes / 1024 / 1024,
                    "write": disk_io.write_bytes / 1024 / 1024
                }
            )
        except:
            pass
        
        # 更新日志面板
        for entry in log_entries:
            panel_name = entry["panel_name"]
            panel_type = entry["panel_type"]
            content = entry["content"]
            
            if panel_name in dashboard.dashboard_manager.panels:
                panel = dashboard.dashboard_manager.panels[panel_name]
                from src.panels.log_panel import LogPanel
                if isinstance(panel, LogPanel):
                    if panel_type == "@":  # 进度条
                        progress_info = parse_progress(content)
                        if progress_info:
                            panel.update_progress(progress_info.get("prefix", "进度"), progress_info)
                    else:  # 普通日志
                        panel.add_log({
                            "level": entry["level"],
                            "timestamp": entry["timestamp"].split(' ')[1].split(',')[0],
                            "content": content
                        })

    @staticmethod
    def _render_dashboard(script_id: str, container):
        """渲染仪表板"""
        if script_id not in StreamlitLoggerManager._dashboards:
            return
            
        dashboard = StreamlitLoggerManager._dashboards[script_id]
        dashboard.render(container) 