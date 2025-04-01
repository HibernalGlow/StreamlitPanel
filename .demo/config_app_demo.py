import streamlit as st
import yaml
import os
import subprocess
from datetime import datetime
import time
import sys
from typing import Dict, List, Union, Optional, Any, Callable
import argparse
import tempfile
import io
from contextlib import redirect_stdout

# 尝试导入所需组件，如果不可用则设置标志
try:
    from streamlit_webterm import webterm
    has_webterm = True
except ImportError:
    has_webterm = False

try:
    from streamlit_ace import st_ace
    has_ace = True
except ImportError:
    has_ace = False

try:
    import paramiko
    has_paramiko = True
except ImportError:
    has_paramiko = False

try:
    from streamlit_terminal import terminal
    has_terminal = True
except ImportError:
    has_terminal = False

st.set_page_config(page_title="四合一配置界面演示", layout="wide")

# 基础类定义
class CheckboxOption:
    """复选框选项"""
    def __init__(self, label: str, id: str, arg: str, default: bool = False):
        self.label = label
        self.id = id
        self.arg = arg
        self.default = default

class InputOption:
    """输入框选项"""
    def __init__(self, label: str, id: str, arg: str, default: str = "", placeholder: str = ""):
        self.label = label
        self.id = id
        self.arg = arg
        self.default = default
        self.placeholder = placeholder

class PresetConfig:
    """预设配置类"""
    def __init__(
        self,
        name: str,
        description: str,
        checkbox_options: List[str],  # 选中的checkbox id列表
        input_values: Dict[str, str]  # input id和值的字典
    ):
        self.name = name
        self.description = description
        self.checkbox_options = checkbox_options
        self.input_values = input_values

# 工具函数
def save_preset(name: str, description: str, checkbox_options: List[CheckboxOption], 
                selected_options: List[str], input_options: List[InputOption]) -> None:
    """保存当前配置为预设"""
    try:
        # 创建新预设
        new_preset = {
            "name": name,
            "description": description,
            "checkbox_options": [opt.id for opt in checkbox_options if opt.id in selected_options],
            "input_values": {opt.id: st.session_state.get(opt.id, "") for opt in input_options}
        }

        # 更新预设列表
        presets = st.session_state.get("presets", {})
        presets[name] = new_preset
        st.session_state["presets"] = presets
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            yaml.dump({"presets": presets}, f, allow_unicode=True)
            st.session_state["config_file"] = f.name
        
        st.success(f"预设 '{name}' 已保存")
        
    except Exception as e:
        st.error(f"保存预设配置失败: {e}")

def load_presets() -> dict:
    """加载预设配置"""
    try:
        if "config_file" in st.session_state and os.path.exists(st.session_state["config_file"]):
            with open(st.session_state["config_file"], 'r', encoding='utf-8') as f:
                return yaml.safe_load(f).get('presets', {})
        return {}
    except Exception as e:
        st.error(f"加载预设配置失败: {e}")
        return {}

def apply_preset(preset_name: str, presets: dict, checkbox_options: List[CheckboxOption], 
                input_options: List[InputOption]) -> None:
    """应用预设配置"""
    if preset_name not in presets:
        return

    preset = presets[preset_name]
    
    # 清空所有输入框
    for opt in input_options:
        if opt.id in st.session_state:
            st.session_state[opt.id] = ""

    # 只设置预设中指定的值
    for option_id, value in preset.get("input_values", {}).items():
        st.session_state[option_id] = value

    # 清空所有复选框选择
    for opt in checkbox_options:
        st.session_state[f"checkbox_{opt.id}"] = False
    
    # 只选择预设中指定的选项
    for option_id in preset.get("checkbox_options", []):
        st.session_state[f"checkbox_{option_id}"] = True

    st.success(f"已应用预设配置: {preset_name}")

def update_command_preview(program: str, checkbox_options: List[CheckboxOption], 
                          input_options: List[InputOption], extra_args: List[str] = None) -> str:
    """更新命令预览"""
    # 使用简化的python命令前缀
    cmd = ["python"]
    
    # 添加程序路径（去掉多余的引号）
    program_path = program.strip('"')
    cmd.append(program_path)

    # 添加选中的功能选项
    for opt in checkbox_options:
        if st.session_state.get(f"checkbox_{opt.id}", False):
            cmd.append(opt.arg)

    # 添加输入框选项
    for opt in input_options:
        value = st.session_state.get(opt.id, "")
        if value:
            cmd.extend([opt.arg, value])

    # 添加额外参数
    if extra_args:
        cmd.extend(extra_args)

    # 返回完整命令
    return " ".join(cmd)

