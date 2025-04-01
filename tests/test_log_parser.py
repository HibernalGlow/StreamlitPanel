"""
测试日志解析功能
"""

import pytest
from src.utils.log_parser import parse_log_line, parse_progress

class TestLogParser:
    """测试日志解析器"""
    
    def test_parse_log_line(self):
        """测试解析单行日志"""
        # 测试普通日志
        log_line = "2025-03-27 22:03:14,456 - INFO - [#status]测试信息"
        result = parse_log_line(log_line)
        
        assert result is not None
        assert result["timestamp"] == "2025-03-27 22:03:14,456"
        assert result["level"] == "INFO"
        assert result["panel_type"] == "#"
        assert result["panel_name"] == "status"
        assert result["content"] == "测试信息"
        
        # 测试进度条日志
        log_line = "2025-03-27 22:03:15,456 - INFO - [@progress]任务 50%"
        result = parse_log_line(log_line)
        
        assert result is not None
        assert result["timestamp"] == "2025-03-27 22:03:15,456"
        assert result["level"] == "INFO"
        assert result["panel_type"] == "@"
        assert result["panel_name"] == "progress"
        assert result["content"] == "任务 50%"
        
        # 测试无效日志
        log_line = "这不是一个有效的日志行"
        result = parse_log_line(log_line)
        assert result is None
    
    def test_parse_progress(self):
        """测试解析进度信息"""
        # 测试简单百分比进度
        content = "任务 50%"
        result = parse_progress(content)
        
        assert result is not None
        assert result["prefix"] == "任务"
        assert result["percentage"] == 50.0
        assert result["is_complete"] is False
        
        # 测试完成的进度
        content = "任务 100%"
        result = parse_progress(content)
        
        assert result is not None
        assert result["is_complete"] is True
        
        # 测试分数形式进度 (小括号)
        content = "任务 (5/10) 50%"
        result = parse_progress(content)
        
        assert result is not None
        assert "prefix" in result
        assert result["current"] == 5
        assert result["total"] == 10
        assert result["percentage"] == 50.0
        assert result["fraction"] == "(5/10)"
        
        # 测试分数形式进度 (方括号)
        content = "任务 [5/10] 50%"
        result = parse_progress(content)
        
        assert result is not None
        assert "prefix" in result
        assert result["current"] == 5
        assert result["total"] == 10
        assert result["percentage"] == 50.0
        assert result["fraction"] == "[5/10]"
        
        # 测试无效进度
        content = "这不是一个有效的进度信息"
        result = parse_progress(content)
        assert result is None 