def test_health_success(app_client):
    resp = app_client.get("/api/health")
    assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
    data = resp.json()
    assert data.get("success") is True, f"success 应为 True, 实际：{data}"
    assert data.get("status") == "running", f"status 应为 running, 实际：{data}"


def test_health_method_not_allowed(app_client):
    resp = app_client.post("/api/health")
    assert resp.status_code == 405, f"状态码应为 405, 实际：{resp.status_code}"


def test_settings_get(app_client):
    resp = app_client.get("/api/settings")
    assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
    data = resp.json()
    assert "success" in data or "data" in data, f"响应格式异常：{data}"


def test_settings_update_empty(app_client):
    resp = app_client.post("/api/settings", json={})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_settings_update_invalid_key(app_client):
    resp = app_client.post("/api/settings", json={"invalid_field": "value"})
    assert resp.status_code in [200, 422], f"状态码：{resp.status_code}"


def test_settings_update_dark_mode(app_client):
    resp = app_client.post("/api/settings", json={"dark_mode": True})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_settings_update_api_key_masking(app_client):
    resp = app_client.get("/api/settings")
    data = resp.json()
    if "data" in data:
        api_key = data["data"].get("openai_api_key", "")
        if api_key and len(api_key) > 10:
            raise AssertionError("API Key 不应明文显示")


def test_login_check(app_client):
    resp = app_client.get("/api/bilibili/login/check")
    assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_login_start(app_client):
    resp = app_client.post("/api/bilibili/login/start")
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_idempotency_health(app_client):
    resp1 = app_client.get("/api/health")
    resp2 = app_client.get("/api/health")
    resp3 = app_client.get("/api/health")
    assert resp1.status_code == resp2.status_code == resp3.status_code


def test_idempotency_settings(app_client):
    payload = {"dark_mode": True}
    resp1 = app_client.post("/api/settings", json=payload)
    resp2 = app_client.post("/api/settings", json=payload)
    assert resp1.status_code == resp2.status_code
