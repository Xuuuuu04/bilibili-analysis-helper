"""
AI辅助工具模块
提供网络搜索、PDF生成等辅助功能
"""

import os
import random
import re
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional

import requests

from src.backend.utils.logger import get_logger
from src.backend.utils.project_paths import research_reports_dir
from src.config import Config

logger = get_logger(__name__)

OPENAI_CONCURRENCY = int(os.getenv("OPENAI_CONCURRENCY", "2"))
EXA_CONCURRENCY = int(os.getenv("EXA_CONCURRENCY", "1"))
BILIBILI_FRAMES_CONCURRENCY = int(os.getenv("BILIBILI_FRAMES_CONCURRENCY", "1"))

OPENAI_SEMAPHORE = threading.BoundedSemaphore(value=max(1, OPENAI_CONCURRENCY))
EXA_SEMAPHORE = threading.BoundedSemaphore(value=max(1, EXA_CONCURRENCY))
# 注意：BILIBILI_FRAMES_SEMAPHORE 在 analyze_video.py 的线程池 worker 中使用，
# 不会阻塞主事件循环。如果未来需要在主事件循环中使用，应改为 asyncio.Semaphore。
BILIBILI_FRAMES_SEMAPHORE = threading.BoundedSemaphore(value=max(1, BILIBILI_FRAMES_CONCURRENCY))


class TTLCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._store = {}

    def get(self, key):
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expire_at = item
            if expire_at and expire_at < now:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl_seconds: int):
        expire_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            self._store[key] = (value, expire_at)


EXA_CACHE = TTLCache()
BILIBILI_CACHE = TTLCache()


@contextmanager
def _semaphore(sema: threading.Semaphore):
    sema.acquire()
    try:
        yield
    finally:
        sema.release()


def _sleep_backoff(attempt: int, base: float = 0.5, cap: float = 10.0):
    delay = min(cap, base * (2**attempt))
    delay = delay * (0.75 + random.random() * 0.5)
    time.sleep(delay)


def openai_chat_completions_stream(client, *, max_retries: int = 4, **params):
    """流式调用 OpenAI Chat Completions，仅在创建连接时持有信号量。

    连接创建阶段的可重试错误会自动重试；流迭代阶段一旦开始就不重试
    （因为部分数据可能已 yield，重试会导致重复数据）。
    """
    attempt = 0
    while True:
        # 仅在创建连接时持有信号量，避免流迭代串行化
        try:
            with _semaphore(OPENAI_SEMAPHORE):
                stream = client.chat.completions.create(**params)
        except Exception as e:
            msg = str(e)
            retryable = any(
                x in msg
                for x in ["429", "Rate limit", "timeout", "timed out", "502", "503", "504"]
            )
            if attempt >= max_retries or not retryable:
                raise
            _sleep_backoff(attempt)
            attempt += 1
            continue

        # 连接创建成功，在信号量外部迭代流
        try:
            for chunk in stream:
                yield chunk
        except Exception:
            # 流中途错误不重试（部分数据可能已 yield），直接抛出
            raise
        return


def web_search_exa(query: str) -> Dict:
    """
    使用 Exa AI 进行网络搜索

    Args:
        query: 搜索查询语句

    Returns:
        {'success': bool, 'data': [搜索结果列表]}
        每个结果包含: title, url, published_date
    """
    try:
        api_key = Config.EXA_API_KEY
        if not api_key:
            return {"success": False, "error": "未配置 Exa API Key"}

        cached = EXA_CACHE.get(("exa_search", query))
        if cached is not None:
            return {"success": True, "data": cached}

        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        payload = {"query": query, "useAutoprompt": True, "numResults": 5, "type": "neural"}

        logger.info(f"[工具] Exa 网络搜索: {query}")
        with _semaphore(EXA_SEMAPHORE):
            for attempt in range(4):
                try:
                    response = requests.post(
                        "https://api.exa.ai/search",
                        json=payload,
                        headers=headers,
                        timeout=(5, 20),
                    )
                    try:
                        res_data = response.json()
                    except Exception:
                        res_data = {}

                    if response.status_code == 200 and "results" in res_data:
                        results = []
                        for item in res_data["results"]:
                            results.append(
                                {
                                    "title": item.get("title", "无标题"),
                                    "url": item.get("url", ""),
                                    "published_date": item.get("publishedDate", "未知"),
                                }
                            )
                        EXA_CACHE.set(("exa_search", query), results, ttl_seconds=600)
                        return {"success": True, "data": results}

                    retryable = response.status_code in (408, 429, 500, 502, 503, 504)
                    if attempt < 3 and retryable:
                        _sleep_backoff(attempt)
                        continue

                    error = res_data.get("error") if isinstance(res_data, dict) else None
                    return {"success": False, "error": error or f"HTTP {response.status_code}"}
                except (requests.Timeout, requests.ConnectionError) as e:
                    if attempt < 3:
                        _sleep_backoff(attempt)
                        continue
                    raise e
    except Exception as e:
        logger.error(f"Exa 搜索失败: {e}")
        return {"success": False, "error": str(e)}


