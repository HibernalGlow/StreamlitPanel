import streamlit as st
import re
import os
import time
import psutil
from datetime import datetime
import threading
import logging
import subprocess
from typing import Dict, List, Optional, Set, Any
import platform
import json
import hashlib
import socket
import webbrowser
from abc import ABC, abstractmethod

# 设置页面配置
st.set_page_config(
    page_title="多脚本日志监控",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 添加一些基本样式
st.markdown("""
<style>
    .stProgress > div > div {
        background-color: #a6e3a1 !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    div[data-testid="stExpander"] {
        background-color: #1e1e2e;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        max-height: calc(100vh - 200px);
        overflow-y: auto;
    }
    
    .green-text {
        color: #a6e3a1;
    }
    
    .yellow-text {
        color: #f9e2af;
    }
    
    .red-text {
        color: #f38ba8;
    }
    
    .progress-text {
        font-family: monospace;
        margin-top: -16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 固定端口号
DEFAULT_PORT = 8501

# 检查端口是否已被占用
def is_port_in_use(port: int) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class BasePanel(ABC):
    """基础面板类"""
    def __init__(self, title: str, icon: str = "", style: str = "default"):
        self.title = title
        self.icon = icon
        self.style = style
        self.is_visible = True
        self.is_expanded = True
        
    @abstractmethod
    def render(self, container):
        """渲染面板内容"""
        pass
    
    def toggle_visibility(self):
        """切换面板可见性"""
        self.is_visible = not self.is_visible
    
    def toggle_expansion(self):
        """切换面板展开状态"""
        self.is_expanded = not self.is_expanded

class LogPanel(BasePanel):
    """日志面板类"""
    def __init__(self, title: str, icon: str = "", style: str = "default"):
        super().__init__(title, icon, style)
        self.logs = []
        self.progress_bars = {}
        
    def add_log(self, log_entry: dict):
        """添加日志条目"""
        self.logs.append(log_entry)
        # 限制日志数量
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
    
    def update_progress(self, progress_id: str, progress_info: dict):
        """更新进度条"""
        self.progress_bars[progress_id] = progress_info
    
    def render(self, container):
        if not self.is_visible:
            return
            
        with container:
            # 创建可折叠区域
            with st.expander(f"{self.icon} {self.title}", expanded=self.is_expanded):
                # 渲染进度条
                for progress_id, progress_info in self.progress_bars.items():
                    percentage = progress_info.get("percentage", 0)
                    text = progress_info.get("text", "")
                    
                    st.progress(min(percentage / 100, 1.0))
                    st.caption(text)
                
                # 渲染日志
                for log in reversed(self.logs):
                    level = log.get("level", "info")
                    timestamp = log.get("timestamp", "")
                    content = log.get("content", "")
                    
                    if level == "error":
                        st.markdown(f'<p class="red-text">❌ [{timestamp}] {content}</p>', unsafe_allow_html=True)
                    elif level == "warning":
                        st.markdown(f'<p class="yellow-text">⚠️ [{timestamp}] {content}</p>', unsafe_allow_html=True)
                    else:
                        st.write(f"ℹ️ [{timestamp}] {content}")

class SystemPanel(BasePanel):
    """系统状态面板类"""
    def __init__(self, title: str = "系统状态", icon: str = "🖥️", style: str = "lightgreen"):
        super().__init__(title, icon, style)
        self.cpu_usage = 0
        self.memory_usage = 0
        self.disk_io = {"read": 0, "write": 0}
        
    def update_stats(self, cpu: float, memory: float, disk_io: dict):
        """更新系统状态"""
        self.cpu_usage = cpu
        self.memory_usage = memory
        self.disk_io = disk_io
    
    def render(self, container):
        if not self.is_visible:
            return
            
        with container:
            with st.expander(f"{self.icon} {self.title}", expanded=self.is_expanded):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CPU使用率", f"{self.cpu_usage:.1f}%")
                    st.metric("内存使用率", f"{self.memory_usage:.1f}%")
                with col2:
                    st.metric("磁盘读取", f"{self.disk_io['read']:.1f}MB/s")
                    st.metric("磁盘写入", f"{self.disk_io['write']:.1f}MB/s")

class PresetPanel(BasePanel):
    """预设面板类"""
    def __init__(self, title: str = "预设配置", icon: str = "⚙️", style: str = "lightblue"):
        super().__init__(title, icon, style)
        self.is_visible = False  # 默认隐藏
        self.presets = {
            "低配模式": {"threads": 1, "batch": 1},
            "中配模式": {"threads": 8, "batch": 8},
            "高配模式": {"threads": 16, "batch": 16}
        }
        
    def render(self, container):
        if not self.is_visible:
            return
            
        with container:
            with st.expander(f"{self.icon} {self.title}", expanded=self.is_expanded):
                # 创建三列布局
                cols = st.columns(3)
                
                # 在每个列中添加预设按钮
                for i, (preset_name, config) in enumerate(self.presets.items()):
                    with cols[i]:
                        if st.button(preset_name, key=f"preset_{preset_name}"):
                            # 更新性能配置
                            self._update_performance_config(config)
                            st.success(f"已切换到{preset_name}")
                
                # 添加自定义配置
                st.subheader("自定义配置")
                custom_threads = st.slider("线程数", 1, 16, 1)
                custom_batch = st.slider("批处理大小", 1, 100, 1)
                
                if st.button("应用自定义配置"):
                    self._update_performance_config({
                        "threads": custom_threads,
                        "batch": custom_batch
                    })
                    st.success("已应用自定义配置")
    
    def _update_performance_config(self, config):
        """更新性能配置"""
        try:
            # 这里可以添加与performance_config.py的交互逻辑
            pass
        except Exception as e:
            st.error(f"更新配置失败: {e}")

class PerformancePanel(BasePanel):
    """性能配置面板类"""
    def __init__(self, title: str = "性能配置", icon: str = "⚡", style: str = "lightgreen"):
        super().__init__(title, icon, style)
        self.is_visible = False  # 默认隐藏
        
    def render(self, container):
        if not self.is_visible:
            return
            
        with container:
            with st.expander(f"{self.icon} {self.title}", expanded=self.is_expanded):
                # 这里可以添加与performance_config.py的交互逻辑
                st.info("性能配置面板已加载")

class DashboardManager:
    """仪表板管理器类"""
    def __init__(self):
        self.panels = {}
        self.columns_per_row = 2
        self.is_visible = True
        
    def add_panel(self, panel_id: str, panel: BasePanel):
        """添加面板"""
        self.panels[panel_id] = panel
    
    def remove_panel(self, panel_id: str):
        """移除面板"""
        if panel_id in self.panels:
            del self.panels[panel_id]
    
    def set_columns_per_row(self, columns: int):
        """设置每行显示的面板数"""
        self.columns_per_row = max(1, min(columns, 4))
    
    def toggle_visibility(self):
        """切换仪表板可见性"""
        self.is_visible = not self.is_visible
    
    def render(self, container):
        """渲染仪表板"""
        if not self.is_visible:
            return
            
        with container:
            # 创建面板网格
            visible_panels = [p for p in self.panels.values() if p.is_visible]
            for i in range(0, len(visible_panels), self.columns_per_row):
                row_panels = visible_panels[i:i + self.columns_per_row]
                cols = st.columns(len(row_panels))
                
                for j, panel in enumerate(row_panels):
                    with cols[j]:
                        panel.render(st.container())

class ScriptDashboard:
    """脚本仪表板类"""
    def __init__(self, script_name: str):
        self.script_name = script_name
        self.start_time = datetime.now()
        self.dashboard_manager = DashboardManager()
        self.is_visible = True
        
        # 初始化基础面板
        self.system_panel = SystemPanel()
        self.dashboard_manager.add_panel("system", self.system_panel)
        
        # 初始化预设和性能面板
        self.preset_panel = PresetPanel()
        self.performance_panel = PerformancePanel()
        self.dashboard_manager.add_panel("preset", self.preset_panel)
        self.dashboard_manager.add_panel("performance", self.performance_panel)
        
    def add_log_panel(self, panel_id: str, title: str, icon: str = "", style: str = "default"):
        """添加日志面板"""
        panel = LogPanel(title, icon, style)
        self.dashboard_manager.add_panel(panel_id, panel)
        return panel
    
    def toggle_visibility(self):
        """切换仪表板可见性"""
        self.is_visible = not self.is_visible
    
    def render(self, container):
        """渲染脚本仪表板"""
        if not self.is_visible:
            return
            
        with container:
            # 显示运行时间
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            
            st.subheader(f"{self.script_name} - 运行时间: {time_str}")
            
            # 添加预设和性能面板的可见性控制
            col1, col2 = st.columns(2)
            with col1:
                self.preset_panel.is_visible = st.checkbox("显示预设配置", value=False)
            with col2:
                self.performance_panel.is_visible = st.checkbox("显示性能配置", value=False)
            
            # 渲染仪表板
            self.dashboard_manager.render(st.container())

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
    _streamlit_process = None
    _config_dir = None
    _last_browser_open = None
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
        if "script_configs" not in st.session_state:
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

# 解析日志行
def parse_log_line(line: str) -> Optional[dict]:
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

# 解析进度信息
def parse_progress(content: str) -> Optional[dict]:
    """解析进度条信息"""
    # 匹配进度百分比: 进度 50%
    progress_match = re.match(r'(.*?)(\d+(?:\.\d+)?)%$', content)
    
    if progress_match:
        prefix, percentage = progress_match.groups()
        return {
            "prefix": prefix.strip(),
            "percentage": float(percentage),
            "is_complete": float(percentage) >= 100.0
        }
    
    # 匹配分数形式进度: (1/10) 10%
    fraction_match = re.match(r'(.*?)(?:\((\d+)/(\d+)\)).*?(\d+(?:\.\d+)?)%$', content)
    
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
        
    # 匹配方括号形式进度: [1/10] 10%
    bracket_match = re.match(r'(.*?)(?:\[(\d+)/(\d+)\]).*?(\d+(?:\.\d+)?)%$', content)
    
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
    
    return None

# 读取日志文件
def read_log_file(log_file: str, last_position: int = 0) -> (List[dict], int):
    """读取日志文件并返回解析后的日志条目和新位置"""
    if not os.path.exists(log_file):
        return [], last_position
    
    try:
        log_entries = []
        new_position = last_position
        
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            # 定位到上次读取位置
            f.seek(last_position)
            
            # 读取新内容
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                log_entry = parse_log_line(line)
                if log_entry:
                    log_entries.append(log_entry)
            
            # 更新读取位置
            new_position = f.tell()
        
        return log_entries, new_position
    except Exception as e:
        st.error(f"读取日志文件出错: {e}")
        return [], last_position

# 检测脚本是否仍在运行
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

# 主应用入口
def main():
    """主应用入口点"""
    st.title("多脚本实时日志监控")
    
    # 初始化会话状态
    if "script_configs" not in st.session_state:
        st.session_state.script_configs = {}
    if "columns_per_row" not in st.session_state:
        st.session_state.columns_per_row = 2
    
    # 侧边栏控制
    st.sidebar.title("设置")
    
    # 布局控制
    st.sidebar.subheader("布局设置")
    columns = st.sidebar.slider("每行显示面板数", 1, 4, st.session_state.columns_per_row)
    st.session_state.columns_per_row = columns
    
    # 刷新间隔
    refresh_interval = st.sidebar.slider("刷新间隔 (秒)", 1, 5, 1)
    
    # 添加强制重新加载配置的开关
    force_reload = st.sidebar.checkbox("强制重新加载配置", value=False, 
                                       help="启用此选项将在每次刷新时重新读取所有配置文件")
    if force_reload and "force_reload_timestamp" not in st.session_state:
        st.session_state.force_reload_timestamp = time.time()
    elif not force_reload and "force_reload_timestamp" in st.session_state:
        del st.session_state.force_reload_timestamp
    
    # 清除缓存按钮
    if st.sidebar.button("清除缓存"):
        st.session_state.script_configs = {}
        StreamlitLoggerManager._dashboards.clear()
        st.sidebar.success("已清除缓存")
    
    # 显示使用说明
    with st.sidebar.expander("使用说明"):
        st.markdown("""
        ### 日志格式说明
        - 普通日志：`[#面板名]日志内容`
        - 进度条：`[@面板名]任务名 百分比%`
        - 分数进度：`[@面板名]任务名 (当前/总数) 百分比%`
        
        ### 特性
        - 自动将开头相同的日志合并为一行
        - 每个脚本使用单独的选项卡
        - 脚本不活跃后会自动关闭选项卡
        - 固定端口运行，便于访问
        - 强制重新加载配置可以解决切换脚本问题
        """)
    
    # 处理命令行参数
    import sys
    
    if len(sys.argv) > 1:
        config_dir = sys.argv[1]
        
        # 如果启用了强制重新加载，则清除配置
        if "force_reload_timestamp" in st.session_state:
            current_time = time.time()
            if current_time - st.session_state.force_reload_timestamp > 5:
                st.session_state.script_configs = {}
                StreamlitLoggerManager._dashboards.clear()
                st.session_state.force_reload_timestamp = current_time
        
        # 监控所有脚本日志文件
        active_scripts = []
        
        # 从配置目录加载脚本
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith('.json'):
                    script_id = file.split('.')[0]
                    
                    # 读取配置文件
                    config_file = os.path.join(config_dir, file)
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                        
                        log_file = config.get("log_file", "")
                        
                        # 检查日志文件是否存在
                        if not log_file or not os.path.exists(log_file):
                            continue
                            
                        # 初始化脚本配置
                        if script_id not in st.session_state.script_configs:
                            StreamlitLoggerManager.set_layout(config.get("layout"), log_file)
                            
                    except Exception as e:
                        st.error(f"读取配置文件出错: {e}")
                        continue
        
        # 更新所有脚本的日志
        for script_id, script_config in list(st.session_state.script_configs.items()):
            log_file = script_config.get("log_file", "")
            
            if log_file and os.path.exists(log_file):
                # 读取日志文件
                last_position = script_config.get("last_position", 0)
                log_entries, new_position = read_log_file(log_file, last_position)
                
                # 更新位置
                script_config["last_position"] = new_position
                
                # 处理日志条目
                if log_entries:
                    StreamlitLoggerManager._update_dashboard(script_id, log_entries)
                    script_config["last_update"] = datetime.now()
                
                # 检查脚本是否活跃
                if is_script_active(script_id):
                    active_scripts.append(script_id)
        
        # 创建选项卡
        if active_scripts:
            # 为每个活跃脚本创建一个选项卡，按照脚本名称排序
            sorted_scripts = sorted(active_scripts, 
                                   key=lambda s: st.session_state.script_configs[s].get("script_name", s))
            
            # 生成带时间戳的页签名称
            tab_names = []
            for script_id in sorted_scripts:
                script_config = st.session_state.script_configs[script_id]
                script_name = script_config.get("script_name", script_id)
                start_time = script_config.get("start_time", datetime.now())
                time_str = start_time.strftime("%H:%M:%S")
                tab_names.append(f"{script_name}@{time_str}")
            
            tabs = st.tabs(tab_names)
            
            # 在每个选项卡中渲染对应脚本的内容
            for i, script_id in enumerate(sorted_scripts):
                with tabs[i]:
                    # 设置每行显示的面板数
                    if script_id in StreamlitLoggerManager._dashboards:
                        StreamlitLoggerManager._dashboards[script_id].dashboard_manager.set_columns_per_row(
                            st.session_state.columns_per_row
                        )
                    
                    # 渲染仪表板
                    StreamlitLoggerManager._render_dashboard(script_id, st.container())
        else:
            st.info("没有活跃的脚本日志")
        
        # 自动刷新
        time.sleep(refresh_interval)
        st.rerun()
    else:
        st.warning("请提供配置目录路径")

if __name__ == "__main__":
    main()