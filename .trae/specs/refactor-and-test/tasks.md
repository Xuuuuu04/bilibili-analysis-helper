# Tasks

- [x] Task 1: 拆分 ai_helpers.py 为独立模块
  - [x] SubTask 1.1: 创建 `src/backend/services/ai/cache.py`，迁移 TTLCache 类及缓存实例（EXA_CACHE, BILIBILI_CACHE）
  - [x] SubTask 1.2: 创建 `src/backend/services/ai/concurrency.py`，迁移信号量常量和 _semaphore/_sleep_backoff 辅助函数
  - [x] SubTask 1.3: 创建 `src/backend/services/ai/openai_streaming.py`，迁移 openai_chat_completions_stream 函数
  - [x] SubTask 1.4: 创建 `src/backend/services/ai/web_search.py`，迁移 web_search_exa 函数
  - [x] SubTask 1.5: 创建 `src/backend/services/ai/report_storage.py`，迁移 save_research_report 函数
  - [x] SubTask 1.6: 将 ai_helpers.py 改为 re-export 兼容层，确保所有原有导入路径仍可用
  - [x] SubTask 1.7: 更新所有引用 ai_helpers 的模块，改为直接导入新模块

- [x] Task 2: 拆分 AIService 为独立子服务
  - [x] SubTask 2.1: 创建 `src/backend/services/ai/video_analysis_service.py`，迁移 generate_full_analysis / generate_full_analysis_stream
  - [x] SubTask 2.2: 创建 `src/backend/services/ai/chat_service.py`，迁移 chat_stream / context_qa_stream
  - [x] SubTask 2.3: 创建 `src/backend/services/ai/article_analysis_service.py`，迁移 generate_article_analysis_stream
  - [x] SubTask 2.4: 创建 `src/backend/services/ai/user_portrait_service.py`，迁移 generate_user_analysis / generate_summary / generate_mindmap
  - [x] SubTask 2.5: 将 AIService 改为薄门面，委托给子服务，保持所有原有方法签名不变
  - [x] SubTask 2.6: 更新 dependencies.py 适配新子服务

- [x] Task 3: 修复 ToolRegistry 全局状态问题
  - [x] SubTask 3.1: 将 ToolRegistry 的 _tools / _tool_categories 从类属性改为实例属性
  - [x] SubTask 3.2: 移除 ToolRegistry.clear() 类方法，改为实例方法
  - [x] SubTask 3.3: 修改 DeepResearchAgent 接受 ToolRegistry 实例参数，不再调用全局 clear
  - [x] SubTask 3.4: 更新 dependencies.py 创建 ToolRegistry 实例并注入

- [x] Task 4: 拆分 bilibili.py 路由
  - [x] SubTask 4.1: 创建 `src/backend/http/api/routes/search.py`，迁移搜索端点
  - [x] SubTask 4.2: 创建 `src/backend/http/api/routes/video.py`，迁移视频数据端点
  - [x] SubTask 4.3: 创建 `src/backend/http/api/routes/image_proxy.py`，迁移图片代理端点
  - [x] SubTask 4.4: 创建 `src/backend/http/api/routes/health.py`，迁移健康检查端点
  - [x] SubTask 4.5: 创建 `src/backend/http/api/routes/login.py`，迁移B站登录端点
  - [x] SubTask 4.6: 删除原 bilibili.py，更新 router.py 注册新路由文件

- [x] Task 5: 补全 conftest.py 公共 fixture
  - [x] SubTask 5.1: 添加 mock_openai_client fixture（模拟 OpenAI 客户端）
  - [x] SubTask 5.2: 添加 mock_bilibili_service fixture（模拟 B站服务）
  - [x] SubTask 5.3: 添加 mock_credential fixture（模拟B站凭据）
  - [x] SubTask 5.4: 添加 app_client fixture（FastAPI TestClient）

- [x] Task 6: 补全 AI 服务层单元测试
  - [x] SubTask 6.1: 创建 `tests/test_video_analysis_service.py`
  - [x] SubTask 6.2: 创建 `tests/test_chat_service.py`
  - [x] SubTask 6.3: 创建 `tests/test_article_analysis_service.py`
  - [x] SubTask 6.4: 创建 `tests/test_user_portrait_service.py`
  - [x] SubTask 6.5: 创建 `tests/test_cache.py`（TTLCache 读写/过期/并发）
  - [x] SubTask 6.6: 创建 `tests/test_concurrency.py`（信号量控制）
  - [x] SubTask 6.7: 创建 `tests/test_openai_streaming.py`（流式调用重试逻辑）
  - [x] SubTask 6.8: 创建 `tests/test_web_search.py`（Exa 搜索 mock）

- [x] Task 7: 补全 B站服务层单元测试
  - [x] SubTask 7.1: 创建 `tests/test_bilibili_service.py`（门面委托测试）
  - [x] SubTask 7.2: 创建 `tests/test_content_service.py`
  - [x] SubTask 7.3: 创建 `tests/test_login_service.py`
  - [x] SubTask 7.4: 创建 `tests/test_search_service.py`

- [x] Task 8: 补全工具注册与数据源测试
  - [x] SubTask 8.1: 创建 `tests/test_tool_registry.py`（注册/查询/执行/实例隔离）
  - [x] SubTask 8.2: 创建 `tests/test_data_source_adapter.py`

- [x] Task 9: 拆分 func_test.py 为模块化集成测试
  - [x] SubTask 9.1: 创建 `tests/test_integration_analyze.py`
  - [x] SubTask 9.2: 创建 `tests/test_integration_search.py`
  - [x] SubTask 9.3: 创建 `tests/test_integration_settings.py`
  - [x] SubTask 9.4: 删除原 func_test.py

- [x] Task 10: 全量测试验证
  - [x] SubTask 10.1: 运行 `pytest tests/ -v` 确保所有测试通过
  - [x] SubTask 10.2: 运行 `ruff check src/` 确保无 lint 错误
  - [x] SubTask 10.3: 启动应用验证 API 端点正常响应

# Task Dependencies
- [Task 2] depends on [Task 1] (AIService 子服务需要导入拆分后的 ai_helpers 模块)
- [Task 3] depends on [Task 2] (DeepResearchAgent 修改依赖 AIService 拆分)
- [Task 6] depends on [Task 1, Task 2] (AI 测试依赖拆分后的模块结构)
- [Task 7] depends on [Task 4] (B站路由拆分后测试结构更清晰)
- [Task 8] depends on [Task 3] (ToolRegistry 测试依赖实例化改造)
- [Task 9] depends on [Task 4, Task 6, Task 7] (集成测试依赖路由和服务拆分)
- [Task 10] depends on [Task 6, Task 7, Task 8, Task 9] (全量验证依赖所有测试就绪)
- [Task 1, Task 4, Task 5] 可并行执行
