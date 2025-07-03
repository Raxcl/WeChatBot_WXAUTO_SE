# -*- coding: utf-8 -*-

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_platform_router():
    """测试平台路由器功能"""
    
    print("=" * 60)
    print("🚀 开始测试多平台路由器")
    print("=" * 60)
    
    try:
        # 测试1: 导入路由器
        print("\n🔧 测试1: 导入路由器模块...")
        from ai_platforms.platform_router import get_platform_response, get_platform_stats, test_all_platforms
        print("✅ 路由器模块导入成功")
        
        # 测试2: 获取平台统计
        print("\n📊 测试2: 获取平台统计信息...")
        stats = get_platform_stats()
        print(f"   - 总平台数: {stats.get('total_platforms', 0)}")
        print(f"   - 可用平台: {len(stats.get('available_platforms', []))}")
        print(f"   - 默认平台: {stats.get('default_platform', 'unknown')}")
        print(f"   - 用户分布: {stats.get('user_distribution', {})}")
        
        # 显示详细平台信息
        available_platforms = stats.get('available_platforms', [])
        for platform in available_platforms:
            print(f"   - 平台: {platform['name']} ({platform['class']})")
        
        # 测试3: 连接测试
        print("\n🔗 测试3: 平台连接测试...")
        test_results = test_all_platforms()
        for platform_name, result in test_results.items():
            status = "✅ 连接成功" if result else "❌ 连接失败"
            print(f"   - {platform_name}: {status}")
        
        # 测试4: 路由测试
        print("\n💬 测试4: 消息路由测试...")
        
        test_cases = [
            ("测试群1", "你好！我是测试消息", "coze"),  # 应该路由到Coze
            ("测试群2", "测试llm_direct", "llm_direct"),  # 应该路由到llm_direct
            ("raxcl", "个人消息测试", "llm_direct"),  # 应该路由到llm_direct
            ("未知用户", "未配置用户测试", "llm_direct"),  # 应该降级到默认平台
        ]
        
        for user_id, message, expected_platform in test_cases:
            print(f"\n   测试用户: {user_id} (期望平台: {expected_platform})")
            print(f"   消息: {message}")
            
            try:
                response = get_platform_response(message, user_id, store_context=False)
                print(f"   ✅ 回复: {response[:100]}{'...' if len(response) > 100 else ''}")
            except Exception as e:
                print(f"   ❌ 路由失败: {str(e)}")
        
        print(f"\n🎉 路由器测试完成！")
        
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保已安装必要的依赖")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        logger.error("测试过程中发生错误", exc_info=True)

if __name__ == "__main__":
    test_platform_router() 