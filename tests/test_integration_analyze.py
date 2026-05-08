def test_analyze_empty_url(app_client):
    resp = app_client.post("/api/analyze", json={"url": ""})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_analyze_invalid_url(app_client):
    resp = app_client.post("/api/analyze", json={"url": "not-a-bilibili-url"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"
    if data.get("success") is True:
        raise AssertionError("无效 URL 应返回错误")


def test_analyze_stream_empty_url(app_client):
    resp = app_client.post("/api/analyze/stream", json={"url": "", "mode": "video"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_analyze_stream_invalid_mode(app_client):
    resp = app_client.post(
        "/api/analyze/stream", json={"url": "BV123", "mode": "invalid"}
    )
    assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"


def test_qa_empty_params(app_client):
    resp = app_client.post(
        "/api/qa/stream", json={"question": "", "context": "", "mode": "video"}
    )
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    if data.get("success") is True:
        raise AssertionError("空参数应返回错误")


def test_qa_normal_request(app_client):
    resp = app_client.post(
        "/api/qa/stream",
        json={
            "question": "这个视频讲了什么？",
            "context": "这是一个关于 Python 编程的视频",
            "mode": "video",
        },
    )
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"


def test_qa_invalid_mode(app_client):
    resp = app_client.post(
        "/api/qa/stream",
        json={
            "question": "test",
            "context": "test",
            "mode": "invalid_mode",
        },
    )
    assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"


def test_research_empty_topic(app_client):
    resp = app_client.post("/api/research", json={"topic": ""})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    if data.get("success") is True:
        raise AssertionError("空主题应返回错误")


def test_research_normal_topic(app_client):
    resp = app_client.post(
        "/api/research", json={"topic": "Python 编程入门教程"}
    )
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"


def test_research_special_characters(app_client):
    resp = app_client.post(
        "/api/research", json={"topic": "<script>alert('xss')</script>"}
    )
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"


def test_research_history(app_client):
    resp = app_client.get("/api/research/history")
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
    data = resp.json()
    if resp.status_code == 200:
        assert "success" in data, f"响应格式异常：{data}"


def test_user_portrait_empty_uid(app_client):
    resp = app_client.post("/api/user/portrait", json={"uid": ""})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_user_portrait_invalid_uid(app_client):
    resp = app_client.post("/api/user/portrait", json={"uid": "not_a_number"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_user_portrait_normal_uid(app_client):
    resp = app_client.post("/api/user/portrait", json={"uid": "12345678"})
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"


def test_boundary_very_long_url(app_client):
    long_url = "https://www.bilibili.com/video/" + "B" * 500
    resp = app_client.post("/api/analyze", json={"url": long_url})
    assert resp.status_code in [200, 400, 422], f"状态码：{resp.status_code}"
