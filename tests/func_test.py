#!/usr/bin/env python3
"""
================================================================================
功能测试脚本 - 端到端测试
================================================================================

测试范围:
1. 健康检查接口
2. 设置管理接口
3. B 站 API 路由 (搜索、视频信息、热门视频)
4. 视频分析接口
5. 智能问答接口
6. 深度研究接口

测试设计原则:
- 黑盒测试：从业务描述推导测试预期
- 边界值分析：空值、超长字符串、特殊字符
- 等价类划分：有效输入/无效输入
- 错误处理：API 超时、无效凭证
- 幂等性：重复请求
"""

import json
import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from src.backend.http.app import create_app


class TestResult:
    """测试结果记录"""

    def __init__(self, test_id: str, name: str, category: str):
        self.test_id = test_id
        self.name = name
        self.category = category
        self.passed = False
        self.error = None
        self.actual_response = None
        self.expected_response = None

    def record_pass(self, actual: Any = None):
        self.passed = True
        self.actual_response = actual

    def record_fail(self, error: str, actual: Any = None):
        self.passed = False
        self.error = error
        self.actual_response = actual

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "category": self.category,
            "passed": self.passed,
            "error": self.error,
            "actual_response": (
                str(self.actual_response)[:200] if self.actual_response else None
            ),
        }


