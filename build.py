#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChatBot 便捷构建脚本
从项目根目录调用build_tools中的构建工具
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # 获取当前脚本所在目录（项目根目录）
    root_dir = Path(__file__).parent.resolve()
    build_tools_dir = root_dir / "build_tools"
    compile_script = build_tools_dir / "compile_and_deploy.py"
    
    # 检查build_tools目录是否存在
    if not build_tools_dir.exists():
        print("❌ build_tools目录不存在！")
        print("请确保构建工具已正确安装")
        sys.exit(1)
    
    # 检查编译脚本是否存在
    if not compile_script.exists():
        print("❌ compile_and_deploy.py不存在！")
        print(f"请检查文件是否在 {compile_script}")
        sys.exit(1)
    
    print("🚀 WeChatBot 便捷构建工具")
    print("=" * 50)
    print("1. 快速打包（不混淆）")
    print("2. 完整打包（含混淆）") 
    print("3. 清理构建文件")
    print("4. 配置文件加密")
    print("5. 显示帮助")
    print("0. 退出")
    print("=" * 50)
    
    try:
        choice = input("请选择操作 (0-5): ").strip()
        
        if choice == "0":
            print("👋 退出构建工具")
            return
        elif choice == "1":
            print("📦 开始快速打包...")
            subprocess.run([sys.executable, str(compile_script), "--no-obfuscation"], 
                         cwd=build_tools_dir)
        elif choice == "2":
            print("📦 开始完整打包（含混淆）...")
            subprocess.run([sys.executable, str(compile_script)], 
                         cwd=build_tools_dir)
        elif choice == "3":
            print("🧹 清理构建文件...")
            subprocess.run([sys.executable, str(compile_script), "--clean"], 
                         cwd=build_tools_dir)
        elif choice == "4":
            print("🔐 配置文件加密...")
            encryptor_script = build_tools_dir / "config_encryptor.py"
            subprocess.run([sys.executable, str(encryptor_script)], 
                         cwd=build_tools_dir)
        elif choice == "5":
            print("📖 显示详细帮助...")
            subprocess.run([sys.executable, str(compile_script), "--help"], 
                         cwd=build_tools_dir)
        else:
            print("❌ 无效选择，请输入0-5之间的数字")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")

if __name__ == "__main__":
    main() 