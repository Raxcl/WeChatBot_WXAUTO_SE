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
        
        if use_obfuscation:
            print("🔒 启用代码混淆...")
            self._obfuscate_code()
            main_file = self.dist_dir / "obfuscated" / "bot.py"
        else:
            main_file = "bot.py"

        # PyInstaller命令
        cmd = [
            "pyinstaller",
            "--onefile",
            "--noconsole", 
            "--name=WeChatBot",
            "--hidden-import=wxautox_wechatbot",
            "--hidden-import=comtypes",
            "--hidden-import=pywin32",
            "--add-data=templates;templates",
            "--add-data=prompts;prompts", 
            "--add-data=emojis;emojis",
            "--distpath=./dist/pyinstaller",
            str(main_file)
        ]
        
        subprocess.run(cmd, check=True)
        print("✅ PyInstaller打包完成")

    def method_cython(self):
        """方案2: Cython编译"""
        print("⚡ 开始Cython编译...")
        
        # 安装依赖
        subprocess.run([sys.executable, "-m", "pip", "install", "cython", "numpy"], check=True)
        
        # 编译
        subprocess.run([sys.executable, "setup_cython.py", "build_ext", "--inplace"], check=True)
        
        # 创建部署目录
        deploy_dir = self.dist_dir / "cython_deploy"
        deploy_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制编译后的文件
        for pattern in ["*.so", "*.pyd"]:
            for file in self.project_dir.glob(pattern):
                shutil.copy2(file, deploy_dir)
        
        # 复制其他必需文件
        for item in self.preserve_items:
            src = self.project_dir / item
            dst = deploy_dir / item
            if src.is_file():
                shutil.copy2(src, dst)
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # 创建启动脚本
        self._create_launcher_script(deploy_dir)
        print("✅ Cython编译完成")

    def method_docker(self):
        """方案3: Docker容器化部署"""
        print("🐳 创建Docker部署...")
        
        dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "bot.py"]
'''
        
        dockerfile_path = self.project_dir / "Dockerfile"
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        
        # Docker构建脚本
        docker_script = '''#!/bin/bash
# Docker部署脚本

echo "🐳 构建Docker镜像..."
docker build -t wechatbot:latest .

echo "📦 保存镜像到文件..."
docker save -o wechatbot.tar wechatbot:latest

echo "✅ Docker镜像构建完成: wechatbot.tar"
echo "📋 客户部署说明:"
echo "1. 加载镜像: docker load -i wechatbot.tar"  
echo "2. 运行容器: docker run -d --name wechatbot -p 5000:5000 wechatbot:latest"
'''
        
        script_path = self.project_dir / "docker_build.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(docker_script)
        os.chmod(script_path, 0o755)
        
        print("✅ Docker配置完成")

    def _obfuscate_code(self):
        """代码混淆"""
        print("🔒 混淆源代码...")
        
        # 安装PyArmor
        subprocess.run([sys.executable, "-m", "pip", "install", "pyarmor"], check=True)
        
        obf_dir = self.dist_dir / "obfuscated"
        obf_dir.mkdir(parents=True, exist_ok=True)
        
        # 混淆核心文件
        for file in self.core_files:
            if (self.project_dir / file).exists():
                cmd = ["pyarmor", "gen", "--output", str(obf_dir), file]
                subprocess.run(cmd, check=True)
        
        # 混淆目录
        for dir_name in ["ai_platforms", "database", "libs"]:
            dir_path = self.project_dir / dir_name
            if dir_path.exists():
                cmd = ["pyarmor", "gen", "--output", str(obf_dir), str(dir_path)]
                subprocess.run(cmd, check=True)

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
    parser = argparse.ArgumentParser(description='WeChatBot源码保护部署工具')
    parser.add_argument('--method', choices=['pyinstaller', 'cython', 'docker', 'all'], 
                       default='pyinstaller', help='选择保护方案')
    parser.add_argument('--no-obfuscation', action='store_true', help='禁用代码混淆')
    parser.add_argument('--clean', action='store_true', help='清理构建目录')
    
    args = parser.parse_args()
    
    protector = SourceProtector()
    
    if args.clean:
        protector.clean_build_dirs()
        print("✅ 构建目录已清理")
        return
    
    print("🚀 开始源码保护部署...")
    
    try:
        if args.method == 'pyinstaller' or args.method == 'all':
            protector.method_pyinstaller(use_obfuscation=not args.no_obfuscation)
        
        if args.method == 'cython' or args.method == 'all':
            protector.method_cython()
        
        if args.method == 'docker' or args.method == 'all':
            protector.method_docker()
        
        # 创建配置加密工具
        protector.create_config_encryptor()
        
        print("\n🎉 部署完成!")
        print("📁 输出目录: ./dist/")
        print("🔐 配置加密工具: config_encryptor.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 