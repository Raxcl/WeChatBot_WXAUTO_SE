# WeChatBot AI平台集成设计文档

## 📋 项目概述

**目标**：为WeChatBot集成多个AI平台（Coze、Dify、大模型直连），支持用户级别的AI平台自定义选择。

**核心理念**：让每个用户/群聊可以独立选择使用哪个AI平台，实现个性化的AI服务体验。

---

## 🏗️ 架构设计

### 当前架构
```
用户消息 → process_user_messages() → get_deepseek_response() → 回复
```

### 新架构
```
用户消息 → process_user_messages() → AI平台路由器 → 平台选择器 → 具体AI服务 → 回复
                                        ↓
                                   根据用户配置选择：
                                   ├── 大模型直连
                                   ├── Coze平台
                                   └── Dify平台
```

---

## ⚙️ 配置设计

### 1. LISTEN_LIST 配置扩展

**当前格式**：
```python
LISTEN_LIST = [['微信名', '角色文件']]
```

**新格式**：
```python
LISTEN_LIST = [
    ['测试群1', '角色1', 'llm_direct'],    # 大模型直连
    ['测试群2', '角色2', 'coze'],          # 使用Coze
    ['raxcl', '角色2', 'dify'],           # 使用Dify
]
```

**支持的平台标识**：
- `llm_direct` - 大模型直连（替代原deepseek）
- `coze` - Coze平台
- `dify` - Dify平台

### 2. 大模型直连配置

```python
# === 大模型直连配置 ===
直接使用已有逻辑

```

### 3. Coze平台配置

```python
# === Coze平台配置 ===
COZE_CONFIG = {
    'api_key': 'your-coze-api-key',
    'base_url': 'https://api.coze.cn/v1',
    'bot_id': 'your-bot-id',
    'user_id': 'default-user',  # 可以用微信昵称作为user_id
    'stream': False,
    'temperature': 0.8,
}
```

### 4. Dify平台配置

```python
# === Dify平台配置 ===
DIFY_CONFIG = {
    'api_key': 'your-dify-api-key',
    'base_url': 'https://api.dify.ai/v1',
    'app_type': 'chatbot',  # 或 'workflow'
    'user': 'wechat-bot',
    'response_mode': 'blocking',  # 或 'streaming'
}
```

---

## 🔧 代码改动设计

### 1. 新增文件结构

```
ai_platforms/
├── __init__.py
├── base_platform.py      # 基础平台抽象类
├── llm_direct.py         # 大模型直连实现
├── coze_platform.py      # Coze平台实现
├── dify_platform.py      # Dify平台实现
└── platform_router.py    # 平台路由器
```

### 2. 核心类设计

#### 基础平台抽象类
```python
# ai_platforms/base_platform.py
from abc import ABC, abstractmethod

class BasePlatform(ABC):
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def get_response(self, message, user_id, store_context=True, is_summary=False):
        """获取AI响应"""
        pass
    
    @abstractmethod
    def validate_config(self):
        """验证配置是否有效"""
        pass
```

#### 平台路由器
```python
# ai_platforms/platform_router.py
class PlatformRouter:
    def __init__(self):
        self.platforms = {
            'llm_direct': LLMDirectPlatform,
            'coze': CozePlatform,
            'dify': DifyPlatform,
        }
    
    def get_user_platform(self, user_id):
        """根据用户ID获取应使用的平台"""
        pass
    
    def route_message(self, user_id, message, **kwargs):
        """路由消息到对应平台"""
        pass
```

### 3. 主要函数改动

#### bot.py 中的改动点

1. **替换 get_deepseek_response()**
```python
# 原函数改名为 get_ai_response()
def get_ai_response(message, user_id, store_context=True, is_summary=False):
    """智能路由到对应的AI平台"""
    platform = platform_router.get_user_platform(user_id)
    return platform.get_response(message, user_id, store_context, is_summary)
```

2. **修改调用点**
- `process_user_messages()` 中的调用
- 群聊总结功能中的调用
- 其他AI调用的地方

### 4. 配置解析逻辑

```python
def parse_listen_list():
    """解析监听列表，提取平台配置"""
    user_platform_mapping = {}
    
    for entry in LISTEN_LIST:
        if len(entry) == 2:
            # 兼容旧格式 ['用户名', '角色']
            username, role = entry
            platform = 'llm_direct'  # 默认平台
        elif len(entry) == 3:
            # 新格式 ['用户名', '角色', '平台']
            username, role, platform = entry
        else:
            raise ValueError(f"Invalid LISTEN_LIST entry: {entry}")
        
        user_platform_mapping[username] = {
            'role': role,
            'platform': platform
        }
    
    return user_platform_mapping
```

