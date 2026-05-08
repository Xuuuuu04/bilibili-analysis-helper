import os
import re
from datetime import datetime
from typing import Optional

from src.backend.utils.logger import get_logger
from src.backend.utils.project_paths import research_reports_dir

logger = get_logger(__name__)


def save_research_report(topic: str, content: str, report_dir: Optional[str] = None):
    try:
        resolved_report_dir = report_dir or str(research_reports_dir())
        if not os.path.exists(resolved_report_dir):
            os.makedirs(resolved_report_dir)

        safe_topic = re.sub(r'[\\/*?:"<>|]', "_", topic)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{timestamp}_{safe_topic}"

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
