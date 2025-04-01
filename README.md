# Streamlit 多脚本日志监控

一个基于Streamlit的实时日志监控系统，支持监控多个脚本的日志输出，并以仪表板形式展示。

## 功能特点

- 支持同时监控多个脚本的日志输出
- 每个脚本使用独立的页签，标题显示"脚本名+启动时间"
- 所有面板均为可折叠区域，方便管理
- 支持通过滑块调整每行显示的面板数量
- 预设面板和性能配置面板在需要时才显示，默认隐藏
- 支持实时显示系统状态（CPU、内存、磁盘IO）
- 自动解析并显示进度条信息
- 支持按级别（INFO/WARNING/ERROR）区分日志显示

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 启动监控服务

```bash
streamlit run main.py /path/to/config/dir
```

其中，`/path/to/config/dir` 是配置目录的路径，该目录应包含要监控的脚本配置文件（`.json`）。

### 配置文件示例

```json
{
  "log_file": "/path/to/script.log",
  "layout": {
    "status": {"title": "📊 总体进度", "style": "lightyellow", "icon": "✅"},
    "progress": {"title": "🔄 当前进度", "style": "lightcyan", "icon": "🔄"}
  }
}
```

### 日志格式

在被监控的脚本中，日志应按以下格式输出：

- 普通日志: `2025-03-27 22:03:14,456 - INFO - [#panel_name]日志内容`
- 进度条: `2025-03-27 22:03:14,456 - INFO - [@panel_name]任务名 50%`
- 带分数的进度条: `2025-03-27 22:03:14,456 - INFO - [@panel_name]任务名 (5/10) 50%`

## 开发

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
python run_tests.py
```

## 项目结构

```
.
├── main.py                # 主入口文件
├── src/                   # 源代码
│   ├── components/        # UI组件
│   ├── panels/            # 面板实现
│   ├── utils/             # 工具函数
│   └── logger_manager.py  # 日志管理器
├── tests/                 # 测试用例
└── requirements.txt       # 依赖文件
``` 