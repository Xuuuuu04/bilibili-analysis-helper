# 架构说明

## 目标

- 后端基于 FastAPI，保持接口兼容（尤其是 SSE 输出格式）
- 分层清晰：HTTP 协议层（routes）与业务编排层（services/usecase）解耦
- 易扩展：后续可替换数据源、模型供应商、缓存/鉴权实现而不影响前端

## 后端结构（FastAPI）

- `src/backend/http/app.py`：应用工厂、CORS、全局异常处理、静态资源挂载
- `src/backend/http/api/routes/*`：薄路由，仅做参数检查与响应封装
- `src/backend/http/usecases/*`：业务流程编排（分析/研究/设置等）
- `src/backend/http/dependencies.py`：依赖注入与单例生命周期管理

## SSE 约定

项目的流式接口统一使用：

- `Content-Type: text/event-stream`
- 每条消息的 wire format：`data: {json}\n\n`
- 不使用 `event:` 字段，前端通过 JSON 内的 `type` 字段分发

相关路由：

- `/api/analyze/stream`
- `/api/chat/stream`
- `/api/research`

## 核心模块与入口

- `src/backend`：领域服务层（B 站能力、AI 能力、数据源抽象、通用工具）
- `asgi.py`：推荐启动入口（初始化日志 + 创建 FastAPI app）