# 执行方式实现
def run_command_and_get_output(command):
    """使用子进程执行命令并获取输出"""
    try:
        # 捕获命令输出
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 创建输出容器
        output_container = st.empty()
        
        # 实时显示输出
        output = ""
        for line in process.stdout:
            output += line
            output_container.code(output)
            
        return_code = process.wait()
        if return_code != 0:
            st.error(f"命令执行失败，返回码: {return_code}")
        
        return output
    except Exception as e:
        st.error(f"执行命令出错: {e}")
        return None

def run_command_on_ssh(host, port, username, password, command):
    """通过SSH执行命令"""
    try:
        if not has_paramiko:
            st.error("未安装paramiko库，无法使用SSH功能")
            return None
            
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port=port, username=username, password=password)
        
        # 创建输出容器
        output_container = st.empty()
        output = ""
        
        # 执行命令
        stdin, stdout, stderr = client.exec_command(command)
        
        # 实时显示输出
        for line in stdout:
            output += line
            output_container.code(output)
            time.sleep(0.1)  # 添加小延迟以模拟实时显示
            
        # 显示错误
        for line in stderr:
            output += f"ERROR: {line}"
            output_container.code(output)
            
        client.close()
        return output
    except Exception as e:
        st.error(f"SSH连接或执行出错: {e}")
        return None

