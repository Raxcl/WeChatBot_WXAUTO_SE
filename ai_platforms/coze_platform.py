# -*- coding: utf-8 -*-

import logging
import time
from .base_platform import BasePlatform
from cozepy import COZE_CN_BASE_URL, Coze, JWTAuth, JWTOAuthApp, Message

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
        'client_id': '',
        'private_key': '',
        'public_key_id': '',
        'api_base_url': 'https://api.coze.cn',
        'bot_id': '',
        'token_ttl': 3600,
        'temperature': 0.8,
        'max_tokens': 2000,
        'stream': False
    }

class CozePlatform(BasePlatform):
    """
    Coze平台实现
    
    使用 Coze SDK 通过 JWT OAuth 进行鉴权和对话
    """
    
    def __init__(self, config=None):
        """初始化 Coze 平台"""
        # 使用现有配置
        if config is None:
            config = COZE_CONFIG
        
        super().__init__(config)
        
        # 参考官方示例直接初始化
        coze_api_base = self.config.get('api_base_url', COZE_CN_BASE_URL)
        
        # 创建 JWT OAuth App
        self.jwt_oauth_app = JWTOAuthApp(
            client_id=self.config['client_id'],
            private_key=self.config['private_key'],
            public_key_id=self.config['public_key_id'],
            base_url=coze_api_base,
        )
        
        # 使用 jwt oauth_app 初始化 Coze 客户端
        self.coze_client = Coze(
            auth=JWTAuth(oauth_app=self.jwt_oauth_app), 
            base_url=coze_api_base
        )
        
        # 初始化时获取第一个 token
        try:
            self.get_access_token()
        except Exception as e:
            logger.warning(f"初始化时 token 获取失败，将在首次使用时重试: {str(e)}")
        
        logger.info(f"Coze 平台初始化成功，Bot ID: {self.config.get('bot_id', '未设置')}")
    
    def get_access_token(self):
        """
        获取访问 token
        """
        try:
            # 使用 JWT OAuth App 获取 token
            access_token = self.jwt_oauth_app.get_access_token()
            
            # 计算过期时间
            expires_at = time.time() + self.config.get('token_ttl', 86400)
            
            # 更新配置中的 token 信息
            self.config['current_token'] = access_token
            self.config['token_expires_at'] = expires_at
            
            logger.info(f"Coze token 获取成功，有效期至: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}")
            return access_token
            
        except Exception as e:
            logger.error(f"Coze token 获取失败: {str(e)}")
            raise
    
    def is_token_expired(self):
        """
        检查 token 是否即将过期
        """
        if not self.config.get('token_expires_at'):
            return True
            
        # 检查是否需要刷新（剩余时间小于阈值）
        remaining_time = self.config['token_expires_at'] - time.time()
        threshold = self.config.get('token_refresh_threshold', 3600)
        
        if remaining_time <= threshold:
            logger.info(f"Coze token 即将过期，剩余时间: {int(remaining_time)}秒")
            return True
            
        return False
    
    def ensure_valid_token(self):
        """
        确保有有效的 token
        """
        if self.config.get('auto_refresh_token', True) and self.is_token_expired():
            logger.info("正在刷新 Coze token...")
            try:
                self.get_access_token()
            except Exception as e:
                logger.error(f"Coze token 刷新失败: {str(e)}")
                raise
    
    def validate_config(self):
        """验证配置是否有效"""
        required_keys = ['client_id', 'private_key', 'public_key_id', 'bot_id']
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            raise ValueError(f"Coze 配置缺少必要参数: {missing_keys}")
        
        if not self.config['client_id'] or self.config['client_id'] == 'your-client-id':
            raise ValueError("Coze 配置中的 client_id 无效")
            
        if not self.config['bot_id'] or self.config['bot_id'] == 'your-bot-id':
            raise ValueError("Coze 配置中的 bot_id 无效")
    
    def get_response(self, message, user_id, store_context=True, is_summary=False):
        """
        获取 Coze 响应
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文 (Coze 内部管理上下文)
            is_summary (bool): 是否为总结任务
        
        Returns:
            str: AI回复内容
        """
        try:
            # 确保有有效的 token
            self.ensure_valid_token()
            
            logger.info(f"调用 Coze API - 用户: {user_id}, 消息: {message[:100]}...")
            
            # 构建消息
            messages = [Message.build_user_question_text(message)]
            
            # 调用 Coze chat API
            chat_result = self.coze_client.chat.create_and_poll(
                bot_id=self.config['bot_id'],
                user_id=user_id,
                additional_messages=messages,
            )
            
            # 提取回复内容
            if chat_result.messages:
                reply_content = ""
                for msg in chat_result.messages:
                    if hasattr(msg, 'content') and msg.content:
                        reply_content += msg.content
                
                if reply_content.strip():
                    logger.info(f"Coze 回复获取成功 - 用户: {user_id}")
                    return reply_content.strip()
            
            # 如果没有获取到有效回复
            logger.warning(f"Coze 未返回有效回复 - 用户: {user_id}")
            return "抱歉，我现在有点忙，稍后再聊吧。"
            
        except Exception as e:
            logger.error(f"Coze API 调用失败 - 用户: {user_id}, 错误: {str(e)}", exc_info=True)
            return self.handle_error(e, user_id)
    
    def handle_error(self, error, user_id):
        """处理错误"""
        error_str = str(error).lower()
        
        if "authentication" in error_str or "authorization" in error_str:
            logger.error(f"Coze 身份验证失败 - 用户: {user_id}")
            return "抱歉，身份验证失败，请检查配置。"
        elif "rate limit" in error_str:
            logger.error(f"Coze 访问频率限制 - 用户: {user_id}")
            return "抱歉，访问频率过高，请稍后再试。"
        elif "quota" in error_str:
            logger.error(f"Coze 配额已用完 - 用户: {user_id}")
            return "抱歉，配额已用完，请联系管理员。"
        else:
            logger.error(f"Coze 未知错误 - 用户: {user_id}, 错误: {error}")
            return "抱歉，服务暂时不可用，请稍后再试。"
    
 