from __future__ import annotations

from server.app.domains.platform.settings import TextbookRAGConfigurationUpdate
from server.app.infrastructure.settings import Settings, get_settings


def test_textbook_rag_defaults_preserve_the_legacy_seed_index_name() -> None:
    assert Settings.textbook_rag_elasticsearch_index == "canonical-rag-chunks-qwen-v1"
    assert TextbookRAGConfigurationUpdate().index_name == "canonical-rag-chunks-qwen-v1"


def test_textbook_ocr_key_enables_ocr_without_entering_platform_settings(monkeypatch) -> None:
    monkeypatch.setenv("TEXTBOOK_OCR_API_KEY", "test-only-key")
    monkeypatch.setenv("TEXTBOOK_OCR_BASE_URL", "https://aigw.example/v1/")
    monkeypatch.setenv("TEXTBOOK_OCR_MODEL", "mineru")
    monkeypatch.setenv("TEXTBOOK_OCR_MAX_OUTPUT_TOKENS", "8192")
    monkeypatch.setenv("TEXTBOOK_EMBEDDING_BATCH_SIZE", "32")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.textbook_ocr_enabled is True
        assert settings.textbook_ocr_api_key == "test-only-key"
        assert settings.textbook_ocr_base_url == "https://aigw.example/v1"
        assert settings.textbook_ocr_model == "mineru"
        assert settings.textbook_ocr_provider == "mineru"
        assert settings.textbook_ocr_protocol == "openai_chat_completions"
        assert settings.textbook_ocr_max_output_tokens == 8192
        assert settings.textbook_embedding_batch_size == 32
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
