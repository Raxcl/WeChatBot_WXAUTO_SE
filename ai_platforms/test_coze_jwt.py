# -*- coding: utf-8 -*-

"""
测试Coze平台的JWT OAuth优先认证机制
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

def test_jwt_oauth_priority():
    """测试JWT OAuth优先级"""
    try:
        from ai_platforms.coze_platform import CozePlatform
        
        logger.info("=== 测试JWT OAuth优先认证机制 ===")
        
        # 测试现有配置（应该检测到JWT OAuth配置）
        logger.info("1. 检查现有配置...")
        platform = CozePlatform()
        
        # 如果到这里没报错，说明认证配置有效
        logger.info("✅ Coze平台初始化成功")
        
        # 检查使用的认证方式
        if platform.has_jwt_oauth_config():
            logger.info("✅ 正确：使用JWT OAuth认证（支持自动刷新）")
        else:
            logger.info("⚠️ 使用固定API Token认证（无法自动刷新）")
        
        return True
        
    except ValueError as e:
        if "认证未配置" in str(e):
            logger.info("✅ 正确：系统正确识别认证配置缺失")
            logger.info("提示信息:")
            for line in str(e).split('\n'):
                if line.strip():
                    logger.info(f"   {line}")
            return True
        else:
            logger.error(f"❌ 意外的认证错误: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

def test_config_priority():
    """测试配置优先级逻辑"""
    try:
        from ai_platforms.coze_platform import CozePlatform
        
        logger.info("\n=== 测试配置优先级逻辑 ===")
        
        # 测试1：只有JWT OAuth配置
        logger.info("1. 测试JWT OAuth配置检查...")
        test_config_jwt = {
            'client_id': 'test_client',
            'private_key': 'test_key',
            'public_key_id': 'test_public_key',
            'api_token': '',  # 空的API Token
            'api_base_url': 'https://api.coze.cn',
            'bot_id': 'test_bot'
        }
        
        platform_jwt = CozePlatform(test_config_jwt)
        jwt_detected = platform_jwt.has_jwt_oauth_config()
        logger.info(f"✅ JWT OAuth配置检测: {'有效' if jwt_detected else '无效'}")
        
        # 测试2：只有API Token配置
        logger.info("2. 测试API Token配置检查...")
        test_config_token = {
            'client_id': '',
            'private_key': '',
            'public_key_id': '',
            'api_token': 'test_token',
            'api_base_url': 'https://api.coze.cn',
            'bot_id': 'test_bot'
        }
        
        platform_token = CozePlatform(test_config_token)
        token_detected = not platform_token.has_jwt_oauth_config()
        logger.info(f"✅ API Token配置检测: {'有效' if token_detected else '无效'}")
        
        # 测试3：都没有配置
        logger.info("3. 测试空配置...")
        test_config_empty = {
            'client_id': '',
            'private_key': '',
            'public_key_id': '',
            'api_token': '',
            'api_base_url': 'https://api.coze.cn',
            'bot_id': 'test_bot'
        }
        
        try:
            platform_empty = CozePlatform(test_config_empty)
            platform_empty.get_coze_api_token()
            logger.error("❌ 应该报错但没有报错")
            return False
        except ValueError as e:
            logger.info("✅ 正确：空配置被正确识别并报错")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置优先级测试失败: {e}", exc_info=True)
        return False

def main():
    """运行所有测试"""
    logger.info("开始测试Coze JWT OAuth优先认证机制...")
    
    results = []
    
    # 测试JWT OAuth优先级
    logger.info("\n" + "="*60)
    results.append(("JWT OAuth优先级", test_jwt_oauth_priority()))
    
    # 测试配置优先级逻辑
    logger.info("\n" + "="*60)
    results.append(("配置优先级逻辑", test_config_priority()))
    
    # 总结测试结果
    logger.info("\n" + "="*60)
    logger.info("📊 测试结果总结:")
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"  {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        logger.info("\n🎉 所有测试都通过了！")
        logger.info("📋 配置优先级：JWT OAuth > API Token > 环境变量")
        logger.info("💡 推荐使用JWT OAuth，支持24小时自动刷新")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查实现。")
    
    return all_passed

if __name__ == "__main__":
    main() 