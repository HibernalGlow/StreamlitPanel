import logging
import time
import random
import os
import sys
from datetime import datetime
from nodes.record.logger_config import setup_logger
from nodes.gui.streamlit.streamlit_logger import StreamlitLoggerManager
import subprocess

# 预设面板定义
PANELS = {
    "system_info": {
        "name": "系统信息",
        "messages": [
            "CPU使用率: {}%",
            "内存使用: {}MB",
            "磁盘空间: {}GB可用",
            "网络流量: {}KB/s",
            "温度: {}°C"
        ],
        "progress": [
            "系统监控",
            "性能检查",
            "设备扫描"
        ]
    },
    "processing": {
        "name": "处理任务",
        "messages": [
            "处理文件: {}",
            "解析数据: {} 条记录",
            "转换格式: {} -> {}",
            "压缩数据: 比率 {}%",
            "写入输出: {} 字节"
        ],
        "progress": [
            "数据处理",
            "文件解析",
            "格式转换"
        ]
    },
    "error_check": {
        "name": "错误检查",
        "messages": [
            "检查模块: {}",
            "验证配置: {}",
            "尝试修复: {} 问题",
            "分析日志: {} 条异常",
            "安全扫描: {} 个风险"
        ],
        "progress": [
            "错误扫描",
            "问题诊断",
            "自动修复"
        ]
    },
    "summary": {
        "name": "结果摘要",
        "messages": [
            "总文件数: {}",
            "成功率: {}%",
            "处理耗时: {}秒",
            "任务ID: {}",
            "输出位置: {}"
        ],
        "progress": [
            "报告生成",
            "结果汇总",
            "状态更新"
        ]
    }
}

# 定义布局配置
STREAMLIT_LAYOUT = {
    "system_info": {"title": "📊 系统信息", "style": "lightgreen"},
    "processing": {"title": "🔄 处理进度", "style": "lightcyan"},
    "error_check": {"title": "❌ 错误检查", "style": "red"},
    "summary": {"title": "📝 结果摘要", "style": "blue"}
}

# 生成模拟日志
def generate_demo_logs(logger):
    """生成模拟日志"""
    # 进度条状态记录
    progress_status = {}
    for panel, info in PANELS.items():
        progress_status[panel] = {}
        for task in info["progress"]:
            progress_status[panel][task] = 0
    
    # 记录起始时间
    start_time = time.time()
    
    try:
        logger.info("[#system_info]演示日志生成已启动")
        count = 0
        
        while True:
            count += 1
            # 为每个面板生成日志
            for panel, info in PANELS.items():
                # 1. 生成普通日志 (70%概率)
                if random.random() < 0.7:
                    message_template = random.choice(info["messages"])
                    
                    # 生成随机参数
                    if "{}" in message_template:
                        if "文件" in message_template or "位置" in message_template:
                            param = f"/path/to/file_{random.randint(1000, 9999)}.dat"
                            message = message_template.format(param)
                        elif "条记录" in message_template or "条异常" in message_template:
                            param = random.randint(1, 1000)
                            message = message_template.format(param)
                        elif "CPU" in message_template or "成功率" in message_template:
                            param = random.randint(1, 100)
                            message = message_template.format(param)
                        elif "内存" in message_template:
                            param = random.randint(100, 8000)
                            message = message_template.format(param)
                        elif "磁盘" in message_template:
                            param = random.randint(10, 1000)
                            message = message_template.format(param)
                        elif "温度" in message_template:
                            param = random.randint(30, 80)
                            message = message_template.format(param)
                        elif "任务ID" in message_template:
                            param = f"TASK-{random.randint(10000, 99999)}"
                            message = message_template.format(param)
                        elif "->" in message_template:
                            formats = ["JSON", "XML", "CSV", "TXT", "YAML", "PROTO"]
                            param1 = random.choice(formats)
                            param2 = random.choice(formats)
                            message = message_template.format(param1, param2)  # 提供两个参数
                        else:
                            param = random.randint(1, 100)
                            message = message_template.format(param)
                    else:
                        message = message_template
                    
                    # 随机决定日志级别 (80% INFO, 15% WARNING, 5% ERROR)
                    log_level = random.choices(
                        [logging.INFO, logging.WARNING, logging.ERROR],
                        weights=[0.8, 0.15, 0.05],
                        k=1
                    )[0]
                    
                    # 输出日志
                    logger.log(log_level, f"[#{panel}]{message}")
                
                # 2. 更新进度条 (30%概率)
                if random.random() < 0.3:
                    task = random.choice(info["progress"])
                    current = progress_status[panel][task]
                    
                    # 增加进度，最大到100%
                    if current < 100:
                        # 随机递增1-5
                        increment = random.randint(1, 5)
                        current = min(current + increment, 100)
                        progress_status[panel][task] = current
                        
                        # 随机选择进度格式 (普通百分比、带括号分数、带方括号分数)
                        format_type = random.choice(["plain", "parentheses", "brackets"])
                        
                        if format_type == "plain":
                            progress_message = f"[@{panel}]{task} {current}%"
                        elif format_type == "parentheses":
                            progress_message = f"[@{panel}]{task} ({current}/100) {current}%"
                        else:  # brackets
                            progress_message = f"[@{panel}]{task} [{current}/100] {current}%"
                        
                        logger.info(progress_message)
                        
                        # 如果进度到100%，输出完成消息
                        if current == 100:
                            logger.info(f"[#{panel}]{task} 任务已完成!")
            
            # 每100次循环报告一次
            if count % 100 == 0:
                logger.info(f"[#system_info]已生成 {count} 条日志")
            
            # 随机暂停0.1-0.5秒
            time.sleep(random.uniform(0.1, 0.5))
            
    except KeyboardInterrupt:
        logger.info("[#summary]演示日志生成已停止")

# 主程序
def main():
    # 1. 初始化日志系统
    config = {
        'script_name': 'demo_log_generator',
        'console_enabled': True
    }
    logger, config_info = setup_logger(config)
    
    print(f"日志文件: {config_info['log_file']}")
    print("正在启动Streamlit日志查看器...")
    
    # 2. 启动Streamlit日志查看器
    try:
        process = StreamlitLoggerManager.init_logger(config_info['log_file'], STREAMLIT_LAYOUT)
        if process:
            print("Streamlit日志查看器启动成功！")
            logger.info("[#system_info]Streamlit日志查看器已启动")
        else:
            print("Streamlit日志查看器启动失败，但将继续生成日志。")
            logger.warning("[#error_check]Streamlit日志查看器启动失败")
    except Exception as e:
        print(f"启动日志查看器时出错: {e}")
        logger.error(f"[#error_check]启动日志查看器时出错: {e}")
    
    print("开始生成演示日志，按Ctrl+C停止...")
    time.sleep(2)  # 等待日志查看器初始化
    
    # 3. 生成日志
    generate_demo_logs(logger)

if __name__ == "__main__":
    main()