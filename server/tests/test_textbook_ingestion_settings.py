from __future__ import annotations

from server.app.infrastructure.settings import get_settings


def test_textbook_ocr_key_enables_ocr_without_entering_platform_settings(monkeypatch) -> None:
    monkeypatch.setenv("TEXTBOOK_OCR_API_KEY", "test-only-key")
    monkeypatch.setenv("TEXTBOOK_OCR_BASE_URL", "https://aigw.example/v1/")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.textbook_ocr_enabled is True
        assert settings.textbook_ocr_api_key == "test-only-key"
        assert settings.textbook_ocr_base_url == "https://aigw.example/v1"
        assert settings.textbook_ocr_model == "mineru"
    finally:
        get_settings.cache_clear()


def test_textbook_ocr_can_be_explicitly_disabled_with_key_present(monkeypatch) -> None:
    monkeypatch.setenv("TEXTBOOK_OCR_API_KEY", "test-only-key")
    monkeypatch.setenv("TEXTBOOK_OCR_ENABLED", "false")
    get_settings.cache_clear()
    try:
        assert get_settings().textbook_ocr_enabled is False
    finally:
        get_settings.cache_clear()
