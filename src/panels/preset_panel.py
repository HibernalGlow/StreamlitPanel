import streamlit as st
from src.components.base_panel import BasePanel
from typing import Dict

class PresetPanel(BasePanel):
    """预设面板类"""
    def __init__(self, title: str = "预设配置", icon: str = "⚙️", style: str = "lightblue"):
        super().__init__(title, icon, style)
        self.is_visible = False  # 默认隐藏
        self.presets = {
            "低配模式": {"threads": 1, "batch": 1},
            "中配模式": {"threads": 8, "batch": 8},
            "高配模式": {"threads": 16, "batch": 16}
        }
        
    def render(self, container):
        if not self.is_visible:
            return
            
        with container:
            with st.expander(f"{self.icon} {self.title}", expanded=self.is_expanded):
                # 创建三列布局
                cols = st.columns(3)
                
                # 在每个列中添加预设按钮
                for i, (preset_name, config) in enumerate(self.presets.items()):
                    with cols[i]:
                        if st.button(preset_name, key=f"preset_{preset_name}"):
                            # 更新性能配置
                            self._update_performance_config(config)
                            st.success(f"已切换到{preset_name}")
                
                # 添加自定义配置
                st.subheader("自定义配置")
                custom_threads = st.slider("线程数", 1, 16, 1)
                custom_batch = st.slider("批处理大小", 1, 100, 1)
                
                if st.button("应用自定义配置"):
                    self._update_performance_config({
                        "threads": custom_threads,
                        "batch": custom_batch
                    })
                    st.success("已应用自定义配置")
    
    def _update_performance_config(self, config: Dict):
        """更新性能配置"""
        try:
            # 这里可以添加与performance_config.py的交互逻辑
            pass
        except Exception as e:
            st.error(f"更新配置失败: {e}") 