import streamlit as st
from src.components.base_panel import BasePanel
from typing import Dict, List

class LogPanel(BasePanel):
    """日志面板类"""
    def __init__(self, title: str, icon: str = "", style: str = "default"):
        super().__init__(title, icon, style)
        self.logs: List[Dict] = []
        self.progress_bars: Dict[str, Dict] = {}
        
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