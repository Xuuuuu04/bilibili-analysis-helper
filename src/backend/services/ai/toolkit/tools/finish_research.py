"""
完成研究报告工具（深度研究专用）
"""

from typing import Dict

from src.backend.services.ai.toolkit.base_tool import BaseTool
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class FinishResearchTool(BaseTool):
    """完成研究报告工具"""

    @property
    def name(self) -> str:
        return "finish_research_and_write_report"

    @property
    def description(self) -> str:
        return "完成所有资料搜集，开始撰写最终详尽的研究报告"

    @property
    def schema(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary_of_findings": {
                            "type": "string",
                            "description": "对研究发现的简要概述",
                        }
                    },
                    "required": ["summary_of_findings"],
                },
            },
        }

    async def execute(self, summary_of_findings: str) -> Dict:
        """
        完成研究并准备撰写报告

        Args:
            summary_of_findings: 研究发现摘要

        Returns:
            Dict: 执行结果
        """
        logger.info(f"[工具] 完成研究报告: {summary_of_findings[:50]}...")

        # 这个工具只是一个信号，告诉Agent进入报告撰写阶段
        # 实际的报告生成由DeepResearchAgent的stream_research方法处理

        return {
            "type": "tool_result",
            "tool": self.name,
            "data": {
                "message": "资料搜集阶段结束。请现在撰写全方位、深度的研究报告，并严格遵守参考来源标注规范。",
                "summary": summary_of_findings,
            },
        }
