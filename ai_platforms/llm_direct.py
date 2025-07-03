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
        
        logger.info(f"LLM Direct platform initialized with model: {self.config['model']}")
    
    def validate_config(self):
        """验证配置是否有效"""
        required_keys = ['api_key', 'base_url', 'model']
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            raise ValueError(f"Missing required config keys: {missing_keys}")
        
        if not self.config['api_key'] or self.config['api_key'] == "your-api-key":
            raise ValueError("Invalid API key in config")
    
    def get_response(self, message, user_id, store_context=True, is_summary=False, system_prompt=None):
        """
        获取大模型响应
        
        直接调用经过验证的 get_deepseek_response 函数，确保使用稳定可靠的实现。
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文
            is_summary (bool): 是否为总结任务
            system_prompt (str): 系统提示词，默认None
        
        Returns:
            str: AI回复内容
        """
        # 调用经过验证的 get_deepseek_response 函数
        return get_deepseek_response(
            message, 
            user_id, 
            store_context=store_context, 
            is_summary=is_summary,
            system_prompt=system_prompt
        )



    
def get_deepseek_response(message, user_id, store_context=True, is_summary=False, system_prompt=None):
    """
    从 DeepSeek API 获取响应，确保正确的上下文处理，并持久化上下文。

    参数:
        message (str): 用户的消息或系统提示词（用于工具调用）。
        user_id (str): 用户或系统组件的标识符。
        store_context (bool): 是否将此交互存储到聊天上下文中。
                              对于工具调用（如解析或总结），设置为 False。
        system_prompt (str): 自定义系统提示词，如果提供将覆盖默认的用户角色提示词。
    """
    try:
        # 延迟导入避免循环依赖
        import bot
        chat_contexts = bot.chat_contexts
        queue_lock = bot.queue_lock
        get_user_prompt = bot.get_user_prompt
        load_chat_contexts = bot.load_chat_contexts
        save_chat_contexts = bot.save_chat_contexts
        
        # 每次调用都重新加载聊天上下文，以应对文件被外部修改的情况
        load_chat_contexts()
        
        logger.info(f"调用 Chat API - ID: {user_id}, 是否存储上下文: {store_context}, 消息: {message[:100]}...") # 日志记录消息片段

        messages_to_send = []
        context_limit = MAX_GROUPS * 2  # 最大消息总数（不包括系统消息）

        if store_context:
            # --- 处理需要上下文的常规聊天消息 ---
            # 1. 获取该用户的系统提示词
            try:
                # 如果提供了自定义系统提示词，优先使用
                if system_prompt:
                    messages_to_send.append({"role": "system", "content": system_prompt})
                    logger.info(f"使用自定义系统提示词 - 用户: {user_id}")
                else:
                    user_prompt = get_user_prompt(user_id)
                    messages_to_send.append({"role": "system", "content": user_prompt})
            except FileNotFoundError as e:
                logger.error(f"用户 {user_id} 的提示文件错误: {e}，使用默认提示。")
                fallback_prompt = system_prompt if system_prompt else "你是一个乐于助人的助手。"
                messages_to_send.append({"role": "system", "content": fallback_prompt})

            # 2. 管理并检索聊天历史记录
            with queue_lock: # 确保对 chat_contexts 的访问是线程安全的
                if user_id not in chat_contexts:
                    chat_contexts[user_id] = []

                # 在添加当前消息之前获取现有历史记录
                history = list(chat_contexts.get(user_id, []))  # 获取副本

                # 如果历史记录超过限制，则进行裁剪
                if len(history) > context_limit:
                    history = history[-context_limit:]  # 保留最近的消息

                # 将历史消息添加到 API 请求列表中
                messages_to_send.extend(history)

                # 3. 将当前用户消息添加到 API 请求列表中
                messages_to_send.append({"role": "user", "content": message})

                # 4. 在准备 API 调用后更新持久上下文
                # 将用户消息添加到持久存储中
                chat_contexts[user_id].append({"role": "user", "content": message})
                # 如果需要，裁剪持久存储（在助手回复后会再次裁剪）
                if len(chat_contexts[user_id]) > context_limit + 1:  # +1 因为刚刚添加了用户消息
                    chat_contexts[user_id] = chat_contexts[user_id][-(context_limit + 1):]
                
                # 保存上下文到文件
                save_chat_contexts() # 在用户消息添加后保存一次

        else:
            # --- 处理工具调用（如提醒解析、总结） ---
            # 如果提供了系统提示词，添加到消息中
            if system_prompt:
                messages_to_send.append({"role": "system", "content": system_prompt})
                logger.info(f"工具调用使用自定义系统提示词 - ID: {user_id}")
            
            messages_to_send.append({"role": "user", "content": message})
            logger.info(f"工具调用 (store_context=False)，ID: {user_id}。仅发送提供的消息。")

        # --- 调用 API ---
        reply = call_chat_api_with_retry(messages_to_send, user_id, is_summary=is_summary)

        # --- 如果需要，存储助手回复到上下文中 ---
        if store_context:
            with queue_lock: # 再次获取锁来更新和保存
                if user_id not in chat_contexts:
                   chat_contexts[user_id] = []  # 安全初始化 (理论上此时应已存在)

                chat_contexts[user_id].append({"role": "assistant", "content": reply})

                if len(chat_contexts[user_id]) > context_limit:
                    chat_contexts[user_id] = chat_contexts[user_id][-context_limit:]
                
                # 保存上下文到文件
                save_chat_contexts() # 在助手回复添加后再次保存
        
        return reply

    except Exception as e:
        logger.error(f"Chat 调用失败 (ID: {user_id}): {str(e)}", exc_info=True)
        return "抱歉，我现在有点忙，稍后再聊吧。"


def strip_before_thought_tags(text):
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
