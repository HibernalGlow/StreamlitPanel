#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单脚本日志监控器演示程序
生成模拟日志并用register_script注册到主应用
"""

import os
import time
import random
import logging
import argparse
from datetime import datetime
import tempfile
from nodes.record.logger_config import setup_logger

# 导入register_script函数
from main import register_script, STREAMLIT_LAYOUT

config = {
    'script_name': 'demo',
    'console_enabled': True
}
logger, config_info = setup_logger(config)

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
        self.duration = duration
        
        # 创建脚本日志目录
         
        # 创建日志文件
        self.log_file = config_info['log_file']
        self.logger = self._setup_logger()
        
        # 注册到主应用
        self.script_info = {
            'script_id': script_name,
            'script_name': script_name,
            'log_file': self.log_file,
            'layout': STREAMLIT_LAYOUT
        }
        register_script(self.script_info)
    
    def _setup_logger(self):
        """设置日志记录器"""
        
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
        # 记录启动信息
        self.logger.info(f"[#status]脚本 {self.script_name} 已启动")
        
        # 模拟文件处理进度
        self._run_file_processing()
        # 模拟图片转换进度
        self._run_image_conversion()
        # 模拟压缩包处理进度
        self._run_archive_operations()
        
        # 启动性能信息记录
        import threading
        perf_thread = threading.Thread(target=self._log_performance)
        perf_thread.daemon = True
        perf_thread.start()
        
        # 主循环
        start_time = time.time()
        while (time.time() - start_time) < self.duration:
            # 记录一些随机状态信息
            self._log_random_status()
            time.sleep(random.uniform(1, 3))
        
        # 结束
        self.logger.info(f"[#status]脚本 {self.script_name} 已完成")
    
    def _log_performance(self):
        """记录性能信息"""
        start_time = time.time()
        while (time.time() - start_time) < self.duration:
            cpu = random.uniform(10, 95)
            memory = random.uniform(100, 500)
            
            self.logger.info(f"[#performance]CPU使用率: {cpu:.1f}%")
            self.logger.info(f"[#performance]内存占用: {memory:.1f} MB")
            
            time.sleep(5)
    
    def _run_file_processing(self):
        """模拟文件处理进度"""
        import threading
        total_files = random.randint(10, 30)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("file_ops", "文件处理", total_files, 0.5, 1.5),
            daemon=True
        )
        thread.start()
    
    def _run_image_conversion(self):
        """模拟图片转换进度"""
        import threading
        total_images = random.randint(20, 40)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("image_convert", "图片转换", total_images, 0.2, 0.8),
            daemon=True
        )
        thread.start()
    
    def _run_archive_operations(self):
        """模拟压缩包处理进度"""
        import threading
        total_archives = random.randint(5, 15)
        
        thread = threading.Thread(
            target=self._simulate_progress,
            args=("archive_ops", "压缩文件处理", total_archives, 1.0, 2.0),
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
        start_time = time.time()
        duration_per_item = self.duration / (total * 1.2)  # 确保能在脚本结束前完成
        
        for i in range(1, total + 1):
            if (time.time() - start_time) >= self.duration:
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
            
            # 延迟，但确保不会超过总时长
            sleep_time = min(random.uniform(min_delay, max_delay), duration_per_item)
            time.sleep(sleep_time)
    
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="单脚本日志监控器演示程序")
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
    
    # 创建并运行模拟脚本
    script_name = "单脚本演示"
    script = DemoScript(script_name, log_dir, args.duration)
    print(f"脚本信息已注册，日志文件: {script.log_file}")
    
    try:
        print("开始运行演示脚本，按Ctrl+C停止...")
        script.run()
    except KeyboardInterrupt:
        print("\n脚本已停止")
    
    print(f"\n演示完成！日志文件保存在: {script.log_file}")
    print("请运行 `streamlit run main.py` 查看日志")


if __name__ == "__main__":
    main() 