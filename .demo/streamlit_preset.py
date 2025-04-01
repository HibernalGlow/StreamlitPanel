import streamlit as st
import logging
import time
import threading
import re
import os
import psutil
from datetime import datetime
import yaml
import queue
import plotly.graph_objects as go
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union

# 设置页面配置
st.set_page_config(
    page_title="Streamlit 日志管理器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 添加自定义CSS
st.markdown("""
<style>
    .panel-header {
        font-weight: bold;
        padding: 5px;
        border-radius: 5px 5px 0 0;
        text-align: center;
    }
    .panel-container {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 5px;
        margin-bottom: 10px;
        overflow: hidden;
    }
    .panel-content {
        min-height: 100px;
        max-height: 300px;
        overflow-y: auto;
        padding: 10px;
        font-family: monospace;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 0.85em;
    }
    .system-info {
        font-family: monospace;
        padding: 5px 10px;
        background-color: #f0f2f6;
        border-radius: 5px;
        margin-top: 10px;
        display: flex;
        justify-content: space-between;
    }
    .progress-item {
        margin-bottom: 5px;
    }
    .log-line {
        margin: 2px 0;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
        padding-bottom: 2px;
    }
    .error-log {
        color: #d62728;
    }
    .warning-log {
        color: #ff7f0e;
    }
    .info-log {
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

@dataclass
class CPUInfo:
    usage: float = 0.0  # 仅保留CPU使用率

@dataclass
class DiskIOInfo:
    read_speed: float = 0.0  # 读取速度 (MB/s)
    write_speed: float = 0.0  # 写入速度 (MB/s)
    read_bytes: int = 0  # 总读取字节数
    write_bytes: int = 0  # 总写入字节数

@dataclass
class SystemStatus:
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory_usage: float = 0.0
    disk_io: DiskIOInfo = field(default_factory=DiskIOInfo)
    last_update: datetime = field(default_factory=datetime.now)

class StreamlitLogHandler(logging.Handler):
    """Streamlit日志处理器"""
    
    def __init__(self, log_file=None):
        super().__init__()
        self.path_regex = re.compile(r'([A-Za-z]:\\[^\s]+|/([^\s/]+/){2,}[^\s/]+|\S+\.[a-zA-Z0-9]+)')
        self.max_msg_length = 150
        self.max_filename_length = 40
        self.enable_truncate = False
        self.log_file = log_file
        self.last_position = 0
        self.log_queue = queue.Queue()
        
    def emit(self, record):
        """处理日志记录"""
        try:
            msg = self.format(record)
            
            # 检查是否包含面板标识符
            if not (msg.startswith('[#') or msg.startswith('[@')):
                return  # 如果没有面板标识符，直接返回不处理
            
            # 检查是否是真正的进度条（同时包含@和%）
            is_progress = '@' in msg and '%' in msg
            
            # 提取面板标签
            progress_match = re.match(r'^\[@(\w{2,})\](.*)$', msg)
            normal_match = re.match(r'^\[#(\w{2,})\](.*)$', msg)
            
            # 获取标签和内容
            panel_name = None
            content = msg
            tag = ""
            
            if progress_match:
                panel_name = progress_match.group(1)
                content = progress_match.group(2).strip()
                tag = f"[@{panel_name}]"
                log_type = "progress"
            elif normal_match:
                panel_name = normal_match.group(1)
                content = normal_match.group(2).strip()
                tag = f"[#{panel_name}]"
                log_type = "normal"
            else:
                panel_name = "update"
                log_type = "normal"
            
            # 为日志条目添加时间戳
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 根据日志级别添加图标
            if record.levelno >= logging.ERROR:
                icon = "❌"
                level = "error"
            elif record.levelno >= logging.WARNING:
                icon = "⚠️"
                level = "warning"
            else:
                icon = "ℹ️"
                level = "info"
            
            # 只在非进度条消息前添加图标
            if log_type != "progress":
                content = f"{icon} {content}"
            
            # 将日志放入队列
            self.log_queue.put({
                "panel": panel_name,
                "content": content,
                "timestamp": timestamp,
                "type": log_type,
                "level": level,
                "raw_message": msg
            })
            
        except Exception as e:
            self.handleError(record)
            
    def _check_log_file(self):
        """检查日志文件更新"""
        if not self.log_file or not os.path.exists(self.log_file):
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                if new_lines:
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            self.emit(logging.makeLogRecord({
                                'msg': line,
                                'levelno': logging.INFO,
                                'created': time.time()
                            }))
                self.last_position = f.tell()
        except Exception as e:
            print(f"Error reading log file: {e}")


class StreamlitLoggerManager:
    """Streamlit日志管理器，支持动态面板和日志劫持"""
    
    _instance = None
    _default_layout = {
        "current_stats": {"ratio": 2, "title": "📊 总体进度", "style": "yellow"},
        "current_progress": {"ratio": 2, "title": "🔄 当前进度", "style": "cyan"},
        "performance": {"ratio": 2, "title": "⚡ 性能配置", "style": "green"},
        "process": {"ratio": 3, "title": "📝 处理日志", "style": "magenta"},
        "update": {"ratio": 2, "title": "ℹ️ 更新日志", "style": "blue"}
    }
    
    @classmethod
    def set_layout(cls, layout_config=None, log_file=None):
        """设置日志布局并初始化
        
        Args:
            layout_config: 布局配置字典
            log_file: 日志文件路径
        """
        if "logger_initialized" not in st.session_state:
            # 使用默认布局或自定义布局
            final_layout = layout_config or cls._default_layout
            
            # 初始化session state变量
            st.session_state.layout_config = final_layout
            st.session_state.log_entries = {panel: [] for panel in final_layout}
            st.session_state.progress_bars = {panel: {} for panel in final_layout}
            st.session_state.system_status = SystemStatus()
            st.session_state.logger_initialized = True
            st.session_state.start_time = datetime.now()
            st.session_state.log_file = log_file
            
            # 配置根日志记录器
            root_logger = logging.getLogger()
            
            # 移除已有的StreamlitLogHandler处理器
            for handler in root_logger.handlers[:]:
                if isinstance(handler, StreamlitLogHandler):
                    root_logger.removeHandler(handler)
            
            # 添加Streamlit处理器
            handler = StreamlitLogHandler(log_file)
            handler.setFormatter(logging.Formatter('%(message)s'))
            handler.setLevel(logging.INFO)
            root_logger.addHandler(handler)
            
            # 将处理器存储到session state
            st.session_state.log_handler = handler
            
            # 启动系统状态监控线程
            threading.Thread(target=cls._monitor_system_status, daemon=True).start()
            
            # 如果提供了日志文件，设置文件监控
            if log_file:
                threading.Thread(target=cls._monitor_log_file, daemon=True).start()

    @classmethod
    def _monitor_system_status(cls):
        """监控系统状态的后台线程"""
        last_io_time = time.time()
        last_io = DiskIOInfo()
        
        try:
            while True:
                if "system_status" in st.session_state:
                    # 更新CPU和内存
                    cpu_usage = psutil.cpu_percent()
                    memory_usage = psutil.virtual_memory().percent
                    
                    # 磁盘IO
                    current_time = time.time()
                    disk_io = psutil.disk_io_counters()
                    
                    if disk_io and (current_time - last_io_time) > 0:
                        time_diff = current_time - last_io_time
                        read_speed = (disk_io.read_bytes - last_io.read_bytes) / time_diff / 1024 / 1024
                        write_speed = (disk_io.write_bytes - last_io.write_bytes) / time_diff / 1024 / 1024
                        
                        disk_io_info = DiskIOInfo(
                            read_speed=read_speed,
                            write_speed=write_speed,
                            read_bytes=disk_io.read_bytes,
                            write_bytes=disk_io.write_bytes
                        )
                        
                        last_io = disk_io_info
                        last_io_time = current_time
                    else:
                        disk_io_info = last_io
                    
                    # 更新状态
                    st.session_state.system_status = SystemStatus(
                        cpu=CPUInfo(usage=cpu_usage),
                        memory_usage=memory_usage,
                        disk_io=disk_io_info,
                        last_update=datetime.now()
                    )
                
                time.sleep(2)  # 更新频率
                
        except Exception as e:
            print(f"系统状态监控错误: {e}")

    @classmethod
    def _monitor_log_file(cls):
        """监控日志文件的后台线程"""
        if "log_handler" in st.session_state and st.session_state.log_file:
            try:
                while True:
                    st.session_state.log_handler._check_log_file()
                    time.sleep(0.1)  # 检查频率
            except Exception as e:
                print(f"日志文件监控错误: {e}")

    @classmethod
    def process_log_queue(cls):
        """处理日志队列中的消息"""
        if "log_handler" in st.session_state:
            handler = st.session_state.log_handler
            
            # 处理队列中的所有消息
            while not handler.log_queue.empty():
                try:
                    log_entry = handler.log_queue.get(block=False)
                    panel = log_entry["panel"]
                    content = log_entry["content"]
                    log_type = log_entry["type"]
                    
                    # 确保面板存在
                    if panel not in st.session_state.log_entries:
                        st.session_state.log_entries[panel] = []
                        st.session_state.progress_bars[panel] = {}
                    
                    # 根据日志类型处理
                    if log_type == "progress":
                        cls._process_progress_entry(panel, content)
                    else:
                        # 为普通日志添加时间戳
                        timestamped_content = f"[{log_entry['timestamp']}] {content}"
                        
                        # 添加到面板日志
                        st.session_state.log_entries[panel].append({
                            "content": timestamped_content,
                            "level": log_entry["level"],
                            "timestamp": log_entry["timestamp"]
                        })
                        
                        # 限制每个面板的日志条数
                        max_logs = 100
                        if len(st.session_state.log_entries[panel]) > max_logs:
                            st.session_state.log_entries[panel] = st.session_state.log_entries[panel][-max_logs:]
                    
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"处理日志错误: {e}")

    @classmethod
    def _process_progress_entry(cls, panel, content):
        """处理进度条日志条目"""
        # 定义进度条正则表达式
        PROGRESS_PATTERN = r'^([^%]*?)(?:\s*(?:(\(|\[)(\d+/\d+)[\)\]])?)?\s*(\d+(?:\.\d+)?)%$'
        
        match = re.match(PROGRESS_PATTERN, content)
        if match:
            prefix = match.group(1).strip()
            bracket_type = match.group(2)  # 括号类型 ( 或 [
            fraction = match.group(3)  # 分数部分 x/y
            percentage = float(match.group(4))  # 百分比值
            
            # 生成进度条标识符
            bar_id = prefix if prefix else f"进度条_{len(st.session_state.progress_bars[panel])}"
            
            # 格式化显示文本
            if fraction and bracket_type:
                display_text = f"{prefix} {bracket_type}{fraction}{')' if bracket_type=='(' else ']'} {percentage:.1f}%"
            else:
                display_text = f"{prefix} {percentage:.1f}%"
            
            # 更新或添加进度条
            st.session_state.progress_bars[panel][bar_id] = {
                "percentage": percentage,
                "text": display_text,
                "is_complete": percentage >= 100
            }
            
            # 移除已完成的进度条（保持较少数量的已完成进度条）
            completed_bars = [bid for bid, bar in st.session_state.progress_bars[panel].items() 
                             if bar["is_complete"]]
            
            # 保留最近的5个已完成进度条
            if len(completed_bars) > 5:
                for bar_id in completed_bars[:-5]:
                    st.session_state.progress_bars[panel].pop(bar_id, None)

def render_logger_ui():
    """渲染日志管理器界面"""
    if "logger_initialized" not in st.session_state:
        st.warning("请先调用 StreamlitLoggerManager.set_layout() 初始化日志管理器")
        return
    
    # 处理日志队列中的消息
    StreamlitLoggerManager.process_log_queue()
    
    # 显示运行时间和系统状态
    elapsed = datetime.now() - st.session_state.start_time
    hours, remainder = divmod(elapsed.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    status = st.session_state.system_status
    
    # 顶部状态栏
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"**运行时间:** {time_str}")
    with col2:
        st.markdown(f"**CPU:** {status.cpu.usage:.1f}%")
    with col3:
        st.markdown(f"**内存:** {status.memory_usage:.1f}%")
    with col4:
        st.markdown(f"**磁盘IO:** R:{status.disk_io.read_speed:.1f}MB/s W:{status.disk_io.write_speed:.1f}MB/s")
    
    # 创建所有面板的组合视图
    layout_config = st.session_state.layout_config
    
    # 计算布局
    panels_by_row = {}
    current_row = []
    total_ratio = 0
    
    # 按照ratio将面板分组到不同行
    for panel_name, config in layout_config.items():
        ratio = config.get("ratio", 1)
        if total_ratio + ratio > 12:  # 每行最大容纳12个单位
            panels_by_row[len(panels_by_row)] = current_row
            current_row = [(panel_name, config)]
            total_ratio = ratio
        else:
            current_row.append((panel_name, config))
            total_ratio += ratio
    
    # 添加最后一行
    if current_row:
        panels_by_row[len(panels_by_row)] = current_row
    
    # 渲染每一行的面板
    for row_idx, panels in panels_by_row.items():
        # 计算每个面板的列宽
        total_ratio = sum(config.get("ratio", 1) for _, config in panels)
        cols = st.columns([config.get("ratio", 1) / total_ratio for _, config in panels])
        
        # 在每列中渲染对应的面板
        for i, (panel_name, config) in enumerate(panels):
            with cols[i]:
                render_panel(panel_name, config)
    
    # 定期刷新界面
    st.empty()
    time.sleep(0.1)
    st.experimental_rerun()

def render_panel(panel_name, config):
    """渲染单个日志面板"""
    title = config.get("title", panel_name)
    style = config.get("style", "blue")
    
    # 将style转换为颜色
    color_map = {
        "yellow": "#ffc107",
        "cyan": "#17a2b8",
        "magenta": "#e83e8c",
        "blue": "#007bff",
        "green": "#28a745",
        "red": "#dc3545",
        "lightblue": "#63c5da",
        "lightgreen": "#90ee90",
        "lightcyan": "#e0ffff",
        "lightmagenta": "#f8bbd0",
        "lightyellow": "#ffffe0",
        "white": "#ffffff",
        "light_gray": "#d3d3d3",
        "dark_gray": "#a9a9a9"
    }
    
    color = color_map.get(style, "#007bff")
    
    # 面板容器
    st.markdown(f"""
    <div class="panel-container">
        <div class="panel-header" style="background-color: {color}; color: white;">
            {title}
        </div>
        <div id="panel-{panel_name}">
    """, unsafe_allow_html=True)
    
    # 渲染进度条
    if panel_name in st.session_state.progress_bars:
        progress_bars = st.session_state.progress_bars[panel_name]
        
        for bar_id, bar_info in list(progress_bars.items()):
            percentage = bar_info["percentage"]
            text = bar_info["text"]
            
            progress_container = st.container()
            with progress_container:
                st.progress(min(percentage / 100, 1.0))
                st.caption(text)
    
    # 渲染日志内容
    if panel_name in st.session_state.log_entries:
        logs = st.session_state.log_entries[panel_name]
        
        log_content = ""
        for log in reversed(logs):  # 最新的日志在顶部
            level_class = f"{log['level']}-log"
            log_content += f'<div class="log-line {level_class}">{log["content"]}</div>'
        
        st.markdown(f"""
        <div class="panel-content">
            {log_content}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

# 使用示例
if __name__ == "__main__":
    # 设置布局
    StreamlitLoggerManager.set_layout({
        "system": {"title": "🖥️ 系统状态", "style": "lightgreen", "ratio": 3},
        "error": {"title": "❌ 错误检查", "style": "red", "ratio": 3},
        "info": {"title": "ℹ️ 信息日志", "style": "lightblue", "ratio": 6},
    })
    
    # 渲染日志界面
    render_logger_ui()
    
    # 如果需要在后台线程中发送日志
    def send_demo_logs():
        """演示日志功能"""
        import random
        import logging
        
        logger = logging.getLogger()
        
        # 等待初始化完成
        time.sleep(1)
        
        while True:
            # 系统面板消息
            logger.info(f"[#system]当前CPU温度: {random.randint(40, 70)}°C")
            
            # 错误面板消息
            if random.random() < 0.2:  # 20%概率产生错误
                logger.error(f"[#error]服务{random.randint(1, 5)}无响应")
            
            # 信息面板消息
            logger.info(f"[#info]用户{random.randint(1000, 9999)}登录成功")
            
            # 进度条消息
            if random.random() < 0.3:  # 30%概率更新进度
                progress = random.randint(0, 100)
                logger.info(f"[@system]系统更新 {progress}%")
                logger.info(f"[@error]错误检查 ({random.randint(0, 10)}/10) {progress}%")
                logger.info(f"[@info]数据同步 [{random.randint(0, 100)}/100] {progress}%")
            
            time.sleep(0.5)
    
    # 启动demo日志线程
    import threading
    demo_thread = threading.Thread(target=send_demo_logs, daemon=True)
    demo_thread.start()