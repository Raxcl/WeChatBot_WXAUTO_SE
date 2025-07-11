#!/usr/bin/env python3
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
    import sys
    import os
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    import config
    config_dict = {key: getattr(config, key) for key in dir(config) if not key.startswith('_')}
    
    # 加密配置
    encrypted = encryptor.encrypt_config(config_dict)
    # 保存到项目根目录
    output_path = os.path.join(os.path.dirname(__file__), '..', 'config_encrypted.json')
    with open(output_path, "w") as f:
        json.dump(encrypted, f, indent=2, ensure_ascii=False)
    
    print("✅ 配置文件已加密保存到 config_encrypted.json")
