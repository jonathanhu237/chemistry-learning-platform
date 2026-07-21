import type { AIConfiguration, AIConfigurationUpdate } from "../../api/settings";

type TextbookRAGUpdate = NonNullable<AIConfigurationUpdate["textbook_rag"]>;

export type AIConfigurationFormValues = Pick<
  AIConfigurationUpdate,
  "provider" | "base_url" | "model" | "connection_check_interval_minutes"
> & {
  api_key?: string;
  textbook_rag?: TextbookRAGUpdate;
};

const DEFAULT_EMBEDDING_PROVIDER = "openai_compatible";
const DEFAULT_EMBEDDING_PROTOCOL = "openai_embeddings";
const DEFAULT_RERANK_PROVIDER = "openai_compatible";
const DEFAULT_RERANK_PROTOCOL = "auto";
const DEFAULT_OCR_PROVIDER = "mineru";
const DEFAULT_OCR_PROTOCOL = "openai_chat_completions";

function text(value: unknown, fallback = "") {
  const normalized = String(value ?? "").trim();
  return normalized || fallback;
}

function number(value: unknown, fallback: number) {
  if (value === null || value === undefined || value === "") return fallback;
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : fallback;
}

export function aiConfigurationFormValues(config: AIConfiguration): AIConfigurationFormValues {
  const textbookRag = config.textbook_rag;
  return {
    provider: text(config.chat_provider?.provider ?? config.provider, "openai"),
    base_url: config.base_url,
    model: config.model,
    connection_check_interval_minutes: config.connection_check_interval_minutes,
    api_key: "",
    textbook_rag: {
      enabled: textbookRag?.enabled ?? false,
      elasticsearch_url: textbookRag?.elasticsearch_url ?? "",
      index_name: textbookRag?.index_name ?? "",
      ocr: {
        enabled: textbookRag?.ocr?.enabled ?? false,
        provider: text(textbookRag?.ocr?.provider, DEFAULT_OCR_PROVIDER),
        protocol: text(textbookRag?.ocr?.protocol, DEFAULT_OCR_PROTOCOL),
        base_url: textbookRag?.ocr?.base_url ?? "",
        endpoint: textbookRag?.ocr?.endpoint ?? "",
        model: textbookRag?.ocr?.model ?? "",
        api_key: "",
        timeout_seconds: number(textbookRag?.ocr?.timeout_seconds, 90),
        concurrency: number(textbookRag?.ocr?.concurrency, 2),
        max_retries: number(textbookRag?.ocr?.max_retries, 3),
        max_output_tokens: number(textbookRag?.ocr?.max_output_tokens, 4096),
        render_dpi: number(textbookRag?.ocr?.render_dpi, 160),
      },
      embedding: {
        provider: text(textbookRag?.embedding?.provider, DEFAULT_EMBEDDING_PROVIDER),
        protocol: text(textbookRag?.embedding?.protocol, DEFAULT_EMBEDDING_PROTOCOL),
        base_url: textbookRag?.embedding?.base_url ?? "",
        endpoint: textbookRag?.embedding?.endpoint ?? "",
        model: textbookRag?.embedding?.model ?? "",
        api_key: "",
        send_dimensions: textbookRag?.embedding?.send_dimensions ?? true,
        batch_size: number(textbookRag?.embedding?.batch_size, 16),
      },
      rerank: {
        provider: text(textbookRag?.rerank?.provider, DEFAULT_RERANK_PROVIDER),
        protocol: text(textbookRag?.rerank?.protocol, DEFAULT_RERANK_PROTOCOL),
        base_url: textbookRag?.rerank?.base_url ?? "",
        endpoint: textbookRag?.rerank?.endpoint ?? "",
        model: textbookRag?.rerank?.model ?? "",
        api_key: "",
      },
      embedding_dimension: number(textbookRag?.embedding_dimension, 1024),
      keyword_top_k: number(textbookRag?.keyword_top_k, 16),
      vector_top_k: number(textbookRag?.vector_top_k, 24),
      rerank_top_k: number(textbookRag?.rerank_top_k, 9),
      final_top_k: number(textbookRag?.final_top_k, 5),
      min_rerank_score: number(textbookRag?.min_rerank_score, 0),
      timeout_seconds: number(textbookRag?.timeout_seconds, 8),
    },
  };
}

