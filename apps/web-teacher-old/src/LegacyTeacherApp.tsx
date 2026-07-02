import { FormEvent, type DependencyList, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  getAuthToken,
  getTeacherDemoClassAnalytics,
  getTeacherDemoClasses,
  getTeacherDemoClassWeakPoints,
  getTeacherDemoEvaluationSystem,
  getTeacherDemoOverview,
  getTeacherDemoQuestionResources,
  getTeacherDemoVideoResources,
  legacyTeacherErrorMessage,
  createTeacherClass,
  createTeacherClassStudent,
  listTeacherClasses,
  listTeacherClassStudents,
  loadCurrentUser,
  setLegacyVideoPointRecommendation,
  setAuthToken,
  teacherLogin,
  type TeacherDemoAnalytics,
  type TeacherDemoClasses,
  type TeacherDemoEvaluationSystem,
  type TeacherDemoOverview,
  type TeacherDemoQuestionResource,
  type TeacherDemoQuestionResources,
  type TeacherDemoVideoResource,
  type TeacherDemoVideoResources,
  type TeacherDemoWeakPoint,
  type TeacherDemoWeakPoints,
  type TeacherClassSummary,
  type TeacherStudentSummary,
  type User,
} from "./api";

const logoSrc = `${import.meta.env.BASE_URL}assets/sysu-lockup-red.svg`;
const forbiddenPathSegments = [
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
  "/publish",
];

type RouteKey = "overview" | "videos" | "questions" | "classes" | "analytics" | "evaluation";
type ObjectiveQuestionType = "single_choice" | "true_false" | "fill_blank";

const navItems: Array<{ key: RouteKey; label: string; path: string }> = [
  { key: "overview", label: "工作台", path: "/" },
  { key: "videos", label: "视频资源", path: "/videos" },
  { key: "questions", label: "题库资源", path: "/questions" },
  { key: "classes", label: "班级", path: "/classes" },
  { key: "analytics", label: "学情分析", path: "/analytics" },
  { key: "evaluation", label: "评价体系", path: "/evaluation" },
];

