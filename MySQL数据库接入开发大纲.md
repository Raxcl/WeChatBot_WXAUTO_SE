# MySQL数据库接入功能开发大纲

## 1. 项目概述

### 1.1 目标
为微信机器人添加MySQL数据库支持，实现永久聊天记录的数据库存储，提升群聊总结功能的查询性能。

### 1.2 核心要求
- 添加数据库总开关，可选择启用/禁用数据库功能
- 保持向后兼容，不影响现有文件存储逻辑
- 临时聊天记录仍使用文件存储（Memory_Temp），永久记录可选择数据库存储
- 群聊总结功能支持从数据库查询历史记录

### 1.3 数据库信息
- **主机**: 43.139.211.77
- **端口**: 3306  
- **用户**: root
- **密码**: cd20c9da2a4a0843
- **数据库名**: wechat_bot

## 2. 数据库设计

### 2.1 表结构设计

#### 2.1.1 用户聊天记录表 (user_chat_messages)
```sql
CREATE TABLE `user_chat_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` varchar(100) NOT NULL COMMENT '用户ID',
  `speaker` varchar(100) NOT NULL COMMENT '发言者',
  `message_content` text NOT NULL COMMENT '消息内容',
  `message_time` datetime NOT NULL COMMENT '消息时间',
  `prompt_name` varchar(100) DEFAULT NULL COMMENT '角色名称',
  `message_type` enum('user','ai','system') DEFAULT 'user' COMMENT '消息类型',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `message_time`),
  KEY `idx_message_time` (`message_time`),
  KEY `idx_user_speaker_time` (`user_id`, `speaker`, `message_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户聊天消息记录表';