export function aiConfigurationUpdateFromForm(
  values: AIConfigurationFormValues,
  current: AIConfiguration,
): AIConfigurationUpdate {
  const chatProvider = text(
    values.provider,
    text(current.chat_provider?.provider ?? current.provider, "openai"),
  );
  const payload: AIConfigurationUpdate = {
    provider: chatProvider,
    base_url: text(values.base_url),
    model: text(values.model),
    connection_check_interval_minutes: number(values.connection_check_interval_minutes, 30),
    enabled_features: current.enabled_features,
    chat_provider: {
      provider: chatProvider,
      base_url: text(values.base_url),
      model: text(values.model),
    },
  };
  const chatApiKey = text(values.api_key);
  if (chatApiKey) {
    payload.api_key = chatApiKey;
    payload.chat_provider = { ...payload.chat_provider!, api_key: chatApiKey };
  }

  const textbookRag = values.textbook_rag;
  if (!textbookRag) return payload;

  const ocrApiKey = text(textbookRag.ocr?.api_key);
  const embeddingApiKey = text(textbookRag.embedding?.api_key);
  const rerankApiKey = text(textbookRag.rerank?.api_key);
  payload.textbook_rag = {
    enabled: Boolean(textbookRag.enabled),
    elasticsearch_url: text(textbookRag.elasticsearch_url),
    index_name: text(textbookRag.index_name),
    ocr: {
      enabled: Boolean(textbookRag.ocr?.enabled),
      provider: text(textbookRag.ocr?.provider, DEFAULT_OCR_PROVIDER),
      protocol: text(textbookRag.ocr?.protocol, DEFAULT_OCR_PROTOCOL),
      base_url: text(textbookRag.ocr?.base_url),
      endpoint: text(textbookRag.ocr?.endpoint),
      model: text(textbookRag.ocr?.model),
      timeout_seconds: number(textbookRag.ocr?.timeout_seconds, 90),
      concurrency: number(textbookRag.ocr?.concurrency, 2),
      max_retries: number(textbookRag.ocr?.max_retries, 3),
      max_output_tokens: number(textbookRag.ocr?.max_output_tokens, 4096),
      render_dpi: number(textbookRag.ocr?.render_dpi, 160),
      ...(ocrApiKey ? { api_key: ocrApiKey } : {}),
    },
    embedding: {
      provider: text(textbookRag.embedding?.provider, DEFAULT_EMBEDDING_PROVIDER),
      protocol: text(textbookRag.embedding?.protocol, DEFAULT_EMBEDDING_PROTOCOL),
      base_url: text(textbookRag.embedding?.base_url),
      endpoint: text(textbookRag.embedding?.endpoint),
      model: text(textbookRag.embedding?.model),
      send_dimensions: textbookRag.embedding?.send_dimensions ?? true,
      batch_size: number(textbookRag.embedding?.batch_size, 16),
      ...(embeddingApiKey ? { api_key: embeddingApiKey } : {}),
    },
    rerank: {
      provider: text(textbookRag.rerank?.provider, DEFAULT_RERANK_PROVIDER),
      protocol: text(textbookRag.rerank?.protocol, DEFAULT_RERANK_PROTOCOL),
      base_url: text(textbookRag.rerank?.base_url),
      endpoint: text(textbookRag.rerank?.endpoint),
      model: text(textbookRag.rerank?.model),
      ...(rerankApiKey ? { api_key: rerankApiKey } : {}),
    },
    embedding_dimension: number(textbookRag.embedding_dimension, 1024),
    keyword_top_k: number(textbookRag.keyword_top_k, 16),
    vector_top_k: number(textbookRag.vector_top_k, 24),
    rerank_top_k: number(textbookRag.rerank_top_k, 9),
    final_top_k: number(textbookRag.final_top_k, 5),
    min_rerank_score: number(textbookRag.min_rerank_score, 0),
    timeout_seconds: number(textbookRag.timeout_seconds, 8),
  };
  return payload;
}
