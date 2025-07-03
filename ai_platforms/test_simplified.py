# -*- coding: utf-8 -*-

"""
测试简化后的AI平台集成
- 去掉了降级策略
- 优化了token获取方式
- 支持system_prompt参数
"""

import logging
import sys
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_llm_direct_platform():
    """测试LLM Direct平台"""
    try:
        from ai_platforms.llm_direct import LLMDirectPlatform
        
        logger.info("=== 测试 LLM Direct 平台 ===")
        
        # 初始化平台
        platform = LLMDirectPlatform()
        logger.info("✅ LLM Direct平台初始化成功")
        
        # 测试基本功能
        response1 = platform.get_response(
            message="你好，简单介绍一下你自己",
            user_id="test_user",
            store_context=False
        )
        logger.info(f"✅ 基本回复: {response1[:100]}...")
        
        # 测试system_prompt功能
        response2 = platform.get_response(
            message="你好，介绍一下你自己",
            user_id="test_user",
            store_context=False,
            system_prompt="你是一位幽默的程序员助手，喜欢用代码术语和比喻来解释事情。"
        )
        logger.info(f"✅ 带system_prompt回复: {response2[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM Direct平台测试失败: {e}", exc_info=True)
        return False

def test_coze_platform():
    """测试Coze平台（预期会失败，因为没有配置token）"""
    try:
        from ai_platforms.coze_platform import CozePlatform
        
        logger.info("=== 测试 Coze 平台 ===")
        
        # 初始化平台（预期失败）
        platform = CozePlatform()
        logger.info("❌ 意外：Coze平台初始化成功了（应该失败的）")
        return False
        
    except ValueError as e:
        if "API Token 未配置" in str(e):
            logger.info("✅ 正确：Coze平台因缺少token而初始化失败")
            logger.info(f"   错误信息: {str(e)[:100]}...")
            return True
        else:
            logger.error(f"❌ 意外的ValueError: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Coze平台测试出现意外错误: {e}")
        return False

def test_platform_router():
    """测试平台路由器（无降级策略）"""
    try:
        from ai_platforms.platform_router import get_platform_response, get_platform_stats
        
        logger.info("=== 测试平台路由器 ===")
        
        # 获取平台统计
        stats = get_platform_stats()
        available_platforms = [p['name'] for p in stats.get('available_platforms', [])]
        logger.info(f"✅ 可用平台: {available_platforms}")
        
        # 测试LLM Direct平台用户
        logger.info("\n测试 LLM Direct 用户...")
        response1 = get_platform_response(
            message="你好",
            user_id="raxcl",  # 配置为llm_direct
            store_context=False
        )
        logger.info(f"✅ LLM Direct用户回复: {response1[:100]}...")
        
        # 测试带system_prompt
        response2 = get_platform_response(
            message="介绍一下你自己",
            user_id="raxcl",
            store_context=False,
            system_prompt="你是一位博学的历史老师。"
        )
        logger.info(f"✅ 带system_prompt回复: {response2[:100]}...")
        
        # 测试Coze平台用户（预期失败）
        logger.info("\n测试 Coze 用户（预期失败）...")
        response3 = get_platform_response(
            message="你好",
            user_id="测试群1",  # 配置为coze
            store_context=False
        )
        
        if "AI服务暂时不可用，请检查平台配置" in response3:
            logger.info("✅ 正确：Coze用户收到了配置错误提示")
        else:
            logger.warning(f"⚠️ 意外回复: {response3[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 平台路由器测试失败: {e}", exc_info=True)
        return False

def main():
    """运行所有测试"""
    logger.info("开始测试简化后的AI平台集成...")
    
    results = []
    
    # 测试LLM Direct平台
    logger.info("\n" + "="*60)
    results.append(("LLM Direct平台", test_llm_direct_platform()))
    
    # 测试Coze平台（预期失败）
    logger.info("\n" + "="*60)
    results.append(("Coze平台错误处理", test_coze_platform()))
    
    # 测试平台路由器
    logger.info("\n" + "="*60)
    results.append(("平台路由器", test_platform_router()))
    
    # 总结测试结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果总结:")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"  {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        logger.info("\n🎉 所有测试都通过了！")
        logger.info("💡 要使用Coze平台，请在config.py中配置正确的api_token")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查实现。")
    
    return all_passed

if __name__ == "__main__":
    main() 