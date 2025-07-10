#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChatBot 源码保护部署脚本
支持多种保护方案：Cython编译、代码混淆、PyInstaller打包
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

class SourceProtector:
    def __init__(self, project_dir="."):
        self.project_dir = Path(project_dir).resolve()
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        
        # 核心源码文件列表
        self.core_files = [
            "bot.py",
            "config.py", 
            "config_editor.py",
            "updater.py"
        ]
        
        # 需要保留的文件和目录
        self.preserve_items = [
            "requirements.txt",
            "templates/",
            "prompts/",
            "emojis/",
            "ai_platforms/",
            "database/",
            "libs/",
            "Demo_Image/",
            "LICENSE",
            "readme.md"
        ]

    def clean_build_dirs(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        # 清理Cython生成的文件
        for file in self.project_dir.glob("*.c"):
            file.unlink()
        for file in self.project_dir.glob("*.so"):
            file.unlink()
        for file in self.project_dir.glob("*.pyd"):
            file.unlink()

    def method_pyinstaller(self, use_obfuscation=True):
        """方案1: PyInstaller打包"""
        print("📦 开始PyInstaller打包...")
        
        # 检查并安装项目依赖
        requirements_file = self.project_dir / "requirements.txt"
        if requirements_file.exists():
            print("📦 安装项目依赖...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True, cwd=self.project_dir)
                print("✅ 项目依赖安装完成")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  项目依赖安装失败: {e}")
                print("🔄 继续执行打包...")
        else:
            print("⚠️  未找到 requirements.txt 文件")
        
        # 检查并安装PyInstaller
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                         capture_output=True, check=True)
            print("✅ PyInstaller 已安装")
        except subprocess.CalledProcessError:
            print("📦 安装 PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        if use_obfuscation:
            print("🔒 启用代码混淆...")
            try:
                self._obfuscate_code()
                main_file = self.dist_dir / "obfuscated" / "bot.py"
                if not main_file.exists():
                    print("⚠️  混淆后的主文件未找到，使用原始文件")
                    main_file = "bot.py"
            except Exception as e:
                print(f"⚠️  代码混淆失败: {e}")
                print("🔄 继续使用原始文件进行打包...")
                main_file = "bot.py"
        else:
            main_file = "bot.py"

        # 创建PyInstaller输出目录
        pyinstaller_dir = self.dist_dir / "pyinstaller"
        pyinstaller_dir.mkdir(parents=True, exist_ok=True)

        # PyInstaller命令
        cmd = [
            "pyinstaller",
            "--onefile",
            # "--noconsole",  # 暂时注释掉，以便看到错误信息
            "--name=WeChatBot",
            # 添加调试选项
            "--debug=all",
            # wxautox_wechatbot 相关隐藏导入
            "--hidden-import=wxautox_wechatbot",
            "--hidden-import=wxautox_wechatbot.logger",
            "--hidden-import=wxautox_wechatbot.param", 
            "--hidden-import=wxautox_wechatbot.languages",
            "--hidden-import=wxautox_wechatbot.uiautomation",
            # 其他依赖的隐藏导入
            "--hidden-import=comtypes",
            "--hidden-import=pywin32",
            "--hidden-import=win32api",
            "--hidden-import=win32con",
            "--hidden-import=win32gui",
            "--hidden-import=win32process",
            "--hidden-import=pywintypes",
            # 新发现的缺失模块
            "--hidden-import=tenacity",
            "--hidden-import=tenacity.retry",
            "--hidden-import=tenacity.stop",
            "--hidden-import=tenacity.wait",
            # OpenAI 相关
            "--hidden-import=openai",
            "--hidden-import=httpx",
            "--hidden-import=httpcore",
            "--hidden-import=h11",
            "--hidden-import=anyio",
            "--hidden-import=sniffio",
            # 数据库相关
            "--hidden-import=sqlalchemy",
            "--hidden-import=sqlalchemy.dialects.sqlite",
            "--hidden-import=sqlalchemy.pool",
            "--hidden-import=database",
            "--hidden-import=database.models",
            "--hidden-import=database.database",
            # 其他依赖
            "--hidden-import=requests",
            "--hidden-import=beautifulsoup4",
            "--hidden-import=bs4",
            "--hidden-import=pyautogui",
            "--hidden-import=PIL",
            "--hidden-import=PIL.Image",
            "--hidden-import=PIL.ImageTk",
            "--hidden-import=json",
            "--hidden-import=queue",
            "--hidden-import=threading",
            "--hidden-import=logging",
            "--hidden-import=datetime",
            "--hidden-import=base64",
            "--hidden-import=urllib.parse",
            # AI平台相关
            "--hidden-import=ai_platforms",
            "--hidden-import=ai_platforms.manager",
            "--hidden-import=ai_platforms.platform_router",
            "--hidden-import=ai_platforms.base_platform",
            "--hidden-import=ai_platforms.coze_platform",
            "--hidden-import=ai_platforms.llm_direct",
            # 收集wxautox_wechatbot包的所有数据文件
            "--collect-data=wxautox_wechatbot",
            # 收集项目的数据文件
            "--collect-data=database",
            "--collect-data=ai_platforms",
            f"--distpath={pyinstaller_dir}",
            str(main_file)
        ]
        
        # 添加数据文件（如果存在的话）
        data_dirs = ["templates", "prompts", "emojis"]
        for data_dir in data_dirs:
            dir_path = self.project_dir / data_dir
            if dir_path.exists():
                cmd.append(f"--add-data={data_dir};{data_dir}")
        
        try:
            print("🔨 执行 PyInstaller 打包...")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, 
                                 cwd=self.project_dir)
            print("✅ PyInstaller打包完成")
            print(f"📁 可执行文件位置: {pyinstaller_dir}/WeChatBot.exe")
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller 打包失败: {e}")
            if e.stderr:
                print(f"错误信息: {e.stderr}")
            print("💡 建议检查依赖项或尝试不使用混淆")
            raise

    def _obfuscate_code(self):
        """代码混淆"""
        print("🔒 混淆源代码...")
        
        try:
            # 检查PyArmor版本并安装
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "show", "pyarmor"], 
                                     capture_output=True, text=True, check=True)
                version_line = [line for line in result.stdout.split('\n') if line.startswith('Version:')]
                if version_line:
                    version = version_line[0].split(':')[1].strip()
                    print(f"✅ PyArmor 版本: {version}")
            except subprocess.CalledProcessError:
                print("📦 安装 PyArmor...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyarmor"], check=True)
            
            obf_dir = self.dist_dir / "obfuscated"
            obf_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用新的 PyArmor 8+ 语法
            print("🔄 使用 PyArmor 8+ 语法进行混淆...")
            
            # 混淆核心文件
            for file in self.core_files:
                file_path = self.project_dir / file
                if file_path.exists():
                    print(f"  混淆文件: {file}")
                    try:
                        # 使用新的语法: pyarmor gen -O output_dir file.py
                        cmd = ["pyarmor", "gen", "-O", str(obf_dir), str(file_path)]
                        subprocess.run(cmd, check=True, cwd=self.project_dir)
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️  文件 {file} 混淆失败，尝试备用方案: {e}")
                        # 如果新语法失败，尝试旧语法
                        try:
                            cmd = ["pyarmor", "obfuscate", "--output", str(obf_dir), str(file_path)]
                            subprocess.run(cmd, check=True, cwd=self.project_dir)
                        except subprocess.CalledProcessError:
                            print(f"❌ 文件 {file} 混淆失败，跳过...")
                            continue
            
            # 混淆目录
            for dir_name in ["ai_platforms", "database"]:
                dir_path = self.project_dir / dir_name
                if dir_path.exists():
                    print(f"  混淆目录: {dir_name}")
                    try:
                        # 对目录中的每个.py文件单独处理
                        for py_file in dir_path.rglob("*.py"):
                            if py_file.name != "__init__.py":  # 跳过__init__.py
                                try:
                                    rel_path = py_file.relative_to(self.project_dir)
                                    output_sub_dir = obf_dir / rel_path.parent
                                    output_sub_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    cmd = ["pyarmor", "gen", "-O", str(output_sub_dir), str(py_file)]
                                    subprocess.run(cmd, check=True, cwd=self.project_dir)
                                except subprocess.CalledProcessError:
                                    print(f"⚠️  跳过文件: {py_file}")
                                    continue
                    except Exception as e:
                        print(f"⚠️  目录 {dir_name} 混淆失败: {e}")
                        continue
            
            print("✅ 代码混淆完成")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ PyArmor 混淆失败: {e}")
            print("💡 尝试手动安装 PyArmor: pip install pyarmor")
            print("💡 或者使用 --no-obfuscation 参数跳过混淆")
            raise
        except Exception as e:
            print(f"❌ 混淆过程中出现未知错误: {e}")
            raise

    def _create_launcher_script(self, deploy_dir):
        """创建启动脚本"""
        launcher_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChatBot启动器 - Cython编译版本
