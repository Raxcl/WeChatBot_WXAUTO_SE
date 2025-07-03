# Coze 平台集成指南

## 概述

本指南将帮助你将 Coze（扣子）平台集成到微信机器人中，实现通过 JWT OAuth 进行鉴权的 AI 对话功能。

## 前置条件

1. **Python 环境**: Python 3.7+
2. **Coze 账户**: 已注册 Coze 账户（[www.coze.cn](https://www.coze.cn)）
3. **已创建的 OAuth App**: 在 Coze 平台创建的 JWT 类型 OAuth 应用

## 步骤 1: 创建 Coze OAuth 应用

### 1.1 访问 OAuth 应用管理页面
- 国内用户：[https://www.coze.cn/open/oauth/apps](https://www.coze.cn/open/oauth/apps)
- 海外用户：[https://www.coze.com/open/oauth/apps](https://www.coze.com/open/oauth/apps)

### 1.2 创建 Service 类型应用
1. 点击"创建应用"
2. 选择应用类型：**Service application**
3. 填写应用信息：
   - 应用名称：例如 "微信机器人"
   - 应用描述：例如 "用于微信机器人的AI对话服务"
4. 提交创建

### 1.3 获取认证信息
创建成功后，你将获得以下信息：
- **Client ID**: 客户端 ID
- **Private Key**: 私钥（PEM 格式）
- **Public Key ID**: 公钥 ID

⚠️ **重要**: 请妥善保存私钥和公钥 ID，避免泄露。

## 步骤 2: 创建 Coze Bot

### 2.1 创建 Bot
1. 访问 [Coze Bot 创建页面](https://www.coze.cn/space/bots)
2. 点击"创建 Bot"
3. 配置 Bot：
   - Bot 名称：例如 "微信助手"
   - 描述：Bot 的功能描述
   - 头像：选择合适的头像
   - 人设与回复逻辑：设置 Bot 的性格和回复风格

### 2.2 发布 Bot
1. 完成 Bot 配置后，点击"发布"
2. 发布成功后，从浏览器地址栏获取 Bot ID
   - 地址格式：`https://www.coze.cn/space/[workspace_id]/bot/[bot_id]`
   - Bot ID 就是 URL 中的最后一串数字

## 步骤 3: 安装依赖

```bash
# 安装 Coze Python SDK
pip install cozepy

# 或者使用项目的 requirements.txt
pip install -r requirements.txt
```

## 步骤 4: 配置项目

### 4.1 更新 config.py
在 `config.py` 中的 `COZE_CONFIG` 部分，你的配置已经基本完成，只需要设置正确的 `bot_id`：

```python
COZE_CONFIG = {
    # JWT OAuth 配置（已配置）
    'client_type': 'jwt',
    'client_id': '1172432460246',  # 你的 Client ID
    'private_key': """-----BEGIN PRIVATE KEY-----
    ...你的私钥...
    -----END PRIVATE KEY-----""",
    'public_key_id': 'Wh_cgx5H1xz0MNA8O5t7-POb3dQmVfdloDc_X8BL0ek',
    'www_base_url': 'https://www.coze.cn',
    'api_base_url': 'https://api.coze.cn',
    
    # Bot 配置（需要设置）
    'bot_id': 'your-bot-id-here',  # ⚠️ 请替换为你的实际 Bot ID
    'stream': False,
    'temperature': 0.8,
    'max_tokens': 2000,
    'token_ttl': 3600,  # JWT token 有效期（秒）
}
```

### 4.2 配置用户映射
在 `config.py` 中的 `LISTEN_LIST` 中添加使用 Coze 平台的用户：

```python
LISTEN_LIST = [
    ['测试群1', '角色1', 'llm_direct'],     # 使用大模型直连
    ['测试群2', '角色2', 'coze'],           # 使用 Coze 平台
    ['用户昵称', '角色名称', 'coze'],        # 使用 Coze 平台
]
```

## 步骤 5: 测试集成

运行测试脚本验证配置：

```bash
python test_coze_integration.py
```

测试脚本会检查：
- ✅ Coze 配置是否完整
- ✅ cozepy 包是否正确安装  
- ✅ Coze 平台是否能正确实例化
- ✅ JWT token 是否能正确生成
- ✅ Chat API 是否能正常调用（需要正确的 bot_id）
- ✅ 平台路由器集成是否正常

## 步骤 6: 启动机器人

如果所有测试通过，你就可以启动微信机器人了：

```bash
python bot.py
```

机器人会根据 `LISTEN_LIST` 配置，自动为不同用户路由到相应的 AI 平台。

## 常见问题

### Q1: JWT token 生成失败
**问题**: 提示认证失败或 token 无效
**解决**: 
- 检查 `client_id` 是否正确
- 检查 `private_key` 格式是否正确（包含 `-----BEGIN PRIVATE KEY-----` 和 `-----END PRIVATE KEY-----`）
- 检查 `public_key_id` 是否正确

### Q2: Chat API 调用失败
**问题**: 提示 Bot 不存在或无权访问
**解决**:
- 检查 `bot_id` 是否正确
- 确保 Bot 已经发布
- 确保 OAuth 应用有访问该 Bot 的权限

### Q3: 依赖安装失败
**问题**: `pip install cozepy` 失败
**解决**:
- 更新 pip: `pip install --upgrade pip`
- 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple cozepy`

### Q4: 编码问题
**问题**: 私钥中包含特殊字符导致配置错误
**解决**:
- 使用三引号字符串 `"""..."""` 包围私钥
- 确保文件编码为 UTF-8

## 高级配置

### 自定义错误处理
你可以在 `ai_platforms/coze_platform.py` 中的 `handle_error` 方法中自定义错误处理逻辑。

### 调整 API 参数
在 `COZE_CONFIG` 中可以调整：
- `temperature`: 控制回复的随机性（0.0-1.0）
- `max_tokens`: 最大回复长度
- `token_ttl`: JWT token 有效期

### 多 Bot 支持
如果需要为不同用户使用不同的 Bot，可以扩展配置结构，在 `LISTEN_LIST` 中加入 Bot ID 信息。

## 参考链接

- [Coze 官方文档](https://www.coze.cn/docs)
- [Coze OAuth JWT 文档](https://www.coze.cn/docs/developer_guides/oauth_jwt)
- [Coze Python SDK](https://github.com/coze-dev/coze-py)

## 技术支持

如果遇到问题，请：
1. 首先运行 `test_coze_integration.py` 检查配置
2. 查看日志输出中的错误信息
3. 参考 Coze 官方文档进行排查

---

**祝你使用愉快！** 🎉 