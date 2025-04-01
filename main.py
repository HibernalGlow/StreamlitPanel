import streamlit as st
import os
import time
import sys
import psutil
import threading
import random
import logging
import tempfile
from datetime import datetime

from src.utils.file_utils import read_log_file, is_script_active
from src.logger_manager import StreamlitLoggerManager

# 脚本信息全局变量
SCRIPTS_INFO = {}

# 定义默认布局配置
STREAMLIT_LAYOUT = {
    "status": {"title": "📊 总体进度", "style": "lightyellow", "icon": "✅"},
    "progress": {"title": "🔄 当前进度", "style": "lightcyan", "icon": "🔄"},
    "performance": {"title": "⚡ 性能配置", "style": "lightgreen", "icon": "⚡"},
    "image_convert": {"title": "🖼️ 图片转换", "style": "lightorange", "icon": "🖼️"},
    "archive_ops": {"title": "📦 压缩包处理", "style": "lightmagenta", "icon": "📦"},
    "file_ops": {"title": "📁 文件操作", "style": "lightblue", "icon": "📁"}
}

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

def register_script(script_info):
    """注册脚本信息
    
    Args:
        script_info: 包含脚本信息的字典，必须包含script_id和log_file字段
    """
    if 'script_id' not in script_info or 'log_file' not in script_info:
        return False
    
    script_id = script_info['script_id']
    log_file = script_info['log_file']
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file):
        return False
    
    # 注册脚本信息
    SCRIPTS_INFO[script_id] = script_info
    
    # 检查是否在Streamlit环境中运行
    try:
        # 初始化脚本配置
        if "script_configs" in st.session_state and script_id not in st.session_state.script_configs:
            layout = script_info.get('layout', STREAMLIT_LAYOUT)
            StreamlitLoggerManager.set_layout(log_file=log_file, layout_config=layout)
            st.session_state.script_configs[script_id] = {
                "script_id": script_id,
                "script_name": script_info.get('script_name', script_id),
                "log_file": log_file,
                "start_time": datetime.now(),
                "last_position": 0
            }
    except:
        # 非Streamlit环境，只保存脚本信息
        pass
    
    return True

# 添加自动日志生成功能
def generate_demo_logs(script_id, log_file, duration=3600):
    """生成演示日志"""
    # 设置日志记录器
    logger = logging.getLogger(script_id)
    
    # 移除所有已有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # 记录开始信息
    logger.info(f"[#status]自动演示脚本 {script_id} 已启动")
    
    # 启动进度模拟线程
    threads = []
    stop_event = threading.Event()
    
    # 文件处理进度
    t1 = threading.Thread(
        target=simulate_progress, 
        args=(logger, "file_ops", "文件处理", 50, 3, 8, stop_event),
        daemon=True
    )
    threads.append(t1)
    
    # 图片转换进度
    t2 = threading.Thread(
        target=simulate_progress, 
        args=(logger, "image_convert", "图片转换", 80, 2, 5, stop_event),
        daemon=True
    )
    threads.append(t2)
    
    # 压缩包处理进度
    t3 = threading.Thread(
        target=simulate_progress, 
        args=(logger, "archive_ops", "压缩文件处理", 30, 5, 10, stop_event),
        daemon=True
    )
    threads.append(t3)
    
    # 性能信息线程
    t4 = threading.Thread(
        target=log_performance,
        args=(logger, stop_event),
        daemon=True
    )
    threads.append(t4)
    
    # 启动所有线程
    for t in threads:
        t.start()
    
    # 主循环，生成随机状态信息
    start_time = time.time()
    while (time.time() - start_time) < duration and not stop_event.is_set():
        log_status(logger)
        time.sleep(random.uniform(1, 3))
    
    # 等待所有线程结束
    stop_event.set()
    for t in threads:
        t.join(timeout=1.0)
    
    logger.info(f"[#status]自动演示脚本 {script_id} 已结束")

def simulate_progress(logger, panel, task_name, total, min_delay, max_delay, stop_event):
    """模拟进度更新"""
    for i in range(1, total + 1):
        if stop_event.is_set():
            break
            
        percentage = (i / total) * 100
        
        # 记录进度
        logger.info(f"[@{panel}]{task_name} [{i}/{total}] {percentage:.1f}%")
        
        # 随机添加一些详细日志
        if random.random() < 0.3:
            logger.info(f"[#{panel}]处理项目 {i}: {task_name}_{i}")
        
        # 随机添加警告或错误
        if random.random() < 0.1:
            if random.random() < 0.3:
                logger.error(f"[#{panel}]处理 {task_name}_{i} 时发生错误")
            else:
                logger.warning(f"[#{panel}]处理 {task_name}_{i} 有潜在问题")
        
        # 随机延迟
        time.sleep(random.uniform(min_delay, max_delay))

def log_performance(logger, stop_event):
    """记录性能信息"""
    while not stop_event.is_set():
        cpu = random.uniform(10, 95)
        memory = random.uniform(100, 500)
        
        logger.info(f"[#performance]CPU使用率: {cpu:.1f}%")
        logger.info(f"[#performance]内存占用: {memory:.1f} MB")
        
        time.sleep(5)

def log_status(logger):
    """记录状态信息"""
    statuses = [
        f"[#status]当前处理批次: {random.randint(1, 100)}",
        f"[#status]已完成任务数: {random.randint(10, 500)}",
        f"[#status]累计处理文件: {random.randint(100, 1000)}个",
        f"[#progress]总体进度: {random.uniform(0, 100):.1f}%",
        f"[#progress]任务队列: {random.randint(0, 50)}个待处理",
        f"[#progress]已分析文件数: {random.randint(10, 200)}个"
    ]
    
    logger.info(random.choice(statuses))