"""

import sys
import importlib.util

def load_compiled_module(module_name, file_path):
    """加载编译后的模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    try:
        # 加载编译后的bot模块
        bot_module = load_compiled_module("bot", "./bot.so")  # Linux/Mac
        # bot_module = load_compiled_module("bot", "./bot.pyd")  # Windows
        
        # 启动bot
        if hasattr(bot_module, 'main'):
            bot_module.main()
        else:
            print("❌ 启动函数未找到")
            
    except ImportError as e:
        print(f"❌ 模块加载失败: {e}")
        print("请检查编译后的文件是否存在")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
'''
        
        launcher_path = deploy_dir / "start_bot.py"
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(launcher_content)

    def create_config_encryptor(self):
        """创建配置文件加密工具"""
        encryptor_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件加密工具
"""

import json
import base64
from cryptography.fernet import Fernet
import os

class ConfigEncryptor:
    def __init__(self):
        self.key_file = "config.key"
        
    def generate_key(self):
        """生成加密密钥"""
        key = Fernet.generate_key()
        with open(self.key_file, 'wb') as f:
            f.write(key)
        return key
    
    def load_key(self):
        """加载密钥"""
        if not os.path.exists(self.key_file):
            return self.generate_key()
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def encrypt_config(self, config_dict):
        """加密配置"""
        key = self.load_key()
        f = Fernet(key)
        
        # 敏感配置项
        sensitive_keys = [
            'DEEPSEEK_API_KEY', 'MOONSHOT_API_KEY', 'DB_PASSWORD',
            'LOGIN_PASSWORD', 'COZE_CONFIG'
        ]
        
        encrypted_config = config_dict.copy()
        
        for key_name in sensitive_keys:
            if key_name in encrypted_config:
                value = str(encrypted_config[key_name])
                encrypted_value = f.encrypt(value.encode())
                encrypted_config[key_name] = base64.b64encode(encrypted_value).decode()
        
        return encrypted_config
    
    def decrypt_config(self, encrypted_config):
        """解密配置"""
        key = self.load_key()
        f = Fernet(key)
        
        sensitive_keys = [
            'DEEPSEEK_API_KEY', 'MOONSHOT_API_KEY', 'DB_PASSWORD', 
            'LOGIN_PASSWORD', 'COZE_CONFIG'
        ]
        
        decrypted_config = encrypted_config.copy()
        
        for key_name in sensitive_keys:
            if key_name in decrypted_config:
                encrypted_value = base64.b64decode(decrypted_config[key_name])
                decrypted_value = f.decrypt(encrypted_value).decode()
                decrypted_config[key_name] = decrypted_value
        
        return decrypted_config

if __name__ == "__main__":
    encryptor = ConfigEncryptor()
    
    # 示例用法
    import config
    config_dict = {key: getattr(config, key) for key in dir(config) if not key.startswith('_')}
    
    # 加密配置
    encrypted = encryptor.encrypt_config(config_dict)
    with open("config_encrypted.json", "w") as f:
        json.dump(encrypted, f, indent=2, ensure_ascii=False)
    
    print("✅ 配置文件已加密保存到 config_encrypted.json")
'''
        
        encryptor_path = self.project_dir / "config_encryptor.py"
        with open(encryptor_path, 'w', encoding='utf-8') as f:
            f.write(encryptor_content)

