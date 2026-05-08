# 重构拆分与测试补全 Spec

## Why
项目核心服务层存在多个"上帝类"（AIService 648行、VideoService 755行、ai_helpers 563行），职责混杂、难以维护和测试；同时测试覆盖率极低，大部分服务模块零测试，仅有的 func_test.py 是单体端到端测试而非单元测试，无法在 CI 中快速定位问题。

## What Changes
- **拆分 AIService**：将视频分析、问答对话、专栏分析、UP主画像、总结/思维导图拆为独立服务类，AIService 保留为薄门面
- **拆分 ai_helpers.py**：将 TTLCache、并发信号量、OpenAI 流式封装、Web 搜索、报告存储拆为独立模块
- **拆分 bilibili.py 路由**：将搜索、视频、图片代理、健康检查、登录拆为独立路由文件
- **修复 ToolRegistry 全局状态**：将类属性状态改为实例属性，消除 `clear()` 导致的潜在竞态条件
- **补全单元测试**：为所有服务模块补全单元测试，使用 mock 隔离外部依赖
- **重构 func_test.py**：拆分为按模块组织的集成测试

## Impact
- Affected specs: AI 服务层、B站服务层、HTTP 路由层、工具注册体系
- Affected code:
  - `src/backend/services/ai/ai_service.py` — 拆分
  - `src/backend/services/ai/ai_helpers.py` — 拆分
  - `src/backend/http/api/routes/bilibili.py` — 拆分
  - `src/backend/services/ai/toolkit/tool_registry.py` — 重构状态管理
  - `src/backend/http/dependencies.py` — 适配新服务类
  - `tests/` — 大幅扩展

## ADDED Requirements

### Requirement: AIService 拆分为独立子服务
系统 SHALL 将 AIService 中的各功能域拆分为独立服务类，AIService 仅作为向后兼容的薄门面委托调用。

#### Scenario: 视频分析服务独立
- **WHEN** 调用 `VideoAnalysisService.generate_full_analysis_stream()`
- **THEN** 功能与原 AIService 同名方法完全一致

#### Scenario: 问答服务独立
- **WHEN** 调用 `ChatService.chat_stream()` 或 `ChatService.context_qa_stream()`
- **THEN** 功能与原 AIService 同名方法完全一致

#### Scenario: 向后兼容
- **WHEN** 通过 `AIService` 调用任何原有方法
- **THEN** 行为与拆分前完全一致，AIService 委托给对应子服务

### Requirement: ai_helpers.py 按职责拆分
系统 SHALL 将 ai_helpers.py 拆分为以下独立模块：
- `cache.py` — TTLCache 类及缓存实例
- `concurrency.py` — 信号量、并发控制
- `openai_streaming.py` — OpenAI 流式调用封装
- `web_search.py` — Exa 网络搜索
- `report_storage.py` — 研究报告保存

#### Scenario: 模块导入兼容
- **WHEN** 其他模块从 `ai_helpers` 导入原有符号（如 `openai_chat_completions_stream`、`save_research_report`）
- **THEN** 仍可正常导入，ai_helpers.py 作为 re-export 兼容层

### Requirement: bilibili.py 路由拆分
系统 SHALL 将 bilibili.py 按功能域拆分为独立路由文件：
- `search.py` — 搜索相关端点
- `video.py` — 视频数据端点
- `image_proxy.py` — 图片代理端点
- `health.py` — 健康检查端点
- `login.py` — B站登录端点

#### Scenario: 路由端点不变
- **WHEN** 前端调用任何原有 API 端点
- **THEN** URL 路径和响应格式与拆分前完全一致

### Requirement: ToolRegistry 实例化状态管理
系统 SHALL 将 ToolRegistry 的类属性状态（`_tools`、`_tool_categories`）改为实例属性，通过依赖注入传递实例，消除全局 `clear()` 调用。

#### Scenario: 多 Agent 实例隔离
- **WHEN** 创建多个 DeepResearchAgent 实例
- **THEN** 各实例的工具注册互不影响

### Requirement: 服务层单元测试覆盖
系统 SHALL 为以下模块提供单元测试，使用 mock 隔离外部依赖（OpenAI API、B站 API、网络请求）：

- `VideoAnalysisService` — 视频分析流式/同步生成
- `ChatService` — 问答对话流
- `ArticleAnalysisService` — 专栏分析
- `UserPortraitService` — UP主画像
- `BilibiliService` — B站服务门面委托
- `VideoService` — 视频信息/字幕/弹幕/评论
- `ContentService` — 专栏/Opus 内容获取
- `LoginService` — 扫码登录流程
- `SearchService` — 搜索功能
- `ToolRegistry` — 工具注册/查询/执行
- `TTLCache` — 缓存读写/过期
- `concurrency` — 信号量控制
- `openai_streaming` — 流式调用重试
- `web_search` — Exa 搜索
- `data_sources` — 数据源适配器/工厂

#### Scenario: 测试可独立运行
- **WHEN** 执行 `pytest tests/`
- **THEN** 所有测试通过，无需真实 API Key 或网络连接

#### Scenario: Mock 隔离
- **WHEN** 测试 AIService 子服务
- **THEN** OpenAI client 被 mock，不发送真实请求

### Requirement: func_test.py 拆分为模块化集成测试
系统 SHALL 将 func_test.py 拆分为按功能域组织的测试文件，保留端到端测试能力但结构更清晰。

#### Scenario: 集成测试分类
- **WHEN** 查看 tests/ 目录
- **THEN** 集成测试按功能域分文件（如 test_integration_analyze.py、test_integration_search.py）

## MODIFIED Requirements

### Requirement: dependencies.py 依赖注入
原有依赖注入 SHALL 适配新的子服务类，AIService 仍作为单例注入，内部自动创建子服务实例。

### Requirement: DeepResearchAgent 工具初始化
DeepResearchAgent SHALL 接受 ToolRegistry 实例作为构造参数，而非调用 `ToolRegistry.clear()` 全局重置。

## REMOVED Requirements
无移除项。
