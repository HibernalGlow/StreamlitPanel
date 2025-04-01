"""
测试日志管理器
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.logger_manager import StreamlitLoggerManager

class TestStreamlitLoggerManager:
    """测试Streamlit日志管理器"""
    
    def test_set_layout(self, mock_streamlit):
        """测试设置布局"""
        # 准备测试数据
        log_file = os.path.join(os.path.dirname(__file__), "test_script.log")
        
        # 创建临时日志文件
        with open(log_file, "w") as f:
            f.write("2025-03-27 15:30:45,123 - INFO - [#status]测试日志信息\n")
        
        try:
            # 测试设置布局
            with patch.object(StreamlitLoggerManager, "_dashboards", {}):
                result = StreamlitLoggerManager.set_layout(None, log_file)
                
                # 验证返回值
                assert result == log_file
                
                # 验证是否创建了仪表板
                script_id = os.path.basename(os.path.dirname(log_file))
                assert script_id in StreamlitLoggerManager._dashboards
                
                # 验证仪表板中是否创建了默认面板
                dashboard = StreamlitLoggerManager._dashboards[script_id]
                for panel_id in StreamlitLoggerManager._default_layout:
                    assert panel_id in dashboard.dashboard_manager.panels
                
                # 验证是否更新了session_state
                assert script_id in mock_streamlit.session_state.script_configs
                assert mock_streamlit.session_state.script_configs[script_id]["log_file"] == log_file
        finally:
            # 清理测试文件
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_update_dashboard(self, mock_streamlit, mock_psutil):
        """测试更新仪表板"""
        # 准备测试数据
        script_id = "test_script"
        log_entries = [
            {
                "timestamp": "2025-03-27 15:30:45,123",
                "level": "INFO",
                "panel_type": "#",
                "panel_name": "status",
                "content": "测试日志信息"
            },
            {
                "timestamp": "2025-03-27 15:30:46,234",
                "level": "WARNING",
                "panel_type": "#",
                "panel_name": "status",
                "content": "测试警告信息"
            },
            {
                "timestamp": "2025-03-27 15:30:47,345",
                "level": "INFO",
                "panel_type": "@",
                "panel_name": "progress",
                "content": "进度 50%"
            }
        ]
        
        # 创建模拟仪表板
        with patch("src.components.script_dashboard.ScriptDashboard") as MockDashboard:
            mock_dashboard = MagicMock()
            mock_status_panel = MagicMock()
            mock_progress_panel = MagicMock()
            
            # 配置模拟面板
            mock_dashboard.dashboard_manager.panels = {
                "status": mock_status_panel,
                "progress": mock_progress_panel
            }
            mock_dashboard.system_panel = MagicMock()
            
            # 使用类型检查
            from src.panels.log_panel import LogPanel
            mock_status_panel.__class__ = LogPanel
            mock_progress_panel.__class__ = LogPanel
            
            # 设置模拟仪表板
            MockDashboard.return_value = mock_dashboard
            StreamlitLoggerManager._dashboards = {script_id: mock_dashboard}
            
            # 调用更新函数
            StreamlitLoggerManager._update_dashboard(script_id, log_entries)
            
            # 验证系统状态是否更新
            mock_dashboard.system_panel.update_stats.assert_called_once()
            
            # 验证日志面板是否更新
            assert mock_status_panel.add_log.call_count == 2
            assert mock_progress_panel.update_progress.call_count == 1
    
    def test_render_dashboard(self, mock_streamlit):
        """测试渲染仪表板"""
        script_id = "test_script"
        container = MagicMock()
        
        # 测试不存在的脚本ID
        with patch.object(StreamlitLoggerManager, "_dashboards", {}):
            StreamlitLoggerManager._render_dashboard("not_exists", container)
            container.assert_not_called()
        
        # 测试正常渲染
        mock_dashboard = MagicMock()
        StreamlitLoggerManager._dashboards = {script_id: mock_dashboard}
        
        StreamlitLoggerManager._render_dashboard(script_id, container)
        mock_dashboard.render.assert_called_once_with(container) 