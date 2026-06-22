import { useEffect, useMemo, useState } from "react";
import type { MouseEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { DownloadOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { App as AntApp, Button, Card, Drawer, Empty, Popover, Select, Space, Statistic, Table, Tabs, Tag, Tooltip, Typography } from "antd";
import type { TableColumnsType } from "antd";
import dayjs from "dayjs";

import type { ClassItem } from "../../api/classes";
import type { Experiment } from "../../api/experiments";
import type {
  AnalyticsDashboard,
  AnalyticsExperimentGroup,
  AnalyticsExperimentGroupState,
  AnalyticsExperimentState,
  StudentAttempt,
  StudentReport,
  TeacherLatestPosttestReport,
  TeacherReportAiContent,
} from "../../api/analytics";
import { getAuthToken } from "../../api/auth";
import { api, apiBase } from "../../api/http";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";

const { Text } = Typography;

type MatrixRow = AnalyticsDashboard["matrix"][number];
type DetailTarget =
  | { kind: "student"; studentId: string; reportSessionId?: string }
  | { kind: "family"; studentId: string; familyId: string }
  | { kind: "experiment"; studentId: string; experimentId: string };

export function AnalyticsPage() {
  const { message } = AntApp.useApp();
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const [classId, setClassId] = useState<string>();
  const [detailTarget, setDetailTarget] = useState<DetailTarget | null>(null);
  const [exporting, setExporting] = useState(false);
  const activeClassId = classId || classes.data?.[0]?.id;
  const dashboard = useQuery({
    queryKey: ["analytics-dashboard", activeClassId],
    queryFn: () => api<AnalyticsDashboard>(`/api/admin/analytics/classes/${activeClassId}/dashboard`),
    enabled: Boolean(activeClassId),
  });
  const selectedStudentId = detailTarget?.studentId;
  const studentReport = useQuery({
    queryKey: ["student-report", activeClassId, selectedStudentId],
    queryFn: () => api<StudentReport>(`/api/admin/analytics/classes/${activeClassId}/students/${selectedStudentId}`),
    enabled: Boolean(activeClassId && selectedStudentId),
  });

  const exportReport = async () => {
    if (!activeClassId) return;
    setExporting(true);
    try {
      const response = await fetch(`${apiBase}/api/admin/analytics/classes/${activeClassId}/export`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      if (!response.ok) {
        message.error("导出失败");
        return;
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const disposition = response.headers.get("Content-Disposition") || "";
      const fileName = disposition.match(/filename="([^"]+)"/)?.[1] || `class-${activeClassId}-learning-analytics.csv`;
      link.href = url;
      link.download = fileName;
      link.click();
      URL.revokeObjectURL(url);
      message.success("已导出学情分数");
    } catch {
      message.error("导出失败");
    } finally {
      setExporting(false);
    }
  };

  const matrixColumns: TableColumnsType<MatrixRow> = useMemo(() => {
    const experiments = dashboard.data?.experiments || [];
    const experimentsById = new Map(experiments.map((experiment) => [experiment.id, experiment]));
    const experimentGroups = dashboard.data?.experiment_groups || groupExperiments(experiments);
    return [
      {
        title: "学生",
        dataIndex: "student_name",
        fixed: "left",
        width: 190,
        render: (_value: unknown, row: MatrixRow) => (
          <Space orientation="vertical" size={1} className="analytics-student-cell">
            <Text strong>{row.student_name || row.student_id}</Text>
            <Text type="secondary">{row.student_id}</Text>
          </Space>
        ),
      },
      {
        title: "均分",
        dataIndex: "average_score",
        fixed: "left",
        width: 92,
        sorter: (a: MatrixRow, b: MatrixRow) => (a.average_score || 0) - (b.average_score || 0),
        render: (value: number | undefined) => <ScorePill score={value ?? 0} />,
      },
      ...experimentGroups.map((group) => ({
        title: <FamilyColumnTitle group={group} />,
        width: 164,
        align: "center" as const,
        render: (_value: unknown, row: MatrixRow) => (
          <FamilyScoreCell
            group={group}
            experimentsById={experimentsById}
            student={row}
            state={row.experiment_groups?.[group.id]}
            onOpen={(event) => {
              event.stopPropagation();
              setDetailTarget({ kind: "family", studentId: row.student_id, familyId: group.id });
            }}
          />
        ),
      })),
    ];
  }, [dashboard.data?.experiment_groups, dashboard.data?.experiments]);

  const experimentGroups = dashboard.data?.experiment_groups || groupExperiments(dashboard.data?.experiments || []);
  const experimentsById = useMemo(
    () => new Map((dashboard.data?.experiments || []).map((experiment) => [experiment.id, experiment])),
    [dashboard.data?.experiments],
  );
  const groupCount = experimentGroups.length;
  const tableScrollX = Math.max(980, 282 + groupCount * 164);
  const selectedStudent = dashboard.data?.matrix.find((row) => row.student_id === selectedStudentId) || null;
  const selectedFamily =
    detailTarget?.kind === "family" ? experimentGroups.find((group) => group.id === detailTarget.familyId) || null : null;
  const selectedFamilyState =
    detailTarget?.kind === "family" && selectedStudent ? selectedStudent.experiment_groups?.[detailTarget.familyId] : undefined;
  const selectedExperiment =
    detailTarget?.kind === "experiment"
      ? dashboard.data?.experiments.find((experiment) => experiment.id === detailTarget.experimentId) || null
      : null;
  const selectedExperimentState =
    detailTarget?.kind === "experiment" && selectedStudent
      ? selectedStudent.experiments[detailTarget.experimentId]
      : undefined;

  return (
    <Space orientation="vertical" size={18} className="full analytics-page">
      <PageTitle
        title="学情分析"
        description="班级实验组分数总览"
        extra={
          <Button icon={<DownloadOutlined />} loading={exporting} onClick={() => void exportReport()}>
            导出分数
          </Button>
        }
      />
      <Card className="analytics-toolbar-card">
        <Space wrap size={12}>
          <Select
            placeholder="选择班级"
            style={{ width: 280 }}
            value={activeClassId}
            onChange={(value) => {
              setClassId(value);
              setDetailTarget(null);
            }}
            options={(classes.data || []).map((item) => ({ value: item.id, label: item.class_name }))}
          />
          <Text type="secondary">未答题实验按 50 分计入。</Text>
        </Space>
      </Card>
      <QueryState loading={dashboard.isLoading} error={dashboard.error} empty={!activeClassId}>
        <div className="stat-grid analytics-stat-grid">
          <Card>
            <Statistic title="班级人数" value={dashboard.data?.metrics.class_size || 0} />
          </Card>
          <Card>
            <Statistic title="班级均分" value={dashboard.data?.metrics.average_score || 0} precision={1} suffix="分" />
          </Card>
          <Card>
            <Statistic title="实验组" value={dashboard.data?.metrics.published_experiment_groups || groupCount} suffix="组" />
          </Card>
          <Card>
            <Statistic title="已有答题学生" value={dashboard.data?.metrics.active_students || 0} />
          </Card>
        </div>
        <Card
          title="学生实验组分数"
          extra={<Text type="secondary">{dashboard.data?.matrix.length || 0} 名学生</Text>}
          className="analytics-matrix-card"
        >
          <Table
            rowKey="student_id"
            size="small"
            scroll={{ x: tableScrollX, y: "calc(100vh - 390px)" }}
            dataSource={dashboard.data?.matrix || []}
            columns={matrixColumns}
            pagination={{ pageSize: 20, showSizeChanger: false }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无学生" /> }}
            onRow={(record) => ({
              onClick: () => setDetailTarget({ kind: "student", studentId: record.student_id }),
            })}
          />
        </Card>
      </QueryState>
      <StudentReportDrawer
        open={detailTarget?.kind === "student"}
        studentId={selectedStudentId}
        studentName={selectedStudent?.student_name}
        report={studentReport.data}
        loading={studentReport.isLoading}
        error={studentReport.error}
        initialReportSessionId={detailTarget?.kind === "student" ? detailTarget.reportSessionId : undefined}
        onClose={() => setDetailTarget(null)}
      />
      <FamilyDetailDrawer
        open={detailTarget?.kind === "family"}
        student={selectedStudent}
        group={selectedFamily}
        state={selectedFamilyState}
        experimentsById={experimentsById}
        report={studentReport.data}
        loading={studentReport.isLoading}
        error={studentReport.error}
        onClose={() => setDetailTarget(null)}
        onOpenExperiment={(experimentId) => {
          if (!selectedStudentId) return;
          setDetailTarget({ kind: "experiment", studentId: selectedStudentId, experimentId });
        }}
        onOpenReport={(reportSessionId) => {
          if (!selectedStudentId) return;
          setDetailTarget({ kind: "student", studentId: selectedStudentId, reportSessionId });
        }}
      />
      <ExperimentEvidenceDrawer
        open={detailTarget?.kind === "experiment"}
        student={selectedStudent}
        experiment={selectedExperiment}
        state={selectedExperimentState}
        report={studentReport.data}
        loading={studentReport.isLoading}
        error={studentReport.error}
        onClose={() => setDetailTarget(null)}
      />
    </Space>
  );
}

function FamilyColumnTitle({ group }: { group: AnalyticsExperimentGroup }) {
  return (
    <Tooltip title={`${group.title} · ${group.experiment_count} 个实验`}>
      <div className="analytics-experiment-title">
        <strong>{group.title}</strong>
        <span>{group.experiment_count} 个实验</span>
      </div>
    </Tooltip>
  );
}

function FamilyScoreCell({
  group,
  experimentsById,
  student,
  state,
  onOpen,
}: {
  group: AnalyticsExperimentGroup;
  experimentsById: Map<string, Experiment>;
  student: MatrixRow;
  state?: AnalyticsExperimentGroupState;
  onOpen: (event: MouseEvent<HTMLButtonElement>) => void;
}) {
  const score = state?.mastery_score ?? 50;
  return (
    <span className="analytics-family-cell">
      <ScorePill score={score} muted={!state?.has_mastery} evidenceCount={state?.evidence_count} onClick={onOpen} />
      <Popover
        placement="right"
        trigger={["hover", "click"]}
        content={<FamilyPreview group={group} experimentsById={experimentsById} student={student} state={state} />}
      >
        <button
          className="analytics-family-info-button"
          type="button"
          aria-label={`${group.title}实验明细`}
          onClick={(event) => event.stopPropagation()}
        >
          <InfoCircleOutlined />
        </button>
      </Popover>
    </span>
  );
}

function FamilyPreview({
  group,
  experimentsById,
  student,
  state,
}: {
  group: AnalyticsExperimentGroup;
  experimentsById: Map<string, Experiment>;
  student: MatrixRow;
  state?: AnalyticsExperimentGroupState;
}) {
  const rows = group.experiment_ids
    .flatMap((experimentId) => {
      const experiment = experimentsById.get(experimentId);
      return experiment ? [{ experiment, state: student.experiments[experimentId] }] : [];
    })
    .sort((a, b) => (a.state?.mastery_score ?? 50) - (b.state?.mastery_score ?? 50));
  return (
    <div className="analytics-family-preview">
      <div className="analytics-family-preview-head">
        <strong>{group.title}</strong>
        <Text type="secondary">
          族均分 {formatScore(state?.mastery_score ?? 50)} · 有证据 {state?.evidence_experiment_count ?? 0}/{group.experiment_count}
        </Text>
      </div>
      <div className="analytics-family-preview-list">
        {rows.map(({ experiment, state: experimentState }) => (
          <div className={`analytics-family-preview-row ${experimentState?.has_mastery ? "" : "is-default"}`} key={experiment.id}>
            <span>{cleanExperimentTitle(experiment.title)}</span>
            <strong>{formatScore(experimentState?.mastery_score ?? 50)}</strong>
            {!experimentState?.has_mastery ? <em>默认 50</em> : null}
          </div>
        ))}
      </div>
      <Text type="secondary">未答题实验按 50 分计入。</Text>
    </div>
  );
}

function StudentReportDrawer({
  open,
  studentId,
  studentName,
  report,
  loading,
  error,
  initialReportSessionId,
  onClose,
}: {
  open: boolean;
  studentId?: string;
  studentName?: string;
  report?: StudentReport;
  loading: boolean;
  error: unknown;
  initialReportSessionId?: string;
  onClose: () => void;
}) {
  const reports = report?.posttest_reports?.length
    ? report.posttest_reports
    : report?.latest_posttest_report
    ? [report.latest_posttest_report]
    : [];
  const [selectedSessionId, setSelectedSessionId] = useState<string>();
  useEffect(() => {
    if (!open) return;
    const nextSessionId = initialReportSessionId || reports[0]?.session_id;
    setSelectedSessionId(nextSessionId);
  }, [initialReportSessionId, open, report]);
  const selectedReport = reports.find((item) => item.session_id === selectedSessionId) || reports[0] || null;
  return (
    <Drawer
      title={`${studentName || studentId || "学生"} · 报告中心`}
      size={720}
      open={open}
      onClose={onClose}
      destroyOnHidden
    >
      <QueryState loading={loading} error={error}>
        {selectedReport ? (
          <Space orientation="vertical" size={16} className="full analytics-drawer-content">
            <Select
              className="analytics-report-select"
              value={selectedReport.session_id}
              onChange={setSelectedSessionId}
              options={reports.map((item) => ({ value: item.session_id, label: reportOptionLabel(item) }))}
            />
            <div className="analytics-report-summary">
              <Statistic title="后测得分" value={selectedReport.score ?? 0} precision={1} suffix="分" />
              <Statistic title="正确题数" value={selectedReport.correct_count} suffix={`/ ${selectedReport.total_count}`} />
              <div>
                <Text type="secondary">完成时间</Text>
                <strong>{formatDate(selectedReport.completed_at)}</strong>
              </div>
            </div>
            <section className="analytics-drawer-section">
              <Text type="secondary">本轮实验</Text>
              <Space size={6} wrap>
                {selectedReport.experiments.map((experiment) => (
                  <Tag key={experiment.id}>{cleanExperimentTitle(String(experiment.title || experiment.code || experiment.id))}</Tag>
                ))}
              </Space>
            </section>
            <AiContentCard title="学习总结" value={selectedReport.ai_summary} />
            <AiContentCard title="错题讲解" value={selectedReport.ai_mistake_explanation} />
            <section className="analytics-drawer-section">
              <div className="analytics-section-title">
                <strong>错题明细</strong>
                <Text type="secondary">{selectedReport.wrong_answers.length} 题</Text>
              </div>
              <AttemptTable
                attempts={selectedReport.wrong_answers}
                emptyText="本次后测没有错题"
                pagination={selectedReport.wrong_answers.length > 5 ? { pageSize: 5, showSizeChanger: false } : false}
              />
            </section>
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该学生暂无已完成后测报告" />
        )}
      </QueryState>
    </Drawer>
  );
}

function FamilyDetailDrawer({
  open,
  student,
  group,
  state,
  experimentsById,
  report,
  loading,
  error,
  onClose,
  onOpenExperiment,
  onOpenReport,
}: {
  open: boolean;
  student: MatrixRow | null;
  group: AnalyticsExperimentGroup | null;
  state?: AnalyticsExperimentGroupState;
  experimentsById: Map<string, Experiment>;
  report?: StudentReport;
  loading: boolean;
  error: unknown;
  onClose: () => void;
  onOpenExperiment: (experimentId: string) => void;
  onOpenReport: (reportSessionId: string) => void;
}) {
  const experimentRows = (group?.experiment_ids || [])
    .map((experimentId) => ({
      experiment: experimentsById.get(experimentId),
      state: student?.experiments[experimentId],
    }))
    .filter((row): row is { experiment: Experiment; state: AnalyticsExperimentState | undefined } => Boolean(row.experiment))
    .sort((a, b) => (a.state?.mastery_score ?? 50) - (b.state?.mastery_score ?? 50));
  const relatedReports = (report?.posttest_reports || []).filter((item) =>
    item.experiments.some((experiment) => group?.experiment_ids.includes(experiment.id)),
  );
  const lowestExperiment =
    state?.lowest_experiment_id && experimentsById.get(state.lowest_experiment_id)
      ? experimentsById.get(state.lowest_experiment_id)
      : experimentRows[0]?.experiment;
  return (
    <Drawer
      title={`${student?.student_name || student?.student_id || "学生"} · ${group?.title || "实验组"}`}
      size={780}
      open={open}
      onClose={onClose}
      destroyOnHidden
    >
      <QueryState loading={loading} error={error}>
        {group ? (
          <Space orientation="vertical" size={16} className="full analytics-drawer-content">
            <div className="analytics-evidence-summary">
              <div>
                <Text type="secondary">族均分</Text>
                <ScorePill score={state?.mastery_score ?? 50} muted={!state?.has_mastery} evidenceCount={state?.evidence_count} />
              </div>
              <div>
                <Text type="secondary">有证据实验</Text>
                <strong>
                  {state?.evidence_experiment_count ?? 0} / {group.experiment_count}
                </strong>
              </div>
              <div>
                <Text type="secondary">最低实验</Text>
                <strong>{lowestExperiment ? cleanExperimentTitle(lowestExperiment.title) : "-"}</strong>
              </div>
            </div>
            <section className="analytics-drawer-section">
              <div className="analytics-section-title">
                <strong>实验分数</strong>
                <Text type="secondary">未答题实验按 50 分计入</Text>
              </div>
              <Table
                rowKey={(row) => row.experiment.id}
                size="small"
                dataSource={experimentRows}
                pagination={false}
                columns={[
                  {
                    title: "实验",
                    render: (_value, row) => (
                      <Space orientation="vertical" size={2} className="full">
                        <Text strong>{cleanExperimentTitle(row.experiment.title)}</Text>
                        <Text type="secondary">{row.experiment.code}</Text>
                      </Space>
                    ),
                  },
                  {
                    title: "mastery",
                    width: 96,
                    render: (_value, row) => (
                      <ScorePill
                        score={row.state?.mastery_score ?? 50}
                        muted={!row.state?.has_mastery}
                        evidenceCount={row.state?.evidence_count}
                      />
                    ),
                  },
                  {
                    title: "证据",
                    width: 84,
                    render: (_value, row) => <Text>{row.state?.evidence_count ?? 0} 条</Text>,
                  },
                  {
                    title: "操作",
                    width: 92,
                    render: (_value, row) => (
                      <Button size="small" onClick={() => onOpenExperiment(row.experiment.id)}>
                        答题证据
                      </Button>
                    ),
                  },
                ]}
              />
            </section>
            <section className="analytics-drawer-section">
              <div className="analytics-section-title">
                <strong>相关后测报告</strong>
                <Text type="secondary">{relatedReports.length} 份</Text>
              </div>
              {relatedReports.length ? (
                <Space orientation="vertical" size={8} className="full">
                  {relatedReports.map((item) => (
                    <button className="analytics-report-link" type="button" key={item.session_id} onClick={() => onOpenReport(item.session_id)}>
                      <span>{reportOptionLabel(item)}</span>
                      <strong>{formatScore(item.score ?? 0)} 分</strong>
                    </button>
                  ))}
                </Space>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无包含该实验组的后测报告" />
              )}
            </section>
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择实验组" />
        )}
      </QueryState>
    </Drawer>
  );
}

function ExperimentEvidenceDrawer({
  open,
  student,
  experiment,
  state,
  report,
  loading,
  error,
  onClose,
}: {
  open: boolean;
  student: MatrixRow | null;
  experiment: Experiment | null;
  state?: MatrixRow["experiments"][string];
  report?: StudentReport;
  loading: boolean;
  error: unknown;
  onClose: () => void;
}) {
  const attempts = (report?.attempts || []).filter((attempt) => attempt.experiment_id === experiment?.id);
  const posttestAttempts = attempts.filter((attempt) => attempt.attempt_kind === "posttest");
  const pretestAttempts = attempts.filter((attempt) => String(attempt.attempt_kind || "").startsWith("pretest"));
  return (
    <Drawer
      title={`${student?.student_name || student?.student_id || "学生"} · ${experiment ? cleanExperimentTitle(experiment.title) : "实验"}`}
      size={760}
      open={open}
      onClose={onClose}
      destroyOnHidden
    >
      <QueryState loading={loading} error={error}>
        {experiment ? (
          <Space orientation="vertical" size={16} className="full analytics-drawer-content">
            <div className="analytics-evidence-summary">
              <div>
                <Text type="secondary">当前实验 mastery</Text>
                <ScorePill score={state?.mastery_score ?? 50} muted={!state?.has_mastery} evidenceCount={state?.evidence_count} />
              </div>
              <div>
                <Text type="secondary">答题证据</Text>
                <strong>{attempts.length} 条</strong>
              </div>
              <div>
                <Text type="secondary">所属学习主题</Text>
                <strong>{experimentFamily(experiment) || experiment.code}</strong>
              </div>
            </div>
            <Tabs
              items={[
                {
                  key: "posttest",
                  label: `课后测试 ${posttestAttempts.length}`,
                  children: <AttemptTable attempts={posttestAttempts} emptyText="暂无该实验的课后测试记录" />,
                },
                {
                  key: "pretest",
                  label: `课前摸底 ${pretestAttempts.length}`,
                  children: <AttemptTable attempts={pretestAttempts} emptyText="暂无该实验的课前摸底记录" />,
                },
                {
                  key: "history",
                  label: `全部记录 ${attempts.length}`,
                  children: <AttemptTable attempts={attempts} emptyText="暂无该实验答题记录" />,
                },
              ]}
            />
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择实验" />
        )}
      </QueryState>
    </Drawer>
  );
}

function AiContentCard({ title, value }: { title: string; value?: TeacherReportAiContent | null }) {
  return (
    <Card size="small" title={title} extra={value ? <Tag>{value.source === "ai" ? "AI 总结" : "规则总结"}</Tag> : null}>
      {value ? (
        <Space orientation="vertical" size={8} className="full">
          <Text>{value.text}</Text>
          {value.generated_at ? <Text type="secondary">生成时间：{formatDate(value.generated_at)}</Text> : null}
        </Space>
      ) : (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="学生尚未生成" />
      )}
    </Card>
  );
}

function AttemptTable({
  attempts,
  emptyText,
  pagination = { pageSize: 6, showSizeChanger: false },
}: {
  attempts: StudentAttempt[];
  emptyText: string;
  pagination?: false | { pageSize: number; showSizeChanger: boolean };
}) {
  return (
    <Table
      rowKey={(row) => String(row.id || row.question_id || row.created_at)}
      size="small"
      dataSource={attempts}
      columns={attemptColumns}
      pagination={pagination}
      locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} /> }}
    />
  );
}

const attemptColumns: TableColumnsType<StudentAttempt> = [
  {
    title: "阶段",
    dataIndex: "attempt_kind_label",
    width: 110,
    render: (value) => <Tag>{String(value || "未标记")}</Tag>,
  },
  {
    title: "题目",
    dataIndex: "stem",
    render: (value, row) => (
      <Space orientation="vertical" size={4} className="full">
        <Text>{String(value || "-")}</Text>
        <Text type="secondary">{row.experiment_title ? cleanExperimentTitle(row.experiment_title) : ""}</Text>
      </Space>
    ),
  },
  {
    title: "作答",
    width: 96,
    render: (_value, row) => renderAnswer(row.submitted_answer_value),
  },
  {
    title: "正确答案",
    width: 110,
    render: (_value, row) => renderAnswer(row.correct_answer),
  },
  {
    title: "结果",
    width: 74,
    render: (_value, row) =>
      row.correct === true ? <Tag color="green">正确</Tag> : row.correct === false ? <Tag color="red">错误</Tag> : <Tag>未判定</Tag>,
  },
];

function ScorePill({
  score,
  muted = false,
  evidenceCount = 0,
  onClick,
}: {
  score: number;
  muted?: boolean;
  evidenceCount?: number;
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void;
}) {
  const title = muted ? "暂无答题证据，按默认 50 分计入" : `答题证据 ${evidenceCount} 条`;
  const className = `analytics-score-pill ${scoreTone(score)} ${muted ? "is-default" : ""}`;
  if (onClick) {
    return (
      <Tooltip title={title}>
        <button className={className} type="button" onClick={onClick}>
          {formatScore(score)}
        </button>
      </Tooltip>
    );
  }
  return (
    <Tooltip title={title}>
      <span className={className}>{formatScore(score)}</span>
    </Tooltip>
  );
}

function formatScore(value: number) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function formatDate(value?: string | null) {
  return value ? dayjs(String(value)).format("YYYY-MM-DD HH:mm") : "-";
}

function reportOptionLabel(report: TeacherLatestPosttestReport) {
  const experimentTitles = report.experiments.map((experiment) => cleanExperimentTitle(String(experiment.title || experiment.code || experiment.id)));
  const experimentLabel =
    experimentTitles.length > 2 ? `${experimentTitles.slice(0, 2).join("、")} 等 ${experimentTitles.length} 个实验` : experimentTitles.join("、");
  return `${formatDate(report.completed_at)} · ${formatScore(report.score ?? 0)} 分${experimentLabel ? ` · ${experimentLabel}` : ""}`;
}

function renderAnswer(value: unknown) {
  if (value === null || value === undefined || value === "") return <Text type="secondary">-</Text>;
  if (Array.isArray(value)) return value.join("、");
  if (typeof value === "boolean") return value ? "正确" : "错误";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function scoreTone(value: number) {
  if (value < 40) return "score-low";
  if (value < 60) return "score-watch";
  if (value < 80) return "score-steady";
  return "score-high";
}

function cleanExperimentTitle(value: string) {
  return value.replace(/^实验\s*\d+-\d+\s*/, "").trim();
}

function groupExperiments(experiments: Experiment[]): AnalyticsExperimentGroup[] {
  const groups = new Map<string, AnalyticsExperimentGroup>();
  experiments.forEach((experiment) => {
    const familyTitle = experimentFamily(experiment) || experiment.code;
    const familyId = experiment.family_id || familyTitle;
    const group = groups.get(familyId) || {
      id: familyId,
      code: experiment.family_code,
      title: familyTitle,
      raw_title: familyTitle,
      experiment_ids: [],
      experiment_count: 0,
    };
    group.experiment_ids.push(experiment.id);
    group.experiment_count += 1;
    groups.set(familyId, group);
  });
  return Array.from(groups.values());
}

function experimentFamily(experiment: Experiment) {
  if (experiment.family_title) return experiment.family_title;
  const metadata = experiment.metadata || {};
  const parentTitle = typeof metadata.parent_title === "string" ? metadata.parent_title : "";
  return cleanExperimentTitle(parentTitle);
}