const objectiveQuestionTypeOptions: Array<{ value: ObjectiveQuestionType; label: string }> = [
  { value: "single_choice", label: "选择题" },
  { value: "true_false", label: "判断题" },
  { value: "fill_blank", label: "填空题" },
];
type LegacyQuestionDemoPoint = {
  node_id: string;
  chapter_id: string;
  title: string;
  summary: string;
  breadcrumb_titles: string[];
  evidence_label: string;
  question_count: number;
};
type LegacyQuestionDraft = {
  key: string;
  id: string;
  pointId: string;
  status: "draft" | "published" | "rejected";
  payload: {
    question_type?: string;
    stem?: string;
    options?: Array<{ label?: string; text?: string } | string>;
    answer?: unknown;
    explanation?: string;
    difficulty?: string;
    status?: string;
  };
  validation_errors: string[];
};
const legacyQuestionChapters = [
  { chapter_id: "chapter-halogen", label: "第13章 卤族元素" },
  { chapter_id: "chapter-nitrogen", label: "第7章 氮族元素" },
  { chapter_id: "chapter-redox", label: "第4章 氧化还原与离子检验" },
];
const legacyQuestionDemoPoints: LegacyQuestionDemoPoint[] = [
  {
    node_id: "legacy-point-chlorine-bleach",
    chapter_id: "chapter-halogen",
    title: "氯水漂白性实验",
    summary: "观察氯水使有色物质褪色，并联系有效成分与氧化性判断。",
    breadcrumb_titles: ["卤族元素", "氯的含氧化合物", "氯水漂白性实验"],
    evidence_label: "教材依据就绪",
    question_count: 5,
  },
  {
    node_id: "legacy-point-nitrite-redox",
    chapter_id: "chapter-nitrogen",
    title: "亚硝酸的氧化性",
    summary: "围绕亚硝酸盐显色、褪色和氧化还原现象进行课堂测评。",
    breadcrumb_titles: ["氮族元素", "亚硝酸盐性质", "亚硝酸的氧化性"],
    evidence_label: "教材依据就绪",
    question_count: 4,
  },
  {
    node_id: "legacy-point-iodide-test",
    chapter_id: "chapter-redox",
    title: "碘离子检验",
    summary: "结合淀粉显色、氧化剂作用和离子检验条件判断实验结论。",
    breadcrumb_titles: ["氧化还原反应", "离子检验", "碘离子检验"],
    evidence_label: "依据部分就绪",
    question_count: 3,
  },
];
const reportPromptVariables = [
  "student_name",
  "student_id",
  "assessment_type",
  "score",
  "correct_count",
  "total_count",
  "correct_rate",
  "wrong_count",
  "wrong_questions",
  "mastery_changes",
  "experiment_points",
];
const defaultReportPrompts = {
  summary: `请基于本次测评报告生成一段中性的学习记录总结，面向学生和老师共同阅读。需要概括测评类型、得分、掌握变化、主要薄弱实验或点位，并给出下一步复习建议。不要使用“你”式聊天口吻，不要出现 AI、模型、提示词等字样。控制在 220 字以内。

学生：{{student_name}}（{{student_id}}）
测评：{{assessment_type}}
得分：{{score}} / {{total_count}}
薄弱点位：{{experiment_points}}`,
  mistake: `请基于本次测评的错题生成一段中性的错题讲解，面向学生和老师共同阅读。先概括共同错因，再按错题说明正确思路和复习抓手。只解释本次已提交错题，不要泄露未提交题目的答案，不要出现 AI、模型、提示词等字样。如果没有错题，简短说明本次没有错题。

测评：{{assessment_type}}
错题数量：{{wrong_count}}
错题列表：{{wrong_questions}}`,
};

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
  if (path.startsWith("/videos")) return "videos";
  if (path.startsWith("/questions")) return "questions";
  if (path.startsWith("/classes")) return "classes";
  if (path.startsWith("/analytics")) return "analytics";
  if (path.startsWith("/evaluation")) return "evaluation";
  return "overview";
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
    if (isForbiddenPath(path)) navigate("/");
  }, [path]);

  if (checkingSession) {
    return <div className="legacy-teacher-loading">正在载入教师端...</div>;
  }

  if (!user) return <LoginScreen onLogin={setUser} />;

  const activeRoute = routeFromPath(isForbiddenPath(path) ? "/" : path);

  return (
    <div className="legacy-teacher-shell">
      <aside className="legacy-sidebar">
        <img src={logoSrc} alt="实验平台标识" className="legacy-sidebar-logo" />
        <strong>无机化学实验教学平台</strong>
        <nav aria-label="旧版教师导航">
          {navItems.map((item) => (
            <NavButton key={item.key} active={activeRoute === item.key} label={item.label} path={item.path} />
          ))}
        </nav>
      </aside>
      <div className="legacy-teacher-main">
        <header className="legacy-teacher-header">
          <div>
            <span>旧版教师展示台</span>
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
        {activeRoute === "videos" ? (
          <VideosPage />
        ) : activeRoute === "questions" ? (
          <QuestionsPage />
        ) : activeRoute === "classes" ? (
          <ClassesPage />
        ) : activeRoute === "analytics" ? (
          <AnalyticsPage />
        ) : activeRoute === "evaluation" ? (
          <EvaluationPage />
        ) : (
          <OverviewPage />
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
        <span className="eyebrow">Teacher Console Classic</span>
        <h1>无机化学实验教学管理平台</h1>
        <p>围绕实验视频、题库资源、班级学情和 BKT 评价体系展示教学反馈闭环。</p>
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
            {submitting ? "登录中..." : "进入教师端" }
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
  if (loading) return <div className="legacy-empty">正在读取展示数据...</div>;
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

function OverviewPage() {
  const { data, error, loading } = useAsyncData<TeacherDemoOverview>(getTeacherDemoOverview, []);

  return (
    <PageFrame
      eyebrow="只读教学资源总览"
      title="教学工作台"
      description="展示实验视频、题库、班级与 BKT 反馈闭环，用于评奖现场快速说明系统已有教学资源。"
    >
      <StateBlock loading={loading} error={error}>
        {data ? (
          <>
            <MetricGrid
              metrics={data.metrics.map((metric) => ({
                label: metric.label,
                value: metric.value,
                unit: metric.unit,
                description: metric.description,
              }))}
            />
            <section className="legacy-card">
              <h2>BKT 教学反馈闭环</h2>
              <div className="legacy-flow">
                {data.loop.map((step) => (
                  <article key={step.title}>
                    <strong>{step.title}</strong>
                    <p>{step.description}</p>
                  </article>
                ))}
              </div>
            </section>
            <section className="legacy-panel-grid">
              <ModuleCard title="视频资源" description="按实验点位查看可学习视频、题目覆盖和推荐学习标签。" path="/videos" />
              <ModuleCard title="题库资源" description="查看题库数量、题型分布和章节点位覆盖情况。" path="/questions" />
              <ModuleCard title="学情分析" description="查看班级平均分、掌握度证据和薄弱点位排行。" path="/analytics" />
            </section>
          </>
        ) : null}
      </StateBlock>
    </PageFrame>
  );
}

function ModuleCard({ title, description, path }: { title: string; description: string; path: string }) {
  return (
    <button className="legacy-module-card" onClick={() => navigate(path)}>
      <strong>{title}</strong>
      <span>{description}</span>
    </button>
  );
}

function VideosPage() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [updatingNodeId, setUpdatingNodeId] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const { data, error, loading } = useAsyncData<TeacherDemoVideoResources>(() => getTeacherDemoVideoResources(submittedQuery), [submittedQuery, reloadKey]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSubmittedQuery(query.trim());
  };

  const items = data?.items || [];
  const playableCount = items.filter((item) => item.has_video).length;
  const recommendedCount = items.filter((item) => item.is_recommended).length;

  const toggleRecommendation = async (item: TeacherDemoVideoResource, recommended: boolean) => {
    setUpdatingNodeId(item.node_id);
    setNotice("");
    setActionError("");
    try {
      await setLegacyVideoPointRecommendation(item.node_id, recommended);
      setNotice(recommended ? `已设为推荐学习：${item.title}` : `已取消推荐学习：${item.title}`);
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setUpdatingNodeId("");
    }
  };

  return (
    <PageFrame
      eyebrow="实验视频证据"
      title="视频资源"
      description="以实验点位为单位展示视频资源，已有视频的点位排在前面；教师推荐学习仅作为静态标签展示。"
    >
      <form className="legacy-search-row" onSubmit={submit}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入实验、试剂、现象或点位名称" />
        <button className="primary-button">搜索</button>
      </form>
      {notice ? <div className="legacy-notice">{notice}</div> : null}
      {actionError ? <div className="legacy-error">{actionError}</div> : null}
      <StateBlock loading={loading} error={error}>
        <MetricGrid
          metrics={[
            { label: submittedQuery ? "搜索结果" : "全部点位", value: data?.total || 0, unit: "项" },
            { label: "已绑定视频", value: playableCount, unit: "项" },
            { label: "推荐学习", value: recommendedCount, unit: "项" },
            { label: "题目覆盖", value: items.reduce((sum, item) => sum + item.published_question_count, 0), unit: "题" },
          ]}
        />
        <section className="legacy-table-card">
          <header>
            <h2>视频点位列表</h2>
            <span>{items.length ? `当前显示 ${items.length} 项` : "暂无数据"}</span>
          </header>
          <div className="legacy-resource-list">
            {items.map((item) => (
              <VideoResourceRow
                key={item.node_id}
                item={item}
                updating={updatingNodeId === item.node_id}
                onToggle={(recommended) => void toggleRecommendation(item, recommended)}
              />
            ))}
          </div>
        </section>
      </StateBlock>
    </PageFrame>
  );
}

function VideoResourceRow({
  item,
  updating,
  onToggle,
}: {
  item: TeacherDemoVideoResource;
  updating: boolean;
  onToggle: (recommended: boolean) => void;
}) {
  return (
    <article className="legacy-resource-row">
      <div>
        <span className="legacy-row-label">{item.has_video ? "已绑定视频" : "待补充视频"}</span>
        {item.is_recommended ? <span className="legacy-row-label gold">推荐学习</span> : null}
      </div>
      <div className="legacy-row-main">
        <strong>{item.title}</strong>
        <p>{item.summary || "暂无摘要。"}</p>
        <small>{item.catalog_path.join(" / ") || "未绑定目录路径"}</small>
      </div>
      <div className="legacy-row-stats">
        <span>视频 {item.published_media_count}</span>
        <span>题目 {item.published_question_count}</span>
        <button className="legacy-secondary-button" disabled={updating} onClick={() => onToggle(!item.is_recommended)}>
          {updating ? "处理中..." : item.is_recommended ? "取消推荐" : "设为推荐"}
        </button>
      </div>
    </article>
  );
}

function QuestionsPage() {
  const { data, error, loading } = useAsyncData<TeacherDemoQuestionResources>(getTeacherDemoQuestionResources, []);
  const pointItems = useMemo(() => (data?.items || []).filter((item) => item.node_kind === "point"), [data]);
  const directoryItems = useMemo(() => (data?.items || []).filter((item) => item.node_kind !== "point"), [data]);

  return (
    <PageFrame
      eyebrow="智能辅助题库建设"
      title="题库资源"
      description="展示教材与实验点位沉淀出的题库资源、题型分布和覆盖情况，并用旧后台风格演示待审题目的生成与教师审核。"
    >
      <StateBlock loading={loading} error={error}>
        {data ? (
          <>
            <MetricGrid
              metrics={[
                { label: "题目总数", value: Number(data.totals.question_count || 0), unit: "题" },
                { label: "已发布", value: Number(data.totals.published_count || 0), unit: "题" },
                { label: "待审题目", value: Number(data.totals.draft_count || 0), unit: "题" },
                { label: "点位覆盖", value: Number(data.totals.point_count || pointItems.length), unit: "项" },
              ]}
            />
            <section className="legacy-card">
              <h2>题库建设流程</h2>
              <div className="legacy-process-grid">
                <span>教材资料</span>
                <span>智能辅助命题</span>
                <span>教师审核</span>
                <span>正式题库</span>
              </div>
            </section>
            <QuestionAuthoringDemo />
            <section className="legacy-table-card">
              <header>
                <h2>点位题库覆盖</h2>
                <span>
                  {pointItems.length} 个实验点位 · {directoryItems.length} 个目录单元
                </span>
              </header>
              <div className="legacy-resource-list">
                {pointItems.slice(0, 120).map((item) => (
                  <QuestionResourceRow key={item.node_id} item={item} />
                ))}
              </div>
            </section>
          </>
        ) : null}
      </StateBlock>
    </PageFrame>
  );
}

function QuestionAuthoringDemo() {
  const [selectedChapterId, setSelectedChapterId] = useState(legacyQuestionChapters[0]?.chapter_id || "");
  const chapterPoints = useMemo(
    () => legacyQuestionDemoPoints.filter((item) => item.chapter_id === selectedChapterId),
    [selectedChapterId],
  );
  const [selectedPointId, setSelectedPointId] = useState(chapterPoints[0]?.node_id || legacyQuestionDemoPoints[0]?.node_id || "");
  const selectedPoint = useMemo(
    () => chapterPoints.find((item) => item.node_id === selectedPointId) || chapterPoints[0] || legacyQuestionDemoPoints[0],
    [chapterPoints, selectedPointId],
  );
  const [questionTypes, setQuestionTypes] = useState<ObjectiveQuestionType[]>(["single_choice"]);
  const [count, setCount] = useState(1);
  const [prompt, setPrompt] = useState(() => defaultQuestionPrompt(selectedPoint));
  const [drafts, setDrafts] = useState<LegacyQuestionDraft[]>([]);
  const [draftCounter, setDraftCounter] = useState(1);
  const [notice, setNotice] = useState("");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!chapterPoints.some((item) => item.node_id === selectedPointId)) {
      setSelectedPointId(chapterPoints[0]?.node_id || "");
    }
  }, [chapterPoints, selectedPointId]);

  useEffect(() => {
    setPrompt(defaultQuestionPrompt(selectedPoint));
    setDrafts([]);
    setNotice("");
  }, [selectedPoint?.node_id]);

  const pendingCount = drafts.filter((item) => item.status === "draft").length;
  const canGenerate = Boolean(selectedPoint?.node_id && prompt.trim() && questionTypes.length);

  const toggleQuestionType = (value: ObjectiveQuestionType, checked: boolean) => {
    setQuestionTypes((current) => {
      const next = checked ? Array.from(new Set([...current, value])) : current.filter((item) => item !== value);
      return next.length ? next : current;
    });
  };

  const submitGeneration = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedPoint) return;
    setNotice("");
    setGenerating(true);
    window.setTimeout(() => {
      const nextDrafts = buildLegacyQuestionDrafts(selectedPoint, questionTypes, count, prompt.trim(), draftCounter);
      setDrafts(nextDrafts);
      setDraftCounter((value) => value + nextDrafts.length);
      setNotice(nextDrafts.length ? `已生成 ${nextDrafts.length} 条待审题目，请教师复核后入库。` : "生成完成，但本次没有返回待审题目。");
      setGenerating(false);
    }, 300);
  };

  const reviewDraft = (draftId: string, status: "published" | "rejected") => {
    setDrafts((current) =>
      current.map((item) =>
        item.id === draftId
          ? {
              ...item,
              status,
              payload: { ...item.payload, status },
            }
          : item,
      ),
    );
    setNotice(status === "published" ? "教师审核通过，题目已入库。" : "已退回这条待审题目。");
  };

  return (
    <section className="legacy-table-card legacy-question-demo" data-testid="legacy-question-authoring-demo">
      <header>
        <h2>智能命题</h2>
        <span>演示数据已载入</span>
      </header>
      <div className="legacy-question-demo-grid">
        <aside className="legacy-question-point-panel">
          <label className="legacy-select-label">
            章节范围
            <select value={selectedChapterId} onChange={(event) => setSelectedChapterId(event.target.value)}>
              {legacyQuestionChapters.map((chapter) => (
                <option key={chapter.chapter_id} value={chapter.chapter_id}>
                  {chapter.label}
                </option>
              ))}
            </select>
          </label>
          <div className="legacy-question-point-list" aria-label="本章点位列表">
            {chapterPoints.length ? (
              chapterPoints.map((item) => (
                <button
                  key={item.node_id}
                  type="button"
                  className={`legacy-question-point-button${item.node_id === selectedPoint?.node_id ? " selected" : ""}`}
                  onClick={() => setSelectedPointId(item.node_id)}
                >
                  <strong>{item.title}</strong>
                  <span>
                    {item.evidence_label} · 题目 {item.question_count}
                  </span>
                </button>
              ))
            ) : (
              <div className="legacy-empty compact">本章暂无可命题点位。</div>
            )}
          </div>
        </aside>

        <form className="legacy-question-prompt-panel" onSubmit={submitGeneration}>
          <div className="legacy-question-selected">
            <span className="legacy-row-label">{selectedPoint?.evidence_label || "待选择点位"}</span>
            <strong>{selectedPoint?.title || "请选择实验点位"}</strong>
            <p>{selectedPoint?.breadcrumb_titles.join(" / ") || "选择一个点位后，可以输入教师提示词生成待审题目。"}</p>
          </div>
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
            教师提示词
            <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} />
          </label>
          <div className="legacy-question-demo-actions">
            <button className="primary-button" disabled={generating || !canGenerate}>
              {generating ? "生成中..." : "生成待审题"}
            </button>
            <button
              type="button"
              className="legacy-secondary-button"
              onClick={() =>
                setPrompt(
                  selectedPoint
                    ? `请围绕“${selectedPoint.title}”生成偏安全注意与易错辨析的课堂测评题，帮助学生区分常见实验现象。`
                    : prompt,
                )
              }
            >
              改为安全与易错倾向
            </button>
          </div>
          {notice ? <div className="legacy-notice compact">{notice}</div> : null}
        </form>

        <section className="legacy-question-review-panel">
          <div className="legacy-question-review-head">
            <strong>待审题目</strong>
            <span>{pendingCount || drafts.length} 条</span>
          </div>
          {drafts.length ? (
            <div className="legacy-question-candidate-list">
              {drafts.slice(0, 4).map((draft) => (
                <DraftReviewCard key={draft.id} draft={draft} onReview={reviewDraft} />
              ))}
            </div>
          ) : (
            <div className="legacy-empty compact">暂无待审题目。输入提示词后会在这里显示教师审核卡片。</div>
          )}
        </section>
      </div>
    </section>
  );
}

