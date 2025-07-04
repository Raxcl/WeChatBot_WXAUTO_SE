# -*- coding: utf-8 -*-

import logging
import os
import time
from typing import Optional
from .base_platform import BasePlatform
from cozepy import COZE_CN_BASE_URL, Coze, TokenAuth

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
    使用基类的上下文管理逻辑，确保与其他平台行为一致
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
        
        logger.info(f"Coze 平台初始化成功，工作流 ID: {self.config.get('bot_id', '未设置')}")
    
    def get_platform_name(self):
        """获取平台名称"""
        return "Coze"
    
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
            # 先检查config.py中是否有有效的缓存token
            cached_token = self.load_token_from_config()
            if cached_token:
                # 使用缓存的token
                self.config['current_token'] = cached_token
                return cached_token
            
            # 缓存中没有有效token，获取新的
            logger.info("正在获取新的JWT OAuth token...")
            
            from cozepy import JWTAuth, JWTOAuthApp
            
            # 创建 JWT OAuth App
            jwt_oauth_app = JWTOAuthApp(
                client_id=self.config['client_id'],
                private_key=self.config['private_key'],
                public_key_id=self.config['public_key_id'],
                base_url=self.coze_api_base,
            )
            
            # 获取token - 使用最大有效期
            oauth_token = jwt_oauth_app.get_access_token(ttl=86399)  # 最大24小时有效期
            logger.info("JWT OAuth token 获取成功，oauth_token: %s", oauth_token)
            
            # 处理过期时间 - expires_in可能是时间戳而不是秒数
            current_time = time.time()
            expires_in_value = oauth_token.expires_in
            
            expires_at = expires_in_value
            logger.info(f"过期时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))}")
            
            # 计算实际剩余时间
            remaining_hours = (expires_at - current_time) / 3600
            logger.info(f"Token实际剩余有效期: {remaining_hours:.1f} 小时")
            
            # 保存token到实例配置中（仅在内存中）
            self.config['current_token'] = oauth_token.access_token
            self.config['token_expires_at'] = expires_at
            
            # 回写token到config.py文件
            self.save_token_to_config(oauth_token.access_token, expires_at)
            
            return oauth_token.access_token
            
        except Exception as e:
            logger.error(f"JWT OAuth token 获取失败: {e}")
            raise ValueError(f"JWT OAuth 认证失败: {e}")
    
    def validate_config(self):
        """验证配置是否有效"""
        # 检查工作流ID（bot_id字段现在用作workflow_id）
        if not self.config.get('bot_id') or self.config['bot_id'] == 'your-bot-id':
            raise ValueError("Coze 配置中的 bot_id 无效，请设置正确的工作流 ID（Workflow ID）")
        
        # 检查API Token（这里不直接验证，留给 get_coze_api_token 方法处理）
        # 这样可以给出更详细的错误信息
    
    def _call_api(self, messages, user_id, **kwargs):
        """
        调用 Coze API
        
        Args:
            messages (list): 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            user_id (str): 用户ID
            **kwargs: 其他参数（如is_summary）
        
        Returns:
            str: AI回复内容
        """
        try:
            # 为保持与LLM Direct完全一致的行为，我们只传递当前消息给Coze
            # 让基类的上下文管理完全接管历史管理，而不依赖Coze平台的自动上下文
            current_message = ""
            system_prompt = None
            
            logger.debug(f"coze消息，messages: {messages}")
            # 只提取当前消息和系统提示词
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                elif msg["role"] == "user":
                    current_message = msg["content"]  # 使用最后一条用户消息
            logger.debug(f"coze system_prompt: {system_prompt}")
            logger.info(f"调用 Coze API - 用户: {user_id}, 当前消息: {current_message[:100]}...")
            logger.info(f"注意: 使用基类上下文管理，确保与LLM Direct行为完全一致")
            
            # 构建工作流参数 - 工作流模式下不需要additional_messages
            parameters = None
            if system_prompt:
                parameters = {"input":current_message,"system_prompt": system_prompt}
            else:
                parameters = {"input": current_message}
            
            # 打印请求参数日志
            logger.info(f"Coze工作流请求参数: workflow_id={self.config['bot_id']}, user_id={user_id}, parameters={parameters}")
            
            workflow = None  # 先定义，便于异常时打印
            # 使用工作流替代对话流，更适合群聊助手场景
            # Call the coze.workflows.runs.create method to create a workflow run
            workflow = self.coze_client.workflows.runs.create(
                workflow_id=self.config['bot_id'],
                parameters=parameters
            )
            
            # 打印Coze API原始返回内容
            logger.info(f"Coze 工作流API原始返回: {repr(workflow)}")
            
            # 检查工作流执行状态和提取结果
            if workflow:
                # 提取工作流执行结果
                reply_content = ""
                try:
                    # 工作流结果可能在不同的属性中，尝试多种可能的结构
                    workflow_data = getattr(workflow, 'data', None)
                    if workflow_data:
                        # 如果结果在data属性中
                        if isinstance(workflow_data, str):
                            # 尝试解析JSON格式的data字段
                            try:
                                import json
                                parsed_data = json.loads(workflow_data)
                                logger.debug(f"成功解析工作流JSON数据: {parsed_data}")
                                
                                # 根据解析结果的结构提取消息内容
                                if isinstance(parsed_data, dict):
                                    # 优先获取data字段中的内容
                                    if 'data' in parsed_data:
                                        reply_content = parsed_data['data']
                                    elif 'content' in parsed_data:
                                        reply_content = parsed_data['content']
                                    elif 'message' in parsed_data:
                                        reply_content = parsed_data['message']
                                    else:
                                        # 如果没有标准字段，尝试获取所有字符串值
                                        for key, value in parsed_data.items():
                                            if isinstance(value, str) and len(value) > 10:  # 假设有意义的回复至少10个字符
                                                reply_content = value
                                                break
                                elif isinstance(parsed_data, str):
                                    reply_content = parsed_data
                                
                                if not reply_content:
                                    logger.warning(f"无法从解析的JSON中提取有效内容: {parsed_data}")
                                    reply_content = workflow_data  # 降级为原始字符串
                                    
                            except json.JSONDecodeError:
                                logger.debug(f"data字段不是有效JSON，直接使用原始字符串: {workflow_data}")
                                reply_content = workflow_data
                        else:
                            data_output = getattr(workflow_data, 'output', None)
                            data_result = getattr(workflow_data, 'result', None)
                            if data_output:
                                reply_content = str(data_output)
                            elif data_result:
                                reply_content = str(data_result)
                    else:
                        # 尝试直接获取output或result属性
                        workflow_output = getattr(workflow, 'output', None)
                        workflow_result = getattr(workflow, 'result', None)
                        
                        if workflow_output:
                            reply_content = str(workflow_output)
                        elif workflow_result:
                            reply_content = str(workflow_result)
                        else:
                            # 如果都没有，尝试直接转换整个workflow对象
                            reply_content = str(workflow)
                            logger.warning(f"未找到标准的工作流输出属性，使用整个结果: {workflow}")
                        
                except Exception as msg_error:
                    logger.warning(f"提取工作流结果时出错: {msg_error}")
                    reply_content = "抱歉，我现在有点忙，稍后再聊吧。"
                
                if reply_content and reply_content.strip():
                    logger.info(f"Coze 工作流执行成功 - 用户: {user_id}")
                    # 工作流可能有不同的使用量统计方式
                    workflow_usage = getattr(workflow, 'usage', None)
                    if workflow_usage:
                        logger.debug(f"工作流资源使用量: {workflow_usage}")
                    return reply_content.strip()
                else:
                    logger.warning(f"Coze 工作流执行完成但无有效输出 - 用户: {user_id}")
                    return "抱歉，我现在有点忙，稍后再聊吧。"
            else:
                logger.warning(f"Coze 工作流执行失败，无返回结果 - 用户: {user_id}")
                return "抱歉，对话处理超时，请稍后再试。"
            
        except Exception as e:
            try:
                error_msg = str(e)
            except Exception as ee:
                error_msg = f"异常对象无法转为字符串: {repr(e)}，二次异常: {repr(ee)}"
            # 特殊处理消息验证错误
            if "validation error for Message" in error_msg:
                logger.error(f"Coze 工作流验证错误 - 用户: {user_id}, 可能是API返回格式异常，原始错误: {error_msg}")
                logger.error(f"workflow内容: {repr(locals().get('workflow', None))}")
                logger.error(f"Coze工作流请求参数: workflow_id={self.config['bot_id']}, user_id={user_id}, parameters={parameters}")
                return "对不起，现在还不行哦"
            else:
                logger.error(f"Coze API 调用失败 - 用户: {user_id}, 错误: {error_msg}", exc_info=True)
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
    
    def load_token_from_config(self):
        """
        从config.py文件加载token
        """
        try:
            import sys
            import os
            
            # 获取config模块
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import config
            
            if not hasattr(config, 'COZE_CONFIG'):
                return None
            
            current_token = config.COZE_CONFIG.get('current_token')
            expires_at = config.COZE_CONFIG.get('token_expires_at')
            
            if not current_token or not expires_at:
                logger.debug("config.py中未找到有效token信息")
                return None
            
            current_time = time.time()
            
            # 获取刷新阈值（默认30分钟）
            refresh_threshold = self.config.get('token_refresh_threshold', 1800)
            
            # 检查token是否过期（使用配置的刷新阈值）
            if current_time < (expires_at - refresh_threshold):
                remaining_hours = (expires_at - current_time) / 3600
                logger.info(f"使用config.py中的缓存token，剩余有效期 {remaining_hours:.1f} 小时")
                
                # 同时更新实例配置
                self.config['token_expires_at'] = expires_at
                
                return current_token
            else:
                logger.info(f"config.py中的token已过期或即将过期（剩余时间少于{refresh_threshold/60:.0f}分钟），将获取新token")
                return None
                
        except Exception as e:
            logger.warning(f"从config.py加载token失败: {e}")
            return None

    def save_token_to_config(self, token, expires_at):
        """
        将token回写到config.py文件
        """
        try:
            import os
            import re
            
            # 获取config.py文件路径
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(project_root, 'config.py')
            
            # 读取config.py文件
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新current_token
            token_pattern = r"'current_token':\s*[^,}]+"
            new_token_line = f"'current_token': '{token}'"
            content = re.sub(token_pattern, new_token_line, content)
            
            # 更新token_expires_at
            expires_pattern = r"'token_expires_at':\s*[^,}]+"
            new_expires_line = f"'token_expires_at': {expires_at}"
            content = re.sub(expires_pattern, new_expires_line, content)
            
            # 写回文件
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Token 已成功回写到config.py文件")
            
            # 同时更新全局配置模块（避免需要重启）
            import sys
            sys.path.insert(0, project_root)
            import config
            if hasattr(config, 'COZE_CONFIG'):
                config.COZE_CONFIG['current_token'] = token
                config.COZE_CONFIG['token_expires_at'] = expires_at
            
        except Exception as e:
            logger.warning(f"回写token到config.py失败: {e}")
    
 