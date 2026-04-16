from pathlib import Path


def project_root() -> Path:
    """Return repository root path based on current file location."""
    return Path(__file__).resolve().parents[3]


def env_file_path() -> Path:
    """Return the canonical .env path in project root."""
    return project_root() / ".env"


def research_reports_dir() -> Path:
    """Return the canonical research report directory path."""
    return project_root() / "research_reports"
