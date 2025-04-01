"""
测试UI组件
"""

import pytest
from unittest.mock import MagicMock, patch

from src.components.base_panel import BasePanel
from src.components.dashboard_manager import DashboardManager
from src.components.script_dashboard import ScriptDashboard

# 创建一个简单的面板实现用于测试
class TestPanel(BasePanel):
    """用于测试的简单面板实现"""
    def __init__(self, title, icon="", style="default"):
        super().__init__(title, icon, style)
        self.render_called = False
        
    def render(self, container):
        if not self.is_visible:
            return
        self.render_called = True


class TestDashboardManager:
    """测试仪表板管理器"""
    
    def test_add_remove_panel(self):
        """测试添加和移除面板"""
        manager = DashboardManager()
        
        # 初始状态
        assert len(manager.panels) == 0
        
        # 添加面板
        panel1 = TestPanel("面板1")
        panel2 = TestPanel("面板2")
        
        manager.add_panel("panel1", panel1)
        manager.add_panel("panel2", panel2)
        
        assert len(manager.panels) == 2
        assert "panel1" in manager.panels
        assert "panel2" in manager.panels
        
        # 移除面板
        manager.remove_panel("panel1")
        
        assert len(manager.panels) == 1
        assert "panel1" not in manager.panels
        assert "panel2" in manager.panels
    
    def test_set_columns_per_row(self):
        """测试设置每行列数"""
        manager = DashboardManager()
        
        # 默认值
        assert manager.columns_per_row == 2
        
        # 设置有效值
        manager.set_columns_per_row(3)
        assert manager.columns_per_row == 3
        
        # 设置超出范围的值
        manager.set_columns_per_row(0)
        assert manager.columns_per_row == 1  # 应该限制为最小值1
        
        manager.set_columns_per_row(10)
        assert manager.columns_per_row == 4  # 应该限制为最大值4
    
    def test_toggle_visibility(self):
        """测试切换可见性"""
        manager = DashboardManager()
        
        # 默认可见
        assert manager.is_visible is True
        
        # 切换可见性
        manager.toggle_visibility()
        assert manager.is_visible is False
        
        manager.toggle_visibility()
        assert manager.is_visible is True
    
    def test_render(self, mock_streamlit):
        """测试渲染"""
        manager = DashboardManager()
        container = MagicMock()
        
        # 添加测试面板
        panel1 = TestPanel("面板1")
        panel2 = TestPanel("面板2")
        panel3 = TestPanel("面板3", icon="🔍")
        
        manager.add_panel("panel1", panel1)
        manager.add_panel("panel2", panel2)
        manager.add_panel("panel3", panel3)
        
        # 设置每行显示2个面板
        manager.set_columns_per_row(2)
        
        # 测试面板可见性控制
        panel2.is_visible = False
        
        # 渲染仪表板
        manager.render(container)
        
        # 检查是否正确渲染
        assert panel1.render_called is True
        assert panel2.render_called is False  # 不可见的面板不应被渲染
        assert panel3.render_called is True
        
        # 测试仪表板可见性控制
        panel1.render_called = False
        panel3.render_called = False
        manager.is_visible = False
        manager.render(container)
        
        # 不可见时不应渲染任何面板
        assert panel1.render_called is False
        assert panel3.render_called is False


class TestScriptDashboard:
    """测试脚本仪表板"""
    
    def test_init(self):
        """测试初始化"""
        dashboard = ScriptDashboard("测试脚本")
        
        assert dashboard.script_name == "测试脚本"
        assert dashboard.is_visible is True
        
        # 检查是否自动创建了基础面板
        assert "system" in dashboard.dashboard_manager.panels
        assert "preset" in dashboard.dashboard_manager.panels
        assert "performance" in dashboard.dashboard_manager.panels
    
    def test_add_log_panel(self):
        """测试添加日志面板"""
        dashboard = ScriptDashboard("测试脚本")
        
        # 添加日志面板
        panel = dashboard.add_log_panel("test_log", "测试日志", "📝", "blue")
        
        assert "test_log" in dashboard.dashboard_manager.panels
        assert dashboard.dashboard_manager.panels["test_log"] is panel
        assert panel.title == "测试日志"
        assert panel.icon == "📝"
        assert panel.style == "blue"
    
    def test_toggle_visibility(self):
        """测试切换可见性"""
        dashboard = ScriptDashboard("测试脚本")
        
        assert dashboard.is_visible is True
        
        dashboard.toggle_visibility()
        assert dashboard.is_visible is False
        
        dashboard.toggle_visibility()
        assert dashboard.is_visible is True 