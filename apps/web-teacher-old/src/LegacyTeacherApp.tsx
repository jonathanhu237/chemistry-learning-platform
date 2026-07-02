import { FormEvent, type DependencyList, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  changeCatalogNodeStatus,
  changeCatalogPointContentPublication,
  createCatalogNode,
  generateLegacyPointQuestions,
  getAnalyticsDashboard,
  getAuthToken,
  getCatalogNode,
  getGlobalAssessmentReportPrompts,
  getStudentReport,
  getTeacherStudentAssessmentReport,
  legacyTeacherErrorMessage,
  listCatalogQuestionBank,
  listQuestionBankQuestions,
  listQuestionDrafts,
  listTeacherClasses,
  listTeacherClassStudents,
  listTeacherStudentAssessmentReports,
  loadCurrentUser,
  publishQuestionDraft,
  rejectQuestionDraft,
  resetGlobalAssessmentReportPrompts,
  saveCatalogPointContent,
  setAuthToken,
  teacherLogin,
  updateCatalogNode,
  updateGlobalAssessmentReportPrompts,
  type AnalyticsDashboard,
  type CatalogNodeDetail,
  type CatalogNodeKind,
  type CatalogQuestionBankNode,
  type CatalogQuestionBankResponse,
  type Question,
  type QuestionDraft,
  type StudentAssessmentReportSummary,
  type StudentReport,
  type TeacherClassSummary,
  type TeacherStudentSummary,
  type User,
} from "./api";

const logoSrc = `${import.meta.env.BASE_URL}assets/sysu-lockup-red.svg`;
const forbiddenPathSegments = [
  "/videos",
  "/classes",
  "/evaluation",
  "/learning-assistant",
  "/ai-config",
  "/monitoring",
  "/rag",
  "/agent",
  "/provider",
  "/web-admin",
  "/recommend",
  "/question-bank",
  "/scores",
  "/workbench",
  "/import",
];

type RouteKey = "experiments" | "questions" | "analytics" | "reports";
type ObjectiveQuestionType = Question["question_type"];

const navItems: Array<{ key: RouteKey; label: string; path: string }> = [
  { key: "experiments", label: "实验与点位", path: "/experiments" },
  { key: "questions", label: "LLM 出题", path: "/questions" },
  { key: "analytics", label: "学情分析", path: "/analytics" },
  { key: "reports", label: "评价报告", path: "/reports" },
];

const objectiveQuestionTypeOptions: Array<{ value: ObjectiveQuestionType; label: string }> = [
  { value: "single_choice", label: "选择题" },
  { value: "true_false", label: "判断题" },
  { value: "fill_blank", label: "填空题" },
];

function currentPath(): string {
  return window.location.pathname || "/";
}