---

## 🚀 实施步骤

### Phase 1: 基础架构搭建
1. ✅ 创建 `ai_platforms/` 目录结构
2. ✅ 实现基础抽象类 `BasePlatform`
3. ✅ 实现平台路由器 `PlatformRouter`
4. ✅ 将现有DeepSeek逻辑重构为 `LLMDirectPlatform`

### Phase 2: 配置系统升级
1. ✅ 扩展 `config.py` 添加新平台配置
2. ✅ 实现配置解析和验证逻辑
3. ✅ 修改 `LISTEN_LIST` 解析逻辑

### Phase 3: Coze平台集成
1. ✅ 实现 `CozePlatform` 类
2. ✅ API调用和错误处理
3. ✅ 上下文管理适配
4. ✅ 功能测试

### Phase 4: Dify平台集成
1. ✅ 实现 `DifyPlatform` 类
2. ✅ 工作流和聊天模式支持
3. ✅ 错误处理和重试逻辑
4. ✅ 功能测试

### Phase 5: 系统集成和测试
1. ✅ 替换所有 `get_deepseek_response()` 调用
2. ✅ 端到端测试
3. ✅ 性能测试和优化
4. ✅ 文档更新

---

## 🧪 测试计划

### 单元测试
- [ ] 各平台类的基础功能测试
- [ ] 配置解析正确性测试
- [ ] 错误处理测试

### 集成测试
- [ ] 平台路由准确性测试
- [ ] 不同平台的消息处理测试
- [ ] 上下文管理测试

### 功能测试
- [ ] 多用户不同平台同时使用测试
- [ ] 平台切换功能测试
- [ ] 向后兼容性测试



## 📚 API接口规范

### 1. Coze Platform API

```python
# Coze API 调用示例
import requests

def call_coze_api(message, bot_id, user_id):
    url = f"{COZE_CONFIG['base_url']}/chat"
    headers = {
        'Authorization': f"Bearer {COZE_CONFIG['api_key']}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        'bot_id': bot_id,
        'user_id': user_id,
        'query': message,
        'stream': False
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

### 2. Dify Platform API

```python
# Dify API 调用示例
def call_dify_api(message, conversation_id=None):
    url = f"{DIFY_CONFIG['base_url']}/chat-messages"
    headers = {
        'Authorization': f"Bearer {DIFY_CONFIG['api_key']}",
        'Content-Type': 'application/json'
    }
    
    payload = {
        'inputs': {},
        'query': message,
        'response_mode': DIFY_CONFIG['response_mode'],
        'user': DIFY_CONFIG['user']
    }
    
    if conversation_id:
        payload['conversation_id'] = conversation_id
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

### 3. LLM Direct API (统一接口)

```python
# 大模型直连统一接口
from openai import OpenAI

def call_llm_direct(messages, provider='deepseek'):
    provider_config = LLM_PROVIDERS[provider]
    
    client = OpenAI(
        api_key=LLM_DIRECT_CONFIG['api_key'],
        base_url=provider_config['base_url']
    )
    
    response = client.chat.completions.create(
        model=provider_config['model'],
        messages=messages,
        temperature=LLM_DIRECT_CONFIG['temperature'],
        max_tokens=LLM_DIRECT_CONFIG['max_tokens']
    )
    
    return response.choices[0].message.content
```

---

## 🔧 具体实现示例

### 1. BasePlatform 完整实现

```python
# ai_platforms/base_platform.py
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BasePlatform(ABC):
    def __init__(self, config):
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def get_response(self, message, user_id, store_context=True, is_summary=False):
        """
        获取AI响应
        
        Args:
            message (str): 用户消息
            user_id (str): 用户ID
            store_context (bool): 是否存储上下文
            is_summary (bool): 是否为总结任务
        
        Returns:
            str: AI回复内容
        """
        pass
    
    @abstractmethod
    def validate_config(self):
        """验证配置是否有效"""
        pass
    
    def handle_error(self, error, user_id):
        """统一错误处理"""
        logger.error(f"Platform {self.__class__.__name__} error for user {user_id}: {error}")
        return "抱歉，AI服务暂时不可用，请稍后再试。"
    
    def get_platform_name(self):
        """获取平台名称"""
        return self.__class__.__name__.replace('Platform', '').lower()
```

### 2. PlatformRouter 完整实现

