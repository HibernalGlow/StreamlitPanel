"""
测试文件操作工具功能
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.utils.file_utils import read_log_file, is_script_active

class TestFileUtils:
    """测试文件工具类"""
    
    def test_read_log_file(self, sample_log_file):
        """测试读取日志文件"""
        # 从头开始读取
        entries, position = read_log_file(sample_log_file, 0)
        
        # 验证读取结果
        assert len(entries) == 5
        assert position > 0
        
        # 验证内容解析正确
        assert entries[0]["panel_name"] == "status"
        assert entries[0]["content"] == "测试日志信息"
        assert entries[0]["level"] == "INFO"
        
        assert entries[1]["level"] == "WARNING"
        assert entries[2]["level"] == "ERROR"
        
        assert entries[3]["panel_type"] == "@"
        assert entries[3]["panel_name"] == "progress"
        assert "50%" in entries[3]["content"]
        
        # 从中间开始读取
        entries_2, position_2 = read_log_file(sample_log_file, position)
        assert len(entries_2) == 0  # 已经读完了
        
        # 测试不存在的文件
        entries_3, position_3 = read_log_file("not_exists.log", 0)
        assert len(entries_3) == 0
        assert position_3 == 0
    
    def test_is_script_active(self, mock_streamlit):
        """测试脚本活跃检测"""
        # 设置模拟数据
        mock_streamlit.session_state.script_configs = {
            "test_script": {
                "log_file": "fake_log.txt",
                "last_update": datetime.now() - timedelta(minutes=2)
            },
            "old_script": {
                "log_file": "fake_log.txt",
                "last_update": datetime.now() - timedelta(minutes=10)
            },
            "no_file_script": {
                "log_file": "not_exists.txt",
                "last_update": datetime.now()
            }
        }
        
        # 模拟文件存在检查
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: path == "fake_log.txt"
            
            # 测试正常活跃的脚本
            assert is_script_active("test_script") is True
            
            # 测试不活跃的脚本 (超时)
            assert is_script_active("old_script") is False
            
            # 测试文件不存在的脚本
            assert is_script_active("no_file_script") is False
            
            # 测试不存在的脚本ID
            assert is_script_active("not_exists") is False 