function navigate(path: string): void {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

function usePath(): string {
  const [path, setPath] = useState(currentPath);
  useEffect(() => {
    const update = () => setPath(currentPath());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return path;
}

function isForbiddenPath(path: string): boolean {
  return forbiddenPathSegments.some((segment) => path.startsWith(segment));
}

function routeFromPath(path: string): RouteKey {
  if (path.startsWith("/questions")) return "questions";
  if (path.startsWith("/analytics")) return "analytics";
  if (path.startsWith("/reports")) return "reports";
  return "experiments";
}

export function LegacyTeacherApp() {
  const path = usePath();
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(getAuthToken()));

  useEffect(() => {
    if (!getAuthToken()) return;
    let active = true;
    setCheckingSession(true);
    loadCurrentUser()
      .then((value) => {
        if (active && (value.role === "admin" || value.role === "teacher" || value.role === "platform_admin")) setUser(value);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setCheckingSession(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (isForbiddenPath(path)) navigate("/experiments");
  }, [path]);

  if (checkingSession) return <div className="legacy-teacher-loading">正在载入教师端...</div>;
  if (!user) return <LoginScreen onLogin={setUser} />;

  const activeRoute = routeFromPath(isForbiddenPath(path) ? "/experiments" : path);

  return (
    <div className="legacy-teacher-shell">
      <aside className="legacy-sidebar">
        <img src={logoSrc} alt="实验平台标识" className="legacy-sidebar-logo" />
        <strong>无机化学实验教学平台</strong>
        <nav aria-label="教师导航">
          {navItems.map((item) => (
            <NavButton key={item.key} active={activeRoute === item.key} label={item.label} path={item.path} />
          ))}
        </nav>
      </aside>
      <div className="legacy-teacher-main">
        <header className="legacy-teacher-header">
          <div>
            <span>教师工作台</span>
            <strong>{user.display_name || user.username}</strong>
          </div>
          <button
            className="text-button"
            onClick={() => {
              setAuthToken("");
              window.location.assign("/");
            }}
          >
            退出登录
          </button>
        </header>
        {activeRoute === "questions" ? (
          <QuestionsPage />
        ) : activeRoute === "analytics" ? (
          <AnalyticsPage />
        ) : activeRoute === "reports" ? (
          <ReportsPage />
        ) : (
          <ExperimentsPage />
        )}
      </div>
    </div>
  );
}

function NavButton({ active, label, path }: { active: boolean; label: string; path: string }) {
  return (
    <button className={active ? "active" : ""} onClick={() => navigate(path)}>
      {label}
    </button>
  );
}

function LoginScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const response = await teacherLogin(username, password);
      if (!["admin", "teacher", "platform_admin"].includes(response.user.role)) {
        throw new Error("该账号不能进入教师端。");
      }
      setAuthToken(response.access_token);
      onLogin(response.user);
    } catch (caught) {
      setError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="legacy-teacher-login">
      <section className="legacy-teacher-login-card">
        <img src={logoSrc} alt="实验平台标识" />
        <span className="eyebrow">Teacher Console</span>
        <h1>无机化学实验教学管理平台</h1>
        <p>管理实验目录与点位资料，基于点位内容出题，并查看学生学习与报告生成结果。</p>
        <form onSubmit={submit}>
          <label>
            账号
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          {error ? <div className="legacy-error">{error}</div> : null}
          <button className="primary-button" disabled={submitting}>
            {submitting ? "登录中..." : "进入教师端"}
          </button>
        </form>
      </section>
    </div>
  );
}

function useAsyncData<T>(loader: () => Promise<T>, deps: DependencyList): { data: T | null; error: string; loading: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loader()
      .then((value) => {
        if (active) setData(value);
      })
      .catch((caught) => {
        if (active) setError(legacyTeacherErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, deps);

  return { data, error, loading };
}

function PageFrame({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children: ReactNode }) {
  return (
    <main className="legacy-teacher-page">
      <section className="legacy-page-head">
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </section>
      {children}
    </main>
  );
}

function StateBlock({ loading, error, children }: { loading: boolean; error: string; children: ReactNode }) {
  if (loading) return <div className="legacy-empty">正在读取数据...</div>;
  if (error) return <div className="legacy-error">{error}</div>;
  return <>{children}</>;
}

function MetricGrid({ metrics }: { metrics: Array<{ label: string; value: ReactNode; unit?: string; description?: string }> }) {
  return (
    <div className="legacy-metric-grid">
      {metrics.map((metric) => (
        <div className="legacy-metric" key={metric.label}>
          <span>{metric.label}</span>
          <strong>
            {metric.value}
            {metric.unit ? <em>{metric.unit}</em> : null}
          </strong>
          {metric.description ? <small>{metric.description}</small> : null}
        </div>
      ))}
    </div>
  );
}

function useCatalogBank(chapterId: string, reloadKey: number) {
  const state = useAsyncData<CatalogQuestionBankResponse>(() => listCatalogQuestionBank(chapterId || undefined), [chapterId, reloadKey]);
  const chapters = state.data?.chapters || [];
  return { ...state, chapters, nodes: state.data?.items || [] };
}

function useDefaultChapter(chapters: Array<{ chapter_id: string }>, selectedChapterId: string, setSelectedChapterId: (value: string) => void) {
  useEffect(() => {
    if (!selectedChapterId && chapters[0]?.chapter_id) setSelectedChapterId(chapters[0].chapter_id);
  }, [chapters, selectedChapterId, setSelectedChapterId]);
}

function nodePath(node?: Pick<CatalogQuestionBankNode, "breadcrumb_titles" | "title"> | null) {
  return (node?.breadcrumb_titles || [node?.title || ""]).filter(Boolean).join(" / ");
}

function ExperimentsPage() {
  const [chapterId, setChapterId] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const catalog = useCatalogBank(chapterId, reloadKey);
  useDefaultChapter(catalog.chapters, chapterId, setChapterId);
  const nodes = catalog.nodes;
  const pointNodes = nodes.filter((item) => item.node_kind === "point");
  const directoryNodes = nodes.filter((item) => item.node_kind === "directory");
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const selectedFallback = useMemo(() => nodes.find((item) => item.node_id === selectedNodeId) || pointNodes[0] || nodes[0], [nodes, pointNodes, selectedNodeId]);

  useEffect(() => {
    if (!selectedNodeId && selectedFallback?.node_id) setSelectedNodeId(selectedFallback.node_id);
    if (selectedNodeId && nodes.length && !nodes.some((item) => item.node_id === selectedNodeId)) setSelectedNodeId(selectedFallback?.node_id || "");
  }, [nodes, selectedFallback, selectedNodeId]);

  const detailState = useAsyncData<CatalogNodeDetail | null>(() => (selectedFallback?.node_id ? getCatalogNode(selectedFallback.node_id) : Promise.resolve(null)), [
    selectedFallback?.node_id,
    reloadKey,
  ]);
  const detail = detailState.data;
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");

  const refresh = () => setReloadKey((value) => value + 1);

  return (
    <PageFrame
      eyebrow="实验与点位管理"
      title="实验目录与点位资料"
      description="维护可学习的实验目录、子目录和点位，并编辑每个点位用于学习与出题的原理、现象和安全三段式资料。"
    >
      <StateBlock loading={catalog.loading} error={catalog.error}>
        <MetricGrid
          metrics={[
            { label: "目录单元", value: directoryNodes.length, unit: "项" },
            { label: "实验点位", value: pointNodes.length, unit: "项" },
            { label: "已发布点位", value: pointNodes.filter((item) => item.status === "published").length, unit: "项" },
            { label: "待补内容", value: pointNodes.filter((item) => item.content_status !== "published").length, unit: "项" },
          ]}
        />
        {notice ? <div className="legacy-notice">{notice}</div> : null}
        {actionError ? <div className="legacy-error">{actionError}</div> : null}
        <div className="legacy-management-grid">
          <section className="legacy-table-card">
            <header>
              <h2>目录树</h2>
              <span>{nodes.length} 个节点</span>
            </header>
            <label className="legacy-select-label">
              章节
              <select value={chapterId} onChange={(event) => setChapterId(event.target.value)}>
                {catalog.chapters.map((chapter) => (
                  <option key={chapter.chapter_id} value={chapter.chapter_id}>
                    {chapter.chapter_title}
                  </option>
                ))}
              </select>
            </label>
            <CreateNodeForm chapterId={chapterId || catalog.chapters[0]?.chapter_id || ""} directories={directoryNodes} onCreated={refresh} onNotice={setNotice} onError={setActionError} />
            <div className="legacy-node-list">
              {nodes.map((node) => (
                <button
                  type="button"
                  key={node.node_id}
                  className={`legacy-node-button${node.node_id === selectedFallback?.node_id ? " selected" : ""}`}
                  onClick={() => setSelectedNodeId(node.node_id)}
                >
                  <strong>{node.title}</strong>
                  <span>{node.node_kind === "point" ? "点位" : "目录"} · {node.status} · {nodePath(node)}</span>
                </button>
              ))}
            </div>
          </section>
          <section className="legacy-table-card">
            <header>
              <h2>节点编辑</h2>
              <span>{selectedFallback?.node_kind === "point" ? "点位资料" : "目录信息"}</span>
            </header>
            <StateBlock loading={detailState.loading} error={detailState.error}>
              {detail ? (
                <NodeEditor
                  detail={detail}
                  onSaved={() => {
                    setNotice("已保存节点资料。");
                    refresh();
                  }}
                  onError={setActionError}
                />
              ) : (
                <div className="legacy-empty compact">请选择一个目录或点位。</div>
              )}
            </StateBlock>
          </section>
        </div>
      </StateBlock>
    </PageFrame>
  );
}

function CreateNodeForm({
  chapterId,
  directories,
  onCreated,
  onNotice,
  onError,
}: {
  chapterId: string;
  directories: CatalogQuestionBankNode[];
  onCreated: () => void;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}) {
  const [kind, setKind] = useState<CatalogNodeKind>("point");
  const [parentId, setParentId] = useState("");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!chapterId || !title.trim()) {
      onError("请先选择章节并填写名称。");
      return;
    }
    setSubmitting(true);
    onNotice("");
    onError("");
    try {
      await createCatalogNode({
        chapter_id: chapterId,
        parent_id: parentId || null,
        node_kind: kind,
        title: title.trim(),
        summary: summary.trim() || null,
      });
      setTitle("");
      setSummary("");
      onNotice(kind === "point" ? "已新增实验点位。" : "已新增目录。");
      onCreated();
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="legacy-inline-form" onSubmit={submit}>
      <div className="legacy-segmented-row" role="radiogroup" aria-label="节点类型">
        {(["point", "directory"] as CatalogNodeKind[]).map((value) => (
          <button type="button" className={kind === value ? "active" : ""} key={value} onClick={() => setKind(value)}>
            {value === "point" ? "点位" : "目录"}
          </button>
        ))}
      </div>
      <label>
        上级目录
        <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
          <option value="">章节根目录</option>
          {directories.map((node) => (
            <option key={node.node_id} value={node.node_id}>
              {nodePath(node)}
            </option>
          ))}
        </select>
      </label>
      <label>
        名称
        <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="输入目录或实验点位名称" />
      </label>
      <label>
        摘要
        <input value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="选填，便于检索和出题" />
      </label>
      <button className="primary-button" disabled={submitting}>
        {submitting ? "创建中..." : "新增节点"}
      </button>
    </form>
  );
}

function NodeEditor({ detail, onSaved, onError }: { detail: CatalogNodeDetail; onSaved: () => void; onError: (value: string) => void }) {
  const node = detail.node;
  const content = detail.point_content;
  const [title, setTitle] = useState(node.title || "");
  const [summary, setSummary] = useState(node.summary || "");
  const [teacherNote, setTeacherNote] = useState(node.teacher_note || "");
  const [pointTitle, setPointTitle] = useState(content?.point_title || node.title || "");
  const [principle, setPrinciple] = useState(content?.principle_text || content?.principle_equation || "");
  const [phenomenon, setPhenomenon] = useState(content?.phenomenon_explanation || "");
  const [safety, setSafety] = useState(content?.safety_note || "");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setTitle(node.title || "");
    setSummary(node.summary || "");
    setTeacherNote(node.teacher_note || "");
    setPointTitle(content?.point_title || node.title || "");
    setPrinciple(content?.principle_text || content?.principle_equation || "");
    setPhenomenon(content?.phenomenon_explanation || "");
    setSafety(content?.safety_note || "");
  }, [node.node_id, node.summary, node.teacher_note, node.title, content]);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim()) {
      onError("请填写节点名称。");
      return;
    }
    setSubmitting(true);
    onError("");
    try {
      await updateCatalogNode(node.node_id, {
        title: title.trim(),
        summary: summary.trim() || null,
        teacher_note: teacherNote.trim() || null,
      });
      if (node.node_kind === "point") {
        await saveCatalogPointContent(node.node_id, {
          point_title: pointTitle.trim() || title.trim(),
          teacher_note: teacherNote.trim() || null,
          principle_mode: "text",
          principle_text: principle.trim() || null,
          phenomenon_explanation: phenomenon.trim() || null,
          safety_note: safety.trim() || null,
        });
      }
      onSaved();
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  const changeStatus = async (action: "publish" | "unpublish" | "archive" | "restore") => {
    setSubmitting(true);
    onError("");
    try {
      await changeCatalogNodeStatus(node.node_id, action);
      if (node.node_kind === "point" && (action === "publish" || action === "unpublish" || action === "archive")) {
        await changeCatalogPointContentPublication(node.node_id, action);
      }
      onSaved();
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="legacy-editor-form" onSubmit={save}>
      <label>
        名称
        <input value={title} onChange={(event) => setTitle(event.target.value)} />
      </label>
      <label>
        摘要
        <textarea value={summary} onChange={(event) => setSummary(event.target.value)} rows={3} />
      </label>
      <label>
        教师备注
        <textarea value={teacherNote} onChange={(event) => setTeacherNote(event.target.value)} rows={3} />
      </label>
      {node.node_kind === "point" ? (
        <div className="legacy-point-content-fields">
          <label>
            点位标题
            <input value={pointTitle} onChange={(event) => setPointTitle(event.target.value)} />
          </label>
          <label>
            原理
            <textarea value={principle} onChange={(event) => setPrinciple(event.target.value)} rows={5} />
          </label>
          <label>
            现象
            <textarea value={phenomenon} onChange={(event) => setPhenomenon(event.target.value)} rows={5} />
          </label>
          <label>
            安全
            <textarea value={safety} onChange={(event) => setSafety(event.target.value)} rows={4} />
          </label>
        </div>
      ) : null}
      <div className="legacy-editor-actions">
        <button className="primary-button" disabled={submitting}>
          {submitting ? "保存中..." : "保存资料"}
        </button>
        <button type="button" className="legacy-secondary-button" disabled={submitting} onClick={() => changeStatus("publish")}>
          发布
        </button>
        <button type="button" className="legacy-secondary-button" disabled={submitting} onClick={() => changeStatus("unpublish")}>
          取消发布
        </button>
      </div>
    </form>
  );
}

function QuestionsPage() {
  const [chapterId, setChapterId] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const catalog = useCatalogBank(chapterId, reloadKey);
  useDefaultChapter(catalog.chapters, chapterId, setChapterId);
  const points = catalog.nodes.filter((node) => node.node_kind === "point");
  const [selectedPointId, setSelectedPointId] = useState("");
  const selectedPoint = points.find((point) => point.node_id === selectedPointId) || points[0];

  useEffect(() => {
    if (!selectedPointId && selectedPoint?.node_id) setSelectedPointId(selectedPoint.node_id);
    if (selectedPointId && points.length && !points.some((point) => point.node_id === selectedPointId)) setSelectedPointId(points[0]?.node_id || "");
  }, [points, selectedPoint, selectedPointId]);

  const detailState = useAsyncData<CatalogNodeDetail | null>(() => (selectedPoint?.node_id ? getCatalogNode(selectedPoint.node_id) : Promise.resolve(null)), [
    selectedPoint?.node_id,
    reloadKey,
  ]);
  const draftsState = useAsyncData(() => (selectedPoint ? listQuestionDrafts({ pointNodeId: selectedPoint.node_id, canonicalPointId: selectedPoint.canonical_point_id || undefined }) : Promise.resolve({ items: [], total: 0 })), [
    selectedPoint?.node_id,
    reloadKey,
  ]);
  const questionsState = useAsyncData(() => {
    if (!selectedPoint) return Promise.resolve({ items: [], total: 0 });
    const params = new URLSearchParams({ limit: "200", point_node_id: selectedPoint.node_id });
    if (selectedPoint.canonical_point_id) params.set("canonical_point_id", selectedPoint.canonical_point_id);
    return listQuestionBankQuestions(params);
  }, [selectedPoint?.node_id, reloadKey]);
  const [questionTypes, setQuestionTypes] = useState<ObjectiveQuestionType[]>(["single_choice"]);
  const [count, setCount] = useState(1);
  const [prompt, setPrompt] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (selectedPoint) {
      setPrompt(`请围绕“${selectedPoint.title}”生成 1 道课堂测评题，依据点位原理、现象和安全资料命题。`);
      setNotice("");
      setActionError("");
    }
  }, [selectedPoint?.node_id]);

  const toggleQuestionType = (value: ObjectiveQuestionType, checked: boolean) => {
    setQuestionTypes((current) => {
      const next = checked ? Array.from(new Set([...current, value])) : current.filter((item) => item !== value);
      return next.length ? next : current;
    });
  };

  const generate = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedPoint || !prompt.trim()) {
      setActionError("请选择点位并填写命题要求。");
      return;
    }
    setGenerating(true);
    setNotice("");
    setActionError("");
    try {
      const response = await generateLegacyPointQuestions({
        experiment_id: selectedPoint.experiment_id,
        prompt: prompt.trim(),
        question_types: questionTypes,
        count,
        difficulty: "basic",
        chapter_ids: [selectedPoint.chapter_id],
        target_point_node_ids: [selectedPoint.node_id],
      });
      setNotice(`已生成 ${response.drafts.length} 条待审题，来源为点位三段式资料。`);
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setGenerating(false);
    }
  };

  const reviewDraft = async (draftId: string, action: "publish" | "reject") => {
    setNotice("");
    setActionError("");
    try {
      if (action === "publish") {
        await publishQuestionDraft(draftId);
        setNotice("教师审核通过，题目已入库。");
      } else {
        await rejectQuestionDraft(draftId);
        setNotice("已退回这条待审题目。");
      }
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    }
  };

  return (
    <PageFrame
      eyebrow="点位资料直接命题"
      title="LLM 出题"
      description="选择一个实验点位，把原理、现象、安全三段式资料连同教师要求交给 LLM 生成待审题；不调用检索增强流程。"
    >
      <StateBlock loading={catalog.loading} error={catalog.error}>
        <MetricGrid
          metrics={[
            { label: "题目总数", value: Number(catalog.data?.totals.question_count || 0), unit: "题" },
            { label: "已发布", value: Number(catalog.data?.totals.published_count || 0), unit: "题" },
            { label: "待审题", value: Number(draftsState.data?.items.filter((item) => item.status === "draft").length || 0), unit: "题" },
            { label: "点位", value: points.length, unit: "项" },
          ]}
        />
        {notice ? <div className="legacy-notice">{notice}</div> : null}
        {actionError ? <div className="legacy-error">{actionError}</div> : null}
        <section className="legacy-table-card legacy-question-demo">
          <header>
            <h2>命题工作区</h2>
            <span>点位资料来源</span>
          </header>
          <div className="legacy-question-demo-grid">
            <aside className="legacy-question-point-panel">
              <label className="legacy-select-label">
                章节范围
                <select value={chapterId} onChange={(event) => setChapterId(event.target.value)}>
                  {catalog.chapters.map((chapter) => (
                    <option key={chapter.chapter_id} value={chapter.chapter_id}>
                      {chapter.chapter_title}
                    </option>
                  ))}
                </select>
              </label>
              <div className="legacy-question-point-list" aria-label="点位列表">
                {points.map((point) => (
                  <button
                    key={point.node_id}
                    type="button"
                    className={`legacy-question-point-button${point.node_id === selectedPoint?.node_id ? " selected" : ""}`}
                    onClick={() => setSelectedPointId(point.node_id)}
                  >
                    <strong>{point.title}</strong>
                    <span>{point.content_status || "未填写资料"} · 题目 {point.counts?.question_count || 0}</span>
                  </button>
                ))}
              </div>
            </aside>
            <form className="legacy-question-prompt-panel" onSubmit={generate}>
              <PointContentSummary detail={detailState.data} loading={detailState.loading} />
              <div className="legacy-question-type-row">
                {objectiveQuestionTypeOptions.map((item) => (
                  <label key={item.value}>
                    <input type="checkbox" checked={questionTypes.includes(item.value)} onChange={(event) => toggleQuestionType(item.value, event.target.checked)} />
                    {item.label}
                  </label>
                ))}
                <label>
                  数量
                  <select value={count} onChange={(event) => setCount(Number(event.target.value) || 1)}>
                    {[1, 2, 3].map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="legacy-textarea-label">
                教师要求
                <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} />
              </label>
              <button className="primary-button" disabled={generating || !selectedPoint}>
                {generating ? "生成中..." : "生成待审题"}
              </button>
            </form>
            <section className="legacy-question-review-panel">
              <div className="legacy-question-review-head">
                <strong>待审题</strong>
                <span>{draftsState.loading ? "读取中" : `${draftsState.data?.items.length || 0} 条`}</span>
              </div>
              <StateBlock loading={draftsState.loading} error={draftsState.error}>
                {draftsState.data?.items.length ? (
                  <div className="legacy-question-candidate-list">
                    {draftsState.data.items.slice(0, 5).map((draft) => (
                      <DraftReviewCard key={draft.id} draft={draft} onReview={reviewDraft} />
                    ))}
                  </div>
                ) : (
                  <div className="legacy-empty compact">暂无待审题。</div>
                )}
              </StateBlock>
            </section>
          </div>
        </section>
        <section className="legacy-table-card">
          <header>
            <h2>正式题库</h2>
            <span>{questionsState.data?.total || 0} 题</span>
          </header>
          <StateBlock loading={questionsState.loading} error={questionsState.error}>
            <div className="legacy-resource-list">
              {(questionsState.data?.items || []).slice(0, 12).map((question) => (
                <QuestionRow key={question.id} question={question} />
              ))}
            </div>
          </StateBlock>
        </section>
      </StateBlock>
    </PageFrame>
  );
}

