# -*- coding: utf-8 -*-

"""
Coze平台配置示例
展示正确的认证方式优先级和配置方法
"""

# === Coze平台配置示例 ===
COZE_CONFIG_EXAMPLE = {
    # === JWT OAuth 认证（支持自动刷新，适合长期运行）===
    'client_id': '你的应用ID',  # 从 Coze 开放平台获取
    'private_key': """-----BEGIN PRIVATE KEY-----
你的私钥内容
-----END PRIVATE KEY-----""",
    'public_key_id': '你的公钥ID',  # 对应私钥的公钥ID
    
    # === 通用配置 ===
    'api_base_url': 'https://api.coze.cn',  # Coze API 端点
    'bot_id': '你的机器人ID',  # 在 Coze 平台创建 Bot 后获取
    
    # === 对话参数 ===
    'stream': False,      # 是否使用流式响应
    'temperature': 0.8,   # 生成文本的随机性
    'max_tokens': 2000,   # 最大回复长度
}

# === 配置说明 ===
"""
Coze平台认证方式：JWT OAuth

✅ 支持自动刷新（24小时有效期，自动续期）
✅ 适合长期运行的机器人
✅ 更安全，不需要暴露长期token

需要配置：client_id, private_key, public_key_id
获取方式：在 Coze 开放平台创建应用，下载私钥

为什么只支持 JWT OAuth？
- 微信机器人需要24小时运行
- JWT token 会自动刷新，确保服务稳定
- 避免因token过期导致的服务中断
"""

# === 实际使用示例 ===
"""
在 config.py 中配置：

COZE_CONFIG = {
    # 方式1：JWT OAuth（推荐）
    'client_id': '1172432460246',
    'private_key': '''-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC7qhVAtVvZWpSd
...（你的私钥内容）...
-----END PRIVATE KEY-----''',
    'public_key_id': 'Wh_cgx5H1xz0MNA8O5t7-POb3dQmVfdloDc_X8BL0ek',
    
    # 方式2：固定Token（备选）
    # 'api_token': 'pat_xxxxxxxxxxxxxxxxxxxxx',
    
    # 通用配置
    'api_base_url': 'https://api.coze.cn',
    'bot_id': '7522683039198085155',
    'stream': False,
    'temperature': 0.8,
    'max_tokens': 2000,
}
""" 