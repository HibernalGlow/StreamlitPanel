"""
测试主程序
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 导入main模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main

class TestMain:
    """测试主程序功能"""
    
    def test_main_no_args(self, mock_streamlit):
        """测试无参数调用main函数"""
        # 不使用命令行参数情况下，主界面应该显示使用说明
        with patch.object(sys, "argv", ["main.py"]):
            main.main()
            # 验证界面是否显示信息提示
            mock_streamlit.info.assert_called()
    
    def test_main_with_config_dir(self, mock_streamlit, sample_config_dir):
        """测试有配置目录参数的main函数"""
        # 模拟sys.argv
        with patch.object(sys, "argv", ["main.py", sample_config_dir]), \
             patch("main.read_log_file") as mock_read_log, \
             patch("main.is_script_active") as mock_is_active, \
             patch("main.StreamlitLoggerManager") as mock_logger_manager, \
             patch("main.time.sleep") as mock_sleep:
            
            # 配置模拟返回值
            mock_read_log.return_value = ([], 0)
            mock_is_active.return_value = True
            
            # 添加模拟脚本配置
            class SessionState:
                def __init__(self):
                    pass
            
            session_state = SessionState()
            mock_streamlit.session_state = session_state
            
            # 调用主函数
            main.main()
            
            # 验证主函数行为
            assert hasattr(mock_streamlit.session_state, "script_configs")
            mock_sleep.assert_called()
    
    def test_main_force_reload(self, mock_streamlit):
        """测试强制重新加载配置"""
        # 设置force_reload
        mock_streamlit.sidebar.checkbox.return_value = True
        
        # 创建SessionState对象
        class SessionState:
            def __init__(self):
                pass
        
        session_state = SessionState()
        mock_streamlit.session_state = session_state
        
        with patch.object(sys, "argv", ["main.py"]), \
             patch("main.time") as mock_time:
            
            # 设置当前时间
            mock_time.time.return_value = 100
            
            # 调用主函数
            main.main()
            
            # 验证是否设置了force_reload_timestamp
            assert hasattr(mock_streamlit.session_state, "force_reload_timestamp")
            assert mock_streamlit.session_state.force_reload_timestamp == 100 