function PointContentSummary({ detail, loading }: { detail: CatalogNodeDetail | null; loading: boolean }) {
  if (loading) return <div className="legacy-empty compact">正在读取点位资料...</div>;
  const content = detail?.point_content;
  return (
    <div className="legacy-question-selected">
      <span className="legacy-row-label">{content?.content_status || "点位资料"}</span>
      <strong>{content?.point_title || detail?.node.title || "请选择实验点位"}</strong>
      <p>{detail?.breadcrumbs.map((item) => item.title).join(" / ") || "选择点位后展示三段式资料。"}</p>
      <dl className="legacy-point-content-summary">
        <div>
          <dt>原理</dt>
          <dd>{content?.principle_text || content?.principle_equation || "未填写"}</dd>
        </div>
        <div>
          <dt>现象</dt>
          <dd>{content?.phenomenon_explanation || "未填写"}</dd>
        </div>
        <div>
          <dt>安全</dt>
          <dd>{content?.safety_note || "未填写"}</dd>
        </div>
      </dl>
    </div>
  );
}

function DraftReviewCard({ draft, onReview }: { draft: QuestionDraft; onReview: (draftId: string, action: "publish" | "reject") => void }) {
  const payload = draft.payload || {};
  const validationErrors = draft.validation_errors || [];
  return (
    <article className="legacy-question-candidate-card">
      <div className="legacy-question-candidate-title">
        <span className="legacy-row-label">{questionTypeLabel(String(payload.question_type || ""))}</span>
        <span className={`legacy-row-label${validationErrors.length ? "" : " gold"}`}>{draft.status === "published" ? "已入库" : validationErrors.length ? "需复核" : "可入库"}</span>
      </div>
      <strong>{String(payload.stem || "待审题目")}</strong>
      <QuestionOptions options={payload.options} />
      <dl className="legacy-question-answer">
        <div>
          <dt>答案</dt>
          <dd>{answerSummary(payload.answer)}</dd>
        </div>
        <div>
          <dt>解析</dt>
          <dd>{String(payload.explanation || "教师确认后再发布进入正式题库。")}</dd>
        </div>
      </dl>
      {validationErrors.length ? <div className="legacy-error compact">{validationErrors.join("；")}</div> : null}
      <div className="legacy-question-card-actions">
        <button className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "publish")}>
          通过入库
        </button>
        <button className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "reject")}>
          退回修改
        </button>
      </div>
    </article>
  );
}