function defaultQuestionPrompt(point?: LegacyQuestionDemoPoint): string {
  return `请围绕“${point?.title || "实验点位"}”生成 1 道适合课堂测评的题目，重点考查实验现象观察与结论判断。`;
}

function promptIntent(prompt: string): "phenomenon" | "safety" | "principle" {
  if (/安全|易错|误区|混淆|倾向|辨析/.test(prompt)) return "safety";
  if (/现象|观察|颜色|沉淀|褪色|显色|描述/.test(prompt)) return "phenomenon";
  return "principle";
}

function buildLegacyQuestionDrafts(
  point: LegacyQuestionDemoPoint,
  questionTypes: ObjectiveQuestionType[],
  count: number,
  prompt: string,
  startIndex: number,
): LegacyQuestionDraft[] {
  const intent = promptIntent(prompt);
  return Array.from({ length: count }, (_, index) => {
    const questionType = questionTypes[index % questionTypes.length];
    const serial = startIndex + index;
    return {
      key: `${point.node_id}-${serial}`,
      id: `legacy-demo-${serial}-${index + 1}`,
      pointId: point.node_id,
      status: "draft",
      payload: legacyQuestionPayload(point, questionType, intent),
      validation_errors: [],
    };
  });
}

function legacyQuestionPayload(
  point: LegacyQuestionDemoPoint,
  questionType: ObjectiveQuestionType,
  intent: "phenomenon" | "safety" | "principle",
): LegacyQuestionDraft["payload"] {
  const intentStem =
    intent === "safety"
      ? "实验安全与易错判断"
      : intent === "phenomenon"
        ? "实验现象观察"
        : "实验原理判断";

  if (questionType === "true_false") {
    return {
      question_type: "true_false",
      stem: `判断：${point.title}只需观察单一现象即可得出完整结论。`,
      answer: { value: "错误" },
      explanation: `${point.title}需要同时结合现象、条件和反应原理判断，不能只依据单一现象下结论。`,
      difficulty: "basic",
    };
  }

  if (questionType === "fill_blank") {
    return {
      question_type: "fill_blank",
      stem: `${point.title}的课堂记录应同时写出实验现象、________和结论依据。`,
      answer: { accepted_answers: ["条件控制", "反应条件"] },
      explanation: `记录${point.title}时需要把观察证据与反应条件对应起来，便于复核结论。`,
      difficulty: "basic",
    };
  }

  return {
    question_type: "single_choice",
    stem: `围绕“${point.title}”进行${intentStem}时，下列哪项最适合作为课堂测评的判断依据？`,
    options: [
      { label: "A", text: point.summary },
      { label: "B", text: "只记录试剂名称，不描述颜色、沉淀或气体等变化。" },
      { label: "C", text: "忽略实验条件，直接套用任意同类反应结论。" },
      { label: "D", text: "只依据一次偶然现象，不与教材证据核对。" },
    ],
    answer: { value: "A" },
    explanation: `${point.title}的测评应把教材证据、关键现象和结论判断对应起来。`,
    difficulty: "basic",
  };
}