# 主配置界面
def create_streamlit_config_app(
    program: str,
    checkbox_options: List[tuple] = None,
    input_options: List[tuple] = None,
    title: str = "配置界面",
    extra_args: List[str] = None,
    preset_configs: dict = None,
    parser: argparse.ArgumentParser = None
):
    """创建Streamlit配置界面"""
    st.title(title)
    
    # 加载自定义CSS
    st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .run-btn>button {
        background-color: #4CAF50;
        color: white;
    }
    .run-btn>button:hover {
        background-color: #45a049;
    }
    .quit-btn>button {
        background-color: #f44336;
        color: white;
    }
    .copy-btn>button {
        background-color: #2196F3;
        color: white;
    }
    .command-preview {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        font-family: monospace;
    }
    .preset-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if "presets" not in st.session_state:
        st.session_state["presets"] = load_presets()
    
    if preset_configs and "presets" in st.session_state and not st.session_state["presets"]:
        # 如果预设为空且提供了预设配置，加载它们
        presets = {}
        for name, config in preset_configs.items():
            presets[name] = {
                "name": name,
                "description": config.get("description", ""),
                "checkbox_options": config.get("checkbox_options", []),
                "input_values": config.get("input_values", {})
            }
        st.session_state["presets"] = presets
    
    # 如果提供了parser并且没有提供选项，则从parser自动生成
    if parser and not (checkbox_options or input_options):
        # 自动从parser生成选项
        checkbox_options = []
        input_options = []
        
        for action in parser._actions:
            # 跳过帮助选项和位置参数
            if action.dest == 'help' or not action.option_strings:
                continue
            
            # 获取选项名称和帮助信息
            opt_name = action.option_strings[0]  # 使用第一个选项字符串
            help_text = action.help or ""
            opt_id = opt_name.lstrip('-').replace('-', '_')
            
            if isinstance(action, argparse._StoreTrueAction):
                # 布尔标志 -> 复选框
                checkbox_options.append((help_text, opt_id, opt_name, False))
            else:
                # 带值的参数 -> 输入框
                default = str(action.default) if action.default is not None else ""
                choices = "/".join(action.choices) if action.choices else ""
                placeholder = choices or f"默认: {default}" if default else ""
                input_options.append((help_text, opt_id, opt_name, default, placeholder))

    # 处理checkbox选项
    cb_opts = []
    if checkbox_options:
        for item in checkbox_options:
            if len(item) == 4:
                label, id, arg, default = item
            else:
                label, id, arg = item
                default = False
            cb_opts.append(CheckboxOption(label, id, arg, default))

    # 处理input选项
    in_opts = []
    if input_options:
        for label, id, arg, *rest in input_options:
            default = rest[0] if len(rest) > 0 else ""
            placeholder = rest[1] if len(rest) > 1 else ""
            in_opts.append(InputOption(label, id, arg, default, placeholder))
    
    # 主界面分为左右两列
    left_col, right_col = st.columns([3, 1])
    
    with left_col:
        # 命令预览区域
        st.subheader("命令预览")
        command = update_command_preview(program, cb_opts, in_opts, extra_args)
        st.code(command, language="bash")
        
        # 参数设置部分
        config_tab1, config_tab2 = st.tabs(["功能开关", "参数设置"])
        
        with config_tab1:
            # 功能开关
            if cb_opts:
                for opt in cb_opts:
                    if f"checkbox_{opt.id}" not in st.session_state:
                        st.session_state[f"checkbox_{opt.id}"] = opt.default
                    st.checkbox(
                        opt.label, 
                        key=f"checkbox_{opt.id}",
                        help=f"参数: {opt.arg}"
                    )
            else:
                st.info("没有可用的功能开关")
        
        with config_tab2:
            # 参数设置
            if in_opts:
                for opt in in_opts:
                    if opt.id not in st.session_state:
                        st.session_state[opt.id] = opt.default
                    st.text_input(
                        opt.label, 
                        key=opt.id,
                        placeholder=opt.placeholder,
                        help=f"参数: {opt.arg}"
                    )
            else:
                st.info("没有可用的参数设置")
        
        # 执行方式选择
        st.subheader("执行方式")
        exec_tab1, exec_tab2, exec_tab3, exec_tab4 = st.tabs([
            "WebTerm", "Subprocess", "SSH", "Terminal"
        ])
        
        with exec_tab1:
            # WebTerm方式
            st.markdown("**使用WebTerm组件在网页中执行命令**")
            if has_webterm:
                if st.button("使用WebTerm执行", key="webterm_btn", type="primary"):
                    st.session_state['run_command'] = command
                
                if 'run_command' in st.session_state and st.session_state['run_command']:
                    webterm(command=st.session_state['run_command'], key="webterm")
            else:
                st.error("未安装streamlit-webterm组件，请使用 `pip install streamlit-webterm` 安装")
                
        with exec_tab2:
            # Subprocess方式
            st.markdown("**使用Subprocess在后台执行命令并显示输出**")
            if st.button("使用Subprocess执行", key="subprocess_btn", type="primary"):
                with st.spinner("正在执行命令..."):
                    output = run_command_and_get_output(command)
                
                if output:
                    st.subheader("执行结果")
                    st.code(output)
        
        with exec_tab3:
            # SSH方式
            st.markdown("**使用SSH连接到远程服务器执行命令**")
            if has_paramiko:
                col1, col2 = st.columns(2)
                with col1:
                    ssh_host = st.text_input("主机", value="localhost", key="ssh_host")
                    ssh_username = st.text_input("用户名", key="ssh_username")
                with col2:
                    ssh_port = st.number_input("端口", value=22, key="ssh_port")
                    ssh_password = st.text_input("密码", type="password", key="ssh_password")
                
                if st.button("使用SSH执行", key="ssh_btn", type="primary"):
                    if ssh_host and ssh_username and ssh_password:
                        with st.spinner("通过SSH执行中..."):
                            output = run_command_on_ssh(ssh_host, ssh_port, ssh_username, ssh_password, command)
                        
                        if output:
                            st.subheader("执行结果")
                            st.code(output)
                    else:
                        st.error("请填写完整的SSH连接信息")
            else:
                st.error("未安装paramiko库，请使用 `pip install paramiko` 安装")
        
        with exec_tab4:
            # Terminal方式
            st.markdown("**使用Terminal组件显示交互式终端**")
            if has_terminal:
                if st.button("使用Terminal执行", key="terminal_btn", type="primary"):
                    st.subheader("终端执行")
                    terminal(command)
            else:
                st.error("未安装streamlit-terminal组件，请使用 `pip install streamlit-terminal` 安装")
    
    with right_col:
        # 预设配置区域
        st.subheader("预设配置")
        presets = st.session_state.get("presets", {})
        
        with st.expander("预设列表", expanded=True):
            if presets:
                preset_names = list(presets.keys())
                preset_descriptions = [f"{name} - {presets[name].get('description', '')}" for name in preset_names]
                selected_preset = st.selectbox("选择预设", preset_descriptions, key="preset_select")
                
                if selected_preset:
                    preset_name = preset_names[preset_descriptions.index(selected_preset)]
                    
                    col_apply, col_delete = st.columns(2)
                    with col_apply:
                        if st.button("应用预设", key="apply_preset"):
                            apply_preset(preset_name, presets, cb_opts, in_opts)
                    
                    with col_delete:
                        if st.button("删除预设", key="delete_preset"):
                            if preset_name in presets:
                                del presets[preset_name]
                                st.session_state["presets"] = presets
                                if "config_file" in st.session_state:
                                    with open(st.session_state["config_file"], 'w', encoding='utf-8') as f:
                                        yaml.dump({"presets": presets}, f, allow_unicode=True)
                                st.success(f"预设 '{preset_name}' 已删除")
                                st.experimental_rerun()
            else:
                st.info("没有可用的预设配置")
        
        # 保存预设
        with st.expander("保存当前配置", expanded=False):
            new_preset_name = st.text_input("预设名称", key="new_preset_name")
            new_preset_desc = st.text_input("预设描述", key="new_preset_desc")
            
            if st.button("保存为新预设", key="save_preset"):
                if new_preset_name:
                    # 收集选中的checkbox
                    selected_options = [opt.id for opt in cb_opts 
                                      if st.session_state.get(f"checkbox_{opt.id}", False)]
                    
                    save_preset(new_preset_name, new_preset_desc, cb_opts, selected_options, in_opts)
                    # 清空输入
                    st.session_state["new_preset_name"] = ""
                    st.session_state["new_preset_desc"] = ""
                    st.experimental_rerun()
                else:
                    st.error("请输入预设名称")
        
        # 操作按钮
        st.subheader("操作")
        
        if st.button("复制命令", key="copy_btn", type="secondary", help="复制命令到剪贴板"):
            import pyperclip
            try:
                pyperclip.copy(command)
                st.success("命令已复制到剪贴板")
            except Exception as e:
                st.error(f"复制失败: {e}")
        
        if st.button("退出", key="quit_btn", type="secondary", help="退出应用"):
            st.warning("Streamlit应用无法直接退出，请关闭浏览器标签页")