function QuestionRow({ question }: { question: Question }) {
  return (
    <article className="legacy-resource-row">
      <div>
        <span className="legacy-row-label">{questionTypeLabel(question.question_type)}</span>
      </div>
      <div className="legacy-row-main">
        <strong>{question.stem}</strong>
        <p>{question.explanation || "暂无解析。"}</p>
      </div>
      <div className="legacy-row-stats">
        <span>{question.status}</span>
        <span>{answerSummary(question.answer)}</span>
      </div>
    </article>
  );
}

function QuestionOptions({ options }: { options: unknown }) {
  if (!Array.isArray(options) || !options.length) return null;
  return (
    <div className="legacy-question-options">
      {options.slice(0, 4).map((option, index) => {
        const label = typeof option === "object" && option ? String((option as { label?: unknown }).label || String.fromCharCode(65 + index)) : String.fromCharCode(65 + index);
        const text = typeof option === "object" && option ? String((option as { text?: unknown }).text || "") : String(option || "");
        return (
          <span key={`${label}-${index}`}>
            <b>{label}</b>
            {text}
          </span>
        );
      })}
    </div>
  );
}

function questionTypeLabel(value: string): string {
  if (value === "single_choice") return "选择题";
  if (value === "true_false") return "判断题";
  if (value === "fill_blank") return "填空题";
  return "题目";
}

