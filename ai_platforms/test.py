# -*- coding: utf-8 -*-

"""
AI平台集成测试脚本

用于测试和验证AI平台集成架构的基础功能，
包括配置解析、路由器初始化、平台连接等。
"""

import logging
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_basic_imports():
    """测试基础模块导入"""
    print("\n🔍 测试基础模块导入...")
    
    try:
        import ai_platforms
        from ai_platforms import (
            BasePlatform, PlatformRouter, LLMDirectPlatform,
            parse_listen_list, create_platform_router, 
            validate_platform_configs, print_platform_info
        )
        print("✅ 核心模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_config_parsing():
    """测试配置解析功能"""
    print("\n🔍 测试配置解析功能...")
    
    try:
        from ai_platforms import parse_listen_list
        
        # 测试正确的3元素格式配置
        valid_format = [
            ['测试用户1', '角色1', 'llm_direct'],
            ['测试用户2', '角色2', 'coze'],
            ['测试用户3', '角色3', 'dify']
        ]
        result = parse_listen_list(valid_format)
        assert len(result) == 3
        assert result['测试用户1']['platform'] == 'llm_direct'
        assert result['测试用户2']['platform'] == 'coze'
        assert result['测试用户3']['platform'] == 'dify'
        print("✅ 3元素格式配置解析成功")
        
        # 测试错误格式（2元素）- 应该抛出错误
        try:
            invalid_format = [['测试用户1', '角色1']]  # 缺少平台参数
            parse_listen_list(invalid_format)
            print("❌ 应该拒绝2元素格式，但是没有")
            return False
        except ValueError:
            print("✅ 正确拒绝了2元素格式")
        
        # 测试无效平台名称
        try:
            invalid_platform = [['测试用户1', '角色1', 'invalid_platform']]
            parse_listen_list(invalid_platform)
            print("❌ 应该拒绝无效平台名称，但是没有")
            return False
        except ValueError:
            print("✅ 正确拒绝了无效平台名称")
        
        return True
    except Exception as e:
        print(f"❌ 配置解析测试失败: {e}")
        return False

def test_platform_initialization():
    """测试平台初始化"""
    print("\n🔍 测试平台初始化...")
    
    try:
        from ai_platforms import LLMDirectPlatform
        
        # 测试LLM Direct平台初始化
        platform = LLMDirectPlatform()
        print(f"✅ LLM Direct平台初始化成功: {platform.get_platform_name()}")
        
        # 测试平台信息
        info = platform.get_platform_info()
        print(f"  平台信息: {info}")
        
        return True
    except Exception as e:
        print(f"❌ 平台初始化失败: {e}")
        return False

def test_router_creation():
    """测试路由器创建"""
    print("\n🔍 测试路由器创建...")
    
    try:
        from ai_platforms import create_platform_router
        
        # 创建测试配置 - 必须是3元素格式
        test_config = [
            ['测试用户1', '角色1', 'llm_direct'],
            ['测试用户2', '角色2', 'coze'],
            ['测试用户3', '角色3', 'dify'],
        ]
        
        # 创建路由器
        router = create_platform_router(test_config)
        print("✅ 路由器创建成功")
        
        # 测试用户平台选择
        platform1 = router.get_user_platform('测试用户1')
        if platform1:
            print(f"✅ 用户1平台选择: {platform1.get_platform_name()}")
        
        # 测试统计信息
        stats = router.get_platform_stats()
        print(f"✅ 路由器统计: {stats['total_platforms']} 个平台, {len(stats['user_distribution'])} 种分布")
        
        return True
    except Exception as e:
        print(f"❌ 路由器创建失败: {e}")
        return False

def test_configuration_validation():
    """测试配置验证"""
    print("\n🔍 测试配置验证...")
    
    try:
        from ai_platforms import validate_platform_configs
        
        results = validate_platform_configs()
        print("✅ 配置验证完成")
        
        for platform, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {platform}: {'有效' if status else '无效'}")
        
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def test_platform_info_display():
    """测试平台信息显示"""
    print("\n🔍 测试平台信息显示...")
    
    try:
        from ai_platforms import create_platform_router, print_platform_info
        from config import LISTEN_LIST
        
        router = create_platform_router(LISTEN_LIST)
        print_platform_info(router)
        
        return True
    except Exception as e:
        print(f"❌ 平台信息显示失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始AI平台集成基础架构测试")
    print("="*60)
    
    tests = [
        ("基础模块导入", test_basic_imports),
        ("配置解析功能", test_config_parsing),
        ("平台初始化", test_platform_initialization),
        ("路由器创建", test_router_creation),
        ("配置验证", test_configuration_validation),
        ("平台信息显示", test_platform_info_display),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "="*60)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！基础架构工作正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
        return False

if __name__ == "__main__":
    # 确保在正确的目录下运行
    if not os.path.exists(os.path.join(parent_dir, "config.py")):
        print("❌ 请确保项目根目录有config.py文件")
        sys.exit(1)
    
    success = run_all_tests()
    sys.exit(0 if success else 1) 