"""
测试各种面板实现
"""

import pytest
from unittest.mock import MagicMock, patch

from src.panels.log_panel import LogPanel
from src.panels.system_panel import SystemPanel
from src.panels.preset_panel import PresetPanel
from src.panels.performance_panel import PerformancePanel

class TestLogPanel:
    """测试日志面板"""
    
    def test_init(self):
        """测试初始化"""
        panel = LogPanel("测试面板", "🔍", "blue")
        assert panel.title == "测试面板"
        assert panel.icon == "🔍"
        assert panel.style == "blue"
        assert panel.is_visible is True
        assert panel.is_expanded is True
        assert len(panel.logs) == 0
        assert len(panel.progress_bars) == 0
    
    def test_add_log(self):
        """测试添加日志"""
        panel = LogPanel("测试面板")
        
        # 添加日志
        panel.add_log({"level": "info", "timestamp": "12:00:00", "content": "测试日志"})
        assert len(panel.logs) == 1
        assert panel.logs[0]["content"] == "测试日志"
        
        # 添加大量日志测试限制
        for i in range(110):
            panel.add_log({"level": "info", "timestamp": "12:00:00", "content": f"日志 {i}"})
        
        # 检查是否限制到最新的100条
        assert len(panel.logs) == 100
        assert "日志 110" not in [log["content"] for log in panel.logs]
        assert "日志 109" in [log["content"] for log in panel.logs]
    
    def test_update_progress(self):
        """测试更新进度条"""
        panel = LogPanel("测试面板")
        
        progress_info = {
            "percentage": 50.0,
            "text": "处理中...",
            "is_complete": False
        }
        
        panel.update_progress("任务1", progress_info)
        assert len(panel.progress_bars) == 1
        assert panel.progress_bars["任务1"]["percentage"] == 50.0
        
        # 更新进度
        progress_info["percentage"] = 75.0
        panel.update_progress("任务1", progress_info)
        assert panel.progress_bars["任务1"]["percentage"] == 75.0
        
        # 添加另一个进度条
        panel.update_progress("任务2", {"percentage": 25.0, "text": "开始..."})
        assert len(panel.progress_bars) == 2
    
    def test_render(self, mock_streamlit):
        """测试渲染"""
        panel = LogPanel("测试面板")
        container = MagicMock()
        
        # 测试可见性控制
        panel.is_visible = False
        panel.render(container)
        container.__enter__.assert_not_called()
        
        # 测试正常渲染
        panel.is_visible = True
        panel.render(container)
        container.__enter__.assert_called()

class TestSystemPanel:
    """测试系统状态面板"""
    
    def test_update_stats(self):
        """测试更新系统状态"""
        panel = SystemPanel()
        
        panel.update_stats(
            cpu=25.5,
            memory=60.2,
            disk_io={"read": 10.5, "write": 5.3}
        )
        
        assert panel.cpu_usage == 25.5
        assert panel.memory_usage == 60.2
        assert panel.disk_io["read"] == 10.5
        assert panel.disk_io["write"] == 5.3 