function answerSummary(answer: unknown): string {
  if (answer && typeof answer === "object" && "value" in answer) return String((answer as { value?: unknown }).value ?? "-");
  if (answer && typeof answer === "object" && "accepted_answers" in answer) {
    const values = (answer as { accepted_answers?: unknown }).accepted_answers;
    return Array.isArray(values) ? values.join(" / ") : String(values || "-");
  }
  return String(answer || "-");
}

function AnalyticsPage() {
  const classState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, []);
  const classes = classState.data || [];
  const [selectedClassId, setSelectedClassId] = useState("");
  useEffect(() => {
    if (!selectedClassId && classes[0]?.id) setSelectedClassId(classes[0].id);
  }, [classes, selectedClassId]);

  const dashboardState = useAsyncData<AnalyticsDashboard | null>(() => (selectedClassId ? getAnalyticsDashboard(selectedClassId) : Promise.resolve(null)), [selectedClassId]);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const dashboard = dashboardState.data;
  const rows = dashboard?.matrix || [];
  const columns = (dashboard?.experiment_groups?.length ? dashboard.experiment_groups : dashboard?.experiments || []).slice(0, 6);

  useEffect(() => {
    if (!selectedStudentId && rows[0]?.student_id) setSelectedStudentId(rows[0].student_id);
  }, [rows, selectedStudentId]);

  const reportState = useAsyncData<StudentReport | null>(
    () => (selectedClassId && selectedStudentId ? getStudentReport(selectedClassId, selectedStudentId) : Promise.resolve(null)),
    [selectedClassId, selectedStudentId],
  );

  return (
    <PageFrame
      eyebrow="学生学习情况"
      title="学情分析"
      description="按班级展示每个学生的参与、得分、掌握度证据和薄弱点位，数据来自新版学情接口。"
    >
      <StateBlock loading={classState.loading} error={classState.error}>
        <section className="legacy-card">
          <label className="legacy-select-label">
            当前班级
            <select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}>
              {classes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.class_name}
                </option>
              ))}
            </select>
          </label>
        </section>
        <StateBlock loading={dashboardState.loading} error={dashboardState.error}>
          {dashboard ? (
            <>
              <MetricGrid
                metrics={[
                  { label: "班级人数", value: dashboard.metrics.class_size, unit: "人" },
                  { label: "参与学生", value: dashboard.metrics.active_students, unit: "人" },
                  { label: "平均分", value: dashboard.metrics.average_score, unit: "分" },
                  { label: "完成率", value: dashboard.metrics.completion_rate, unit: "%" },
                ]}
              />
              <section className="legacy-table-card">
                <header>
                  <h2>学生掌握矩阵</h2>
                  <span>{rows.length} 名学生</span>
                </header>
                <div className="legacy-learning-matrix">
                  <div className="legacy-learning-matrix-head">
                    <span>学生</span>
                    <span>平均</span>
                    {columns.map((item) => (
                      <span key={item.id}>{item.title}</span>
                    ))}
                  </div>
                  {rows.map((student) => (
                    <button
                      type="button"
                      className={`legacy-learning-matrix-row${student.student_id === selectedStudentId ? " selected" : ""}`}
                      key={student.student_id}
                      onClick={() => setSelectedStudentId(student.student_id)}
                    >
                      <strong>{student.student_name}</strong>
                      <span>{student.average_score ?? "-"}</span>
                      {columns.map((item) => {
                        const state = student.experiment_groups?.[item.id] || student.experiments?.[item.id];
                        return <span key={item.id}>{state ? `${Math.round(Number(state.mastery_score || state.score || 0))}%` : "-"}</span>;
                      })}
                    </button>
                  ))}
                </div>
              </section>
              <section className="legacy-table-card">
                <header>
                  <h2>学生报告摘要</h2>
                  <span>{selectedStudentId || "未选择学生"}</span>
                </header>
                <StateBlock loading={reportState.loading} error={reportState.error}>
                  {reportState.data ? <StudentReportPanel report={reportState.data} /> : <div className="legacy-empty compact">请选择学生。</div>}
                </StateBlock>
              </section>
            </>
          ) : null}
        </StateBlock>
      </StateBlock>
    </PageFrame>
  );
}

