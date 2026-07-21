from pathlib import Path


def test_teacher_proxy_accepts_configured_textbook_upload_limit() -> None:
    nginx = Path("server/nginx/frontend.conf.template").read_text(encoding="utf-8")
    dockerfile = Path("server/Dockerfile.frontend").read_text(encoding="utf-8")
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "client_max_body_size ${CLIENT_MAX_BODY_SIZE};" in nginx
    assert "ENV CLIENT_MAX_BODY_SIZE=1m" in dockerfile
    assert 'CLIENT_MAX_BODY_SIZE: "${TEXTBOOK_UPLOAD_PROXY_MAX_MB:-210}m"' in compose
    assert compose.count("CLIENT_MAX_BODY_SIZE:") == 1
    assert "TEXTBOOK_UPLOAD_PROXY_MAX_MB=210" in Path(".env.example").read_text(encoding="utf-8")


def test_backend_host_port_defaults_to_loopback() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert '"${BACKEND_HOST_BIND:-127.0.0.1}:${BACKEND_HOST_PORT:-8000}:8000"' in compose
