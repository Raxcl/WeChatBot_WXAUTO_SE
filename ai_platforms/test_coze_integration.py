# -*- coding: utf-8 -*-

"""
Coze 平台集成测试脚本

使用此脚本来测试你的 Coze JWT OAuth 配置是否正确。

用法:
    cd ai_platforms
    python test_coze_integration.py
"""

import sys
import os
import logging

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_coze_config():
    """测试 Coze 配置"""
    print("🧪 测试 Coze 配置...")
    
    try:
        from config import COZE_CONFIG
        
        # 检查必要的配置项
        required_keys = ['client_id', 'private_key', 'public_key_id', 'bot_id']
        missing_keys = []
        
        for key in required_keys:
            if not COZE_CONFIG.get(key) or COZE_CONFIG[key] in ['your-client-id', 'your-bot-id']:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 缺少或无效的配置项: {missing_keys}")
            print("请在 config.py 中的 COZE_CONFIG 中设置正确的值")
            return False
        
        print("✅ Coze 配置项检查通过")
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入配置: {e}")
        return False

def test_cozepy_import():
    """测试 cozepy 包是否正确安装"""
    print("📦 测试 cozepy 包导入...")
    
    try:
        from cozepy import Coze, JWTAuth, JWTOAuthApp, Message
        print("✅ cozepy 包导入成功")
        return True
    except ImportError as e:
        print(f"❌ cozepy 包导入失败: {e}")
        print("请运行: pip install cozepy")
        return False

def test_coze_platform():
    """测试 Coze 平台实例化"""
    print("🚀 测试 Coze 平台实例化...")
    
    try:
        from coze_platform import CozePlatform
        
        # 创建平台实例
        platform = CozePlatform()
        
        # 验证配置
        platform.validate_config()
        
        print("✅ Coze 平台实例化成功")
        return platform
        
    except Exception as e:
        print(f"❌ Coze 平台实例化失败: {e}")
        return None

def test_jwt_token_generation(platform):
    """测试 JWT token 生成"""
    print("🔑 测试 JWT token 生成...")
    
    try:
        if platform and platform.jwt_oauth_app:
            # 尝试生成 token
            token = platform.jwt_oauth_app.get_access_token(ttl=300)  # 5分钟有效期
            print("✅ JWT token 生成成功")
            print(f"Token 类型: {type(token)}")
            return True
        else:
            print("❌ 平台或 JWT OAuth App 未初始化")
            return False
            
    except Exception as e:
        print(f"❌ JWT token 生成失败: {e}")
        return False

def test_coze_chat_api(platform):
    """测试 Coze Chat API（需要正确的 bot_id）"""
    print("💬 测试 Coze Chat API...")
    
    try:
        from config import COZE_CONFIG
        
        if COZE_CONFIG.get('bot_id') == 'your-bot-id':
            print("⚠️  跳过 Chat API 测试：请在 config.py 中设置正确的 bot_id")
            return False
        
        if platform and platform.coze_client:
            # 测试简单的对话
            test_message = "你好，这是一个测试消息"
            test_user_id = "test_user_123"
            
            print(f"发送测试消息: {test_message}")
            response = platform.get_response(test_message, test_user_id, store_context=False)
            
            print(f"收到回复: {response[:100]}...")
            print("✅ Coze Chat API 测试成功")
            return True
        else:
            print("❌ Coze 客户端未初始化")
            return False
            
    except Exception as e:
        print(f"❌ Coze Chat API 测试失败: {e}")
        return False

def test_platform_router_integration():
    """测试平台路由器集成"""
    print("🔀 测试平台路由器集成...")
    
    try:
        from platform_router import PlatformRouter
        from . import get_coze_platform
        
        # 测试延迟导入
        coze_class = get_coze_platform()
        if coze_class is None:
            print("❌ 无法通过延迟导入获取 Coze 平台")
            return False
        
        # 创建测试用的用户映射
        test_mapping = {
            'test_user': {
                'role': '测试角色',
                'platform': 'coze'
            }
        }
        
        # 创建路由器
        router = PlatformRouter(test_mapping)
        
        # 测试平台获取
        platform = router.get_user_platform('test_user')
        if platform and platform.__class__.__name__ == 'CozePlatform':
            print("✅ 平台路由器集成成功")
            return True
        else:
            print("❌ 平台路由器无法正确获取 Coze 平台")
            return False
            
    except Exception as e:
        print(f"❌ 平台路由器集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 Coze 平台集成测试")
    print("=" * 50)
    
    tests = [
        ("配置检查", test_coze_config),
        ("cozepy 包导入", test_cozepy_import),
        ("平台实例化", test_coze_platform),
    ]
    
    results = {}
    platform = None
    
    # 执行基础测试
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_name == "平台实例化":
            platform = test_func()
            results[test_name] = platform is not None
        else:
            results[test_name] = test_func()
    
    # 如果基础测试通过，执行高级测试
    if platform:
        print(f"\n📋 JWT Token 生成:")
        results["JWT Token 生成"] = test_jwt_token_generation(platform)
        
        print(f"\n📋 Chat API 测试:")
        results["Chat API 测试"] = test_coze_chat_api(platform)
    
    print(f"\n📋 路由器集成:")
    results["路由器集成"] = test_platform_router_integration()
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name}")
        if passed_test:
            passed += 1
    
    print(f"\n📈 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Coze 平台集成成功！")
        print("\n📝 下一步:")
        print("1. 在 config.py 中设置正确的 bot_id（在 Coze 平台创建 Bot 后获取）")
        print("2. 在 LISTEN_LIST 中添加使用 'coze' 平台的用户配置")
        print("3. 启动微信机器人测试实际对话")
    else:
        print(f"\n⚠️  还有 {total-passed} 个测试未通过，请检查配置和依赖")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 