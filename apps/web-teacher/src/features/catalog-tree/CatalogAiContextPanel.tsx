import { Alert, Button, Descriptions, Empty, Space, Tag, Typography } from "antd";

import type { CatalogNodeDetail, CatalogPointRagProbe, CatalogStaticEvidenceBinding } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { useCatalogPointAiContext, type CatalogMutations } from "./catalogTreeHooks";

const { Text, Title } = Typography;

function statusColor(status?: string | null) {
  if (status === "healthy" || status === "succeeded" || status === "synced" || status === "available_static_fallback" || status === "fresh") return "green";
  if (status === "failed" || status === "unavailable") return "red";
  if (status === "stale" || status === "stale_fallback_evidence") return "orange";
  if (status === "pending" || status === "running") return "gold";
  return "default";
}

function valueList(value: unknown) {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${key}: ${String(item ?? "-")}`);
}

function previewText(value: unknown) {
  return String(value || "").trim() || "-";
}

function EvidenceRow({ binding }: { binding: CatalogStaticEvidenceBinding }) {
  return (
    <div className="catalog-ai-evidence-row">
      <div>
        <Text strong copyable>
          {binding.chunk_id}
        </Text>
        <p>{binding.source_title || binding.source_file || binding.document_id || "-"}</p>
        <small>
          {[
            binding.page_number ? `page ${binding.page_number}` : "",
            binding.section_title || "",
            binding.content_type ? `type ${binding.content_type}` : "",
          ]
            .filter(Boolean)
            .join(" / ") || "-"}
        </small>
      </div>
      <Space wrap>
        <Tag>{binding.evidence_role}</Tag>
        <Tag color={statusColor(binding.selection_status)}>{binding.selection_status}</Tag>
        <Tag color={statusColor(binding.freshness_status)}>{binding.freshness_status}</Tag>
      </Space>
      <div className="catalog-ai-score-grid">
        <span>score {binding.score ?? "-"}</span>
        <span>rerank {binding.rerank_score ?? "-"}</span>
      </div>
      <Text type="secondary">{binding.text_preview || "-"}</Text>
    </div>
  );
}

function ProbeResult({ probe }: { probe?: CatalogPointRagProbe }) {
  if (!probe) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Run a dynamic RAG probe to inspect recall and rerank behavior." />;
  return (
    <div className="catalog-ai-probe-result">
      <Alert
        showIcon
        type={probe.ok ? "success" : "warning"}
        title={probe.ok ? "Dynamic RAG probe completed" : `Dynamic RAG probe stopped at ${probe.failed_stage || "unknown stage"}`}
        description={probe.reason || "Evidence was selected from the configured RAG pipeline."}
      />
      <Descriptions size="small" column={2}>
        <Descriptions.Item label="runtime">{String(probe.runtime_health?.status || "-")}</Descriptions.Item>
        <Descriptions.Item label="recall source">{probe.recall_source || "-"}</Descriptions.Item>
        <Descriptions.Item label="query status">{probe.query_strategy?.status || "-"}</Descriptions.Item>
        <Descriptions.Item label="fallback reason">{probe.query_strategy?.fallback_reason || "-"}</Descriptions.Item>
      </Descriptions>
      <div className="catalog-ai-split">
        <section>
          <Title level={5}>Generated queries</Title>
          {probe.generated_queries.length ? (
            <ol>
              {probe.generated_queries.map((query) => (
                <li key={query}>{query}</li>
              ))}
            </ol>
          ) : (
            <Text type="secondary">No query variants were generated.</Text>
          )}
        </section>
        <section>
          <Title level={5}>Candidate counts</Title>
          {valueList(probe.candidate_counts).map((line) => (
            <Tag key={line}>{line}</Tag>
          ))}
        </section>
      </div>
      <section>
        <Title level={5}>Final evidence</Title>
        {probe.final_evidence.length ? (
          <div className="catalog-ai-evidence-list">
            {probe.final_evidence.map((item, index) => (
              <div className="catalog-ai-probe-evidence" key={`${item.chunk_id || index}`}>
                <Text strong copyable>
                  {String(item.chunk_id || "-")}
                </Text>
                <Space wrap>
                  <Tag>{String(item.recall_source || item.source || "-")}</Tag>
                  <Tag>score {String(item.score ?? "-")}</Tag>
                  <Tag>rerank {String(item.rerank_score ?? "-")}</Tag>
                </Space>
                <Text type="secondary">{String(item.source_file || item.source_title || "-")}</Text>
                <p>{String(item.text_preview || "")}</p>
              </div>
            ))}
          </div>
        ) : (
          <Text type="secondary">No grounded evidence was returned.</Text>
        )}
      </section>
    </div>
  );
}

export function CatalogAiContextPanel({ detail, mutations }: { detail: CatalogNodeDetail; mutations: CatalogMutations }) {
  const nodeId = detail.node.node_id;
  const contextQuery = useCatalogPointAiContext(nodeId, detail.node.node_kind === "point");
  const probe = mutations.runRagProbe.data?.node_id === nodeId ? mutations.runRagProbe.data : undefined;
  const jobState = contextQuery.data?.job_state || detail.job_state;
  const evidenceState = jobState?.evidence_state;

  return (
    <section className="catalog-editor-section catalog-ai-context-panel">
      <div className="catalog-panel-title-row">
        <div>
          <Title level={4}>AI Context</Title>
          <Text type="secondary">Teacher-only diagnostics for static fallback evidence, dynamic RAG, and point context.</Text>
        </div>
        <Space wrap>
          <Button
            size="small"
            loading={mutations.triggerPointJob.isPending}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "rag-refresh" })}
          >
            Refresh RAG evidence
          </Button>
          <Button size="small" loading={mutations.triggerPointJob.isPending} onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "retry" })}>
            Retry failed job
          </Button>
          <Button size="small" type="primary" loading={mutations.runRagProbe.isPending} onClick={() => mutations.runRagProbe.mutate({ nodeId })}>
            Run RAG probe
          </Button>
        </Space>
      </div>
      <QueryState loading={contextQuery.isLoading} error={contextQuery.error} empty={!contextQuery.data}>
        {contextQuery.data ? (
          <>
            <section className="catalog-ai-band">
              <Title level={5}>Student-facing point content</Title>
              <Descriptions size="small" column={2} bordered>
                <Descriptions.Item label="node id">{contextQuery.data.node_id}</Descriptions.Item>
                <Descriptions.Item label="path">{contextQuery.data.catalog_path_text || "-"}</Descriptions.Item>
                <Descriptions.Item label="title">{contextQuery.data.point_title}</Descriptions.Item>
                <Descriptions.Item label="publication">{String(contextQuery.data.publication_state.content_status || "-")}</Descriptions.Item>
                <Descriptions.Item label="phenomenon">{previewText(contextQuery.data.student_facing_content.phenomenon_explanation)}</Descriptions.Item>
                <Descriptions.Item label="safety">{previewText(contextQuery.data.student_facing_content.safety_note)}</Descriptions.Item>
              </Descriptions>
              <div className="catalog-ai-equations">
                {(contextQuery.data.student_facing_content.reaction_equations || []).length ? (
                  contextQuery.data.student_facing_content.reaction_equations?.map((equation) => (
                    <Tag key={`${equation.row_order}-${equation.raw_text}`}>{equation.canonical_display || equation.raw_text}</Tag>
                  ))
                ) : (
                  <Text type="secondary">{previewText(contextQuery.data.student_facing_content.principle_text)}</Text>
                )}
              </div>
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>Static fallback evidence</Title>
                <Tag color={statusColor(contextQuery.data.static_evidence.status)}>{contextQuery.data.static_evidence.status}</Tag>
              </div>
              <Alert
                showIcon
                type={contextQuery.data.static_evidence.static_fallback_missing ? "info" : "success"}
                title={contextQuery.data.static_evidence.message}
                description="These chunk ids and rerank values are teacher diagnostics. They are not published to students."
              />
              {contextQuery.data.static_evidence.bindings.length ? (
                <div className="catalog-ai-evidence-list">
                  {contextQuery.data.static_evidence.bindings.map((binding) => (
                    <EvidenceRow binding={binding} key={`${binding.chunk_id}-${binding.evidence_role}`} />
                  ))}
                </div>
              ) : null}
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>Dynamic RAG probe</Title>
                <Tag color={statusColor(String(contextQuery.data.dynamic_rag.runtime_health?.status || ""))}>
                  {String(contextQuery.data.dynamic_rag.runtime_health?.status || "unknown")}
                </Tag>
              </div>
              <Alert showIcon type="info" title={contextQuery.data.dynamic_rag.note} />
              <ProbeResult probe={probe} />
            </section>

            <section className="catalog-ai-band">
              <Title level={5}>Teacher-only teaching notes</Title>
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label="node note">{contextQuery.data.teacher_only_notes.node_teacher_note || "-"}</Descriptions.Item>
                <Descriptions.Item label="point note">{contextQuery.data.teacher_only_notes.point_teacher_note || "-"}</Descriptions.Item>
              </Descriptions>
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>ES and evidence jobs</Title>
                <Space>
                  <Tag color={statusColor(jobState?.es_state?.sync_status)}>{jobState?.es_state?.sync_status || "no-es-state"}</Tag>
                  <Tag color={statusColor(evidenceState?.evidence_status)}>{evidenceState?.evidence_status || "missing"}</Tag>
                </Space>
              </div>
              <Descriptions size="small" column={2}>
                <Descriptions.Item label="ES action">{jobState?.es_state?.desired_action || "-"}</Descriptions.Item>
                <Descriptions.Item label="ES error">{jobState?.es_state?.last_error || "-"}</Descriptions.Item>
                <Descriptions.Item label="evidence mode">{evidenceState?.source_mode || "-"}</Descriptions.Item>
                <Descriptions.Item label="evidence error">{evidenceState?.latest_error || "-"}</Descriptions.Item>
              </Descriptions>
            </section>
          </>
        ) : null}
      </QueryState>
    </section>
  );
}