function DraftReviewCard({
  draft,
  onReview,
}: {
  draft: LegacyQuestionDraft;
  onReview: (draftId: string, status: "published" | "rejected") => void;
}) {
  const payload = draft.payload || {};
  const options = Array.isArray(payload.options) ? payload.options : [];
  const validationErrors = Array.isArray(draft.validation_errors) ? draft.validation_errors : [];
  return (
    <article className="legacy-question-candidate-card">
      <div className="legacy-question-candidate-title">
        <span className="legacy-row-label">{questionTypeLabel(payload.question_type)}</span>
        <span className={`legacy-row-label${draft.status === "published" ? " gold" : ""}`}>
          {draft.status === "published" ? "已入库" : draft.status === "rejected" ? "已退回" : validationErrors.length ? "需复核" : "可入库"}
        </span>
      </div>
      <strong>{payload.stem || "待审题目已生成，等待教师审核。"}</strong>
      {options.length ? (
        <div className="legacy-question-options">
          {options.slice(0, 4).map((option, index) => {
            const { label, text } = normalizeOptionDisplay(option, index);
            return (
              <span key={`${label}-${index}`}>
                <b>{label}</b>
                {text}
              </span>
            );
          })}
        </div>
      ) : null}
      <dl className="legacy-question-answer">
        <div>
          <dt>答案</dt>
          <dd>{answerSummary(payload.answer)}</dd>
        </div>
        <div>
          <dt>解析</dt>
          <dd>{payload.explanation || "教师确认后再发布进入正式题库。"}</dd>
        </div>
      </dl>
      {validationErrors.length ? <div className="legacy-error compact">{validationErrors.join("；")}</div> : null}
      <div className="legacy-question-card-actions">
        <button className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "published")}>
          通过入库
        </button>
        <button className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "rejected")}>
          退回修改
        </button>
      </div>
    </article>
  );
}