```

#### 2.1.2 群聊记录表 (group_chat_messages)
```sql
CREATE TABLE `group_chat_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `group_id` varchar(100) NOT NULL COMMENT '群聊ID',
  `speaker` varchar(100) NOT NULL COMMENT '发言者',
  `message_content` text NOT NULL COMMENT '消息内容',
  `message_time` datetime NOT NULL COMMENT '消息时间',
  `prompt_name` varchar(100) DEFAULT NULL COMMENT '角色名称',
  `message_type` enum('user','ai','system') DEFAULT 'user' COMMENT '消息类型',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_group_time` (`group_id`, `message_time`),
  KEY `idx_message_time` (`message_time`),
  KEY `idx_group_speaker_time` (`group_id`, `speaker`, `message_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='群聊消息记录表';
```

#### 2.1.3 群聊总结记录表 (group_summaries)
```sql
CREATE TABLE `group_summaries` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `group_name` varchar(100) NOT NULL COMMENT '群聊名称',
  `summary_content` text NOT NULL COMMENT '总结内容',
  `summary_date` date NOT NULL COMMENT '总结日期',
  `time_range` varchar(20) NOT NULL COMMENT '时间范围',
  `message_count` int DEFAULT 0 COMMENT '消息数量',
  `prompt_file` varchar(100) DEFAULT NULL COMMENT '使用的提示词文件',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_group_date_range` (`group_name`, `summary_date`, `time_range`),
  KEY `idx_summary_date` (`summary_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='群聊总结记录表';
```

### 2.2 索引设计说明
- **主要查询场景**: 按用户/群聊+时间范围查询消息
- **复合索引**: (user_id/group_id, message_time) 优化时间范围查询
- **单列索引**: message_time 支持全局时间查询

## 3. 配置文件修改

### 3.1 config.py 新增配置项
```python
# === MySQL数据库配置 ===
# 数据库总开关
ENABLE_DATABASE = False

# 数据库连接信息
DB_HOST = '43.139.211.77'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = 'cd20c9da2a4a0843'
DB_NAME = 'wechat_bot'
DB_CHARSET = 'utf8mb4'

# 数据库连接池配置
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
DB_POOL_RECYCLE = 3600  # 连接回收时间（秒）
```

## 4. 技术实现方案

### 4.1 依赖库
- **SQLAlchemy**: ORM框架
- **PyMySQL**: MySQL驱动
- **sqlalchemy.pool**: 连接池管理

### 4.2 核心模块设计

#### 4.2.1 数据库管理器 (database.py)
```python
class DatabaseManager:
    """数据库连接管理器"""
    def __init__(self):
        self.engine = None
        self.Session = None
        self.is_initialized = False
    
    def initialize(self):
        """初始化数据库连接"""
        
    def get_session(self):
        """获取数据库会话"""
        
    def test_connection(self):
        """测试数据库连接"""
        
    def close(self):
        """关闭数据库连接"""
```

#### 4.2.2 数据模型 (models.py)
```python
class UserChatMessage(Base):
    """用户聊天消息模型"""
    
class GroupChatMessage(Base):
    """群聊消息模型"""
    
class GroupSummary(Base):
    """群聊总结模型"""
```

### 4.3 逻辑修改点

#### 4.3.1 永久聊天记录存储
- **函数**: `log_to_permanent_archive()`
- **位置**: bot.py:2988-3021
- **修改内容**: 
  - 添加数据库存储分支
  - 根据是否为群聊选择不同的表
  - 保持文件存储作为备用方案

#### 4.3.2 群聊总结数据获取
- **函数**: `get_chat_messages_for_summary()`
- **位置**: bot.py:2092-2225
- **修改内容**:
  - 添加数据库查询分支
  - 优化SQL查询性能
  - 保持文件查询作为后备

#### 4.3.3 群聊总结存储
- **函数**: `process_group_summary()`
- **位置**: bot.py:2226-2350
- **修改内容**:
  - 将总结结果存储到数据库
  - 避免重复总结

## 5. 实施步骤

### 5.1 阶段一：基础设施搭建
1. **创建数据库模块文件**
   - `database.py`: 数据库连接管理
   - `models.py`: 数据模型定义

2. **更新配置文件**
   - 在 `config.py` 中添加数据库配置项

3. **更新依赖**
   - 在 `requirements.txt` 中添加数据库相关依赖

### 5.2 阶段二：核心功能实现
1. **修改聊天记录存储函数**
   - 修改 `log_to_permanent_archive()` 函数
   - 添加数据库存储逻辑
   - 实现用户/群聊表的自动选择

2. **修改群聊总结功能**
   - 修改 `get_chat_messages_for_summary()` 函数
   - 实现数据库查询逻辑
   - 修改 `process_group_summary()` 存储总结结果

### 5.3 阶段三：测试和优化
1. **功能测试**
   - 测试数据库开关功能
   - 测试聊天记录存储
   - 测试群聊总结功能

2. **性能优化**
   - 数据库查询优化
   - 连接池配置调优
   - 错误处理完善

## 6. 关键设计决策

### 6.1 表分离策略
- **用户表** (`user_chat_messages`): 存储私聊消息，数据量相对较小
- **群聊表** (`group_chat_messages`): 存储群聊消息，数据量较大，独立管理
- **好处**: 避免单表过大，提升查询和维护性能

### 6.2 兼容性保证
- 数据库功能为可选，默认关闭
- 文件存储逻辑完全保留，作为后备方案
- 新旧系统可以平滑切换

### 6.3 错误处理策略
- 数据库连接失败时自动降级到文件存储
- 记录详细的错误日志
- 提供连接状态检查功能

## 7. 预期效果

### 7.1 性能提升
- 群聊总结查询速度提升 10-50 倍（取决于历史数据量）
- 支持更复杂的数据分析和统计

### 7.2 扩展性增强
- 为未来功能提供数据基础（如用户行为分析、热词统计等）
- 支持数据备份和恢复
- 便于数据清理和维护

### 7.3 稳定性保障
- 连接池管理确保数据库连接稳定
- 事务支持保证数据一致性
- 错误自动降级保证服务可用性

---

**开发优先级**: 高
**预估工期**: 2-3天
**风险评估**: 低（向后兼容设计） 