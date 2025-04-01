import socket

# 固定端口号
DEFAULT_PORT = 8501

def is_port_in_use(port: int = DEFAULT_PORT) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0 