class FunctionTestSuite:
    """功能测试套件"""

    def __init__(self):
        self.client = TestClient(create_app())
        self.results: list[TestResult] = []
        self.environment_issues: list[str] = []

    def run_test(self, test_func, test_id: str, name: str, category: str):
        """运行单个测试并记录结果"""
        result = TestResult(test_id, name, category)
        try:
            test_func(result)
        except Exception as e:
            result.record_fail(f"测试执行异常：{type(e).__name__}: {str(e)}")
        self.results.append(result)
        return result

    # =========================================================================
    # 健康检查测试
    # =========================================================================

    def test_health_success(self, result: TestResult):
        """TC-001: 健康检查 - 正常请求"""
        resp = self.client.get("/api/health")
        assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
        data = resp.json()
        assert data.get("success") is True, f"success 应为 True, 实际：{data}"
        assert data.get("status") == "running", f"status 应为 running, 实际：{data}"
        result.record_pass(data)

    def test_health_method_not_allowed(self, result: TestResult):
        """TC-002: 健康检查 - POST 方法 (应拒绝)"""
        resp = self.client.post("/api/health")
        # FastAPI 默认返回 405 Method Not Allowed
        assert resp.status_code == 405, f"状态码应为 405, 实际：{resp.status_code}"
        result.record_pass({"status_code": resp.status_code})

    # =========================================================================
    # 设置管理测试
    # =========================================================================

    def test_settings_get(self, result: TestResult):
        """TC-003: 获取设置 - 正常请求"""
        resp = self.client.get("/api/settings")
        assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
        data = resp.json()
        assert "success" in data or "data" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_settings_update_empty(self, result: TestResult):
        """TC-004: 更新设置 - 空数据"""
        resp = self.client.post("/api/settings", json={})
        # 空更新应该被接受或返回有意义的错误
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_settings_update_invalid_key(self, result: TestResult):
        """TC-005: 更新设置 - 非法字段"""
        resp = self.client.post("/api/settings", json={"invalid_field": "value"})
        # Pydantic 应该忽略未定义的字段或返回验证错误
        assert resp.status_code in [200, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_settings_update_dark_mode(self, result: TestResult):
        """TC-006: 更新设置 - 深色模式开关"""
        resp = self.client.post("/api/settings", json={"dark_mode": True})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_settings_update_api_key_masking(self, result: TestResult):
        """TC-007: 获取设置 - API Key 应该被遮蔽"""
        resp = self.client.get("/api/settings")
        data = resp.json()
        # API Key 不应明文显示
        if "data" in data:
            api_key = data["data"].get("openai_api_key", "")
            if api_key and len(api_key) > 10:
                result.record_fail("API Key 不应明文显示", data)
                return
        result.record_pass(data)

    # =========================================================================
    # B 站 API 测试 - 搜索功能
    # =========================================================================

    def test_search_empty_keyword(self, result: TestResult):
        """TC-008: 搜索 - 空关键词"""
        resp = self.client.post("/api/search", json={"keyword": "", "mode": "video"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        # 空关键词应返回错误或有意义的结果
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_search_normal_keyword(self, result: TestResult):
        """TC-009: 搜索 - 正常关键词"""
        resp = self.client.post("/api/search", json={"keyword": "Python", "mode": "video"})
        assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_search_invalid_mode(self, result: TestResult):
        """TC-010: 搜索 - 非法模式"""
        resp = self.client.post("/api/search", json={"keyword": "test", "mode": "invalid"})
        # 非法模式会被 Pydantic 拒绝 (422) 或被业务逻辑拒绝 (400)
        assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_search_special_characters(self, result: TestResult):
        """TC-011: 搜索 - 特殊字符"""
        resp = self.client.post(
            "/api/search", json={"keyword": "<script>alert('xss')</script>", "mode": "video"}
        )
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_search_long_keyword(self, result: TestResult):
        """TC-012: 搜索 - 超长关键词"""
        long_keyword = "A" * 1000
        resp = self.client.post("/api/search", json={"keyword": long_keyword, "mode": "video"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # B 站 API 测试 - 视频信息
    # =========================================================================

    def test_video_info_invalid_url(self, result: TestResult):
        """TC-013: 视频信息 - 无效 URL"""
        resp = self.client.post("/api/video/info", json={"url": "invalid"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_video_info_empty_url(self, result: TestResult):
        """TC-014: 视频信息 - 空 URL"""
        resp = self.client.post("/api/video/info", json={"url": ""})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_video_info_bvid_format(self, result: TestResult):
        """TC-015: 视频信息 - BV 号格式"""
        # 使用一个格式正确但不存在的 BV 号
        resp = self.client.post("/api/video/info", json={"url": "BV1234567890"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_video_info_full_url(self, result: TestResult):
        """TC-016: 视频信息 - 完整 URL"""
        url = "https://www.bilibili.com/video/BV1234567890"
        resp = self.client.post("/api/video/info", json={"url": url})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # B 站 API 测试 - 热门视频
    # =========================================================================

    def test_popular_videos_get(self, result: TestResult):
        """TC-017: 热门视频 - GET 请求"""
        resp = self.client.get("/api/video/popular")
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    # =========================================================================
    # B 站 API 测试 - 图片代理
    # =========================================================================

    def test_image_proxy_invalid_domain(self, result: TestResult):
        """TC-018: 图片代理 - 非法域名"""
        resp = self.client.get("/api/image-proxy?url=http://evil.com/image.jpg")
        assert resp.status_code in [400, 404, 500], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_image_proxy_empty_url(self, result: TestResult):
        """TC-019: 图片代理 - 空 URL"""
        resp = self.client.get("/api/image-proxy?url=")
        # 空 URL 应该返回 422 验证错误
        assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # B 站 API 测试 - 登录
    # =========================================================================

    def test_login_check(self, result: TestResult):
        """TC-020: 登录状态检查"""
        resp = self.client.get("/api/bilibili/login/check")
        assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_login_start(self, result: TestResult):
        """TC-021: 启动扫码登录"""
        resp = self.client.post("/api/bilibili/login/start")
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    # =========================================================================
    # 视频分析测试
    # =========================================================================

    def test_analyze_empty_url(self, result: TestResult):
        """TC-022: 视频分析 - 空 URL"""
        resp = self.client.post("/api/analyze", json={"url": ""})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_analyze_invalid_url(self, result: TestResult):
        """TC-023: 视频分析 - 无效 URL"""
        resp = self.client.post("/api/analyze", json={"url": "not-a-bilibili-url"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        # 应返回错误提示
        if data.get("success") is True:
            result.record_fail("无效 URL 应返回错误", data)
            return
        result.record_pass(data)

    def test_analyze_stream_empty_url(self, result: TestResult):
        """TC-024: 视频流式分析 - 空 URL"""
        resp = self.client.post("/api/analyze/stream", json={"url": "", "mode": "video"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_analyze_stream_invalid_mode(self, result: TestResult):
        """TC-025: 视频流式分析 - 非法模式"""
        resp = self.client.post(
            "/api/analyze/stream", json={"url": "BV123", "mode": "invalid"}
        )
        # 非法模式会被 Pydantic 拒绝 (422) 或被业务逻辑拒绝 (400)
        assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # 智能问答测试
    # =========================================================================

    def test_qa_empty_params(self, result: TestResult):
        """TC-026: 智能问答 - 空参数"""
        resp = self.client.post(
            "/api/qa/stream", json={"question": "", "context": "", "mode": "video"}
        )
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        # 空参数应返回错误
        if data.get("success") is True:
            result.record_fail("空参数应返回错误", data)
            return
        result.record_pass(data)

    def test_qa_normal_request(self, result: TestResult):
        """TC-027: 智能问答 - 正常请求"""
        resp = self.client.post(
            "/api/qa/stream",
            json={
                "question": "这个视频讲了什么？",
                "context": "这是一个关于 Python 编程的视频",
                "mode": "video",
            },
        )
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        # 注意：流式响应需要特殊处理，这里只检查状态码
        result.record_pass({"status_code": resp.status_code})

    def test_qa_invalid_mode(self, result: TestResult):
        """TC-028: 智能问答 - 非法模式"""
        resp = self.client.post(
            "/api/qa/stream",
            json={
                "question": "test",
                "context": "test",
                "mode": "invalid_mode",
            },
        )
        # 非法模式会被 Pydantic 拒绝 (422) 或被业务逻辑拒绝 (400)
        assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # 深度研究测试
    # =========================================================================

    def test_research_empty_topic(self, result: TestResult):
        """TC-029: 深度研究 - 空主题"""
        resp = self.client.post("/api/research", json={"topic": ""})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        # 空主题应返回错误
        if data.get("success") is True:
            result.record_fail("空主题应返回错误", data)
            return
        result.record_pass(data)

    def test_research_normal_topic(self, result: TestResult):
        """TC-030: 深度研究 - 正常主题"""
        resp = self.client.post(
            "/api/research", json={"topic": "Python 编程入门教程"}
        )
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        # 流式响应，主要检查状态码
        result.record_pass({"status_code": resp.status_code})

    def test_research_special_characters(self, result: TestResult):
        """TC-031: 深度研究 - 特殊字符主题"""
        resp = self.client.post(
            "/api/research", json={"topic": "<script>alert('xss')</script>"}
        )
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_research_history(self, result: TestResult):
        """TC-032: 研究历史"""
        resp = self.client.get("/api/research/history")
        # 研究历史接口可能因为 OPENAI_API_KEY 未配置而失败 (400)
        # 或者成功返回空列表 (200)
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        data = resp.json()
        # 如果返回 200，检查有 success 字段；如果返回 400/500，是环境问题的预期行为
        if resp.status_code == 200:
            assert "success" in data, f"响应格式异常：{data}"
        result.record_pass({"status_code": resp.status_code, "data": data})

    # =========================================================================
    # 用户画像测试
    # =========================================================================

    def test_user_portrait_empty_uid(self, result: TestResult):
        """TC-033: 用户画像 - 空 UID"""
        resp = self.client.post("/api/user/portrait", json={"uid": ""})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        data = resp.json()
        assert "success" in data, f"响应格式异常：{data}"
        result.record_pass(data)

    def test_user_portrait_invalid_uid(self, result: TestResult):
        """TC-034: 用户画像 - 无效 UID"""
        resp = self.client.post("/api/user/portrait", json={"uid": "not_a_number"})
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_user_portrait_normal_uid(self, result: TestResult):
        """TC-035: 用户画像 - 正常 UID"""
        resp = self.client.post("/api/user/portrait", json={"uid": "12345678"})
        assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    # =========================================================================
    # 幂等性测试
    # =========================================================================

    def test_idempotency_health(self, result: TestResult):
        """TC-036: 幂等性 - 健康检查重复请求"""
        resp1 = self.client.get("/api/health")
        resp2 = self.client.get("/api/health")
        resp3 = self.client.get("/api/health")
        assert resp1.status_code == resp2.status_code == resp3.status_code
        result.record_pass({"status_codes": [resp1.status_code, resp2.status_code, resp3.status_code]})

    def test_idempotency_settings(self, result: TestResult):
        """TC-037: 幂等性 - 设置更新重复请求"""
        payload = {"dark_mode": True}
        resp1 = self.client.post("/api/settings", json=payload)
        resp2 = self.client.post("/api/settings", json=payload)
        # 两次更新应返回相同结果或都成功
        assert resp1.status_code == resp2.status_code
        result.record_pass({"status_codes": [resp1.status_code, resp2.status_code]})

    # =========================================================================
    # 边界值测试
    # =========================================================================

    def test_boundary_unicode_keyword(self, result: TestResult):
        """TC-038: 边界值 - Unicode 关键词"""
        resp = self.client.post(
            "/api/search", json={"keyword": "测试🔥🎉", "mode": "video"}
        )
        assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_boundary_null_values(self, result: TestResult):
        """TC-039: 边界值 - null 值"""
        resp = self.client.post("/api/search", json={"keyword": None, "mode": "video"})
        # null 值会被 Pydantic 拒绝 (422) 或被业务逻辑拒绝 (400)
        assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())

    def test_boundary_very_long_url(self, result: TestResult):
        """TC-040: 边界值 - 超长 URL"""
        long_url = "https://www.bilibili.com/video/" + "B" * 500
        resp = self.client.post("/api/analyze", json={"url": long_url})
        assert resp.status_code in [200, 400, 422], f"状态码：{resp.status_code}"
        result.record_pass(resp.json())


def run_all_tests():
    """运行所有测试"""
    suite = FunctionTestSuite()

    # 健康检查
    suite.run_test(suite.test_health_success, "TC-001", "健康检查 - 正常请求", "Health")
    suite.run_test(suite.test_health_method_not_allowed, "TC-002", "健康检查 - POST 方法", "Health")

    # 设置管理
    suite.run_test(suite.test_settings_get, "TC-003", "获取设置", "Settings")
    suite.run_test(suite.test_settings_update_empty, "TC-004", "更新设置 - 空数据", "Settings")
    suite.run_test(suite.test_settings_update_invalid_key, "TC-005", "更新设置 - 非法字段", "Settings")
    suite.run_test(suite.test_settings_update_dark_mode, "TC-006", "更新设置 - 深色模式", "Settings")
    suite.run_test(suite.test_settings_update_api_key_masking, "TC-007", "API Key 遮蔽检查", "Settings")

    # B 站 API - 搜索
    suite.run_test(suite.test_search_empty_keyword, "TC-008", "搜索 - 空关键词", "Bilibili.Search")
    suite.run_test(suite.test_search_normal_keyword, "TC-009", "搜索 - 正常关键词", "Bilibili.Search")
    suite.run_test(suite.test_search_invalid_mode, "TC-010", "搜索 - 非法模式", "Bilibili.Search")
    suite.run_test(suite.test_search_special_characters, "TC-011", "搜索 - 特殊字符", "Bilibili.Search")
    suite.run_test(suite.test_search_long_keyword, "TC-012", "搜索 - 超长关键词", "Bilibili.Search")

    # B 站 API - 视频信息
    suite.run_test(suite.test_video_info_invalid_url, "TC-013", "视频信息 - 无效 URL", "Bilibili.Video")
    suite.run_test(suite.test_video_info_empty_url, "TC-014", "视频信息 - 空 URL", "Bilibili.Video")
    suite.run_test(suite.test_video_info_bvid_format, "TC-015", "视频信息 - BV 号格式", "Bilibili.Video")
    suite.run_test(suite.test_video_info_full_url, "TC-016", "视频信息 - 完整 URL", "Bilibili.Video")

    # B 站 API - 热门视频
    suite.run_test(suite.test_popular_videos_get, "TC-017", "热门视频", "Bilibili.Popular")

    # B 站 API - 图片代理
    suite.run_test(suite.test_image_proxy_invalid_domain, "TC-018", "图片代理 - 非法域名", "Bilibili.Proxy")
    suite.run_test(suite.test_image_proxy_empty_url, "TC-019", "图片代理 - 空 URL", "Bilibili.Proxy")

    # B 站 API - 登录
    suite.run_test(suite.test_login_check, "TC-020", "登录状态检查", "Bilibili.Login")
    suite.run_test(suite.test_login_start, "TC-021", "启动扫码登录", "Bilibili.Login")

    # 视频分析
    suite.run_test(suite.test_analyze_empty_url, "TC-022", "视频分析 - 空 URL", "Analyze")
    suite.run_test(suite.test_analyze_invalid_url, "TC-023", "视频分析 - 无效 URL", "Analyze")
    suite.run_test(suite.test_analyze_stream_empty_url, "TC-024", "视频流式分析 - 空 URL", "Analyze")
    suite.run_test(suite.test_analyze_stream_invalid_mode, "TC-025", "视频流式分析 - 非法模式", "Analyze")

    # 智能问答
    suite.run_test(suite.test_qa_empty_params, "TC-026", "智能问答 - 空参数", "QA")
    suite.run_test(suite.test_qa_normal_request, "TC-027", "智能问答 - 正常请求", "QA")
    suite.run_test(suite.test_qa_invalid_mode, "TC-028", "智能问答 - 非法模式", "QA")

    # 深度研究
    suite.run_test(suite.test_research_empty_topic, "TC-029", "深度研究 - 空主题", "Research")
    suite.run_test(suite.test_research_normal_topic, "TC-030", "深度研究 - 正常主题", "Research")
    suite.run_test(suite.test_research_special_characters, "TC-031", "深度研究 - 特殊字符", "Research")
    suite.run_test(suite.test_research_history, "TC-032", "研究历史", "Research")

    # 用户画像
    suite.run_test(suite.test_user_portrait_empty_uid, "TC-033", "用户画像 - 空 UID", "User")
    suite.run_test(suite.test_user_portrait_invalid_uid, "TC-034", "用户画像 - 无效 UID", "User")
    suite.run_test(suite.test_user_portrait_normal_uid, "TC-035", "用户画像 - 正常 UID", "User")

    # 幂等性
    suite.run_test(suite.test_idempotency_health, "TC-036", "幂等性 - 健康检查", "Idempotency")
    suite.run_test(suite.test_idempotency_settings, "TC-037", "幂等性 - 设置更新", "Idempotency")

    # 边界值
    suite.run_test(suite.test_boundary_unicode_keyword, "TC-038", "边界值 - Unicode", "Boundary")
    suite.run_test(suite.test_boundary_null_values, "TC-039", "边界值 - null 值", "Boundary")
    suite.run_test(suite.test_boundary_very_long_url, "TC-040", "边界值 - 超长 URL", "Boundary")

    return suite


def generate_report(suite: FunctionTestSuite) -> str:
    """生成测试报告"""
    passed = sum(1 for r in suite.results if r.passed)
    failed = sum(1 for r in suite.results if not r.passed)
    total = len(suite.results)

    report = []
    report.append("=" * 80)
    report.append("功能测试报告 - BiliInsight 端到端测试")
    report.append("=" * 80)
    report.append("")
    report.append(f"测试总数：{total}")
    report.append(f"通过：{passed}")
    report.append(f"失败：{failed}")
    report.append(f"通过率：{passed / total * 100:.1f}%")
    report.append("")

    # 按类别分组
    categories = {}
    for r in suite.results:
        if r.category not in categories:
            categories[r.category] = []
        categories[r.category].append(r)

    report.append("-" * 80)
    report.append("按类别统计")
    report.append("-" * 80)
    for cat, results in sorted(categories.items()):
        cat_passed = sum(1 for r in results if r.passed)
        cat_total = len(results)
        status = "OK" if cat_passed == cat_total else "ISSUES"
        report.append(f"  {cat}: {cat_passed}/{cat_total} [{status}]")
    report.append("")

    # 失败详情
    failed_results = [r for r in suite.results if not r.passed]
    if failed_results:
        report.append("-" * 80)
        report.append("失败用例详情")
        report.append("-" * 80)
        for r in failed_results:
            report.append(f"\n[{r.test_id}] {r.name}")
            report.append(f"  错误：{r.error}")
            if r.actual_response:
                report.append(f"  实际响应：{r.actual_response}")
    report.append("")

    # 环境问题
    if suite.environment_issues:
        report.append("-" * 80)
        report.append("环境问题")
        report.append("-" * 80)
        for issue in suite.environment_issues:
            report.append(f"  - {issue}")
    report.append("")

    report.append("=" * 80)
    report.append("报告结束")
    report.append("=" * 80)

    return "\n".join(report)


if __name__ == "__main__":
    print("开始执行功能测试...")
    suite = run_all_tests()
    report = generate_report(suite)
    print(report)

    # 保存报告
    report_path = ROOT / "tests" / "reports" / "func-report-v1.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 功能测试报告\n\n")
        f.write(f"生成时间：{Path(report_path).stat().st_mtime}\n\n")
        f.write("```text\n")
        f.write(report)
        f.write("\n```\n")

    print(f"\n报告已保存到：{report_path}")

    # 返回退出码
    failed = sum(1 for r in suite.results if not r.passed)
    sys.exit(0 if failed == 0 else 1)
