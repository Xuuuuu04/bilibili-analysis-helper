def test_search_empty_keyword(app_client):
    resp = app_client.post("/api/search", json={"keyword": "", "mode": "video"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_search_normal_keyword(app_client):
    resp = app_client.post("/api/search", json={"keyword": "Python", "mode": "video"})
    assert resp.status_code == 200, f"状态码应为 200, 实际：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_search_invalid_mode(app_client):
    resp = app_client.post("/api/search", json={"keyword": "test", "mode": "invalid"})
    assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"


def test_search_special_characters(app_client):
    resp = app_client.post(
        "/api/search", json={"keyword": "<script>alert('xss')</script>", "mode": "video"}
    )
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_search_long_keyword(app_client):
    long_keyword = "A" * 1000
    resp = app_client.post("/api/search", json={"keyword": long_keyword, "mode": "video"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_video_info_invalid_url(app_client):
    resp = app_client.post("/api/video/info", json={"url": "invalid"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_video_info_empty_url(app_client):
    resp = app_client.post("/api/video/info", json={"url": ""})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_video_info_bvid_format(app_client):
    resp = app_client.post("/api/video/info", json={"url": "BV1234567890"})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_video_info_full_url(app_client):
    url = "https://www.bilibili.com/video/BV1234567890"
    resp = app_client.post("/api/video/info", json={"url": url})
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_popular_videos_get(app_client):
    resp = app_client.get("/api/video/popular")
    assert resp.status_code in [200, 400, 500], f"状态码：{resp.status_code}"
    data = resp.json()
    assert "success" in data, f"响应格式异常：{data}"


def test_image_proxy_invalid_domain(app_client):
    resp = app_client.get("/api/image-proxy?url=http://evil.com/image.jpg")
    assert resp.status_code in [400, 404, 500], f"状态码：{resp.status_code}"


def test_image_proxy_empty_url(app_client):
    resp = app_client.get("/api/image-proxy?url=")
    assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"


def test_boundary_unicode_keyword(app_client):
    resp = app_client.post(
        "/api/search", json={"keyword": "测试🔥🎉", "mode": "video"}
    )
    assert resp.status_code in [200, 400], f"状态码：{resp.status_code}"


def test_boundary_null_values(app_client):
    resp = app_client.post("/api/search", json={"keyword": None, "mode": "video"})
    assert resp.status_code in [400, 422], f"状态码：{resp.status_code}"
