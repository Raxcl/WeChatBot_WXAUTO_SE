# -*- coding: utf-8 -*-

import logging
import json
import re
from .base_platform import BasePlatform

# 导入现有的配置
try:
    import sys
    import os
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import (
        DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MODEL, 
        TEMPERATURE, MAX_TOKEN, MAX_GROUPS,
        ENABLE_SENSITIVE_CONTENT_CLEARING
    )
    
    # 注意：bot模块的导入将在需要时进行，避免循环导入
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    # 设置默认值，避免程序崩溃
    DEEPSEEK_API_KEY = ""
    DEEPSEEK_BASE_URL = ""
    MODEL = ""
    TEMPERATURE = 1.1
    MAX_TOKEN = 2000
    MAX_GROUPS = 5
    ENABLE_SENSITIVE_CONTENT_CLEARING = False

logger = logging.getLogger(__name__)

class LLMDirectPlatform(BasePlatform):
    """
    大模型直连平台实现
    
    直接调用大模型API（如DeepSeek、OpenAI等），
    复用基类的上下文管理机制。
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
        
        logger.info(f"LLM Direct platform initialized with model: {self.config['model']}")
    
    def validate_config(self):
        """验证配置是否有效"""
        required_keys = ['api_key', 'base_url', 'model']
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")
        
        if not self.config['api_key'] or self.config['api_key'] == "your-api-key":
            raise ValueError("Invalid API key in config")
    
    def get_platform_name(self):
        """获取平台名称"""
        return "LLM Direct"
    
    def _call_api(self, messages, user_id, **kwargs):
        """
        调用大模型API
        
        Args:
            messages (list): 消息列表
            user_id (str): 用户ID
            **kwargs: 其他参数（如is_summary）
        
        Returns:
            str: AI回复内容
        """
        is_summary = kwargs.get('is_summary', False)
        return call_chat_api_with_retry(messages, user_id, is_summary=is_summary)


def strip_before_thought_tags(text):
    """去除思考标签前的内容"""
    # 匹配并截取 </thought> 或 </think> 后面的内容
    match = re.search(r'(?:</thought>|</think>)([\s\S]*)', text)
    if match:
        return match.group(1)
    else:
        return text

def call_chat_api_with_retry(messages_to_send, user_id, max_retries=2, is_summary=False):
    """
    调用 Chat API 并在第一次失败或返回空结果时重试。

    参数:
        messages_to_send (list): 要发送给 API 的消息列表。
        user_id (str): 用户或系统组件的标识符。
        max_retries (int): 最大重试次数。
        is_summary (bool): 是否为总结任务。

    返回:
        str: API 返回的文本回复。
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            logger.debug(f"发送给 API 的消息 (ID: {user_id}): {messages_to_send}")

            # 延迟导入避免循环依赖
            import bot
            client = bot.client
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages_to_send,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKEN,
                stream=False
            )

            if response.choices:
                content = response.choices[0].message.content
                if content:
                    content = content.strip()
                    if content and "[image]" not in content:
                        filtered_content = strip_before_thought_tags(content)
                        if filtered_content:
                            return filtered_content

            # 记录错误日志
            logger.error(f"错误请求消息体: {MODEL}")
            logger.error(json.dumps(messages_to_send, ensure_ascii=False, indent=2))
            logger.error(f"\033[31m错误：API 返回了空的选择项或内容为空。模型名:{MODEL}\033[0m")
            logger.error(f"完整响应对象: {response}")

        except Exception as e:
            logger.error(f"错误请求消息体: {MODEL}")
            logger.error(json.dumps(messages_to_send, ensure_ascii=False, indent=2))
            error_info = str(e)
            logger.error(f"自动重试：第 {attempt + 1} 次调用 {MODEL}失败 (ID: {user_id}) 原因: {error_info}", exc_info=False)

            # 细化错误分类
            if "real name verification" in error_info:
                logger.error("\033[31m错误：API 服务商反馈请完成实名认证后再使用！\033[0m")
                break  # 终止循环，不再重试
            elif "rate limit" in error_info:
                logger.error("\033[31m错误：API 服务商反馈当前访问 API 服务频次达到上限，请稍后再试！\033[0m")
            elif "payment required" in error_info:
                logger.error("\033[31m错误：API 服务商反馈您正在使用付费模型，请先充值再使用或使用免费额度模型！\033[0m")
                break  # 终止循环，不再重试
            elif "user quota" in error_info or "is not enough" in error_info or "UnlimitedQuota" in error_info:
                logger.error("\033[31m错误：API 服务商反馈，你的余额不足，请先充值再使用! 如有余额，请检查令牌是否为无限额度。\033[0m")
                break  # 终止循环，不再重试
            elif "Api key is invalid" in error_info:
                logger.error("\033[31m错误：API 服务商反馈 API KEY 不可用，请检查配置选项！\033[0m")
            elif "service unavailable" in error_info:
                logger.error("\033[31m错误：API 服务商反馈服务器繁忙，请稍后再试！\033[0m")
            elif "sensitive words detected" in error_info:
                logger.error("\033[31m错误：Prompt或消息中含有敏感词，无法生成回复，请联系API服务商！\033[0m")
                if ENABLE_SENSITIVE_CONTENT_CLEARING:
                    logger.warning(f"已开启敏感词自动清除上下文功能，开始清除用户 {user_id} 的聊天上下文")
                    # 延迟导入避免循环依赖
                    import bot
                    clear_chat_context = bot.clear_chat_context
                    clear_memory_temp_files = bot.clear_memory_temp_files
                    clear_chat_context(user_id)
                    if is_summary:
                        clear_memory_temp_files(user_id)  # 如果是总结任务，清除临时文件
                break  # 终止循环，不再重试
            else:
                logger.error("\033[31m未知错误：" + error_info + "\033[0m")

        attempt += 1

    raise RuntimeError("抱歉，我现在有点忙，稍后再聊吧。")


# 为了兼容性，保留原有的函数（现在只是一个包装器）
def get_deepseek_response(message, user_id, store_context=True, is_summary=False, system_prompt=None):
    """
    兼容性包装器，建议直接使用LLMDirectPlatform
    """
    logger.warning("get_deepseek_response函数已弃用，建议使用LLMDirectPlatform")
    platform = LLMDirectPlatform()
    return platform.get_response(message, user_id, store_context, is_summary, system_prompt)
