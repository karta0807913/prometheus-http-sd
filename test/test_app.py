from pathlib import Path


def test_target_non_exist_should_404(client):
    from prometheus_http_sd.config import config

    config.root_dir = str(Path(__file__).parent / "app_root")
    resp = client.get("/targets/no-exist")
    assert resp.status_code == 404


def test_app_target_with_parameters(client):
    from prometheus_http_sd.config import config
    import json

    config.root_dir = str(Path(__file__).parent / "app_root")

    response = client.get("/targets/echo_target?domain=example.com&info=test")
    assert response.status_code == 200
    body = json.loads(response.data.decode("utf-8"))
    assert body == [
        {
            "labels": {"domain": "example.com", "info": "test"},
            "targets": ["127.0.0.1:8080"],
        }
    ]
