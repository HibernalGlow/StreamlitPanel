import streamlit as st
from src.components.base_panel import BasePanel
import importlib
import os
import sys

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
                try:
                    # 尝试动态导入performance_config模块
                    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
                    if root_path not in sys.path:
                        sys.path.append(root_path)
                    
                    # 导入性能配置模块
                    try:
                        perf_config = importlib.import_module("config.performance_config")
                        
                        # 显示当前配置信息
                        st.subheader("当前性能配置")
                        st.write(f"线程数: {perf_config.get_thread_count()}")
                        st.write(f"批处理大小: {perf_config.get_batch_size()}")
                        
                        # 添加交互控件
                        if st.button("打开性能配置界面"):
                            # 启动性能配置GUI
                            try:
                                ConfigGUI = getattr(perf_config, "ConfigGUI", None)
                                if ConfigGUI:
                                    st.info("正在启动性能配置界面...")
                                    # 在新线程中启动GUI
                                    import threading
                                    gui_thread = threading.Thread(target=lambda: ConfigGUI().run())
                                    gui_thread.daemon = True
                                    gui_thread.start()
                                else:
                                    st.warning("性能配置模块缺少ConfigGUI类")
                            except Exception as e:
                                st.error(f"启动GUI失败: {str(e)}")
                    except ImportError:
                        st.warning("找不到性能配置模块 (config.performance_config)")
                except Exception as e:
                    st.error(f"性能配置面板错误: {str(e)}") 