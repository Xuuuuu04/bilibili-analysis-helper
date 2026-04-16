# BILIBILI SUMMARIZE

## 1. 总体架构与目录结构（5–6 分钟）
我把系统分成四层，目的是让职责清晰、可维护、可扩展。

四层结构如下。
- 入口层：`asgi.py`
- HTTP 接口层：`src/backend/http/`
- 用例编排层：`src/backend/http/usecases/`
- 服务能力层：`src/backend/services/`

此外还有配置中心 `src/config.py` 和前端 `src/frontend/`。

### 1.1 入口层：`asgi.py`
入口只做两件事：初始化日志 + 创建 FastAPI 应用。

`asgi.py` 中的关键片段：
```python
from src.backend.utils.logger import setup_logging
from src.backend.http.app import create_app

setup_logging(...)
app = create_app()
```

我采用应用工厂模式（Application Factory），原因是：
- 延迟初始化，避免循环导入
- 测试时可以创建多个独立应用实例
- 启动逻辑集中可控

### 1.2 HTTP 层：`src/backend/http/`
HTTP 层负责请求入口、参数校验、路由组织和异常处理。

`src/backend/http/app.py` 做了这些工作：
- 创建 FastAPI 实例
- 注册异常处理器
- 配置 CORS
- 注册 API 路由
- 挂载静态资源

关键片段：
```python
app = FastAPI(title="Bilibili Analysis Helper", version="1.0.0")
app.include_router(api_router)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
```

这意味着我可以用一个服务同时承载前端页面和 API，部署更简单。

### 1.3 用例编排层：`src/backend/http/usecases/`
这一层是我架构里非常关键的一层。
它的职责不是“提供能力”，而是“把能力编排成完整业务流程”。

举例：视频分析需要字幕、弹幕、评论、关键帧、统计数据，这些是不同 service 的能力，usecase 把这些能力串起来形成一个业务流程。

代表文件：
- `src/backend/http/usecases/analyze_service.py`
- `src/backend/http/usecases/research_service.py`
- `src/backend/http/usecases/user_service.py`
- `src/backend/http/usecases/settings_service.py`

### 1.4 服务能力层：`src/backend/services/`
这是能力封装层，分为两大块。
- `services/bilibili/`：封装 B站 API 能力
- `services/ai/`：封装 AI 调用与提示词

这层只负责“能力”，不直接处理业务逻辑，因此复用性强。

### 1.5 配置中心：`src/config.py`
这里集中管理模型、API Base、Key、开关、日志级别等。
例如：
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("model")
QA_MODEL = os.getenv("QA_MODEL", "Qwen/Qwen2.5-72B-Instruct")
```
这样可以快速切换模型、快速更换 API Provider。

### 1.6 前端层：`src/frontend/`
前端是纯 HTML/CSS/JS，入口是 `index.html`，核心交互逻辑在 `script.js`。
前端做的事情包括：
- 输入链接或关键词
- SSE 流式渲染分析过程
- 展示结构化报告
- 研究报告历史管理
- 模式切换（视频/专栏/用户/研究）

`script.js` 很长，但核心点是：它把后端的 SSE 流式输出转换为用户可理解的进度与结果展示。

## 2. 核心业务流程：视频分析（6–8 分钟）
这是系统最核心的流程，也是我展示 AI 工程能力的重点。

### 2.1 路由入口
入口在 `src/backend/http/api/routes/analyze.py`：
```python
@router.post("/analyze/stream")
async def analyze_video_stream(payload, analyze_service=Depends(get_analyze_service)):
    return StreamingResponse(iterate_in_threadpool(analyze_service.stream_analyze(...)))
```

我选择 SSE（Server-Sent Events）而不是一次性返回，是为了让用户实时看到进度。

### 2.2 用例编排流程
核心逻辑在 `src/backend/http/usecases/analyze_service.py`。
我做的流程是：
1. 提取 BVID
2. 并行获取字幕、弹幕、评论、统计、标签、合集、相关推荐
3. 构建统一上下文文本
4. 抽取关键帧
5. 调用 AI 生成分析
6. SSE 流式输出

核心逻辑（简化版）：
```python
subtitle = get_video_subtitles(bvid)
danmakus = get_video_danmaku(bvid)
comments = get_video_comments(bvid)
stats = get_video_stats(bvid)
frames = extract_video_frames(bvid)

