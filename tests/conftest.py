"""
Pytest配置文件
用于设置测试环境、fixtures和模拟对象
"""

import pytest
import os
import sys
import tempfile
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# 将根目录添加到模块搜索路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 模拟Streamlit
@pytest.fixture
def mock_streamlit():
    """模拟streamlit模块"""
    streamlit_mock = MagicMock()
    
    # 创建一个具有属性的字典来模拟session_state
    class SessionState:
        def __init__(self):
            self.script_configs = {}
    
    session_state = SessionState()
    streamlit_mock.session_state = session_state
    
    with patch("src.utils.file_utils.st", streamlit_mock), \
         patch("src.logger_manager.st", streamlit_mock), \
         patch("src.panels.log_panel.st", streamlit_mock), \
         patch("src.panels.system_panel.st", streamlit_mock), \
         patch("src.panels.preset_panel.st", streamlit_mock), \
         patch("src.panels.performance_panel.st", streamlit_mock), \
         patch("src.components.script_dashboard.st", streamlit_mock), \
         patch("src.components.dashboard_manager.st", streamlit_mock), \
         patch("main.st", streamlit_mock):
        yield streamlit_mock

@pytest.fixture
def mock_psutil():
    """模拟psutil模块"""
    psutil_mock = MagicMock()
    # 配置CPU使用率返回值
    psutil_mock.cpu_percent.return_value = 10.5
    
    # 配置内存信息返回值
    memory_mock = MagicMock()
    memory_mock.percent = 45.2
    psutil_mock.virtual_memory.return_value = memory_mock
    
    # 配置磁盘IO信息返回值
    disk_io_mock = MagicMock()
    disk_io_mock.read_bytes = 1024 * 1024 * 100  # 100MB
    disk_io_mock.write_bytes = 1024 * 1024 * 50   # 50MB
    psutil_mock.disk_io_counters.return_value = disk_io_mock
    
    with patch("src.logger_manager.psutil", psutil_mock):
        yield psutil_mock

@pytest.fixture
def sample_log_file():
    """创建临时的示例日志文件"""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".log") as tmp:
        # 写入一些测试日志条目
        tmp.write("2025-03-27 15:30:45,123 - INFO - [#status]测试日志信息\n")
        tmp.write("2025-03-27 15:30:46,234 - WARNING - [#status]测试警告信息\n")
        tmp.write("2025-03-27 15:30:47,345 - ERROR - [#status]测试错误信息\n")
        tmp.write("2025-03-27 15:30:48,456 - INFO - [@progress]进度 50%\n")
        tmp.write("2025-03-27 15:30:49,567 - INFO - [@progress]任务 (5/10) 50%\n")
        tmp.flush()
        tmp.close()
        
        yield tmp.name
        
        # 清理临时文件
        os.unlink(tmp.name)

@pytest.fixture
def sample_config_dir():
    """创建临时的配置目录和配置文件"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建临时日志文件
        log_file = os.path.join(tmp_dir, "test_script.log")
        with open(log_file, "w") as f:
            f.write("2025-03-27 15:30:45,123 - INFO - [#status]测试日志信息\n")
        
        # 创建临时配置文件
        config = {
            "log_file": log_file,
            "layout": {
                "status": {"title": "📊 状态", "style": "lightblue", "icon": "✅"},
                "progress": {"title": "🔄 进度", "style": "lightgreen", "icon": "🔄"}
            }
        }
        
        config_file = os.path.join(tmp_dir, "test_script.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
        
        yield tmp_dir
        
        # 清理由测试创建的临时文件（目录会自动清理）
        if os.path.exists(log_file):
            os.unlink(log_file) 