function questionTypeLabel(value: string | undefined): string {
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

function normalizeOptionDisplay(option: { label?: string; text?: string } | string, index: number): { label: string; text: string } {
  const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
  const rawText = typeof option === "string" ? option : option.text || "";
  const text = rawText.replace(new RegExp(`^\\s*${label}\\s*[.、．)）:]\\s*`), "");
  return { label, text };
}

function QuestionResourceRow({ item }: { item: TeacherDemoQuestionResource }) {
  return (
    <article className="legacy-resource-row">
      <div>
        <span className="legacy-row-label">{item.published_count > 0 ? "有题" : "待补题"}</span>
      </div>
      <div className="legacy-row-main">
        <strong>{item.title}</strong>
        <p>{item.breadcrumb_titles.join(" / ") || "未绑定目录路径"}</p>
      </div>
      <div className="legacy-row-stats">
        <span>总题 {item.question_count}</span>
        <span>选择 {item.choice_count}</span>
        <span>判断 {item.true_false_count}</span>
        <span>填空 {item.fill_blank_count}</span>
      </div>
    </article>
  );
}

function ClassesPage() {
  const [classReloadKey, setClassReloadKey] = useState(0);
  const [studentReloadKey, setStudentReloadKey] = useState(0);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [className, setClassName] = useState("");
  const [classDescription, setClassDescription] = useState("");
  const [studentId, setStudentId] = useState("");
  const [studentName, setStudentName] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [creatingClass, setCreatingClass] = useState(false);
  const [creatingStudent, setCreatingStudent] = useState(false);
  const classState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, [classReloadKey]);
  const classes = classState.data || [];

  useEffect(() => {
    if (!selectedClassId && classes[0]?.id) setSelectedClassId(classes[0].id);
  }, [classes, selectedClassId]);

  const selectedClass = classes.find((item) => item.id === selectedClassId) || null;
  const studentState = useAsyncData<TeacherStudentSummary[]>(
    () => (selectedClassId ? listTeacherClassStudents(selectedClassId) : Promise.resolve([])),
    [selectedClassId, studentReloadKey],
  );
  const students = studentState.data || [];
  const activatedCount = students.filter((item) => item.activated || item.status === "active").length;
  const pendingCount = students.filter((item) => !item.activated && item.status !== "active" && item.status !== "disabled").length;

  const submitClass = async (event: FormEvent) => {
    event.preventDefault();
    const nextClassName = className.trim();
    if (!nextClassName) {
      setActionError("请先填写班级名称。");
      return;
    }
    setCreatingClass(true);
    setNotice("");
    setActionError("");
    try {
      const created = await createTeacherClass({
        class_name: nextClassName,
        description: classDescription.trim() || undefined,
      });
      setSelectedClassId(created.id);
      setClassName("");
      setClassDescription("");
      setNotice(`已创建班级：${created.class_name}`);
      setClassReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingClass(false);
    }
  };

  const submitStudent = async (event: FormEvent) => {
    event.preventDefault();
    const nextStudentId = studentId.trim();
    const nextStudentName = studentName.trim();
    if (!selectedClassId) {
      setActionError("请先选择班级。");
      return;
    }
    if (!nextStudentId || !nextStudentName) {
      setActionError("请填写学号和姓名。");
      return;
    }
    setCreatingStudent(true);
    setNotice("");
    setActionError("");
    try {
      const created = await createTeacherClassStudent(selectedClassId, {
        student_id: nextStudentId,
        student_name: nextStudentName,
      });
      setStudentId("");
      setStudentName("");
      setNotice(`已创建学生：${created.student_name}（${created.student_id}），初始密码以当前班级设置为准。`);
      setStudentReloadKey((value) => value + 1);
      setClassReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingStudent(false);
    }
  };

  return (
    <PageFrame
      eyebrow="班级与学生管理"
      title="班级"
      description="使用现有班级与花名册接口维护旧学生端可登录的学习范围；新增学生首次登录时使用当前班级的初始密码策略。"
    >
      <StateBlock loading={classState.loading} error={classState.error}>
        <MetricGrid
          metrics={[
            { label: "班级数", value: classes.length, unit: "个" },
            { label: "当前班级学生", value: students.length, unit: "人" },
            { label: "已激活", value: activatedCount, unit: "人" },
            { label: "待首次登录", value: pendingCount, unit: "人" },
          ]}
        />
        {notice ? <div className="legacy-notice">{notice}</div> : null}
        {actionError ? <div className="legacy-error">{actionError}</div> : null}
        <div className="legacy-class-management-grid">
          <section className="legacy-table-card">
            <header>
              <h2>班级列表</h2>
              <span>{classes.length ? `当前共 ${classes.length} 个班级` : "暂无班级"}</span>
            </header>
            <form className="legacy-inline-form" onSubmit={submitClass}>
              <label>
                班级名称
                <input value={className} onChange={(event) => setClassName(event.target.value)} placeholder="例如：无机化学一班" />
              </label>
              <label>
                班级说明
                <input value={classDescription} onChange={(event) => setClassDescription(event.target.value)} placeholder="选填" />
              </label>
              <button className="primary-button" disabled={creatingClass}>
                {creatingClass ? "创建中..." : "创建班级"}
              </button>
            </form>
            <div className="legacy-class-grid management">
              {classes.map((item) => (
                <ClassCard key={item.id} item={item} selected={item.id === selectedClassId} onSelect={() => setSelectedClassId(item.id)} />
              ))}
            </div>
          </section>
          <section className="legacy-table-card">
            <header>
              <h2>学生名单</h2>
              <span>{selectedClass ? selectedClass.class_name : "未选择班级"}</span>
            </header>
            <div className="legacy-roster-note">
              账号为学号；初始密码以当前班级设置为准，可能是统一初始密码或学号。学生首次登录旧学生端后，系统会自动激活账号并关联到当前班级。
            </div>
            <form className="legacy-inline-form two-column" onSubmit={submitStudent}>
              <label>
                学号
                <input disabled={!selectedClassId} value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="例如：2026001" />
              </label>
              <label>
                姓名
                <input disabled={!selectedClassId} value={studentName} onChange={(event) => setStudentName(event.target.value)} placeholder="学生姓名" />
              </label>
              <button className="primary-button" disabled={!selectedClassId || creatingStudent}>
                {creatingStudent ? "创建中..." : "创建学生"}
              </button>
            </form>
            {selectedClassId ? (
              <StateBlock loading={studentState.loading} error={studentState.error}>
                {students.length ? (
                  <div className="legacy-student-table legacy-student-table-management">
                    {students.map((student) => (
                      <StudentRosterRow key={student.id || student.student_id} student={student} />
                    ))}
                  </div>
                ) : (
                  <div className="legacy-empty compact">当前班级暂无学生。</div>
                )}
              </StateBlock>
            ) : (
              <div className="legacy-empty compact">请先创建或选择一个班级。</div>
            )}
          </section>
        </div>
      </StateBlock>
    </PageFrame>
  );
}