content = subtitle + danmakus + comments + stats
ai.generate_full_analysis_stream(video_info, content, frames)
```

### 2.3 多源上下文融合
我不是仅仅把字幕给模型，而是融合：
- 字幕或 AI 总结
- 弹幕（实时情绪）
- 评论（高赞观点）
- 统计信息（播放、点赞、评论数等）
- 标签与推荐

这样做的价值是：
- AI 更有“证据”，输出更可信
- 可以输出“舆情分析”而不仅是内容总结

### 2.4 多模态关键帧分析
关键帧提取在 `src/backend/services/bilibili/video_service.py`。
我会从 B站预览图切片中采样关键帧，转为 base64 给模型。

这一点让 AI 不只是“看文字”，还能“看到画面”。
对于讲解类、PPT类视频尤其重要。

## 3. AI 服务与提示词工程（6–8 分钟）
这是我项目的核心亮点之一。
我强调的是：**AI 不是简单调用，而是“可控输出 + 可解释结构”。**

### 3.1 AI 统一入口
AI 的统一入口在 `src/backend/services/ai/ai_service.py`。
它负责三类任务：
- 视频分析
- 问答对话
- 深度研究 Agent

初始化逻辑：
```python
self.client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_API_BASE)
self.model = Config.OPENAI_MODEL
self.qa_model = Config.QA_MODEL
self.research_model = Config.DEEP_RESEARCH_MODEL
```

好处是：不同任务可以用不同模型，成本与效果可控。

### 3.2 提示词工程
提示词集中管理在 `src/backend/services/ai/prompts.py`。
这里我专门设计了“反幻觉约束”，比如：
```text
【分析准则 - 严禁幻觉】
1. 仅限素材
2. 禁止推测
3. 视觉一致性
```

此外输出结构严格规定为三大板块：
- 内容深度总结
- 弹幕互动与舆情分析
- 评论区深度解析

这样输出就是结构化报告，而不是一段碎片化文本。

### 3.3 失败降级策略
在 `AIService.generate_full_analysis_stream` 中，如果模型请求超时或失败，会自动降级为“纯文本分析”而不依赖关键帧。
这个策略保证了系统稳定性。

## 4. 深度研究 Agent（4–6 分钟）
这是项目最有“研究感”的模块，也是复试里最能体现 AI 思维的亮点。

入口在 `src/backend/http/api/routes/research.py`。
核心逻辑在 `src/backend/services/ai/agents/deep_research_agent.py`。

### 4.1 Agent 工作方式
深度研究 Agent 会：
- 自动拆题
- 搜索 B站视频
- 调用工具分析视频
- 搜索全网内容
- 汇总成研究报告

### 4.2 工具化能力
我注册了多个工具进入 ToolRegistry：
```python
tools = [SearchVideosTool(), AnalyzeVideoTool(), WebSearchTool(), ...]
ToolRegistry.register(tool)
```

这意味着 AI 不只是“写报告”，而是可以执行真实检索与分析操作，具备“研究员”能力。

### 4.3 并行分析
当模型一次性提出多个视频分析任务时，我会并行执行 analyze_video。
这在 `deep_research_agent.py` 里有专门的并行逻辑，显著提升研究效率。

## 5. B站服务封装（3–4 分钟）
B站能力统一入口在 `src/backend/services/bilibili/bilibili_service.py`。
它封装了多个子服务：
- `video_service.py`：视频信息、字幕、弹幕、评论、关键帧
- `search_service.py`：搜索视频/用户/专栏
- `user_service.py`：UP 主信息与作品

### 5.1 字幕与降级策略
在 `video_service.py`，如果字幕获取失败，会降级到 AI 总结或视频简介。
这确保分析不中断。

### 5.2 弹幕与评论采样
弹幕和评论是高频数据，如果全量获取会非常慢。
我做了采样策略，保证速度和代表性兼顾。

### 5.3 登录支持
登录凭据通过 `Config` 管理。
登录后可以获取更完整的数据，体验更好。

## 6. 工程设计亮点（3–4 分钟）
我在工程上强调可维护性与扩展性。

亮点总结如下：
- 应用工厂模式：启动清晰、测试友好
- 依赖注入 + 单例：AI 和 B站服务复用连接池
- 用例编排层：路由与业务清晰分离
- SSE 流式响应：增强用户体验
- 配置中心化：模型、Key、API Base 随时切换

## 7. 结尾总结（2–3 分钟）
最后总结一下我的亮点：
- 多模态分析（字幕 + 画面）
- 多源上下文融合（弹幕 + 评论 + 统计）
- 结构化报告输出（可直接复盘）
- 深度研究 Agent（工具编排 + 自动化研究）

在这个项目里，我主要负责：
- 方向定义与功能规划
- 架构设计与模块划分
- AI 提示词工程与模型选型
- 系统优化与体验策略

一句话收尾：
“我做的是一个具备系统工程思维的 AI 应用，而不是一个简单的模型调用工具。”

---

# 代码引用速查

入口
- `asgi.py`

HTTP 层
- `src/backend/http/app.py`
- `src/backend/http/api/router.py`
- `src/backend/http/api/routes/*.py`
- `src/backend/http/api/utils.py`

用例编排层
- `src/backend/http/usecases/analyze_service.py`
- `src/backend/http/usecases/research_service.py`
- `src/backend/http/usecases/user_service.py`
- `src/backend/http/usecases/settings_service.py`

AI 层
- `src/backend/services/ai/ai_service.py`
- `src/backend/services/ai/prompts.py`
- `src/backend/services/ai/agents/deep_research_agent.py`

B站层
- `src/backend/services/bilibili/bilibili_service.py`
- `src/backend/services/bilibili/video_service.py`

配置
- `src/config.py`
