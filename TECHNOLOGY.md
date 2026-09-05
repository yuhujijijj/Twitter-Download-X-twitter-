# Twitter Download 技术文档

## 项目概述

本项目是一个 Twitter 媒体内容下载工具，支持下载用户发布的图片、视频等媒体文件，并提供同步管理功能。

## 技术栈

### 编程语言
- **Python 3.x** - 主要开发语言

### 核心库

#### 网络请求
- **httpx** - 异步HTTP客户端，用于发送API请求和下载媒体文件
  - 支持同步和异步请求
  - 内置重试机制
  - 支持代理配置

#### GUI框架
- **Tkinter** - Python标准GUI库，用于构建图形用户界面
  - 轻量级，无需额外安装
  - 跨平台支持
  - 丰富的控件库（ttk）

#### 数据处理
- **json** - 处理配置文件和API响应数据
- **csv** - 生成用户推文数据表格
- **pickle** - 缓存用户信息数据
- **re** - 正则表达式，用于文本处理和文件名解析

#### 文件操作
- **os** - 目录遍历、文件路径处理
- **time** - 时间戳转换和计时

### 架构设计

#### 模块划分

| 模块 | 功能 | 依赖 |
|------|------|------|
| `main.py` | 主下载逻辑，处理Twitter API请求和媒体下载 | httpx, asyncio |
| `sync_manager.py` | 同步管理，扫描已有用户并支持更新下载 | os, pickle |
| `common.py` | 共享工具函数，配置管理，HTTP请求封装 | json |
| `text_down.py` | 推文文本内容下载 | - |
| `reply_down.py` | 回复内容下载 | httpx |
| `tag_down.py` | 标签推文下载 | httpx |
| `profile_down.py` | 用户资料下载 | httpx |
| `gui.py` | 图形用户界面 | tkinter |
| `user_info.py` | 用户信息数据结构 | - |
| `csv_gen.py` | CSV文件生成 | csv |
| `md_gen.py` | Markdown文件生成 | - |
| `cache_gen.py` | 缓存管理 | pickle |
| `url_utils.py` | URL工具函数 | - |

#### 核心流程

1. **下载流程**
   - 读取配置文件（settings.json）
   - 获取用户信息（通过Twitter API）
   - 遍历用户推文（分页获取）
   - 解析媒体URL
   - 异步下载媒体文件
   - 生成CSV/MD日志文件

2. **同步管理流程**
   - 扫描指定目录下的用户文件夹
   - 读取用户缓存信息
   - 解析文件夹中的文件信息
   - 显示用户列表
   - 选择用户进行更新下载

#### 设计模式

- **单例模式**：配置管理（settings）
- **工厂模式**：文件生成器（csv_gen, md_gen）
- **策略模式**：不同下载类型（默认/转推/亮点/点赞）

### API使用

#### Twitter GraphQL API

项目使用 Twitter 的 GraphQL API 进行数据获取：

- **用户信息**：`UserByScreenName` 查询
- **用户媒体推文**：`UserMedia` 查询
- **用户所有推文**：`UserTweets` 查询
- **用户亮点内容**：`UserHighlightsTweets` 查询
- **用户点赞内容**：`Likes` 查询

#### 请求头配置

```python
{
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILg...',
    'cookie': '<用户Cookie>',
    'x-csrf-token': '<CSRF Token>'
}
```

### 异步下载

使用 `asyncio` 和 `httpx.AsyncClient` 实现并发下载：

- 并发数可配置（默认8）
- 使用信号量控制并发
- 自动重试机制（最多50次）
- 支持视频和图片格式

### 缓存机制

- **用户信息缓存**：存储用户ID、昵称等信息，避免重复请求
- **下载日志缓存**：记录已下载的媒体URL，避免重复下载
- 缓存文件使用pickle序列化存储

### 配置管理

配置文件 `settings.json` 包含以下选项：

| 配置项 | 类型 | 说明 |
|--------|------|------|
| save_path | string | 保存路径 |
| user_lst | string | 用户列表，逗号分隔 |
| cookie | string | Twitter Cookie |
| has_retweet | bool | 是否下载转推 |
| high_lights | bool | 是否下载亮点内容 |
| likes | bool | 是否下载点赞内容 |
| time_range | string | 时间范围（格式：YYYY-MM-DD:YYYY-MM-DD） |
| down_log | bool | 是否记录下载日志 |
| autoSync | bool | 是否自动同步 |
| image_format | string | 图片格式（orig/jpg/png） |
| has_video | bool | 是否下载视频 |
| log_output | bool | 是否显示下载日志 |
| max_concurrent_requests | int | 最大并发请求数 |
| request_interval | float | 请求间隔（秒） |
| proxy | string | 代理地址 |
| md_output | bool | 是否生成Markdown文件 |
| media_count_limit | int | 媒体数量限制 |
| completion_sound | bool | 任务完成后是否播放提示音 |
| completion_sound_path | string | 提示音路径，默认 `sounds`，目录内使用 `default.wav` |
| language | string | 界面语言：`zh-CN` 或 `en-US` |

GUI 支持在“其他选项”中点击“试听”预览当前提示音。提示音支持 Windows WAV 文件；任务完成播放不会阻塞下载流程。

下载地址 `save_path` 必须是用户主动选择并保存的已有文件夹；GUI 不会在空路径时回退到当前目录。小窗口模式通过 Canvas 和鼠标滚轮支持完整浏览下载设置。

### 错误处理

- **API限流**：检测429状态码，自动等待后重试
- **网络异常**：自动重试机制
- **文件下载失败**：自动重试，最多50次
- **权限错误**：路径扫描时检查访问权限
- **模块缺失**：延迟导入，避免不必要的依赖错误

### 注意事项

1. **依赖安装**：运行前需安装依赖 `pip install -r requirements.txt`
2. **Cookie配置**：需要有效的Twitter Cookie才能使用
3. **网络环境**：需要能够访问Twitter的网络环境
4. **权限问题**：确保保存路径和扫描路径有读写权限