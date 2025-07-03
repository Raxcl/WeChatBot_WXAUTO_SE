# -*- coding: utf-8 -*-

import logging
import os
import time
from typing import Optional
from .base_platform import BasePlatform
from cozepy import COZE_CN_BASE_URL, ChatStatus, Coze, Message, TokenAuth

logger = logging.getLogger(__name__)

# 导入现有配置
try:
    import sys
    import os
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config import COZE_CONFIG
except ImportError as e:
    logger.error(f"Failed to import config: {e}")
    # 设置默认配置避免程序崩溃
    COZE_CONFIG = {
        # JWT OAuth 配置（必需）
        'client_id': '',
        'private_key': '',
        'public_key_id': '',
        
        # 通用配置
        'api_base_url': 'https://api.coze.cn',
        'bot_id': '',
        'temperature': 0.8,
        'max_tokens': 2000,
        'stream': False
    }

class CozePlatform(BasePlatform):
    """
    Coze平台实现
    
    基于官方示例使用 Coze SDK 进行对话
    支持 system_prompt 参数
    """
    
    def __init__(self, config=None):
        """初始化 Coze 平台"""
        # 使用现有配置
        if config is None:
            config = COZE_CONFIG.copy()
        
        super().__init__(config)
        
        # 获取API Base URL
        self.coze_api_base = self.get_coze_api_base()
        
        # 获取API Token
        self.api_token = self.get_coze_api_token()
        
        # 初始化 Coze 客户端
        self.coze_client = Coze(
            auth=TokenAuth(token=self.api_token), 
            base_url=self.coze_api_base
        )
        
        logger.info(f"Coze 平台初始化成功，Bot ID: {self.config.get('bot_id', '未设置')}")
    
    def get_coze_api_base(self) -> str:
        """获取 Coze API Base URL"""
        # 优先使用环境变量
        coze_api_base = os.getenv("COZE_API_BASE")
        if coze_api_base:
            return coze_api_base
        
        # 使用配置文件中的设置
        return self.config.get('api_base_url', COZE_CN_BASE_URL)
    
    def get_coze_api_token(self) -> str:
        """获取 Coze API Token（仅支持JWT OAuth）"""
        # 检查JWT OAuth配置
        if not self.has_jwt_oauth_config():
            raise ValueError(
                "Coze JWT OAuth 配置缺失！请配置以下参数：\n"
                "- client_id: 应用ID\n"
                "- private_key: 私钥（PEM格式）\n"
                "- public_key_id: 公钥ID\n"
                "获取方式：https://www.coze.cn/open/docs/developer_guides/authentication"
            )
        
        logger.info("使用 JWT OAuth 方式获取 Token（支持自动刷新）")
        return self.get_jwt_token()
    
    def has_jwt_oauth_config(self) -> bool:
        """检查是否有完整的JWT OAuth配置"""
        client_id = self.config.get('client_id')
        private_key = self.config.get('private_key')
        public_key_id = self.config.get('public_key_id')
        
        return (
            client_id is not None and client_id.strip() != '' and
            private_key is not None and private_key.strip() != '' and
            public_key_id is not None and public_key_id.strip() != ''
        )
    
    def get_jwt_token(self) -> str:
        """使用JWT OAuth获取token"""
        try:
            from cozepy import JWTAuth, JWTOAuthApp
            
            # 创建 JWT OAuth App
            jwt_oauth_app = JWTOAuthApp(
                client_id=self.config['client_id'],
                private_key=self.config['private_key'],
                public_key_id=self.config['public_key_id'],
                base_url=self.coze_api_base,
            )
            
            # 获取token
            oauth_token = jwt_oauth_app.get_access_token()
            logger.info("JWT OAuth token 获取成功")
            return oauth_token.access_token
            
        except Exception as e:
            logger.error(f"JWT OAuth token 获取失败: {e}")
            raise ValueError(f"JWT OAuth 认证失败: {e}")
    
    def validate_config(self):
        """验证配置是否有效"""
        # 检查Bot ID
        if not self.config.get('bot_id') or self.config['bot_id'] == 'your-bot-id':
            raise ValueError("Coze 配置中的 bot_id 无效，请设置正确的 Bot ID")
        
        # 检查API Token（这里不直接验证，留给 get_coze_api_token 方法处理）
        # 这样可以给出更详细的错误信息
    
    def get_response(self, message, user_id, store_context=True, is_summary=False, system_prompt=None):
        """
        获取 Coze 响应
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文 (Coze 内部管理上下文)
            is_summary (bool): 是否为总结任务
            system_prompt (str): 系统提示词
        
        Returns:
            str: AI回复内容
        """
        try:
            logger.info(f"调用 Coze API - 用户: {user_id}, 消息: {message[:100]}...")
            
            # 构建消息列表
            additional_messages = []
            
            # 如果有系统提示词，添加为助手回复（按照Coze的建议格式）
            if system_prompt:
                additional_messages.extend([
                    Message.build_user_question_text("请按照以下角色设定进行对话："),
                    Message.build_assistant_answer(system_prompt),
                ])
            
            # 添加用户消息
            additional_messages.append(Message.build_user_question_text(message))
            
            # 使用官方推荐的 create_and_poll 方法
            chat_poll = self.coze_client.chat.create_and_poll(
                bot_id=self.config['bot_id'],
                user_id=user_id,
                additional_messages=additional_messages,
            )
            
            # 提取回复内容
            reply_content = ""
            if chat_poll.messages:
                for message_obj in chat_poll.messages:
                    if hasattr(message_obj, 'content') and message_obj.content:
                        reply_content += message_obj.content
            
            # 检查对话状态
            if chat_poll.chat.status == ChatStatus.COMPLETED:
                if reply_content.strip():
                    logger.info(f"Coze 回复获取成功 - 用户: {user_id}")
                    if hasattr(chat_poll.chat, 'usage') and chat_poll.chat.usage:
                        logger.debug(f"Token 使用量: {chat_poll.chat.usage.token_count}")
                    return reply_content.strip()
                else:
                    logger.warning(f"Coze 对话完成但无有效回复 - 用户: {user_id}")
                    return "抱歉，我现在有点忙，稍后再聊吧。"
            else:
                logger.warning(f"Coze 对话未正常完成，状态: {chat_poll.chat.status} - 用户: {user_id}")
                return "抱歉，对话处理超时，请稍后再试。"
            
        except Exception as e:
            logger.error(f"Coze API 调用失败 - 用户: {user_id}, 错误: {str(e)}", exc_info=True)
            return self.handle_error(e, user_id)
    
    def handle_error(self, error, user_id):
        """处理错误"""
        error_str = str(error).lower()
        
        if "authentication" in error_str or "authorization" in error_str or "401" in error_str:
            logger.error(f"Coze 身份验证失败 - 用户: {user_id}")
            return "抱歉，身份验证失败，请检查配置。"
        elif "rate limit" in error_str or "429" in error_str:
            logger.error(f"Coze 访问频率限制 - 用户: {user_id}")
            return "抱歉，访问频率过高，请稍后再试。"
        elif "quota" in error_str or "insufficient" in error_str:
            logger.error(f"Coze 配额已用完 - 用户: {user_id}")
            return "抱歉，配额已用完，请联系管理员。"
        elif "timeout" in error_str:
            logger.error(f"Coze 请求超时 - 用户: {user_id}")
            return "抱歉，请求超时，请稍后再试。"
        elif "network" in error_str or "connection" in error_str:
            logger.error(f"Coze 网络连接失败 - 用户: {user_id}")
            return "抱歉，网络连接失败，请稍后再试。"
        else:
            logger.error(f"Coze 未知错误 - 用户: {user_id}, 错误: {error}")
            return "抱歉，服务暂时不可用，请稍后再试。"
    
 