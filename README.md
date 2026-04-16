<div align="center">
  <h1>BiliInsight | AI 视频深度分析助手</h1>
  <img src="assets/logo.svg" width="200" alt="BiliInsight Logo">
  <h3>深度研究 · 视频洞察 · 全能助手</h3>
</div>

**一键提取 B 站视频字幕、弹幕、评论及关键帧画面，通过 AI 多模态大模型生成深度总结、思维导图及舆情分析报告。**

<div align="center">

[简体中文](README.md) | [English](README_EN.md) | [日本語](README_JP.md)

</div>

<div align="center">

![BiliBili Logo](https://img.shields.io/badge/BiliBili-FF6699?style=for-the-badge&logo=bilibili&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-ready-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

[快速开始](#🚀-快速开始) • [功能特性](#✨-功能特性) • [项目截图](#🖼️-项目截图) • [技术栈](#🛠️-技术栈) • [致谢](#🙏-致谢)

</div>

## ✨ 功能特性

- **🔬 深度研究 (全新)**：自动化课题研究员，多轮自动搜集与分析，生成长篇深度报告。
- **📋 深度内容总结**：秒级提炼视频章节与核心知识点。
- **🖼️ 多模态视觉分析**：结合视频关键帧，画面细节不遗漏。
- **💬 舆情价值深挖**：看透弹幕热梗与评论区高赞观点。
- **🤖 智能对话问答**：针对视频内容进行深度互动追问。
- **📝 专栏与 Opus 解析**：支持 B 站文章及动态图文的深度逻辑拆解。
- **🎭 UP 主深度画像**：基于近期作品分析创作者的调性与价值。
- **🔐 B 站登录支持**：支持扫码登录以获取更高质量的评论与互动数据。
- **🎨 现代艺术化 UI**：极致流畅的响应式设计，支持深色模式与全屏沉浸对话。

## 🖼️ 项目截图

### 🏠 主页预览
![主页截图](assets/主页截图.png)

### ⚙️ 分析过程
![分析中](assets/分析中.png)

### 📊 深度分析结果
| 视频总结 | 互动舆情 |
| :---: | :---: |
| ![视频总结](assets/视频总结.png) | ![弹幕分析](assets/弹幕分析.png) |

| 评论深度解析 | 视频文本提取 |
| :---: | :---: |
| ![评论分析](assets/评论分析.png) | ![视频文本提取](assets/视频文本提取.png) |

### 📝 专栏与对话
| 专题文档解析 | 分析后AI对话 |
| :---: | :---: |
| ![专题文档解析](assets/专题文档解析.png) | ![分析后AI对话](assets/分析后AI对话.png) |

### 🎭 UP 主深度画像
![UP主画像](assets/UP主画像.png)

## 🚀 快速开始

1. **安装依赖**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/dev.txt
   ```
   如需启用 PDF 导出功能，再执行：
   ```bash
   pip install -r requirements/optional-pdf.txt
   ```

2. **配置环境**
   复制 `.env.example` 为 `.env` 并填写您的 API Key。
   或者直接进入面板后，通过右上角设置按钮进行配置。

3. **启动应用**
   ```bash
   uvicorn asgi:app --reload --host 0.0.0.0 --port 5001
   ```
   访问 `http://localhost:5001` 即可开始使用。

## 🏗️ 项目结构

```text
Bilibili_Analysis_Helper/
├── .github/             # CI（lint/format/test）
├── asgi.py             # FastAPI 启动入口（推荐）
├── pyproject.toml      # 工具链配置（black/ruff/pytest/mypy）
├── requirements.txt    # 默认开发依赖入口
├── requirements/       # 依赖分层（base/dev/optional）
├── .env.example        # 环境变量模板
├── README.md           # 项目文档
├── tests/              # 单元测试
└── src/                # 核心源代码包
    ├── backend/        # 统一后端（领域能力 + HTTP：src/backend/http）
    ├── frontend/       # 前端网页资源（HTML、CSS、JS）
    └── config.py       # 系统统一配置文件
```

## 🛠️ 技术栈

- **后端**：Python (FastAPI), `bilibili-api-python`, `aiohttp`
- **前端**：原生 HTML/JS/CSS3, `Marked.js` (Markdown 渲染)
- **AI 引擎**：支持 OpenAI 兼容格式的所有视觉多模态大模型 (推荐：SiliconCloud, Qwen)

## 🙏 致谢

- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) - 强大的 B 站 API 封装库。
- [SiliconCloud](https://cloud.siliconflow.cn/) - 提供极速算力支持。
- [LobeHub Icons](https://github.com/lobehub/lobe-icons) - 精美的厂商图标支持。

---

## 💖 赞助与支持

如果您觉得这个项目对您有所帮助，欢迎请作者喝杯咖啡 ☕。您的支持是我持续维护 and 开发新功能的动力！

<div align="center">

![Sponsor QR Code](assets/donate.jpg)

*扫码赞赏，备注“B站总结”*

</div>

---

Created by [mumu_xsy](https://gitcode.com/mumu_xsy) | [项目仓库](https://gitcode.com/mumu_xsy/Bilibili_Analysis_Helper)


## 开发进度（截至 2026-02-07）
- 已完成可公开仓库基线整理：补齐许可证、清理敏感与内部说明文件。
- 当前版本可构建/可运行，后续迭代以 issue 与提交记录持续公开追踪。

## 目录结构
- 结构说明：[`docs/PROJECT_STRUCTURE.md`](./docs/PROJECT_STRUCTURE.md)
