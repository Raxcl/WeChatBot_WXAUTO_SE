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
        
        logger.info(f"平台路由器初始化完成，共 {len(self.platform_instances)} 个平台")
        logger.info(f"用户映射包含 {len(user_platform_mapping)} 个用户")
    
    def _init_platforms(self):
        """初始化所有平台实例"""
        # 平台类映射
        platform_classes: Dict[str, Any] = {
            'llm_direct': LLMDirectPlatform,
        }
        
        # 延迟导入其他平台，避免循环依赖
        try:
            from .coze_platform import CozePlatform
            platform_classes['coze'] = CozePlatform
        except Exception as e:
            logger.warning(f"Coze 平台不可用: {e}")
        
        # Dify平台暂未实现
        # try:
        #     from .dify_platform import DifyPlatform
        #     platform_classes['dify'] = DifyPlatform
        # except Exception as e:
        #     logger.warning(f"Dify 平台不可用: {e}")
        
        # 初始化各平台实例
        for platform_name, platform_class in platform_classes.items():
            try:
                self.platform_instances[platform_name] = platform_class()
                logger.info(f"成功初始化 {platform_name} 平台")
            except Exception as e:
                logger.error(f"初始化 {platform_name} 平台失败: {e}")
                # 直接跳过失败的平台，不使用降级
    
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
            logger.error(f"用户 {user_id} 配置的平台 {platform_name} 不可用")
            return None
        
        logger.debug(f"为用户 {user_id} 选择平台 {platform.get_platform_name()}")
        return platform
    
    def route_message(self, user_id: str, message: str, store_context: bool = True, is_summary: bool = False, system_prompt: Optional[str] = None) -> str:
        """
        路由消息到对应平台
        
        Args:
            user_id (str): 用户ID
            message (str): 用户消息
            store_context (bool): 是否存储上下文，默认True
            is_summary (bool): 是否为总结任务，默认False
            system_prompt (str): 系统提示词，默认None
        
        Returns:
            str: AI回复
        """
        platform = self.get_user_platform(user_id)
        if not platform:
            return "抱歉，AI服务暂时不可用。"
        
        try:
            logger.info(f"将用户 {user_id} 的消息路由到 {platform.get_platform_name()}")
            logger.info(f"message: {message}")
            logger.info(f"store_context: {store_context}")
            logger.info(f"is_summary: {is_summary}")
            logger.info(f"system_prompt: {system_prompt}")
            response = platform.get_response(
                message, 
                user_id, 
                store_context=store_context, 
                is_summary=is_summary,
                system_prompt=system_prompt
            )
            return response if response else "抱歉，未能获取到有效回复。"
        except Exception as e:
            logger.error(f"为用户 {user_id} 路由消息时发生错误: {e}")
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
                    logger.info(f"平台 {name} 连接测试: {'通过' if results[name] else '失败'}")
                except Exception as e:
                    results[name] = False
                    logger.error(f"平台 {name} 连接测试失败: {e}")
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
        logger.info(f"已更新 {len(user_platform_mapping)} 个用户的平台映射")
    
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
            logger.info(f"成功添加平台: {name}")
        except Exception as e:
            logger.error(f"添加平台 {name} 失败: {e}")
            raise


# 全局路由器实例
_global_router: Optional[PlatformRouter] = None


def _load_user_platform_mapping():
    """
    从配置文件加载用户平台映射
    
    Returns:
        dict: 用户平台映射字典
    """
    try:
        # 导入配置
        import sys
        import os
        # 添加项目根目录到路径
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from config import LISTEN_LIST
        
        # 转换LISTEN_LIST为字典格式
        user_mapping = {}
        for entry in LISTEN_LIST:
            if len(entry) >= 3:
                user_id, role, platform = entry[0], entry[1], entry[2]
                user_mapping[user_id] = {
                    'role': role,
                    'platform': platform
                }
            elif len(entry) >= 2:
                user_id, role = entry[0], entry[1]
                user_mapping[user_id] = {
                    'role': role,
                    'platform': 'llm_direct'  # 默认平台
                }
        
        logger.info(f"已加载 {len(user_mapping)} 个用户的平台映射")
        return user_mapping
        
    except Exception as e:
        logger.error(f"加载用户平台映射失败: {e}")
        return {}


def _get_global_router() -> PlatformRouter:
    """
    获取全局路由器实例（单例模式）
    
    Returns:
        PlatformRouter: 路由器实例
    """
    global _global_router
    
    if _global_router is None:
        user_mapping = _load_user_platform_mapping()
        _global_router = PlatformRouter(user_mapping)
        logger.info("全局平台路由器初始化完成")
    
    return _global_router


def get_platform_response(message: str, user_id: str, store_context: bool = True, is_summary: bool = False, system_prompt: Optional[str] = None) -> str:
    """
    统一的平台响应函数（供主程序调用）
    
    Args:
        message (str): 用户消息
        user_id (str): 用户ID
        store_context (bool): 是否存储上下文，默认True
        is_summary (bool): 是否为总结任务，默认False
        system_prompt (str): 系统提示词，默认None
    
    Returns:
        str: AI回复
    """
    try:
        router = _get_global_router()
        return router.route_message(
            user_id, 
            message, 
            store_context=store_context, 
            is_summary=is_summary,
            system_prompt=system_prompt
        )
    except Exception as e:
        logger.error(f"用户 {user_id} 的平台路由失败: {e}")
        return "抱歉，AI服务暂时不可用，请检查平台配置。"


def get_platform_stats() -> Dict[str, Any]:
    """
    获取平台统计信息
    
    Returns:
        dict: 平台统计信息
    """
    try:
        router = _get_global_router()
        return router.get_platform_stats()
    except Exception as e:
        logger.error(f"获取平台统计信息失败: {e}")
        return {'error': str(e)}


def test_all_platforms() -> Dict[str, Any]:
    """
    测试所有平台连接
    
    Returns:
        dict: 各平台连接测试结果
    """
    try:
        router = _get_global_router()
        return router.test_all_platforms()
    except Exception as e:
        logger.error(f"测试平台连接失败: {e}")
        return {'error': str(e)}


def reload_user_mapping():
    """
    重新加载用户平台映射配置
    """
    global _global_router
    try:
        user_mapping = _load_user_platform_mapping()
        if _global_router:
            _global_router.update_user_mapping(user_mapping)
            logger.info("用户平台映射重新加载完成")
        else:
            # 如果路由器未初始化，创建新的
            _global_router = PlatformRouter(user_mapping)
            logger.info("创建全局平台路由器，使用新的映射配置")
    except Exception as e:
        logger.error(f"重新加载用户映射失败: {e}")
        raise 