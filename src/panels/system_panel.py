import streamlit as st
from src.components.base_panel import BasePanel
from typing import Dict

class SystemPanel(BasePanel):
    """系统状态面板类"""
    def __init__(self, title: str = "系统状态", icon: str = "🖥️", style: str = "lightgreen"):
        super().__init__(title, icon, style)
        self.cpu_usage = 0
        self.memory_usage = 0
        self.disk_io = {"read": 0, "write": 0}
        
    def update_stats(self, cpu: float, memory: float, disk_io: Dict):
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