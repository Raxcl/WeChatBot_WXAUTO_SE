# -*- coding: utf-8 -*-

"""
AI Platform Integration Module
多AI平台集成模块

This module provides a unified interface for integrating multiple AI platforms
including LLM Direct, Coze, and Dify platforms.
"""

from .base_platform import BasePlatform
from .platform_router import PlatformRouter
from .llm_direct import LLMDirectPlatform

# 导出配置相关函数
from .manager import (
    parse_listen_list,
    create_platform_router,
    validate_platform_configs,
    print_platform_info,
    init_global_router,
    get_global_router,
    route_user_message
)

# 延迟导入，避免循环依赖
def get_coze_platform():
    """延迟导入Coze平台"""
    try:
        from .coze_platform import CozePlatform
        return CozePlatform
    except ImportError as e:
        print(f"Coze platform not available: {e}")
        return None

def get_dify_platform():
    """延迟导入Dify平台"""
    try:
        from .dify_platform import DifyPlatform
        return DifyPlatform
    except ImportError as e:
        print(f"Dify platform not available: {e}")
        return None

__all__ = [
    # 核心类
    'BasePlatform',
    'PlatformRouter', 
    'LLMDirectPlatform',
    
    # 配置函数
    'parse_listen_list',
    'create_platform_router',
    'validate_platform_configs',
    'print_platform_info',
    'init_global_router',
    'get_global_router',
    'route_user_message',
    
    # 延迟加载函数
    'get_coze_platform',
    'get_dify_platform'
]

__version__ = '1.0.0' 