def main():
    parser = argparse.ArgumentParser(
        description='WeChatBot源码保护部署工具',
        epilog='''
使用示例:
  python compile_and_deploy.py                    # 使用默认PyInstaller方案
  python compile_and_deploy.py --no-obfuscation   # 禁用代码混淆
  python compile_and_deploy.py --clean            # 清理构建目录
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--no-obfuscation', action='store_true', help='禁用代码混淆')
    parser.add_argument('--clean', action='store_true', help='清理构建目录')
    
    args = parser.parse_args()
    
    protector = SourceProtector()
    
    if args.clean:
        protector.clean_build_dirs()
        print("✅ 构建目录已清理")
        return
    
    print("🚀 开始源码保护部署...")
    print(f"📍 项目目录: {protector.project_dir}")
    print(f"🛡️  保护方案: PyInstaller")
    print(f"🔒 代码混淆: {'禁用' if args.no_obfuscation else '启用'}")
    print("-" * 50)
    
    success_methods = []
    failed_methods = []
    
    try:
        try:
            print("\n📦 执行 PyInstaller 方案...")
            protector.method_pyinstaller(use_obfuscation=not args.no_obfuscation)
            success_methods.append("PyInstaller")
        except Exception as e:
            print(f"❌ PyInstaller 方案失败: {e}")
            failed_methods.append(("PyInstaller", str(e)))
        
        # 创建配置加密工具
        try:
            print("\n🔐 创建配置加密工具...")
            protector.create_config_encryptor()
            print("✅ 配置加密工具创建完成")
        except Exception as e:
            print(f"⚠️  配置加密工具创建失败: {e}")
        
        # 显示结果摘要
        print("\n" + "=" * 60)
        print("🎉 部署结果摘要")
        print("=" * 60)
        
        if success_methods:
            print("✅ 成功的方案:")
            for method in success_methods:
                print(f"   • {method}")
        
        if failed_methods:
            print("\n❌ 失败的方案:")
            for method, error in failed_methods:
                print(f"   • {method}: {error}")
        
        print(f"\n📁 输出目录: {protector.dist_dir}")
        if protector.dist_dir.exists():
            print("📋 生成的文件:")
            for item in protector.dist_dir.iterdir():
                if item.is_dir():
                    print(f"   📁 {item.name}/")
                else:
                    print(f"   📄 {item.name}")
        
        print(f"\n🔐 配置加密工具: config_encryptor.py")
        
        if failed_methods and not success_methods:
            print("\n💡 解决建议:")
            print("   • 检查Python环境和依赖项")
            print("   • 尝试使用 --no-obfuscation 参数")
            print("   • 单独测试每个方案以定位问题")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        print("💡 建议检查环境配置或联系技术支持")
        sys.exit(1)

if __name__ == "__main__":
    main() 