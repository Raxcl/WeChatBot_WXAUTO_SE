# -*- coding: utf-8 -*-

import sys
import os
import logging
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

def test_coze_platform():
    """测试 Coze 平台功能"""
    
    print("=" * 60)
    print("🚀 开始测试 Coze 平台功能")
    print("=" * 60)
    
    try:
        # 导入配置和平台
        from config import COZE_CONFIG
        from ai_platforms.coze_platform import CozePlatform
        
        print(f"\n📋 当前配置信息:")
        print(f"   - Client ID: {COZE_CONFIG.get('client_id', '未配置')}")
        print(f"   - Bot ID: {COZE_CONFIG.get('bot_id', '未配置')}")
        print(f"   - API Base URL: {COZE_CONFIG.get('api_base_url', '未配置')}")
        print(f"   - Token TTL: {COZE_CONFIG.get('token_ttl', 3600)}秒")
        print(f"   - 自动刷新Token: {COZE_CONFIG.get('auto_refresh_token', True)}")
        
        # 测试1: 初始化平台
        print(f"\n🔧 测试1: 初始化 Coze 平台...")
        coze_platform = CozePlatform()
        print("✅ Coze 平台初始化成功")
        
        # 测试2: 验证配置
        print(f"\n🔍 测试2: 验证配置...")
        coze_platform.validate_config()
        print("✅ 配置验证通过")
        
        # 测试3: Token管理
        print(f"\n🔑 测试3: Token 管理...")
        
        # 显示当前token状态
        if coze_platform.config.get('current_token'):
            expires_at = coze_platform.config.get('token_expires_at')
            if expires_at:
                expire_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expires_at))
                remaining = int(expires_at - time.time())
                print(f"   - 当前Token状态: 已获取")
                print(f"   - 过期时间: {expire_time}")
                print(f"   - 剩余时间: {remaining}秒")
            else:
                print("   - 当前Token状态: 已获取但无过期时间记录")
        else:
            print("   - 当前Token状态: 未获取")
        
        # 测试token是否过期
        is_expired = coze_platform.is_token_expired()
        print(f"   - Token是否需要刷新: {'是' if is_expired else '否'}")
        
        # 手动刷新token测试
        print(f"   - 手动刷新Token...")
        coze_platform.get_access_token()
        print("✅ Token 获取成功")
        
        # 测试4: API调用
        print(f"\n💬 测试4: API 调用...")
        
        test_messages = [
            "你好！",
            "请介绍一下你自己",
            "今天天气怎么样？"
        ]
        
        test_user_id = "test_user_001"
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   测试消息 {i}: {message}")
            try:
                response = coze_platform.get_response(
                    message=message,
                    user_id=test_user_id,
                    store_context=True,
                    is_summary=False
                )
                print(f"   ✅ 回复: {response[:100]}{'...' if len(response) > 100 else ''}")
                
                # 每次调用间隔1秒，避免频率限制
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ API调用失败: {str(e)}")
                logger.error(f"API调用失败", exc_info=True)
        
        # 测试5: 错误处理
        print(f"\n🚨 测试5: 错误处理...")
        
        # 测试空消息
        try:
            response = coze_platform.get_response("", test_user_id)
            print(f"   ✅ 空消息处理: {response}")
        except Exception as e:
            print(f"   ✅ 空消息错误处理: {str(e)}")
        
        print(f"\n🎉 所有测试完成！")
        
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保已安装 cozepy 依赖: pip install cozepy")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        logger.error("测试过程中发生错误", exc_info=True)
        
        # 提供一些常见问题的解决建议
        error_str = str(e).lower()
        print(f"\n💡 可能的解决方案:")
        
        if "client_id" in error_str or "invalid" in error_str:
            print("   - 检查 config.py 中的 client_id 是否正确")
            print("   - 确认 Coze 平台的 JWT 应用配置")
            
        elif "bot_id" in error_str:
            print("   - 检查 config.py 中的 bot_id 是否正确")
            print("   - 确认在 Coze 平台已创建 Bot")
            
        elif "private_key" in error_str or "public_key" in error_str:
            print("   - 检查私钥格式是否正确")
            print("   - 确认 public_key_id 是否匹配")
            
        elif "authentication" in error_str or "authorization" in error_str:
            print("   - 检查 JWT 配置是否正确")
            print("   - 确认应用权限设置")
            
        else:
            print("   - 检查网络连接")
            print("   - 查看完整错误日志")
            print("   - 确认 Coze API 服务状态")

if __name__ == "__main__":
    test_coze_platform() 