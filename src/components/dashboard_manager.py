import streamlit as st
from src.components.base_panel import BasePanel
from typing import Dict

class DashboardManager:
    """仪表板管理器类"""
    def __init__(self):
        self.panels: Dict[str, BasePanel] = {}
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