function ClassCard({ item, selected, onSelect }: { item: TeacherClassSummary; selected: boolean; onSelect: () => void }) {
  return (
    <button className={`legacy-card class-card legacy-class-card-button ${selected ? "selected" : ""}`} onClick={onSelect}>
      <span className="legacy-row-label">{item.status === "active" ? "使用中" : item.status}</span>
      <h2>{item.class_name}</h2>
      <p>{item.description || "无备注。"}</p>
      <div className="legacy-card-stats">
        <span>学生 {item.student_count}</span>
        <span>{selected ? "已选中" : "点选"}</span>
      </div>
    </button>
  );
}

function StudentRosterRow({ student }: { student: TeacherStudentSummary }) {
  const statusText = student.status === "disabled" ? "已停用" : student.activated || student.status === "active" ? "已激活" : "待首次登录";
  return (
    <article>
      <strong>{student.student_name}</strong>
      <span>{student.student_id}</span>
      <span>{statusText}</span>
      <span>{student.activation_mode === "default_password" ? "班级初始密码" : "自主注册"}</span>
    </article>
  );
}

function AnalyticsPage() {
  const classState = useAsyncData<TeacherDemoClasses>(getTeacherDemoClasses, []);
  const classes = classState.data?.classes || [];
  const [selectedClassId, setSelectedClassId] = useState("");

  useEffect(() => {
    if (!selectedClassId && classes[0]?.id) setSelectedClassId(classes[0].id);
  }, [classes, selectedClassId]);

  const analyticsState = useAsyncData<TeacherDemoAnalytics | null>(
    () => (selectedClassId ? getTeacherDemoClassAnalytics(selectedClassId) : Promise.resolve(null)),
    [selectedClassId],
  );
  const weakState = useAsyncData<TeacherDemoWeakPoints | null>(
    () => (selectedClassId ? getTeacherDemoClassWeakPoints(selectedClassId) : Promise.resolve(null)),
    [selectedClassId],
  );

  const analytics = analyticsState.data;
  const weakPoints = weakState.data?.point_items || [];

  return (
    <PageFrame
      eyebrow="BKT 学情展示"
      title="学情分析"
      description="按班级展示学生掌握情况、答题证据和薄弱实验点位，帮助教师说明个性化复习与智能组卷依据。"
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
        <StateBlock loading={analyticsState.loading || weakState.loading} error={analyticsState.error || weakState.error}>
          {analytics ? (
            <>
              <MetricGrid
                metrics={[
                  { label: "班级人数", value: Number(analytics.metrics.class_size || 0), unit: "人" },
                  { label: "参与学生", value: Number(analytics.metrics.active_students || 0), unit: "人" },
                  { label: "平均分", value: Number(analytics.metrics.average_score || 0), unit: "分" },
                  { label: "薄弱点位", value: weakPoints.length, unit: "项" },
                ]}
              />
              <section className="legacy-table-card">
                <header>
                  <h2>学生掌握情况</h2>
                  <span>{analytics.students.length} 名学生</span>
                </header>
                <div className="legacy-student-table">
                  {analytics.students.map((student) => (
                    <article key={student.student_id}>
                      <strong>{student.student_name}</strong>
                      <span>{student.student_id}</span>
                      <span>平均 {student.average_score}</span>
                      <span>证据 {student.evidence_count}</span>
                      <span>{student.status}</span>
                    </article>
                  ))}
                </div>
              </section>
              <section className="legacy-table-card">
                <header>
                  <h2>薄弱点位排行</h2>
                  <span>{weakPoints.length ? `当前共 ${weakPoints.length} 项` : "暂无薄弱点位"}</span>
                </header>
                <div className="legacy-resource-list">
                  {(weakPoints.length ? weakPoints : weakState.data?.items || []).slice(0, 20).map((item, index) => (
                    <WeakPointRow key={`${item.point_node_id || item.point_key || item.point_title}-${index}`} item={item} />
                  ))}
                </div>
              </section>
            </>
          ) : null}
        </StateBlock>
      </StateBlock>
    </PageFrame>
  );
}

