import os
from datetime import datetime
from typing import Dict

from src.backend.services.ai.cache import BILIBILI_CACHE, EXA_CACHE, TTLCache  # noqa: F401
from src.backend.services.ai.concurrency import (  # noqa: F401
    BILIBILI_FRAMES_CONCURRENCY,
    BILIBILI_FRAMES_SEMAPHORE,
    EXA_CONCURRENCY,
    EXA_SEMAPHORE,
    OPENAI_CONCURRENCY,
    OPENAI_SEMAPHORE,
)
from src.backend.services.ai.openai_streaming import openai_chat_completions_stream  # noqa: F401
from src.backend.services.ai.report_storage import save_research_report  # noqa: F401
from src.backend.services.ai.web_search import web_search_exa  # noqa: F401
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


def generate_bili_style_pdf(topic: str, content: str, output_path: str):
    try:
        import markdown2
        from reportlab.lib.fonts import addMapping
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xhtml2pdf import pisa

        font_registered = False
        current_font_name = "SimHei"

        font_configs = [
            ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
            ("YaHei", "C:/Windows/Fonts/msyh.ttc"),
            ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
        ]

        for name, path in font_configs:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))

                    addMapping(name, 0, 0, name)
                    addMapping(name, 1, 0, name)
                    addMapping(name, 0, 1, name)
                    addMapping(name, 1, 1, name)

                    current_font_name = name
                    font_registered = True
                    logger.debug(f"[PDF] 成功注册并映射字体: {name} (路径: {path})")
                    break
                except Exception as e:
                    logger.debug(f"[PDF] 尝试注册字体 {name} 失败: {e}")

        if not font_registered:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont

            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            current_font_name = "STSong-Light"
            logger.debug(f"[PDF] 未找到系统字体，使用内置保底字体: {current_font_name}")

        html_content = markdown2.markdown(
            content, extras=["tables", "fenced-code-blocks", "break-on-newline"]
        )

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

        with open(output_path, "wb") as f:
            pisa_status = pisa.CreatePDF(full_html, dest=f, encoding="utf-8")

        if pisa_status.err:
            logger.error("PDF 生成过程中出现错误")

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise RuntimeError(f"PDF 渲染出错: {str(e)}") from e


def extract_content_from_response(response) -> str:
    try:
        logger.debug(f"_extract_content - 响应类型: {type(response)}")

        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
            logger.debug(f"提取到内容长度: {len(content) if content else 0}")

            if (
                content
                and content.strip().startswith("<!doctype")
                or content.strip().startswith("<html")
            ):
                raise ValueError("API返回了HTML页面而不是文本内容，请检查API配置和网络连接")

            return content

        if isinstance(response, str):
            if response.strip().startswith("<!doctype") or response.strip().startswith("<html"):
                raise ValueError("API返回了HTML页面，请检查OPENAI_API_BASE配置")
            return response

        if isinstance(response, dict):
            if "choices" in response and response["choices"]:
                return response["choices"][0]["message"]["content"]
            if "content" in response:
                return response["content"]
            if "text" in response:
                return response["text"]
            if "error" in response:
                raise ValueError(f"API返回错误: {response['error']}")

        result = str(response)
        logger.warning(f"响应格式未知，转为字符串: {result[:200]}")
        return result
    except Exception as e:
        logger.error(f"提取内容失败: {str(e)}, 响应类型: {type(response)}")
        raise


def extract_tokens_from_response(response) -> int:
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
    sections = {"summary": "", "danmaku": "", "comments": ""}

    current_section = None
    lines = analysis_text.split("\n")

    for line in lines:
        if "内容深度总结" in line or "第一板块" in line:
            current_section = "summary"
        elif "弹幕互动" in line or "第二板块" in line or "舆情分析" in line:
            current_section = "danmaku"
        elif "评论区深度" in line or "第三板块" in line or "评论解析" in line:
            current_section = "comments"
        elif current_section:
            sections[current_section] += line + "\n"

    return sections
