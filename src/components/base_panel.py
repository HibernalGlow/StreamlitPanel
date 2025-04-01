from abc import ABC, abstractmethod
import streamlit as st

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