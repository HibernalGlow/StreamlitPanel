"""
运行测试脚本
简化测试命令行调用
"""
import os
import sys
import pytest

def main():
    """运行所有测试"""
    print("======== 开始运行Streamlit日志监控系统测试 ========")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建测试参数
    args = [
        "-v",
        "--cov=src",
        "--cov=main.py",
        "--cov-report=term-missing",
        "tests"
    ]
    
    # 运行测试
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        print("\n✅ 所有测试通过!")
    else:
        print(f"\n❌ 测试失败，退出代码: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 