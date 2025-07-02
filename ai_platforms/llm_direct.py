# -*- coding: utf-8 -*-

import logging
import json
import re
from openai import OpenAI
from .base_platform import BasePlatform

# 导入现有的配置和函数
try:
    import sys
    import os
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import (
        DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MODEL, 
        TEMPERATURE, MAX_TOKEN, MAX_GROUPS
    )
    # 导入现有的上下文管理函数
    from bot import (
        chat_contexts, queue_lock, get_user_prompt,
        load_chat_contexts, save_chat_contexts
    )
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    # 设置默认值，避免程序崩溃
    DEEPSEEK_API_KEY = ""
    DEEPSEEK_BASE_URL = ""
    MODEL = ""
    TEMPERATURE = 1.1
    MAX_TOKEN = 2000
    MAX_GROUPS = 5

logger = logging.getLogger(__name__)

class LLMDirectPlatform(BasePlatform):
    """
    大模型直连平台实现
    
    直接调用大模型API（如DeepSeek、OpenAI等），
    复用现有的逻辑和上下文管理机制。
    """
    
    def __init__(self, config=None):
        """初始化大模型直连平台"""
        # 使用现有配置
        if config is None:
            config = {
                'api_key': DEEPSEEK_API_KEY,
                'base_url': DEEPSEEK_BASE_URL,
                'model': MODEL,
                'temperature': TEMPERATURE,
                'max_tokens': MAX_TOKEN,
                'max_groups': MAX_GROUPS
            }
        
        super().__init__(config)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.config['api_key'],
            base_url=self.config['base_url']
        )
        
        logger.info(f"LLM Direct platform initialized with model: {self.config['model']}")
    
    def validate_config(self):
        """验证配置是否有效"""
        required_keys = ['api_key', 'base_url', 'model']
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")
        
        if not self.config['api_key'] or self.config['api_key'] == "your-api-key":
            raise ValueError("Invalid API key in config")
    
    def get_response(self, message, user_id, store_context=True, is_summary=False):
        """
        获取大模型响应
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文
            is_summary (bool): 是否为总结任务
        
        Returns:
            str: AI回复内容
        """
        try:
            # 重新加载聊天上下文
            load_chat_contexts()
            
            logger.info(f"LLM Direct API call - ID: {user_id}, store_context: {store_context}, message: {message[:100]}...")
            
            messages_to_send = []
            context_limit = self.config.get('max_groups', MAX_GROUPS) * 2
            
            if store_context:
                # 处理需要上下文的常规聊天消息
                try:
                    user_prompt = get_user_prompt(user_id)
                    messages_to_send.append({"role": "system", "content": user_prompt})
                except FileNotFoundError as e:
                    logger.error(f"User {user_id} prompt file error: {e}, using default prompt.")
                    messages_to_send.append({"role": "system", "content": "你是一个乐于助人的助手。"})
                
                # 管理并检索聊天历史记录
                with queue_lock:
                    if user_id not in chat_contexts:
                        chat_contexts[user_id] = []
                    
                    # 获取现有历史记录
                    history = list(chat_contexts.get(user_id, []))
                    
                    # 如果历史记录超过限制，则进行裁剪
                    if len(history) > context_limit:
                        history = history[-context_limit:]
                    
                    # 将历史消息添加到API请求列表中
                    messages_to_send.extend(history)
                    
                    # 将当前用户消息添加到API请求列表中
                    messages_to_send.append({"role": "user", "content": message})
                    
                    # 更新持久上下文
                    chat_contexts[user_id].append({"role": "user", "content": message})
                    if len(chat_contexts[user_id]) > context_limit + 1:
                        chat_contexts[user_id] = chat_contexts[user_id][-(context_limit + 1):]
                    
                    # 保存上下文到文件
                    save_chat_contexts()
            else:
                # 处理工具调用（如提醒解析、总结）
                messages_to_send.append({"role": "user", "content": message})
                logger.info(f"Tool call (store_context=False), ID: {user_id}. Only sending provided message.")
            
            # 调用API
            reply = self._call_api_with_retry(messages_to_send, user_id, is_summary=is_summary)
            
            # 如果需要，存储助手回复到上下文中
            if store_context:
                with queue_lock:
                    if user_id not in chat_contexts:
                        chat_contexts[user_id] = []
                    
                    chat_contexts[user_id].append({"role": "assistant", "content": reply})
                    
                    if len(chat_contexts[user_id]) > context_limit:
                        chat_contexts[user_id] = chat_contexts[user_id][-context_limit:]
                    
                    # 保存上下文到文件
                    save_chat_contexts()
            
            return reply
            
        except Exception as e:
            logger.error(f"LLM Direct call failed (ID: {user_id}): {str(e)}", exc_info=True)
            return self.handle_error(e, user_id)
    
    def _call_api_with_retry(self, messages_to_send, user_id, max_retries=2, is_summary=False):
        """
        调用API并在失败时重试
        
        Args:
            messages_to_send (list): 要发送给API的消息列表
            user_id (str): 用户ID
            max_retries (int): 最大重试次数
            is_summary (bool): 是否为总结任务
        
        Returns:
            str: API返回的文本回复
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                logger.debug(f"Sending to API (ID: {user_id}): {messages_to_send}")
                
                response = self.client.chat.completions.create(
                    model=self.config['model'],
                    messages=messages_to_send,
                    temperature=self.config['temperature'],
                    max_tokens=self.config['max_tokens'],
                    stream=False
                )
                
                if response.choices:
                    content = response.choices[0].message.content.strip()
                    if content and "[image]" not in content:
                        filtered_content = self._strip_before_thought_tags(content)
                        if filtered_content:
                            return filtered_content
                
                # 记录错误日志
                logger.error(f"Error request body: {self.config['model']}")
                logger.error(json.dumps(messages_to_send, ensure_ascii=False, indent=2))
                logger.error(f"API returned empty choices or content. Model: {self.config['model']}")
                logger.error(f"Full response object: {response}")
                
            except Exception as e:
                logger.error(f"Error request body: {self.config['model']}")
                logger.error(json.dumps(messages_to_send, ensure_ascii=False, indent=2))
                error_info = str(e)
                logger.error(f"Auto retry: attempt {attempt + 1} call {self.config['model']} failed (ID: {user_id}) reason: {error_info}", exc_info=False)
                
                # 细化错误分类
                if self._should_stop_retry(error_info):
                    break
                
            attempt += 1
        
        raise RuntimeError("抱歉，我现在有点忙，稍后再聊吧。")
    
    def _should_stop_retry(self, error_info):
        """
        判断是否应该停止重试
        
        Args:
            error_info (str): 错误信息
        
        Returns:
            bool: 是否应该停止重试
        """
        stop_retry_keywords = [
            "real name verification",
            "payment required", 
            "user quota",
            "is not enough",
            "UnlimitedQuota",
            "Api key is invalid",
            "sensitive words detected"
        ]
        
        for keyword in stop_retry_keywords:
            if keyword in error_info:
                logger.error(f"Stop retry due to: {keyword}")
                return True
        
        return False
    
    def _strip_before_thought_tags(self, text):
        """
        匹配并截取 </thought> 或 </think> 后面的内容
        
        Args:
            text (str): 原始文本
        
        Returns:
            str: 处理后的文本
        """
        match = re.search(r'(?:</thought>|</think>)([\s\S]*)', text)
        if match:
            return match.group(1)
        else:
            return text 