def start_demo_script():
    """启动演示脚本"""
    # 创建临时日志目录
    log_dir = tempfile.mkdtemp(prefix="streamlit_demo_")
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建演示脚本
    for i in range(1, 5):  # 创建4个演示脚本
        script_id = f"demo_{i}"
        script_name = f"演示脚本 {i}"
        log_file = os.path.join(log_dir, f"{script_id}.log")
        
        # 创建日志文件
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")
        
        # 注册脚本
        script_info = {
            'script_id': script_id,
            'script_name': script_name,
            'log_file': log_file,
            'layout': STREAMLIT_LAYOUT
        }
        register_script(script_info)
        
        # 启动日志生成线程
        thread = threading.Thread(
            target=generate_demo_logs,
            args=(script_id, log_file, 3600),  # 运行1小时
            daemon=True
        )
        thread.start()

def main():
    """主应用入口点"""
    st.title("多脚本实时日志监控")
    
    # 初始化会话状态
    if not hasattr(st.session_state, "script_configs"):
        st.session_state.script_configs = {}
    if not hasattr(st.session_state, "columns_per_row"):
        st.session_state.columns_per_row = 2
    if not hasattr(st.session_state, "demo_started"):
        st.session_state.demo_started = False
    if not hasattr(st.session_state, "show_system_info"):
        st.session_state.show_system_info = False
    
    # 启动演示脚本
    if not st.session_state.demo_started:
        start_demo_script()
        st.session_state.demo_started = True
    
    # 从SCRIPTS_INFO加载脚本信息
    for script_id, script_info in SCRIPTS_INFO.items():
        if script_id not in st.session_state.script_configs:
            log_file = script_info.get("log_file")
            if log_file and os.path.exists(log_file):
                layout = script_info.get('layout', STREAMLIT_LAYOUT)
                StreamlitLoggerManager.set_layout(log_file=log_file, layout_config=layout)
                st.session_state.script_configs[script_id] = {
                    "script_id": script_id,
                    "script_name": script_info.get('script_name', script_id),
                    "log_file": log_file,
                    "start_time": datetime.now(),
                    "last_position": 0
                }
    
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
    if force_reload and not hasattr(st.session_state, "force_reload_timestamp"):
        st.session_state.force_reload_timestamp = time.time()
    elif not force_reload and hasattr(st.session_state, "force_reload_timestamp"):
        delattr(st.session_state, "force_reload_timestamp")
    
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
    
    # 监控所有脚本日志文件
    active_scripts = []
    
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
        # 添加全局系统状态面板
        with st.expander("系统状态概览", expanded=st.session_state.show_system_info):
            # 系统状态概览
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("活跃脚本数", len(active_scripts))
            
            with col2:
                cpu_usage = psutil.cpu_percent()
                st.metric("CPU使用率", f"{cpu_usage:.1f}%")
            
            with col3:
                memory = psutil.virtual_memory()
                st.metric("内存使用率", f"{memory.percent:.1f}%")
            
            with col4:
                # 切换系统信息展开状态的按钮
                if st.button("默认" + ("折叠" if st.session_state.show_system_info else "展开")):
                    st.session_state.show_system_info = not st.session_state.show_system_info
                    st.experimental_rerun()
            
            # 分隔线
            st.divider()
            
            # 磁盘信息
            st.subheader("磁盘使用情况")
            disk_cols = st.columns(4)
            disks = []
            
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    disks.append({
                        "device": disk.device,
                        "mountpoint": disk.mountpoint,
                        "fstype": disk.fstype,
                        "total": usage.total / (1024 * 1024 * 1024),  # GB
                        "used": usage.used / (1024 * 1024 * 1024),    # GB
                        "percent": usage.percent
                    })
                except:
                    pass
            
            for i, disk in enumerate(disks[:4]):  # 显示前4个磁盘
                with disk_cols[i % 4]:
                    st.metric(
                        f"{disk['mountpoint']} ({disk['fstype']})",
                        f"{disk['percent']}%",
                        f"{disk['used']:.1f}/{disk['total']:.1f} GB"
                    )
            
            # 脚本情况摘要
            st.subheader("脚本情况摘要")
            script_summary_cols = st.columns(len(active_scripts))
            
            for i, script_id in enumerate(sorted(active_scripts, 
                               key=lambda s: st.session_state.script_configs[s].get("script_name", s))):
                script_config = st.session_state.script_configs[script_id]
                script_name = script_config.get("script_name", script_id)
                start_time = script_config.get("start_time", datetime.now())
                running_time = (datetime.now() - start_time).total_seconds() / 60
                
                with script_summary_cols[i]:
                    st.metric(
                        script_name,
                        f"运行 {running_time:.1f} 分钟",
                        f"上次更新: {datetime.now().strftime('%H:%M:%S')}"
                    )
        
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
        st.info("没有活跃的脚本日志，请先运行demo.py生成日志")
        st.markdown("""
        ### 使用方法：
        1. 运行 `python demo.py --count 1 --duration 60` 生成日志
        2. 启动应用 `streamlit run main.py`
        
        ### 或者直接注册脚本：
        ```python
        from main import register_script
        
        script_info = {
            'script_id': '脚本ID',
            'script_name': '脚本名称',
            'log_file': '日志文件路径'
        }
        
        register_script(script_info)
        ```        """)
    
    # 自动刷新
    time.sleep(refresh_interval)
    st.rerun()

if __name__ == "__main__":
    main() 
