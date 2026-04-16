# 数据源抽象层使用指南

## 概述

数据源抽象层提供统一的多平台数据访问接口，支持视频、用户、评论等数据的获取。

## 快速开始

### 方式1: 使用适配器（推荐）

自动识别平台，最简单的方式：

```python
from src.backend.services.data_sources import DataSourceAdapter

# 创建适配器
adapter = DataSourceAdapter()

# 获取视频信息（自动识别平台）
result = await adapter.get_video_info("https://www.bilibili.com/video/BV1xx411c7mD")

if result['success']:
    video_info = result['data']
    print(f"标题: {video_info['title']}")
    print(f"作者: {video_info['author']}")
else:
    print(f"错误: {result['error']}")
```

### 方式2: 使用工厂创建数据源

需要更多控制时使用：

```python
from src.backend.services.data_sources import DataSourceFactory

# 从URL自动创建数据源
source = DataSourceFactory.create_from_url("https://www.bilibili.com/video/BV1xx411c7mD")

# 提取视频ID
video_id = await source.extract_video_id(url)

# 获取视频信息
result = await source.get_video_info(video_id)
```

### 方式3: 便捷函数

最简单的方式：

```python
from src.backend.services.data_sources import get_video_info_universal

result = await get_video_info_universal("https://www.bilibili.com/video/BV1xx411c7mD")
```

## 详细用法

### 视频相关操作

```python
from src.backend.services.data_sources import DataSourceAdapter

adapter = DataSourceAdapter()

# 获取视频信息
result = await adapter.get_video_info("https://www.bilibili.com/video/BV1xx411c7mD")

# 获取字幕
result = await adapter.get_video_subtitles("https://www.bilibili.com/video/BV1xx411c7mD")

# 获取评论
result = await adapter.get_video_comments(
    "https://www.bilibili.com/video/BV1xx411c7mD",
    max_count=100,
    sort_by="hot"  # 或 "time"
)

# 获取弹幕
result = await adapter.get_video_danmaku(
    "https://www.bilibili.com/video/BV1xx411c7mD",
    max_count=1000
)
```

### 用户相关操作

```python
# 获取用户信息
result = await adapter.get_user_info("https://space.bilibili.com/123456")

# 获取用户投稿
result = await adapter.get_user_videos(
    "https://space.bilibili.com/123456",
    limit=10
)
```

### 搜索操作

```python
# 搜索视频（指定平台）
result = await adapter.search_videos(
    "Python教程",
    platform="bilibili",
    limit=10
)

# 搜索用户
result = await adapter.search_users(
    "罗翔",
    platform="bilibili",
    limit=5
)
```

### 热门内容

```python
# 获取热门视频
result = await adapter.get_popular_videos(
    platform="bilibili",
    limit=10
)
```

## B站特有功能

```python
# 创建B站数据源
from src.backend.services.data_sources import BilibiliSource

source = BilibiliSource()

# 获取专栏文章
result = await source.get_article_content(cvid=12345)

# 获取Opus动态
result = await source.get_opus_content(opus_id=12345)

# 验证登录凭据
result = await source.validate_credentials()
```

## 扩展新平台

### 步骤1: 创建数据源类

```python
from src.backend.services.data_sources.base import DataSource
from typing import Dict, List, Optional, Any

class DouyinSource(DataSource):
    """抖音数据源"""

    @property
    def platform_name(self) -> str:
        return "douyin"

    @property
    def supported_domains(self) -> List[str]:
        return ["douyin.com", "www.douyin.com"]

    def __init__(self, api_key: str = None):
        self._api_key = api_key

    # 实现所有抽象方法...
    async def extract_video_id(self, url: str) -> Optional[str]:
        # 提取视频ID逻辑
        pass

    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        # 获取视频信息逻辑
        pass

    # 实现其他必需方法...
```

### 步骤2: 注册数据源

