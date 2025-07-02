# -*- coding: utf-8 -*-

"""
AI平台管理模块

负责解析LISTEN_LIST配置，管理用户平台映射，
创建和管理路由器，提供配置验证和统计功能。
"""

import logging
from typing import Dict, List, Tuple, Any
from . import PlatformRouter, BasePlatform

logger = logging.getLogger(__name__)

def parse_listen_list(listen_list: List[List[str]]) -> Dict[str, Dict[str, str]]:
    """
    解析监听列表，提取平台配置
    
    Args:
        listen_list (list): LISTEN_LIST配置
            支持格式:
            - ['用户名', '角色', '平台']              # 必须使用3元素格式
    
    Returns:
        dict: 用户平台映射配置
            格式: {user_id: {'role': 'role_name', 'platform': 'platform_name'}}
    
    Raises:
        ValueError: 配置格式错误时抛出
    """
    user_platform_mapping = {}
    
    for i, entry in enumerate(listen_list):
        try:
            if len(entry) != 3:
                raise ValueError(f"Invalid entry format: {entry}. Must have exactly 3 elements: ['用户名', '角色', '平台']")
            
            # 必须使用3元素格式
            username, role, platform = entry
            
            # 验证平台名称
            valid_platforms = ['llm_direct', 'coze', 'dify']
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform '{platform}' for user {username}. Valid platforms: {valid_platforms}")
            
            # 检查用户名是否重复
            if username in user_platform_mapping:
                logger.warning(f"Duplicate user '{username}' found in LISTEN_LIST, overwriting previous config")
            
            user_platform_mapping[username] = {
                'role': role,
                'platform': platform
            }
            
            logger.debug(f"Mapped user '{username}' to role '{role}' on platform '{platform}'")
            
        except Exception as e:
            logger.error(f"Error parsing LISTEN_LIST entry {i}: {entry}, error: {e}")
            raise ValueError(f"Invalid LISTEN_LIST entry at index {i}: {entry}") from e
    
    logger.info(f"Successfully parsed {len(user_platform_mapping)} users from LISTEN_LIST")
    return user_platform_mapping

def create_platform_router(listen_list: List[List[str]]) -> PlatformRouter:
    """
    创建平台路由器实例
    
    Args:
        listen_list (list): LISTEN_LIST配置
    
    Returns:
        PlatformRouter: 配置好的平台路由器实例
    """
    try:
        # 解析配置
        user_platform_mapping = parse_listen_list(listen_list)
        
        # 创建路由器
        router = PlatformRouter(user_platform_mapping)
        
        logger.info("Platform router created successfully")
        return router
        
    except Exception as e:
        logger.error(f"Failed to create platform router: {e}")
        raise

def validate_platform_configs() -> Dict[str, bool]:
    """
    验证所有平台配置的有效性
    
    Returns:
        dict: 各平台配置验证结果
    """
    results = {}
    
    # 验证LLM Direct配置
    try:
        from . import LLMDirectPlatform
        platform = LLMDirectPlatform()
        results['llm_direct'] = True
        logger.info("LLM Direct platform config validation: PASS")
    except Exception as e:
        results['llm_direct'] = False
        logger.error(f"LLM Direct platform config validation: FAIL - {e}")
    
    # 验证Coze配置
    try:
        from . import get_coze_platform
        coze_class = get_coze_platform()
        if coze_class:
            platform = coze_class()
            results['coze'] = True
            logger.info("Coze platform config validation: PASS")
        else:
            results['coze'] = False
            logger.warning("Coze platform not available")
    except Exception as e:
        results['coze'] = False
        logger.error(f"Coze platform config validation: FAIL - {e}")
    
    # 验证Dify配置
    try:
        from . import get_dify_platform
        dify_class = get_dify_platform()
        if dify_class:
            platform = dify_class()
            results['dify'] = True
            logger.info("Dify platform config validation: PASS")
        else:
            results['dify'] = False
            logger.warning("Dify platform not available")
    except Exception as e:
        results['dify'] = False
        logger.error(f"Dify platform config validation: FAIL - {e}")
    
    return results

def get_platform_usage_stats(router: PlatformRouter) -> Dict[str, Any]:
    """
    获取平台使用统计
    
    Args:
        router (PlatformRouter): 平台路由器实例
    
    Returns:
        dict: 统计信息
    """
    try:
        stats = router.get_platform_stats()
        
        # 添加额外的统计信息
        total_users = sum(stats['user_distribution'].values())
        stats['total_users'] = total_users
        
        # 计算各平台使用比例
        if total_users > 0:
            stats['platform_percentages'] = {
                platform: round((count / total_users) * 100, 2)
                for platform, count in stats['user_distribution'].items()
            }
        else:
            stats['platform_percentages'] = {}
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting platform usage stats: {e}")
        return {}

def print_platform_info(router: PlatformRouter):
    """
    打印平台信息和统计
    
    Args:
        router (PlatformRouter): 平台路由器实例
    """
    print("\n" + "="*50)
    print("🚀 AI平台集成状态报告")
    print("="*50)
    
    # 平台状态
    stats = get_platform_usage_stats(router)
    print(f"\n📊 平台统计:")
    print(f"  总平台数: {stats.get('total_platforms', 0)}")
    print(f"  总用户数: {stats.get('total_users', 0)}")
    
    # 可用平台
    available_platforms = stats.get('available_platforms', [])
    print(f"\n✅ 可用平台 ({len(available_platforms)}):")
    for platform in available_platforms:
        print(f"  - {platform['name']} ({platform['class']})")
    
    # 用户分布
    user_dist = stats.get('user_distribution', {})
    platform_pct = stats.get('platform_percentages', {})
    if user_dist:
        print(f"\n👥 用户分布:")
        for platform, count in user_dist.items():
            percentage = platform_pct.get(platform, 0)
            print(f"  - {platform}: {count} 用户 ({percentage}%)")
    
    # 连接测试
    print(f"\n🔗 连接测试:")
    test_results = router.test_all_platforms()
    for platform, status in test_results.items():
        status_icon = "✅" if status else "❌"
        status_text = "PASS" if status else "FAIL"
        print(f"  {status_icon} {platform}: {status_text}")
    
    print("\n" + "="*50)

# 全局路由器实例
_global_router = None

def get_global_router() -> PlatformRouter:
    """
    获取全局路由器实例
    
    Returns:
        PlatformRouter: 全局路由器实例
    """
    global _global_router
    if _global_router is None:
        raise RuntimeError("Global router not initialized. Call init_global_router() first.")
    return _global_router

def init_global_router(listen_list: List[List[str]]) -> PlatformRouter:
    """
    初始化全局路由器
    
    Args:
        listen_list (list): LISTEN_LIST配置
    
    Returns:
        PlatformRouter: 初始化的全局路由器实例
    """
    global _global_router
    _global_router = create_platform_router(listen_list)
    logger.info("Global platform router initialized")
    return _global_router

def route_user_message(user_id: str, message: str, **kwargs) -> str:
    """
    路由用户消息的便捷函数
    
    Args:
        user_id (str): 用户ID
        message (str): 用户消息
        **kwargs: 其他参数
    
    Returns:
        str: AI回复
    """
    router = get_global_router()
    return router.route_message(user_id, message, **kwargs) 