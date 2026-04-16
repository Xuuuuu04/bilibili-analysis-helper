from pathlib import Path

import pytest

from src.backend.http.core.errors import NotFoundError
from src.backend.http.usecases import research_service as research_service_module
from src.backend.http.usecases.research_service import ResearchService


def test_list_history_uses_absolute_report_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report_dir = tmp_path / "research_reports"
    report_dir.mkdir()
    (report_dir / "20250207_abc_topic-a.md").write_text("content", encoding="utf-8")
    (report_dir / "20250207_abc_topic-a.pdf").write_text("fake", encoding="utf-8")
    (report_dir / "20240207_old_topic-b.md").write_text("old", encoding="utf-8")

    monkeypatch.setattr(research_service_module, "research_reports_dir", lambda: report_dir)
    service = ResearchService(ai_service=None, bilibili_service=None)  # type: ignore[arg-type]

    payload = service.list_history()
    assert payload["success"] is True
    assert payload["data"][0]["id"] == "20250207_abc_topic-a"
    assert payload["data"][0]["has_md"] is True
    assert payload["data"][0]["has_pdf"] is True


def test_resolve_download_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    report_dir = tmp_path / "research_reports"
    report_dir.mkdir()
    target = report_dir / "file_1.md"
    target.write_text("x", encoding="utf-8")

    monkeypatch.setattr(research_service_module, "research_reports_dir", lambda: report_dir)
    service = ResearchService(ai_service=None, bilibili_service=None)  # type: ignore[arg-type]

    resolved_path, filename = service.resolve_download_path("file_1", "md")
    assert resolved_path == str(target)
    assert filename == "file_1.md"

    with pytest.raises(NotFoundError):
        service.resolve_download_path("missing", "md")