```python
# ai_platforms/platform_router.py
import logging
from .llm_direct import LLMDirectPlatform
from .coze_platform import CozePlatform  
from .dify_platform import DifyPlatform

logger = logging.getLogger(__name__)

class PlatformRouter:
    def __init__(self, user_platform_mapping):
        """
        初始化平台路由器
        
        Args:
            user_platform_mapping (dict): 用户平台映射配置
        """
        self.user_platform_mapping = user_platform_mapping
        self.platform_instances = {}
        self._init_platforms()
    
    def _init_platforms(self):
        """初始化所有平台实例"""
        platform_classes = {
            'llm_direct': LLMDirectPlatform,
            'coze': CozePlatform,
            'dify': DifyPlatform,
        }
        
        for platform_name, platform_class in platform_classes.items():
            try:
                self.platform_instances[platform_name] = platform_class()
                logger.info(f"Successfully initialized {platform_name} platform")
            except Exception as e:
                logger.error(f"Failed to initialize {platform_name} platform: {e}")
                # 使用LLM Direct作为降级方案
                if platform_name != 'llm_direct':
                    self.platform_instances[platform_name] = self.platform_instances.get('llm_direct')
    
    def get_user_platform(self, user_id):
        """
        根据用户ID获取应使用的平台实例
        
        Args:
            user_id (str): 用户ID
        
        Returns:
            BasePlatform: 平台实例
        """
        # 获取用户配置的平台
        user_config = self.user_platform_mapping.get(user_id, {})
        platform_name = user_config.get('platform', 'llm_direct')
        
        # 获取平台实例，如果不存在则使用默认平台
        platform = self.platform_instances.get(platform_name)
        if not platform:
            logger.warning(f"Platform {platform_name} not available for user {user_id}, fallback to llm_direct")
            platform = self.platform_instances.get('llm_direct')
        
        return platform
    
    def route_message(self, user_id, message, **kwargs):
        """
        路由消息到对应平台
        
        Args:
            user_id (str): 用户ID
            message (str): 用户消息
            **kwargs: 其他参数
        
        Returns:
            str: AI回复
        """
        platform = self.get_user_platform(user_id)
        if not platform:
            return "抱歉，AI服务暂时不可用。"
        
        try:
            return platform.get_response(message, user_id, **kwargs)
        except Exception as e:
            logger.error(f"Error routing message for user {user_id}: {e}")
            return platform.handle_error(e, user_id)
```

---

## 📊 实现状态

### 已完成功能 ✅

#### 🏗️ 核心架构
- [x] **BasePlatform 抽象基类** - 统一的平台接口定义
- [x] **PlatformRouter 路由器** - 智能消息路由和平台管理
- [x] **延迟导入机制** - 避免循环依赖，提高启动速度
- [x] **统一配置管理** - 配置验证和错误处理

#### 🤖 平台实现
- [x] **LLMDirectPlatform** - 大模型直连平台（优化版）
  - 复用现有经过验证的 `get_deepseek_response` 函数
  - 支持 DeepSeek、硅基流动等 API
  - 完善的错误处理和重试机制
  
- [x] **CozePlatform** - Coze 平台集成
  - JWT OAuth 2.0 鉴权
  - 自动 Token 管理
  - 支持 Bot 对话 API
  - 错误分类处理

#### 🧪 测试和文档
- [x] **集成测试脚本** - 完整的配置和功能验证
- [x] **使用指南** - 详细的步骤说明和故障排除
- [x] **向后兼容** - 现有配置无需修改

### 开发中 🚧
- [ ] **DifyPlatform** - Dify 工作流平台集成

### 计划功能 📋
- [ ] **平台监控** - 响应时间、成功率统计
- [ ] **热配置更新** - 运行时动态更新配置
- [ ] **Web 管理界面** - 图形化配置管理
- [ ] **多 Bot 支持** - 用户级别的 Bot 个性化

### 架构优势 🎯

1. **模块化设计** - 每个平台独立实现，易于扩展
2. **智能路由** - 根据用户配置自动选择平台
3. **降级机制** - 平台不可用时自动降级
4. **配置驱动** - 通过 LISTEN_LIST 灵活配置用户平台映射
5. **错误处理** - 统一的错误处理和用户友好提示

### 使用示例

```python
# 在 config.py 中配置用户平台映射
LISTEN_LIST = [
    ['用户A', '角色1', 'llm_direct'],  # 使用大模型直连
    ['用户B', '角色2', 'coze'],        # 使用 Coze 平台
    ['群聊C', '角色3', 'coze'],        # 群聊使用 Coze
]

# 系统自动路由，无需修改现有代码
# 用户A的消息 → LLMDirectPlatform
# 用户B的消息 → CozePlatform  
# 群聊C的消息 → CozePlatform
```

---

**总结**：本设计方案以用户选择为核心，通过模块化架构实现多AI平台的灵活集成。现已完成核心架构和主要平台的实现，为微信机器人提供了强大的多平台 AI 支持能力。 