# -*- coding: utf-8 -*-

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BasePlatform(ABC):
    """
    AI平台基类
    
    提供通用的上下文管理、系统提示词处理等功能
    子类只需要实现具体的API调用逻辑
    """
    
    def __init__(self, config):
        """初始化平台"""
        self.config = config or {}
        
        # 导入bot模块用于上下文管理（延迟导入避免循环依赖）
        self._bot_module = None
        self._context_limit = None
        
        logger.info(f"{self.__class__.__name__} 初始化完成")
    
    def _get_bot_module(self):
        """延迟加载bot模块避免循环依赖"""
        if self._bot_module is None:
            try:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                import bot
                self._bot_module = bot
                
                # 获取上下文限制
                from config import MAX_GROUPS
                self._context_limit = MAX_GROUPS * 2
                
            except ImportError as e:
                logger.error(f"无法导入bot模块: {e}")
                raise
        return self._bot_module
    
    @abstractmethod
    def validate_config(self):
        """验证配置是否有效（子类必须实现）"""
        pass
    
    @abstractmethod
    def _call_api(self, messages, user_id, **kwargs):
        """
        调用具体平台的API（子类必须实现）
        
        Args:
            messages (list): 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            user_id (str): 用户ID
            **kwargs: 其他平台特定参数
            
        Returns:
            str: AI回复内容
        """
        pass
    
    def get_response(self, message, user_id, store_context=True, is_summary=False, system_prompt=None):
        """
        获取AI响应（通用逻辑）
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文
            is_summary (bool): 是否为总结任务
            system_prompt (str): 系统提示词
        
        Returns:
            str: AI回复内容
        """
        try:
            bot = self._get_bot_module()
            
            logger.info(f"调用 {self.__class__.__name__} API - ID: {user_id}, 存储上下文: {store_context}, 消息: {message[:100]}...")
            
            # 构建消息列表
            messages_to_send = []
            
            if store_context:
                # 处理需要上下文的常规聊天消息
                messages_to_send = self._build_context_messages(message, user_id, system_prompt)
            else:
                # 处理工具调用（如提醒解析、总结）
                if system_prompt:
                    messages_to_send.append({"role": "system", "content": system_prompt})
                    logger.info(f"工具调用使用自定义系统提示词 - ID: {user_id}")
                
                messages_to_send.append({"role": "user", "content": message})
                logger.info(f"工具调用 (store_context=False)，ID: {user_id}")
            
            # 调用具体平台的API
            reply = self._call_api(messages_to_send, user_id, is_summary=is_summary)
            
            # 存储助手回复到上下文中
            if store_context:
                self._save_assistant_response(user_id, reply)
            
            return reply
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} 调用失败 (ID: {user_id}): {str(e)}", exc_info=True)
            return "抱歉，我现在有点忙，稍后再聊吧。"
    
    def _build_context_messages(self, message, user_id, system_prompt=None):
        """构建包含上下文的消息列表"""
        bot = self._get_bot_module()
        
        # 重新加载聊天上下文
        bot.load_chat_contexts()
        
        messages_to_send = []
        
        # 1. 获取系统提示词
        try:
            if system_prompt:
                messages_to_send.append({"role": "system", "content": system_prompt})
                logger.info(f"使用自定义系统提示词 - 用户: {user_id}")
            else:
                user_prompt = bot.get_user_prompt(user_id)
                messages_to_send.append({"role": "system", "content": user_prompt})
        except FileNotFoundError as e:
            logger.error(f"用户 {user_id} 的提示文件错误: {e}，使用默认提示。")
            fallback_prompt = system_prompt if system_prompt else "你是一个乐于助人的助手。"
            messages_to_send.append({"role": "system", "content": fallback_prompt})
        
        # 2. 管理聊天历史记录
        with bot.queue_lock:
            if user_id not in bot.chat_contexts:
                bot.chat_contexts[user_id] = []
            
            # 获取历史记录并裁剪
            history = list(bot.chat_contexts.get(user_id, []))
            if len(history) > self._context_limit:
                history = history[-self._context_limit:]
            
            # 添加历史消息
            messages_to_send.extend(history)
            
            # 添加当前用户消息
            messages_to_send.append({"role": "user", "content": message})
            
            # 更新持久上下文
            bot.chat_contexts[user_id].append({"role": "user", "content": message})
            if len(bot.chat_contexts[user_id]) > self._context_limit + 1:
                bot.chat_contexts[user_id] = bot.chat_contexts[user_id][-(self._context_limit + 1):]
            
            # 保存上下文
            bot.save_chat_contexts()
        
        return messages_to_send
    
    def _save_assistant_response(self, user_id, reply):
        """保存助手回复到上下文"""
        bot = self._get_bot_module()
        
        with bot.queue_lock:
            if user_id not in bot.chat_contexts:
                bot.chat_contexts[user_id] = []
            
            bot.chat_contexts[user_id].append({"role": "assistant", "content": reply})
            
            if len(bot.chat_contexts[user_id]) > self._context_limit:
                bot.chat_contexts[user_id] = bot.chat_contexts[user_id][-self._context_limit:]
            
            bot.save_chat_contexts()
    
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
        logger.error(f"平台 {self.__class__.__name__} 用户 {user_id} 发生错误: {error_msg}")
        
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
            'name': self.get_platform_name(),
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
            logger.error(f"平台 {self.get_platform_name()} 连接测试失败: {e}")
            return False 