function WeakPointRow({ item }: { item: TeacherDemoWeakPoint }) {
  return (
    <article className="legacy-resource-row">
      <div>
        <span className="legacy-row-label">薄弱</span>
      </div>
      <div className="legacy-row-main">
        <strong>{item.point_title}</strong>
        <p>{item.experiment_title || item.representative_questions[0]?.stem || "暂无代表题。"}</p>
      </div>
      <div className="legacy-row-stats">
        <span>错误 {item.incorrect_count}</span>
        <span>尝试 {item.attempt_count}</span>
        <span>{item.incorrect_rate}%</span>
      </div>
    </article>
  );
}

function EvaluationPage() {
  const { data, error, loading } = useAsyncData<TeacherDemoEvaluationSystem>(getTeacherDemoEvaluationSystem, []);

  return (
    <PageFrame
      eyebrow="分数评价体系"
      title="评价体系"
      description="说明旧版展示中 BKT 掌握度的评价对象、证据来源、分档含义和教学输出。"
    >
      <StateBlock loading={loading} error={error}>
        {data ? (
          <>
            <div className="legacy-evaluation-grid">
              <section className="legacy-card">
                <h2>评价对象</h2>
                <TagList values={data.evaluated_objects} />
              </section>
              <section className="legacy-card">
                <h2>证据来源</h2>
                <TagList values={data.evidence_sources} />
              </section>
              <section className="legacy-card wide">
                <h2>更新机制</h2>
                <p>{data.update_mechanism}</p>
              </section>
              <section className="legacy-card wide">
                <h2>掌握度分档</h2>
                <div className="legacy-band-list">
                  {data.score_bands.map((band) => (
                    <article key={band.label}>
                      <strong>{band.label}</strong>
                      <span>
                        {band.min_score ?? 0} - {band.max_score ?? 100}
                      </span>
                      <p>{band.description}</p>
                    </article>
                  ))}
                </div>
              </section>
              <section className="legacy-card wide">
                <h2>教学输出</h2>
                <TagList values={data.outputs} />
              </section>
            </div>
            <ReportPromptDemo />
          </>
        ) : null}
      </StateBlock>
    </PageFrame>
  );
}

