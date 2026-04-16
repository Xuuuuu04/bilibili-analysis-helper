"""
================================================================================
深度研究用例服务 (src/backend/http/usecases/research_service.py)
================================================================================
"""

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from src.backend.http.core.errors import BadRequestError, NotFoundError
from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService
from src.backend.utils.project_paths import research_reports_dir


class ResearchService:
    def __init__(self, ai_service: AIService, bilibili_service: BilibiliService):
        self._ai = ai_service
        self._bilibili = bilibili_service

    def stream(self, topic: str) -> Iterator[dict]:
        if not topic:
            raise BadRequestError("请输入研究课题")
        return self._ai.deep_research_stream(topic, self._bilibili)

    def list_history(self) -> dict:
        report_dir = research_reports_dir()
        if not report_dir.exists():
            return {"success": True, "data": []}

        reports_dict: dict[str, dict] = {}
        for file_path in report_dir.iterdir():
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            if suffix not in {".md", ".pdf"}:
                continue

            base = file_path.stem
            ext = suffix.lstrip(".")
            if base not in reports_dict:
                stats = file_path.stat()
                parts = base.split("_", 2)
                topic = parts[2] if len(parts) > 2 else base
                reports_dict[base] = {
                    "id": base,
                    "topic": topic,
                    "created_at": datetime.fromtimestamp(stats.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "has_md": False,
                    "has_pdf": False,
                }

            if ext == "md":
                reports_dict[base]["has_md"] = True
            if ext == "pdf":
                reports_dict[base]["has_pdf"] = True

        reports = list(reports_dict.values())
        reports.sort(key=lambda item: item["id"], reverse=True)
        return {"success": True, "data": reports}

    def resolve_download_path(self, file_id: str, format: str) -> tuple[str, str]:
        if format not in {"md", "pdf"}:
            raise BadRequestError("无效的格式")
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            raise BadRequestError("无效的文件ID")

        filename = f"{file_id}.{format}"
        filepath = research_reports_dir() / filename
        # 路径安全验证：确保解析后的路径在允许目录内
        if not filepath.resolve().is_relative_to(research_reports_dir().resolve()):
            raise BadRequestError("无效的文件路径")
        if not filepath.exists():
            raise NotFoundError("报告不存在")
        return str(filepath), filename

    def read_report(self, filename: str) -> dict:
        if ".." in filename or "/" in filename or "\\" in filename:
            raise BadRequestError("无效的文件名")

        safe_name = Path(filename).name
        filepath = research_reports_dir() / safe_name
        # 路径安全验证：确保解析后的路径在允许目录内
        if not filepath.resolve().is_relative_to(research_reports_dir().resolve()):
            raise BadRequestError("无效的文件路径")
        if not filepath.exists():
            raise NotFoundError("报告不存在")

        with filepath.open("r", encoding="utf-8") as handle:
            content = handle.read()

        return {"success": True, "data": {"content": content, "filename": safe_name}}
