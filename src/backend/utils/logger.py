"""
统一日志系统
提供标准化的日志输出格式和文件持久化
"""

import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.backend.utils.request_context import get_request_id


# 日志颜色配置
class LogColors:
    """终端日志颜色"""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    # 级别颜色
    DEBUG = "\033[36m"  # 青色
    INFO = "\033[32m"  # 绿色
    WARNING = "\033[33m"  # 黄色
    ERROR = "\033[31m"  # 红色
    CRITICAL = "\033[35m"  # 紫色

    # 模块标签颜色
    MODULE = "\033[38;5;214m"  # 橙色
    TIMESTAMP = "\033[90m"  # 深灰
    FILENAME = "\033[38;5;39m"  # 蓝色


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（控制台）"""

    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def format(self, record):
        # 获取对应级别的颜色
        level_color = self.COLORS.get(record.levelno, LogColors.RESET)

        # 格式化级别名称（加粗）
        levelname = f"{LogColors.BOLD}{level_color}{record.levelname:<8}{LogColors.RESET}"

        # 格式化时间戳
        timestamp = f"{LogColors.TIMESTAMP}{self.formatTime(record, self.datefmt)}{LogColors.RESET}"

        # 格式化模块名
        module_name = f"{LogColors.MODULE}[{record.name:20.20}]{LogColors.RESET}"

        # 格式化位置信息
        location = ""
        if hasattr(record, "pathname") and hasattr(record, "lineno"):
            filename = Path(record.pathname).name
            location = f"{LogColors.FILENAME}{filename}:{record.lineno}{LogColors.RESET}"

        # 格式化消息
        message = record.getMessage()
        request_id = get_request_id()

        # 组合格式
        formatted = f"{timestamp} {levelname} {module_name} [rid:{request_id}]"
        if location:
            formatted += f" {location}"
        formatted += f" - {message}"

        # 添加异常信息（如果有）
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class FileFormatter(logging.Formatter):
    """文件日志格式化器（无颜色）"""

    def format(self, record):
        # 格式化级别名称
        levelname = f"{record.levelname:<8}"

        # 格式化时间戳
        timestamp = self.formatTime(record, self.datefmt)

        # 格式化模块名
        module_name = f"[{record.name:20.20}]"

        # 格式化位置信息
        location = ""
        if hasattr(record, "pathname") and hasattr(record, "lineno"):
            filename = Path(record.pathname).name
            location = f"{filename}:{record.lineno}"

        # 格式化消息
        message = record.getMessage()
        request_id = get_request_id()

        # 组合格式
        formatted = f"{timestamp} {levelname} {module_name} [rid:{request_id}]"
        if location:
            formatted += f" {location}"
        formatted += f" - {message}"

        # 添加异常信息（如果有）
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


# 日志目录（项目根目录下的 logs 文件夹）
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 当前日志文件（基于启动时间）
START_TIME = datetime.now()
CURRENT_LOG_FILE = LOG_DIR / f"app_{START_TIME.strftime('%Y%m%d_%H%M%S')}.log"


def setup_logging(
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """
    配置应用程序的日志系统

    Args:
        level: 根日志级别
        console_level: 控制台日志级别
        log_to_file: 是否记录到文件
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
    """
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 清除现有的处理器
    root_logger.handlers.clear()

    # 1. 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = ColoredFormatter(datefmt="%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. 文件处理器（按时间分割）
    if log_to_file:
        file_handler = TimedRotatingFileHandler(
            filename=str(CURRENT_LOG_FILE),
            when="midnight",  # 每天午夜分割
            interval=1,  # 间隔1天
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_formatter = FileFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


# 日志器缓存
_loggers = {}


def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    获取或创建日志器

    Args:
        name: 日志器名称（通常使用模块名，如 __name__）
        level: 日志级别（可选，默认使用全局配置）

    Returns:
        logging.Logger: 配置好的日志器实例

    Example:
        from src.backend.utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("这是一条信息")
        logger.error("这是一条错误")
    """
    if name in _loggers:
        return _loggers[name]

    # 创建日志器
    logger = logging.getLogger(name)

    # 设置日志级别
    if level is None:
        level = logging.INFO
    logger.setLevel(level)

    # 避免重复添加 handler（使用 propagation）
    logger.propagate = True

    # 缓存日志器
    _loggers[name] = logger

    return logger


def set_global_level(level: int):
    """
    设置全局日志级别

    Args:
        level: 日志级别 (logging.DEBUG, logging.INFO, etc.)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 更新所有已存在的日志器
    for logger in _loggers.values():
        logger.setLevel(level)


def get_current_log_file() -> Path:
    """获取当前日志文件路径"""
    return CURRENT_LOG_FILE


def get_log_dir() -> Path:
    """获取日志目录路径"""
    return LOG_DIR


# 便捷函数
def debug(msg: str, name: str = None):
    """输出 DEBUG 级别日志"""
    if name:
        get_logger(name).debug(msg)
    else:
        logging.debug(msg)


def info(msg: str, name: str = None):
    """输出 INFO 级别日志"""
    if name:
        get_logger(name).info(msg)
    else:
        logging.info(msg)


def warning(msg: str, name: str = None):
    """输出 WARNING 级别日志"""
    if name:
        get_logger(name).warning(msg)
    else:
        logging.warning(msg)


def error(msg: str, name: str = None, exc_info: bool = False):
    """输出 ERROR 级别日志"""
    if name:
        get_logger(name).error(msg, exc_info=exc_info)
    else:
        logging.error(msg, exc_info=exc_info)


# 自动初始化日志系统
setup_logging()