def save_research_report(topic: str, content: str, report_dir: Optional[str] = None):
    """
    将研究报告保存到本地 Markdown 文件

    Args:
        topic: 研究课题
        content: 报告内容
        report_dir: 报告保存目录

    Returns:
        {'success': bool, 'path': str} - 保存的文件路径
    """
    try:
        resolved_report_dir = report_dir or str(research_reports_dir())
        if not os.path.exists(resolved_report_dir):
            os.makedirs(resolved_report_dir)

        # 清理文件名
        safe_topic = re.sub(r'[\\/*?:"<>|]', "_", topic)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{timestamp}_{safe_topic}"

        # 保存 Markdown
        md_filepath = os.path.join(resolved_report_dir, f"{filename_base}.md")
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(f"# 研究课题：{topic}\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(content)

        logger.info(f"研究报告已持久化: {md_filepath}")
        return {"success": True, "path": md_filepath}

    except Exception as e:
        logger.warning(f"保存报告失败: {e}")
        return {"success": False, "error": str(e)}


def generate_bili_style_pdf(topic: str, content: str, output_path: str):
    """
    生成 Bilibili 风格的 PDF 报告

    Args:
        topic: 研究课题
        content: 报告内容（Markdown格式）
        output_path: 输出PDF路径

    Raises:
        Exception: PDF生成失败时抛出异常
    """
    try:
        import markdown2
        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xhtml2pdf import pisa

        # --- 1. 更加健壮的字体注册逻辑 ---
        font_registered = False
        current_font_name = "SimHei"  # 默认使用黑体，因为它是 .ttf 格式，兼容性最好

        # 路径列表 (Windows) - 优先选择 .ttf 格式避开权限问题
        font_configs = [
            ("SimHei", "C:/Windows/Fonts/simhei.ttf"),  # 黑体 (.ttf) - 兼容性王者
            ("YaHei", "C:/Windows/Fonts/msyh.ttc"),  # 微软雅黑 (.ttc)
            ("SimSun", "C:/Windows/Fonts/simsun.ttc"),  # 宋体 (.ttc)
        ]

        for name, path in font_configs:
            if os.path.exists(path):
                try:
                    # 注册字体
                    pdfmetrics.registerFont(TTFont(name, path))

                    # 强制映射加粗、斜体到同一个字体文件，防止跳回 Helvetica
                    addMapping(name, 0, 0, name)  # normal
                    addMapping(name, 1, 0, name)  # bold
                    addMapping(name, 0, 1, name)  # italic
                    addMapping(name, 1, 1, name)  # bold italic

                    current_font_name = name
                    font_registered = True
                    logger.debug(f"[PDF] 成功注册并映射字体: {name} (路径: {path})")
                    break  # 只要注册成功一个就退出循环
                except Exception as e:
                    logger.debug(f"[PDF] 尝试注册字体 {name} 失败: {e}")

        if not font_registered:
            # 最后的保底：使用内置的 STSong-Light (无需外部文件)
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont

            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            current_font_name = "STSong-Light"
            logger.debug(f"[PDF] 未找到系统字体，使用内置保底字体: {current_font_name}")

        # --- 2. 准备 HTML 内容 ---
        # 强化加粗内容的样式，使其在 PDF 中呈现 B 站粉色
        html_content = markdown2.markdown(
            content, extras=["tables", "fenced-code-blocks", "break-on-newline"]
        )

        # Bilibili 风格 CSS
        # 关键修复：添加 -pdf-font-encoding: identity-H; 以支持中文字符
        bili_css = f"""
        @page {{
            size: a4;
            margin: 2cm;
            @frame footer {{
                -pdf-frame-content: footerContent;
                bottom: 1cm;
                margin-left: 2cm;
                margin-right: 2cm;
                height: 1cm;
            }}
        }}
        body {{
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
            color: #18191C;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #FB7299;
            padding-bottom: 20px;
            margin-bottom: 30px;
            position: relative;
        }}
        .logo-box {{
            margin-bottom: 10px;
        }}
        .logo-text {{
            color: #FB7299;
            font-size: 24px;
            font-weight: bold;
        }}
        h1 {{
            color: #FB7299;
            font-size: 26px;
            margin-top: 10px;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}
        h2 {{
            color: #00AEEC;
            border-left: 5px solid #00AEEC;
            padding-left: 10px;
            margin-top: 25px;
            font-size: 20px;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}
        h3 {{
            color: #18191C;
            font-size: 18px;
            margin-top: 20px;
            border-bottom: 1px solid #E3E5E7;
            padding-bottom: 5px;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}
        p {{
            margin-bottom: 12px;
            font-size: 13px;
            text-align: justify;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}

        /* 强化加粗样式：B站粉色且加粗 */
        strong, b {{
            color: #FB7299;
            font-weight: bold;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}

        .meta {{
            font-size: 11px;
            color: #9499A0;
            margin-bottom: 20px;
        }}
        .footer {{
            text-align: center;
            font-size: 10px;
            color: #9499A0;
            border-top: 1px solid #E3E5E7;
            padding-top: 10px;
        }}
        blockquote {{
            background-color: #F6F7F8;
            border-left: 4px solid #FB7299;
            padding: 10px 20px;
            margin: 20px 0;
            font-style: italic;
            color: #61666D;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 11px;
        }}
        th {{
            background-color: #FB7299;
            color: white;
            font-weight: bold;
            padding: 8px;
            border: 1px solid #FB7299;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}
        td {{
            padding: 8px;
            border: 1px solid #E3E5E7;
            text-align: left;
            font-family: "{current_font_name}";
            -pdf-font-encoding: identity-H;
        }}
        tr:nth-child(even) {{
            background-color: #FAFAFA;
        }}
        img {{
            max-width: 100%;
        }}
        """

        full_html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>{bili_css}</style>
        </head>
        <body>
            <div class="header">
                <div class="logo-box">
                    <div style="background-color: #FB7299; padding: 10px; border-radius: 8px; display: inline-block; margin-bottom: 5px;">
                        <span style="color: white; font-size: 20px; font-weight: bold;">BiliInsight</span>
                    </div>
                </div>
                <h1>{topic}</h1>
                <div class="meta">
                    报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
                    AI 深度研究专家 |
                    内容驱动：Bilibili Data
                </div>
            </div>

            <div class="content">
                {html_content}
            </div>

            <div id="footerContent" class="footer">
                © 2025 BiliInsight - 深度研究 · 视频洞察 · 全能助手 | 由 AI 驱动的深度研究引擎 | 第 <pdf:pagenumber> 页
            </div>
        </body>
        </html>
        """

        # 生成 PDF
        with open(output_path, "wb") as f:
            # 关键：指定 encoding='utf-8' 并在 pisa 中处理
            pisa_status = pisa.CreatePDF(full_html, dest=f, encoding="utf-8")

        if pisa_status.err:
            logger.error("PDF 生成过程中出现错误")

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise RuntimeError(f"PDF 渲染出错: {str(e)}") from e


def extract_content_from_response(response) -> str:
    """
    提取响应内容，兼容不同API格式

    Args:
        response: OpenAI API响应对象

    Returns:
        提取的文本内容

    Raises:
        ValueError: 当响应格式错误时
    """
    try:
        logger.debug(f"_extract_content - 响应类型: {type(response)}")

        # 尝试标准OpenAI格式
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
            logger.debug(f"提取到内容长度: {len(content) if content else 0}")

            # 检查是否是HTML（错误响应）
            if (
                content
                and content.strip().startswith("<!doctype")
                or content.strip().startswith("<html")
            ):
                raise ValueError("API返回了HTML页面而不是文本内容，请检查API配置和网络连接")

            return content

        # 如果是字符串，直接返回
        if isinstance(response, str):
            # 检查是否是HTML
            if response.strip().startswith("<!doctype") or response.strip().startswith("<html"):
                raise ValueError("API返回了HTML页面，请检查OPENAI_API_BASE配置")
            return response

        # 如果是字典，尝试提取内容
        if isinstance(response, dict):
            if "choices" in response and response["choices"]:
                return response["choices"][0]["message"]["content"]
            if "content" in response:
                return response["content"]
            if "text" in response:
                return response["text"]
            # 如果字典中有error
            if "error" in response:
                raise ValueError(f"API返回错误: {response['error']}")

        # 尝试转换为字符串
        result = str(response)
        logger.warning(f"响应格式未知，转为字符串: {result[:200]}")
        return result
    except Exception as e:
        logger.error(f"提取内容失败: {str(e)}, 响应类型: {type(response)}")
        raise


def extract_tokens_from_response(response) -> int:
    """
    提取token使用量，兼容不同API格式

    Args:
        response: OpenAI API响应对象

    Returns:
        token使用量，失败返回0
    """
    try:
        if hasattr(response, "usage") and response.usage:
            if hasattr(response.usage, "total_tokens"):
                return response.usage.total_tokens

        if isinstance(response, dict):
            if "usage" in response:
                return response["usage"].get("total_tokens", 0)

        return 0
    except Exception as e:
        logger.warning(f"提取tokens失败: {str(e)}")
        return 0


def parse_analysis_response(analysis_text: str) -> Dict:
    """
    解析分析响应，提取结构化内容

    Args:
        analysis_text: AI分析返回的完整文本

    Returns:
        {'summary': str, 'danmaku': str, 'comments': str}
    """
    sections = {"summary": "", "danmaku": "", "comments": ""}

    current_section = None
    lines = analysis_text.split("\n")

    for line in lines:
        # 匹配第一板块：内容总结
        if "内容深度总结" in line or "第一板块" in line:
            current_section = "summary"
        # 匹配第二板块：弹幕分析
        elif "弹幕互动" in line or "第二板块" in line or "舆情分析" in line:
            current_section = "danmaku"
        # 匹配第三板块：评论分析
        elif "评论区深度" in line or "第三板块" in line or "评论解析" in line:
            current_section = "comments"
        elif current_section:
            sections[current_section] += line + "\n"

    return sections
