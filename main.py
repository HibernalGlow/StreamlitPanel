import streamlit as st
import os
import time
import sys
import psutil
from datetime import datetime
import json

from src.utils.file_utils import read_log_file, is_script_active
from src.logger_manager import StreamlitLoggerManager

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