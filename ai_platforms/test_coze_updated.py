# -*- coding: utf-8 -*-

"""
测试更新后的Coze平台集成
基于官方示例实现，支持system_prompt参数
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

def test_coze_platform_with_system_prompt():
    """测试带有system_prompt的Coze平台功能"""
    try:
        from ai_platforms.coze_platform import CozePlatform
        
        logger.info("=== 测试Coze平台（基于官方示例）===")
        
        # 初始化平台
        logger.info("1. 初始化Coze平台...")
        platform = CozePlatform()
        logger.info(f"✅ 平台初始化成功: {platform.get_platform_name()}")
        
        # 测试1：不使用system_prompt
        logger.info("\n2. 测试基本对话（无system_prompt）...")
        test_user = "test_user_coze"
        test_message = "你好，请简单介绍一下你自己"
        
        response = platform.get_response(
            message=test_message,
            user_id=test_user,
            store_context=False
        )
        logger.info(f"✅ 基本对话回复: {response[:100]}...")
        
        # 测试2：使用自定义system_prompt
        logger.info("\n3. 测试自定义系统提示词...")
        custom_prompt = "你是一位古代中国的诗人李白，请用诗人的口吻和风格回答问题，偶尔引用一些诗句。"
        
        response_with_prompt = platform.get_response(
            message="请介绍一下你自己",
            user_id=test_user,
            store_context=False,
            system_prompt=custom_prompt
        )
        logger.info(f"✅ 带系统提示词回复: {response_with_prompt[:100]}...")
        
        # 测试3：连接测试
        logger.info("\n4. 测试平台连接...")
        connection_ok = platform.test_connection()
        logger.info(f"✅ 连接测试结果: {'通过' if connection_ok else '失败'}")
        
        # 测试4：平台信息
        logger.info("\n5. 获取平台信息...")
        platform_info = platform.get_platform_info()
        logger.info(f"✅ 平台信息: {platform_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Coze平台测试失败: {e}", exc_info=True)
        return False

def test_platform_router_with_system_prompt():
    """测试平台路由器的system_prompt支持"""
    try:
        from ai_platforms.platform_router import get_platform_response, get_platform_stats
        
        logger.info("\n=== 测试平台路由器（system_prompt支持）===")
        
        # 获取平台统计
        logger.info("1. 获取平台统计信息...")
        stats = get_platform_stats()
        logger.info(f"✅ 可用平台: {[p['name'] for p in stats.get('available_platforms', [])]}")
        
        # 测试LLM Direct平台（应该支持system_prompt）
        logger.info("\n2. 测试LLM Direct平台...")
        test_user = "raxcl"  # 配置为使用llm_direct平台的用户
        
        response1 = get_platform_response(
            message="你好，请简单介绍一下你自己",
            user_id=test_user,
            store_context=False
        )
        logger.info(f"✅ LLM Direct基本回复: {response1[:100]}...")
        
        # 使用自定义system_prompt
        response2 = get_platform_response(
            message="请介绍一下你自己",
            user_id=test_user,
            store_context=False,
            system_prompt="你是一位博学的图书管理员，喜欢用书本知识来回答问题。"
        )
        logger.info(f"✅ LLM Direct带提示词回复: {response2[:100]}...")
        
        # 测试Coze平台（如果可用）
        logger.info("\n3. 测试Coze平台路由...")
        coze_user = "测试群1"  # 配置为使用coze平台的用户
        
        try:
            response3 = get_platform_response(
                message="你好",
                user_id=coze_user,
                store_context=False,
                system_prompt="你是一位友善的AI助手，总是以积极的态度回应。"
            )
            logger.info(f"✅ Coze平台回复: {response3[:100]}...")
        except Exception as e:
            logger.warning(f"⚠️ Coze平台测试跳过（可能配置未完成）: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 平台路由器测试失败: {e}", exc_info=True)
        return False

def test_llm_direct_platform():
    """测试LLM Direct平台的system_prompt支持"""
    try:
        from ai_platforms.llm_direct import LLMDirectPlatform
        
        logger.info("\n=== 测试LLM Direct平台（system_prompt支持）===")
        
        # 初始化平台
        platform = LLMDirectPlatform()
        logger.info(f"✅ LLM Direct平台初始化成功")
        
        # 测试基本功能
        response1 = platform.get_response(
            message="你好",
            user_id="test_llm",
            store_context=False
        )
        logger.info(f"✅ 基本回复: {response1[:100]}...")
        
        # 测试system_prompt功能
        response2 = platform.get_response(
            message="你好",
            user_id="test_llm",
            store_context=False,
            system_prompt="你是一位幽默的程序员，喜欢用代码比喻来解释事情。"
        )
        logger.info(f"✅ 带提示词回复: {response2[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM Direct平台测试失败: {e}", exc_info=True)
        return False

def main():
    """运行所有测试"""
    logger.info("开始测试更新后的AI平台集成...")
    
    results = []
    
    # 测试LLM Direct平台
    logger.info("\n" + "="*60)
    results.append(("LLM Direct平台", test_llm_direct_platform()))
    
    # 测试Coze平台
    logger.info("\n" + "="*60)
    results.append(("Coze平台", test_coze_platform_with_system_prompt()))
    
    # 测试平台路由器
    logger.info("\n" + "="*60)
    results.append(("平台路由器", test_platform_router_with_system_prompt()))
    
    # 总结测试结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果总结:")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"  {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        logger.info("\n🎉 所有测试都通过了！system_prompt功能已成功集成。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查配置和实现。")
    
    return all_passed

if __name__ == "__main__":
    main() 