function ReportPromptDemo() {
  const [summaryPrompt, setSummaryPrompt] = useState(defaultReportPrompts.summary);
  const [mistakePrompt, setMistakePrompt] = useState(defaultReportPrompts.mistake);
  const [status, setStatus] = useState<"global" | "saved" | "edited">("global");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);

  const markEdited = () => {
    setStatus("edited");
    setNotice("");
    setActionError("");
  };

  const appendVariable = (variable: string) => {
    setSummaryPrompt((current) => `${current}${current.endsWith("\n") ? "" : "\n"}{{${variable}}}`);
    markEdited();
  };

  const restoreDefault = () => {
    setSummaryPrompt(defaultReportPrompts.summary);
    setMistakePrompt(defaultReportPrompts.mistake);
    setStatus("global");
    setNotice("已恢复默认报告 Prompt。");
    setActionError("");
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!summaryPrompt.trim() || !mistakePrompt.trim()) {
      setActionError("请填写报告总结 Prompt 和错题讲解 Prompt。");
      return;
    }
    setSaving(true);
    setNotice("");
    setActionError("");
    await new Promise((resolve) => window.setTimeout(resolve, 300));
    setSaving(false);
    setStatus("saved");
    setNotice("报告 Prompt 已保存，本次演示将按新的总结和错题讲解口径生成报告。");
  };

  return (
    <section className="legacy-table-card legacy-report-prompt-card" data-testid="legacy-report-prompt-demo">
      <header>
        <h2>测评报告 Prompt</h2>
        <div className="legacy-report-prompt-header-actions">
          <span>{status === "global" ? "全局默认" : status === "saved" ? "已保存" : "编辑中"}</span>
          <button className="legacy-secondary-button" type="button" onClick={restoreDefault}>
            恢复默认
          </button>
        </div>
      </header>
      <p className="legacy-report-prompt-intro">
        学生提交课前测试、自主测评、智能测评或点位测评后，会按这里的 Prompt 生成报告总结和错题讲解。
      </p>
      <div className="legacy-report-variable-list">
        {reportPromptVariables.map((variable) => (
          <button type="button" className="legacy-report-variable-chip" onClick={() => appendVariable(variable)} key={variable}>
            {variable}
          </button>
        ))}
      </div>
      <form className="legacy-report-prompt-form" onSubmit={submit}>
        <label className="legacy-textarea-label">
          报告总结 Prompt
          <textarea
            value={summaryPrompt}
            maxLength={6000}
            rows={6}
            onChange={(event) => {
              setSummaryPrompt(event.target.value);
              markEdited();
            }}
          />
          <span className="legacy-report-prompt-count">{summaryPrompt.length} / 6000</span>
        </label>
        <label className="legacy-textarea-label">
          错题讲解 Prompt
          <textarea
            value={mistakePrompt}
            maxLength={6000}
            rows={6}
            onChange={(event) => {
              setMistakePrompt(event.target.value);
              markEdited();
            }}
          />
          <span className="legacy-report-prompt-count">{mistakePrompt.length} / 6000</span>
        </label>
        {notice ? <div className="legacy-notice compact">{notice}</div> : null}
        {actionError ? <div className="legacy-error compact">{actionError}</div> : null}
        <div className="legacy-report-prompt-actions">
          <button className="primary-button" disabled={saving}>
            {saving ? "保存中..." : "保存报告 Prompt"}
          </button>
        </div>
      </form>
    </section>
  );
}

function TagList({ values }: { values: string[] }) {
  return (
    <div className="legacy-tag-list">
      {values.map((value) => (
        <span key={value}>{value}</span>
      ))}
    </div>
  );
}
