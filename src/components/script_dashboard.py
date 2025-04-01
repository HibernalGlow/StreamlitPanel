import streamlit as st
from datetime import datetime
from typing import Optional

from src.components.dashboard_manager import DashboardManager
from src.panels.system_panel import SystemPanel
from src.panels.preset_panel import PresetPanel
from src.panels.performance_panel import PerformancePanel
from src.panels.log_panel import LogPanel

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
        
    def add_log_panel(self, panel_id: str, title: str, icon: str = "", style: str = "default") -> LogPanel:
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
            
            # 显示标题和运行时间
            st.subheader(f"{self.script_name} - 运行时间: {time_str}")
            
            # 顶部可扩展区域，包含配置面板控制
            with st.expander("控制面板配置", expanded=False):
                # 添加每行列数滑块
                columns_per_row = st.slider(
                    "每行显示面板数", 
                    min_value=1, 
                    max_value=4, 
                    value=self.dashboard_manager.columns_per_row,
                    key=f"slider_{self.script_name}"
                )
                self.dashboard_manager.set_columns_per_row(columns_per_row)
                
                # 添加预设和性能面板的可见性控制
                col1, col2 = st.columns(2)
                with col1:
                    self.preset_panel.is_visible = st.checkbox(
                        "显示预设配置", 
                        value=self.preset_panel.is_visible,
                        key=f"preset_visible_{self.script_name}"
                    )
                with col2:
                    self.performance_panel.is_visible = st.checkbox(
                        "显示性能配置", 
                        value=self.performance_panel.is_visible,
                        key=f"perf_visible_{self.script_name}"
                    )
            
            # 渲染仪表板
            self.dashboard_manager.render(st.container()) 