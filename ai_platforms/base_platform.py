# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BasePlatform(ABC):
    """
    AI平台基础抽象类
    
    所有AI平台实现都应该继承此类，并实现必要的抽象方法。
    提供统一的接口规范和通用的错误处理机制。
    """
    
    def __init__(self, config=None):
        """
        初始化平台
        
        Args:
            config (dict, optional): 平台配置字典
        """
        self.config = config or {}
        self.platform_name = self.get_platform_name()
        
        # 验证配置
        try:
            self.validate_config()
            logger.info(f"成功初始化 {self.platform_name} 平台")
        except Exception as e:
            logger.error(f"初始化 {self.platform_name} 平台失败: {e}")
            raise
    
    @abstractmethod
    def get_response(self, message, user_id, store_context=True, is_summary=False, system_prompt=None):
        """
        获取AI响应
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID  
            store_context (bool): 是否存储上下文，默认True
            is_summary (bool): 是否为总结任务，默认False
            system_prompt (str): 系统提示词，默认None
        
        Returns:
            str: AI回复内容
        
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        pass
    
    @abstractmethod
    def validate_config(self):
        """
        验证配置是否有效
        
        Raises:
            ValueError: 配置无效时抛出
            NotImplementedError: 子类必须实现此方法
        """
        pass
    
    def handle_error(self, error, user_id):
        """
        统一错误处理
        
        Args:
            error (Exception): 发生的错误
            user_id (str): 用户ID
        
        Returns:
            str: 错误提示消息
        """
        error_msg = str(error)
        logger.error(f"平台 {self.platform_name} 用户 {user_id} 发生错误: {error_msg}")
        
        # 根据错误类型返回不同的提示
        if "rate limit" in error_msg.lower():
            return "抱歉，AI服务访问频率过高，请稍后再试。"
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            return "抱歉，AI服务余额不足，请联系管理员。"
        elif "timeout" in error_msg.lower():
            return "抱歉，AI服务响应超时，请稍后再试。"
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return "抱歉，AI服务认证失败，请联系管理员。"
        else:
            return "抱歉，AI服务暂时不可用，请稍后再试。"
    
    def get_platform_name(self):
        """
        获取平台名称
        
        Returns:
            str: 平台名称
        """
        class_name = self.__class__.__name__
        # 去掉Platform后缀，转换为小写
        if class_name.endswith('Platform'):
            return class_name[:-8].lower()
        return class_name.lower()
    
    def get_platform_info(self):
        """
        获取平台信息
        
        Returns:
            dict: 包含平台名称和配置信息的字典
        """
        return {
            'name': self.platform_name,
            'class': self.__class__.__name__,
            'config_keys': list(self.config.keys()) if self.config else []
        }
    
    def test_connection(self):
        """
        测试平台连接
        
        Returns:
            bool: 连接是否正常
        """
        try:
            # 发送一个简单的测试消息
            test_response = self.get_response(
                message="测试连接", 
                user_id="test_user", 
                store_context=False,
                is_summary=False,
                system_prompt=None
            )
            return bool(test_response and len(test_response.strip()) > 0)
        except Exception as e:
            logger.error(f"平台 {self.platform_name} 连接测试失败: {e}")
            return False 