```python
from src.backend.services.data_sources import DataSourceFactory

# 注册抖音数据源
DataSourceFactory.register_source('douyin.com', DouyinSource)

# 现在可以自动识别抖音URL
source = DataSourceFactory.create_from_url("https://www.douyin.com/video/12345")
```

### 步骤3: 使用新平台

```python
from src.backend.services.data_sources import DataSourceAdapter

adapter = DataSourceAdapter()

# 自动识别抖音URL
result = await adapter.get_video_info("https://www.douyin.com/video/12345")
```

## 错误处理

```python
from src.backend.services.data_sources import (
    DataSourceAdapter,
    UnsupportedPlatformError,
    VideoNotFoundError,
)

adapter = DataSourceAdapter()

try:
    result = await adapter.get_video_info(url)
    if result['success']:
        print(f"视频标题: {result['data']['title']}")
    else:
        print(f"获取失败: {result['error']}")

except UnsupportedPlatformError as e:
    print(f"不支持的平台: {e}")

except VideoNotFoundError as e:
    print(f"视频不存在: {e}")
```

## 响应格式

所有数据源返回统一的响应格式：

```python
{
    'success': bool,      # 是否成功
    'data': Any,          # 响应数据（成功时）
    'error': str,         # 错误信息（失败时）
    'platform': str       # 平台标识
}
```

## 平台检测

```python
from src.backend.services.data_sources import DataSourceFactory

# 检查URL是否支持
if DataSourceFactory.is_supported_url(url):
    print("支持此URL")

# 获取平台名称
platform = DataSourceFactory.get_platform_from_url(url)
print(f"平台: {platform}")

# 获取所有支持的平台
platforms = DataSourceFactory.get_supported_platforms()
print(f"支持的平台: {platforms}")
```

## 性能优化

### 使用缓存

工厂默认会缓存数据源实例：

```python
# 使用缓存（默认）
source = DataSourceFactory.create_from_url(url, use_cache=True)

# 不使用缓存
source = DataSourceFactory.create_from_url(url, use_cache=False)
```

### 清空缓存

```python
# 清空工厂缓存
DataSourceFactory.clear_cache()

# 清空适配器缓存
adapter = DataSourceAdapter()
adapter.clear_cache()
```

## 设计原则

1. **开闭原则**: 对扩展开放，对修改关闭
2. **依赖倒置**: 依赖抽象而非具体实现
3. **单一职责**: 每个数据源只负责一个平台
4. **里氏替换**: 所有数据源可互相替换

## 架构图

```
┌─────────────────────────────────────────────────┐
│              DataSourceAdapter                   │
│           (统一接口适配器层)                      │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│           DataSourceFactory                      │
│          (数据源工厂/注册表)                     │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
      ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Bilibili  │ │ YouTube  │ │ Douyin   │
│ Source   │ │ Source   │ │ Source   │
│(已实现)   │ │(预留)     │ │(未来)    │
└──────────┘ └──────────┘ └──────────┘
      │           │           │
      └───────────┴───────────┘
                  │
                  ▼
         ┌────────────────┐
         │  DataSource    │
         │ (抽象基类)      │
         └────────────────┘
```

## 测试

运行测试套件：

```bash
python src/backend/services/data_sources/test_data_sources.py
```

## 常见问题

### Q: 如何处理不支持的平台？

A: 工厂会抛出 `UnsupportedPlatformError`：

```python
try:
    source = DataSourceFactory.create_from_url(url)
except UnsupportedPlatformError:
    print("此平台暂不支持")
```

### Q: YouTube数据源什么时候实现？

A: YouTube数据源已预留接口，等待实现。需要 YouTube Data API v3 凭据。

### Q: 能否同时使用多个平台？

A: 可以！适配器会自动识别每个URL的平台：

```python
adapter = DataSourceAdapter()

bilibili_result = await adapter.get_video_info("https://www.bilibili.com/...")
youtube_result = await adapter.get_video_info("https://www.youtube.com/...")
```

## 更多示例

查看测试文件获取更多使用示例：

```bash
src/backend/services/data_sources/test_data_sources.py
```
