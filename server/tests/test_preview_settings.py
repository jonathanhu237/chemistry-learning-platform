from server.app.infrastructure.settings import get_settings


def test_student_preview_allowed_origins_default_to_app_base_url(monkeypatch):
    monkeypatch.setenv("STUDENT_PREVIEW_APP_BASE_URL", "http://example.test:15173")
    monkeypatch.delenv("STUDENT_PREVIEW_ALLOWED_ORIGINS", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.student_preview_app_base_url == "http://example.test:15173"
    assert settings.student_preview_allowed_origins == ("http://example.test:15173",)

    get_settings.cache_clear()


def test_student_preview_allowed_origins_can_be_explicitly_overridden(monkeypatch):
    monkeypatch.setenv("STUDENT_PREVIEW_APP_BASE_URL", "http://example.test:15173")
    monkeypatch.setenv(
        "STUDENT_PREVIEW_ALLOWED_ORIGINS",
        "http://example.test:15173,http://localhost:15173",
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.student_preview_allowed_origins == (
        "http://example.test:15173",
        "http://localhost:15173",
    )

    get_settings.cache_clear()