# 预设配置示例
PRESET_CONFIGS = {
    "默认配置": {
        "description": "基础配置示例",
        "checkbox_options": ["feature1", "feature3"],
        "input_values": {
            "number": "100",
            "text": "默认值",
            "path": "/tmp",
            "choice": "A"
        }
    },
    "快速模式": {
        "description": "优化性能的配置",
        "checkbox_options": ["feature1", "feature2", "feature4"],
        "input_values": {
            "number": "200",
            "text": "fast",
            "path": "/var/tmp",
            "choice": "B"
        }
    },
    "调试模式": {
        "description": "用于开发调试",
        "checkbox_options": ["feature2", "feature4", "feature5"],
        "input_values": {
            "number": "50",
            "text": "debug",
            "path": "./logs",
            "choice": "C"
        }
    }
}

# 运行应用
if __name__ == "__main__":
    # 在界面顶部显示组件安装状态
    st.sidebar.title("组件状态")
    st.sidebar.markdown(f"- WebTerm: {'已安装 ✅' if has_webterm else '未安装 ❌'}")
    st.sidebar.markdown(f"- Ace编辑器: {'已安装 ✅' if has_ace else '未安装 ❌'}")
    st.sidebar.markdown(f"- SSH (paramiko): {'已安装 ✅' if has_paramiko else '未安装 ❌'}")
    st.sidebar.markdown(f"- Terminal: {'已安装 ✅' if has_terminal else '未安装 ❌'}")
    
    if not any([has_webterm, has_paramiko, has_terminal]):
        st.sidebar.error("请安装至少一个执行组件:")
        st.sidebar.code("pip install streamlit-webterm paramiko streamlit-terminal")
    
    # 演示用例
    parser = argparse.ArgumentParser(description='Test argument parser')
    parser.add_argument('--feature1', action='store_true', help='功能选项1')
    parser.add_argument('--feature2', action='store_true', help='功能选项2')
    parser.add_argument('--feature3', action='store_true', help='功能选项3')
    parser.add_argument('--feature4', action='store_true', help='功能选项4')
    parser.add_argument('--feature5', action='store_true', help='功能选项5')
    parser.add_argument('--number', type=int, default=100, help='数字参数')
    parser.add_argument('--text', type=str, help='文本参数')
    parser.add_argument('--path', type=str, help='路径参数')
    parser.add_argument('--choice', choices=['A', 'B', 'C'], default='A', help='选择参数')

    create_streamlit_config_app(
        program="demo_program.py",
        title="Streamlit四合一配置界面演示",
        parser=parser,
        preset_configs=PRESET_CONFIGS
    )