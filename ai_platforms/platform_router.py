# -*- coding: utf-8 -*-

import logging
from typing import Dict, Optional, Any
from .base_platform import BasePlatform
from .llm_direct import LLMDirectPlatform

logger = logging.getLogger(__name__)

class PlatformRouter:
    """
    AI平台路由器
    
    负责根据用户配置选择合适的AI平台，管理多个平台实例，
    并提供统一的消息路由接口。
    """
    
    def __init__(self, user_platform_mapping: Dict[str, Dict[str, str]]):
        """
        初始化平台路由器
        
        Args:
            user_platform_mapping (dict): 用户平台映射配置
                格式: {user_id: {'role': 'role_name', 'platform': 'platform_name'}}
        """
        self.user_platform_mapping = user_platform_mapping
        self.platform_instances: Dict[str, BasePlatform] = {}
        self.default_platform = 'llm_direct'
        
        # 初始化所有平台
        self._init_platforms()
        
        logger.info(f"PlatformRouter initialized with {len(self.platform_instances)} platforms")
        logger.info(f"User mapping contains {len(user_platform_mapping)} users")
    
    def _init_platforms(self):
        """初始化所有平台实例"""
        # 平台类映射
        platform_classes = {
            'llm_direct': LLMDirectPlatform,
        }
        
        # 延迟导入其他平台，避免循环依赖
        try:
            from . import get_coze_platform
            coze_class = get_coze_platform()
            if coze_class:
                platform_classes['coze'] = coze_class
        except Exception as e:
            logger.warning(f"Coze platform not available: {e}")
        
        try:
            from . import get_dify_platform
            dify_class = get_dify_platform()
            if dify_class:
                platform_classes['dify'] = dify_class
        except Exception as e:
            logger.warning(f"Dify platform not available: {e}")
        
        # 初始化各平台实例
        for platform_name, platform_class in platform_classes.items():
            try:
                self.platform_instances[platform_name] = platform_class()
                logger.info(f"Successfully initialized {platform_name} platform")
            except Exception as e:
                logger.error(f"Failed to initialize {platform_name} platform: {e}")
                # 对于非默认平台，使用默认平台作为降级方案
                if platform_name != self.default_platform:
                    logger.warning(f"Using {self.default_platform} as fallback for {platform_name}")
                    # 注意：这里不直接赋值，而是在get_user_platform中处理降级
    
    def get_user_platform(self, user_id: str) -> Optional[BasePlatform]:
        """
        根据用户ID获取应使用的平台实例
        
        Args:
            user_id (str): 用户ID
        
        Returns:
            BasePlatform: 平台实例，如果找不到则返回默认平台
        """
        # 获取用户配置的平台
        user_config = self.user_platform_mapping.get(user_id, {})
        platform_name = user_config.get('platform', self.default_platform)
        
        # 获取平台实例
        platform = self.platform_instances.get(platform_name)
        
        if not platform:
            logger.warning(f"Platform {platform_name} not available for user {user_id}, fallback to {self.default_platform}")
            platform = self.platform_instances.get(self.default_platform)
        
        if not platform:
            logger.error(f"No available platform for user {user_id}")
            return None
        
        logger.debug(f"Selected platform {platform.get_platform_name()} for user {user_id}")
        return platform
    
    def route_message(self, user_id: str, message: str, store_context: bool = True, is_summary: bool = False) -> str:
        """
        路由消息到对应平台
        
        Args:
            user_id (str): 用户ID
            message (str): 用户消息
            store_context (bool): 是否存储上下文，默认True
            is_summary (bool): 是否为总结任务，默认False
        
        Returns:
            str: AI回复
        """
        platform = self.get_user_platform(user_id)
        if not platform:
            return "抱歉，AI服务暂时不可用。"
        
        try:
            logger.debug(f"Routing message from {user_id} to {platform.get_platform_name()}")
            response = platform.get_response(message, user_id, store_context=store_context, is_summary=is_summary)
            return response if response else "抱歉，未能获取到有效回复。"
        except Exception as e:
            logger.error(f"Error routing message for user {user_id}: {e}")
            error_response = platform.handle_error(e, user_id)
            return error_response if error_response else "抱歉，处理您的请求时发生错误。"
    
    def get_user_config(self, user_id: str) -> Dict[str, str]:
        """
        获取用户配置
        
        Args:
            user_id (str): 用户ID
        
        Returns:
            dict: 用户配置字典，包含role和platform
        """
        return self.user_platform_mapping.get(user_id, {
            'role': 'default',
            'platform': self.default_platform
        })
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """
        获取平台统计信息
        
        Returns:
            dict: 包含各平台状态的统计信息
        """
        stats = {
            'total_platforms': len(self.platform_instances),
            'available_platforms': [],
            'user_distribution': {},
            'default_platform': self.default_platform
        }
        
        # 统计可用平台
        for name, platform in self.platform_instances.items():
            if platform:
                stats['available_platforms'].append({
                    'name': name,
                    'class': platform.__class__.__name__,
                    'info': platform.get_platform_info()
                })
        
        # 统计用户分布
        for user_id, config in self.user_platform_mapping.items():
            platform_name = config.get('platform', self.default_platform)
            if platform_name not in stats['user_distribution']:
                stats['user_distribution'][platform_name] = 0
            stats['user_distribution'][platform_name] += 1
        
        return stats
    
    def test_all_platforms(self) -> Dict[str, bool]:
        """
        测试所有平台连接状态
        
        Returns:
            dict: 各平台的连接测试结果
        """
        results = {}
        for name, platform in self.platform_instances.items():
            if platform:
                try:
                    results[name] = platform.test_connection()
                    logger.info(f"Platform {name} connection test: {'PASS' if results[name] else 'FAIL'}")
                except Exception as e:
                    results[name] = False
                    logger.error(f"Platform {name} connection test failed: {e}")
            else:
                results[name] = False
        
        return results
    
    def update_user_mapping(self, user_platform_mapping: Dict[str, Dict[str, str]]):
        """
        更新用户平台映射
        
        Args:
            user_platform_mapping (dict): 新的用户平台映射配置
        """
        self.user_platform_mapping = user_platform_mapping
        logger.info(f"Updated user platform mapping for {len(user_platform_mapping)} users")
    
    def add_platform(self, name: str, platform_class, config=None):
        """
        动态添加新平台
        
        Args:
            name (str): 平台名称
            platform_class: 平台类
            config (dict, optional): 平台配置
        """
        try:
            self.platform_instances[name] = platform_class(config)
            logger.info(f"Successfully added platform: {name}")
        except Exception as e:
            logger.error(f"Failed to add platform {name}: {e}")
            raise 