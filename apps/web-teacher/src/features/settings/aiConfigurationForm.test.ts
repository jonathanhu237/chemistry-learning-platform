import { describe, expect, it } from "vitest";

import type { AIConfiguration } from "../../api/settings";
import { aiConfigurationFormValues, aiConfigurationUpdateFromForm } from "./aiConfigurationForm";

function configuration(): AIConfiguration {
  return {
    provider: "openai_compatible",
    base_url: "https://chat.example/v1",
    model: "chat-model",
    connection_check_interval_minutes: 30,
    api_key_configured: true,
    api_key_fingerprint: "sk-…1234",
    enabled_features: {
      rag_access_enabled: true,
      student_ai_assistant: true,
      student_learning_analytics: false,
      question_bank_assistant: true,
      teacher_learning_analytics: false,
    },
    status: {
      ready: true,
      message: "ready",
      effective_mode: "external",
      connectivity_status: "connected",
      check_interval_minutes: 30,
      recent_request_count: 0,
      recent_error_count: 0,
      usage_buckets: [],
      usage_trends: {},
    },
    student_ai_policy: {
      active: true,
      version: "v1",
      model: "chat-model",
      coverage: [],
      recent_decision_count: 0,
      invalid_decision_count: 0,
      outcomes: [],
    },
    textbook_rag: {
      enabled: true,
      elasticsearch_url: "http://elasticsearch:9200",
      index_name: "chemistry-textbooks-bge-v1",
      ocr: {
        role: "textbook_ocr",
        enabled: true,
        provider: "mineru",
        protocol: "openai_chat_completions",
        base_url: "https://ocr.example/v1",
        endpoint: "/chat/completions",
        model: "mineru-model",
        api_key_configured: true,
        api_key_fingerprint: "ocr-…1234",
        timeout_seconds: 120,
        concurrency: 4,
        max_retries: 5,
        max_output_tokens: 8192,
        render_dpi: 180,
      },
      embedding: {
        role: "textbook_embedding",
        provider: "openai_compatible",
        protocol: "openai_embeddings",
        base_url: "https://embedding.example/v1",
        endpoint: "/embeddings",
        model: "bge-m3",
        api_key_configured: true,
        api_key_fingerprint: "emb-…1234",
        send_dimensions: false,
        batch_size: 10,
      },
      rerank: {
        role: "textbook_rerank",
        provider: "openai_compatible",
        protocol: "auto",
        base_url: "https://rerank.example/v1",
        endpoint: "/rerank",
        model: "bge-reranker-v2-m3",
        api_key_configured: true,
        api_key_fingerprint: "rank-…1234",
      },
      embedding_dimension: 1024,
      keyword_top_k: 16,
      vector_top_k: 24,
      rerank_top_k: 9,
      final_top_k: 5,
      min_rerank_score: 0,
      timeout_seconds: 10,
    },
    can_edit: true,
  };
}

describe("AI configuration form mapping", () => {
  it("initializes every provider setting while keeping stored secrets out of the form", () => {
    const values = aiConfigurationFormValues(configuration());

    expect(values.provider).toBe("openai_compatible");
    expect(values.textbook_rag).toMatchObject({
      index_name: "chemistry-textbooks-bge-v1",
      ocr: {
        provider: "mineru",
        protocol: "openai_chat_completions",
        endpoint: "/chat/completions",
        api_key: "",
        concurrency: 4,
        max_output_tokens: 8192,
      },
      embedding: {
        provider: "openai_compatible",
        protocol: "openai_embeddings",
        endpoint: "/embeddings",
        model: "bge-m3",
        api_key: "",
        send_dimensions: false,
        batch_size: 10,
      },
      rerank: {
        provider: "openai_compatible",
        protocol: "auto",
        endpoint: "/rerank",
        model: "bge-reranker-v2-m3",
        api_key: "",
      },
    });
  });

  it("submits protocol controls and newly entered role secrets", () => {
    const current = configuration();
    const values = aiConfigurationFormValues(current);
    values.textbook_rag!.ocr.api_key = "new-ocr-key";
    values.textbook_rag!.embedding.api_key = "new-embedding-key";
    values.textbook_rag!.rerank.api_key = "new-rerank-key";

    const payload = aiConfigurationUpdateFromForm(values, current);

    expect(payload.provider).toBe("openai_compatible");
    expect(payload.chat_provider?.provider).toBe("openai_compatible");
    expect(payload.textbook_rag).toMatchObject({
      ocr: {
        provider: "mineru",
        protocol: "openai_chat_completions",
        endpoint: "/chat/completions",
        api_key: "new-ocr-key",
        max_output_tokens: 8192,
      },
      embedding: {
        provider: "openai_compatible",
        protocol: "openai_embeddings",
        endpoint: "/embeddings",
        send_dimensions: false,
        batch_size: 10,
        api_key: "new-embedding-key",
      },
      rerank: {
        provider: "openai_compatible",
        protocol: "auto",
        endpoint: "/rerank",
        api_key: "new-rerank-key",
      },
      min_rerank_score: 0,
    });
  });

  it("omits blank secrets so the backend can retain configured credentials", () => {
    const current = configuration();
    const payload = aiConfigurationUpdateFromForm(aiConfigurationFormValues(current), current);

    expect(payload).not.toHaveProperty("api_key");
    expect(payload.textbook_rag?.ocr).not.toHaveProperty("api_key");
    expect(payload.textbook_rag?.embedding).not.toHaveProperty("api_key");
    expect(payload.textbook_rag?.rerank).not.toHaveProperty("api_key");
  });

  it("submits blank endpoints explicitly while still omitting blank secrets", () => {
    const current = configuration();
    const values = aiConfigurationFormValues(current);
    values.textbook_rag!.ocr.endpoint = "";
    values.textbook_rag!.embedding.endpoint = "";
    values.textbook_rag!.rerank.endpoint = "";

    const payload = aiConfigurationUpdateFromForm(values, current);

    expect(payload.textbook_rag?.ocr.endpoint).toBe("");
    expect(payload.textbook_rag?.embedding.endpoint).toBe("");
    expect(payload.textbook_rag?.rerank.endpoint).toBe("");
    expect(payload.textbook_rag?.ocr).not.toHaveProperty("api_key");
    expect(payload.textbook_rag?.embedding).not.toHaveProperty("api_key");
    expect(payload.textbook_rag?.rerank).not.toHaveProperty("api_key");
  });
});
