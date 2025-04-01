#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多脚本日志监控器演示程序
同时启动多个模拟脚本进程，每个脚本生成不同类型的日志
"""

import os
import time
import random
import logging
import threading
import argparse
from datetime import datetime
import sys
import tempfile

# 添加父目录到路径，以便导入streamlit_logger
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(current_dir)))

from nodes.gui.streamlit.streamlit_logger import StreamlitLoggerManager

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S,%f'
)

class DemoScript:
    """模拟脚本类，生成各种类型的日志"""
    
    def __init__(self, script_name, log_dir, duration=60):
        """初始化模拟脚本
        
        Args:
            script_name: 脚本名称
            log_dir: 日志目录
            duration: 脚本运行时长（秒）
        """
        self.script_name = script_name
        self.log_dir = log_dir
        self.duration = duration
        
        # 创建脚本日志目录
        self.script_dir = os.path.join(log_dir, script_name)
        os.makedirs(self.script_dir, exist_ok=True)
        
        # 创建日志文件
        self.log_file = os.path.join(self.script_dir, f"{script_name}.log")
        
        # 配置日志处理器
        self.logger = self._setup_logger()
        
        # 停止标志
        self.stop_flag = threading.Event()
    
    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(self.script_name)
        
        # 移除所有已有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        
        return logger
    
    def run(self):
        """运行模拟脚本"""
        # 启动Streamlit日志监控器
        StreamlitLoggerManager.init_logger(self.log_file)
        
        # 记录启动信息
        self.logger.info(f"[#status]脚本 {self.script_name} 已启动")
        
        # 模拟不同类型的进度
        self._run_file_processing()
        self._run_image_conversion()
        self._run_archive_operations()
        
        # 记录性能信息
        threading.Thread(target=self._log_performance, daemon=True).start()
        
        # 主循环
        start_time = time.time()
        while not self.stop_flag.is_set() and (time.time() - start_time) < self.duration:
            # 记录一些随机状态信息
            self._log_random_status()
            time.sleep(random.uniform(1, 3))
        
        # 结束
        self.logger.info(f"[#status]脚本 {self.script_name} 已完成")
    
    def _log_performance(self):
        """记录性能信息"""
        while not self.stop_flag.is_set():
            cpu = random.uniform(10, 95)
            memory = random.uniform(100, 500)
            
            self.logger.info(f"[#performance]CPU使用率: {cpu:.1f}%")
            self.logger.info(f"[#performance]内存占用: {memory:.1f} MB")
            
            time.sleep(5)
    
    def _run_file_processing(self):
        """模拟文件处理进度"""
        total_files = random.randint(10, 50)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("file_ops", "文件处理", total_files, 0.5, 1.5),
            daemon=True
        )
        thread.start()
    
    def _run_image_conversion(self):
        """模拟图片转换进度"""
        total_images = random.randint(20, 100)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("image_convert", "图片转换", total_images, 0.2, 0.8),
            daemon=True
        )
        thread.start()
    
    def _run_archive_operations(self):
        """模拟压缩包处理进度"""
        total_archives = random.randint(5, 15)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("archive_ops", "压缩文件处理", total_archives, 1.0, 3.0),
            daemon=True
        )
        thread.start()
    
    def _simulate_progress(self, panel, task_name, total, min_delay, max_delay):
        """模拟进度更新
        
        Args:
            panel: 面板名称
            task_name: 任务名称
            total: 总数量
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        for i in range(1, total + 1):
            if self.stop_flag.is_set():
                break
                
            percentage = (i / total) * 100
            
            # 记录进度
            self.logger.info(f"[@{panel}]{task_name} [{i}/{total}] {percentage:.1f}%")
            
            # 随机添加一些详细日志
            if random.random() < 0.3:
                self.logger.info(f"[#{panel}]处理项目 {i}: {task_name}_{i}")
            
            # 随机添加警告或错误
            if random.random() < 0.1:
                if random.random() < 0.3:
                    self.logger.error(f"[#{panel}]处理 {task_name}_{i} 时发生错误")
                else:
                    self.logger.warning(f"[#{panel}]处理 {task_name}_{i} 有潜在问题")
            
            # 随机延迟
            time.sleep(random.uniform(min_delay, max_delay))
    
    def _log_random_status(self):
        """记录随机状态信息"""
        statuses = [
            f"[#status]当前处理批次: {random.randint(1, 100)}",
            f"[#status]已完成任务数: {random.randint(10, 500)}",
            f"[#status]累计处理文件: {random.randint(100, 1000)}个",
            f"[#progress]总体进度: {random.uniform(0, 100):.1f}%",
            f"[#progress]任务队列: {random.randint(0, 50)}个待处理",
            f"[#progress]已分析文件数: {random.randint(10, 200)}个"
        ]
        
        self.logger.info(random.choice(statuses))
    
    def stop(self):
        """停止脚本运行"""
        self.stop_flag.set()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多脚本日志监控器演示程序")
    parser.add_argument('--count', type=int, default=3, help="启动的脚本数量")
    parser.add_argument('--duration', type=int, default=60, help="脚本运行时长（秒）")
    parser.add_argument('--log-dir', type=str, default=None, help="日志目录")
    
    args = parser.parse_args()
    
    # 创建临时日志目录
    log_dir = args.log_dir
    if log_dir is None:
        log_dir = tempfile.mkdtemp(prefix="streamlit_logger_demo_")
    else:
        os.makedirs(log_dir, exist_ok=True)
    
    print(f"日志目录: {log_dir}")
    
    # 创建并启动模拟脚本
    scripts = []
    for i in range(args.count):
        script_name = f"demo_script_{i+1}"
        script = DemoScript(script_name, log_dir, args.duration)
        scripts.append(script)
        
        # 在线程中启动脚本
        thread = threading.Thread(target=script.run)
        thread.start()
    
    try:
        # 等待所有脚本运行完成
        time.sleep(args.duration)
    except KeyboardInterrupt:
        print("正在停止所有脚本...")
        for script in scripts:
            script.stop()
    
    print(f"演示完成，日志文件保存在: {log_dir}")

if __name__ == "__main__":
    main() 