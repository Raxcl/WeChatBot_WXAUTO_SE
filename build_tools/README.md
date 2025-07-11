# WeChatBot 构建工具集

这个目录包含了WeChatBot项目的所有构建、编译、部署和加密相关的工具。

## 文件说明

### 核心工具

1. **`compile_and_deploy.py`** - 主要的编译部署脚本
   - 支持PyInstaller打包
   - 支持PyArmor代码混淆
   - 自动创建统一发布包
   
2. **`config_encryptor.py`** - 配置文件加密工具
   - 加密敏感配置项（API密钥等）
   - 生成加密密钥文件
   
3. **`WeChatBot.spec`** - PyInstaller配置文件
   - 定义打包参数和依赖
   - 自动生成的配置模板

## 使用方法

### 1. 快速打包（不混淆）
```bash
cd build_tools
python compile_and_deploy.py --no-obfuscation
```

### 2. 完整打包（含混淆）
```bash
cd build_tools
python compile_and_deploy.py
```

### 3. 清理构建文件
```bash
cd build_tools
python compile_and_deploy.py --clean
```

### 4. 加密配置文件
```bash
cd build_tools
python config_encryptor.py
```

## 输出结构

执行打包后，会在项目根目录的 `dist/release/` 下生成统一的发布包：

```
dist/
└── release/
    ├── executable/          # 可执行文件
    │   └── WeChatBot.exe
    ├── source_code/         # 源码（混淆后的或原始的）
    ├── resources/           # 资源文件
    ├── documentation/       # 文档
    ├── obfuscated/         # 混淆源码备份（如果启用混淆）
    ├── config.py           # 配置文件
    ├── config_encryptor.py # 配置加密工具
    └── README_RELEASE.txt  # 使用说明
```

## 注意事项

1. **路径**: 所有工具都假设项目根目录在上一级目录
2. **依赖**: 需要安装PyInstaller和PyArmor（工具会自动安装）
3. **权限**: 在Windows上可能需要管理员权限

## 工具依赖

- Python 3.9-3.12
- PyInstaller（自动安装）
- PyArmor（如需混淆，自动安装）
- cryptography（配置加密需要）

## 技术支持

如有问题请参考项目主文档或联系技术支持。 