function StudentReportPanel({ report }: { report: StudentReport }) {
  const latest = report.latest_posttest_report;
  const weakPoints = report.weak_video_points || [];
  return (
    <div className="legacy-report-summary-grid">
      <article>
        <strong>最近测评</strong>
        <p>{latest ? `${latest.score ?? "-"} 分，${latest.correct_count}/${latest.total_count} 正确` : "暂无测评报告。"}</p>
        <p>{latest?.ai_summary?.text || "暂无学习总结。"}</p>
      </article>
      <article>
        <strong>薄弱点位</strong>
        {weakPoints.length ? (
          weakPoints.slice(0, 5).map((item) => (
            <span key={item.point_title}>
              {item.point_title} · 错误率 {item.incorrect_rate}%
            </span>
          ))
        ) : (
          <p>暂无薄弱点位。</p>
        )}
      </article>
    </div>
  );
}

function ReportsPage() {
  const promptState = useAsyncData(getGlobalAssessmentReportPrompts, []);
  const classState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, []);
  const classes = classState.data || [];
  const [summaryPrompt, setSummaryPrompt] = useState("");
  const [mistakePrompt, setMistakePrompt] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [selectedReportId, setSelectedReportId] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (promptState.data) {
      setSummaryPrompt(promptState.data.settings.summary_prompt);
      setMistakePrompt(promptState.data.settings.mistake_prompt);
    }
  }, [promptState.data]);
  useEffect(() => {
    if (!selectedClassId && classes[0]?.id) setSelectedClassId(classes[0].id);
  }, [classes, selectedClassId]);

  const studentsState = useAsyncData<TeacherStudentSummary[]>(() => (selectedClassId ? listTeacherClassStudents(selectedClassId) : Promise.resolve([])), [selectedClassId]);
  const students = studentsState.data || [];
  useEffect(() => {
    if (!selectedStudentId && students[0]?.student_id) setSelectedStudentId(students[0].student_id);
    if (selectedStudentId && students.length && !students.some((student) => student.student_id === selectedStudentId)) setSelectedStudentId(students[0]?.student_id || "");
  }, [selectedStudentId, students]);

  const reportsState = useAsyncData(
    () => (selectedClassId && selectedStudentId ? listTeacherStudentAssessmentReports(selectedClassId, selectedStudentId) : Promise.resolve({ reports: [] as StudentAssessmentReportSummary[] })),
    [selectedClassId, selectedStudentId],
  );
  const reports = reportsState.data?.reports || [];
  useEffect(() => {
    if (!selectedReportId && reports[0]?.id) setSelectedReportId(reports[0].id);
    if (selectedReportId && reports.length && !reports.some((report) => report.id === selectedReportId)) setSelectedReportId(reports[0]?.id || "");
  }, [reports, selectedReportId]);

  const reportDetailState = useAsyncData(
    () => (selectedClassId && selectedStudentId && selectedReportId ? getTeacherStudentAssessmentReport(selectedClassId, selectedStudentId, selectedReportId) : Promise.resolve(null)),
    [selectedClassId, selectedStudentId, selectedReportId],
  );

  const savePrompts = async (event: FormEvent) => {
    event.preventDefault();
    if (!summaryPrompt.trim() || !mistakePrompt.trim()) {
      setActionError("请填写报告总结 Prompt 和错题讲解 Prompt。");
      return;
    }
    setSaving(true);
    setNotice("");
    setActionError("");
    try {
      await updateGlobalAssessmentReportPrompts({ summary_prompt: summaryPrompt, mistake_prompt: mistakePrompt });
      setNotice("报告生成 Prompt 已保存。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  const resetPrompts = async () => {
    setSaving(true);
    setNotice("");
    setActionError("");
    try {
      const response = await resetGlobalAssessmentReportPrompts();
      setSummaryPrompt(response.settings.summary_prompt);
      setMistakePrompt(response.settings.mistake_prompt);
      setNotice("已恢复默认报告 Prompt。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageFrame
      eyebrow="评价报告生成"
      title="评价报告"
      description="维护测评报告生成 Prompt，并查看学生提交测评后生成的学习总结与错题讲解。"
    >
      {notice ? <div className="legacy-notice">{notice}</div> : null}
      {actionError ? <div className="legacy-error">{actionError}</div> : null}
      <StateBlock loading={promptState.loading || classState.loading} error={promptState.error || classState.error}>
        <div className="legacy-management-grid">
          <section className="legacy-table-card">
            <header>
              <h2>报告生成 Prompt</h2>
              <span>{promptState.data?.source === "global" ? "全局设置" : "班级设置"}</span>
            </header>
            <div className="legacy-report-variable-list">
              {(promptState.data?.supported_variables || []).map((variable) => (
                <button
                  type="button"
                  className="legacy-report-variable-chip"
                  key={variable}
                  onClick={() => setSummaryPrompt((current) => `${current}${current.endsWith("\n") ? "" : "\n"}{{${variable}}}`)}
                >
                  {variable}
                </button>
              ))}
            </div>
            <form className="legacy-report-prompt-form" onSubmit={savePrompts}>
              <label className="legacy-textarea-label">
                报告总结 Prompt
                <textarea value={summaryPrompt} onChange={(event) => setSummaryPrompt(event.target.value)} rows={7} />
              </label>
              <label className="legacy-textarea-label">
                错题讲解 Prompt
                <textarea value={mistakePrompt} onChange={(event) => setMistakePrompt(event.target.value)} rows={7} />
              </label>
              <div className="legacy-editor-actions">
                <button className="primary-button" disabled={saving}>
                  {saving ? "保存中..." : "保存 Prompt"}
                </button>
                <button type="button" className="legacy-secondary-button" disabled={saving} onClick={resetPrompts}>
                  恢复默认
                </button>
              </div>
            </form>
          </section>
          <section className="legacy-table-card">
            <header>
              <h2>学生报告</h2>
              <span>{reports.length} 份</span>
            </header>
            <div className="legacy-filter-row">
              <label>
                班级
                <select value={selectedClassId} onChange={(event) => setSelectedClassId(event.target.value)}>
                  {classes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.class_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                学生
                <select value={selectedStudentId} onChange={(event) => setSelectedStudentId(event.target.value)}>
                  {students.map((student) => (
                    <option key={student.student_id} value={student.student_id}>
                      {student.student_name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <StateBlock loading={studentsState.loading || reportsState.loading} error={studentsState.error || reportsState.error}>
              <div className="legacy-report-list">
                {reports.map((report) => (
                  <button
                    type="button"
                    key={report.id}
                    className={report.id === selectedReportId ? "selected" : ""}
                    onClick={() => setSelectedReportId(report.id)}
                  >
                    <strong>{report.title}</strong>
                    <span>{report.score} 分 · 错题 {report.wrong_count}</span>
                  </button>
                ))}
              </div>
              <StateBlock loading={reportDetailState.loading} error={reportDetailState.error}>
                {reportDetailState.data ? (
                  <article className="legacy-report-detail">
                    <h2>{reportDetailState.data.title}</h2>
                    <strong>学习总结</strong>
                    <p>{reportDetailState.data.summary.text}</p>
                    <strong>错题讲解</strong>
                    <p>{reportDetailState.data.mistake_explanation.text}</p>
                  </article>
                ) : (
                  <div className="legacy-empty compact">当前学生暂无报告。</div>
                )}
              </StateBlock>
            </StateBlock>
          </section>
        </div>
      </StateBlock>
    </PageFrame>
  );
}
