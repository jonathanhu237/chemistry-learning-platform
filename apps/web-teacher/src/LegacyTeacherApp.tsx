import { FormEvent, type CSSProperties, type DependencyList, type MouseEvent as ReactMouseEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  bindCatalogPointMedia,
  changeCatalogNodeStatus,
  changeCurrentPassword,
  changeCatalogPointMediaBinding,
  createCatalogNode,
  createTeacherAccount,
  createTeacherClass,
  createTeacherClassStudent,
  generateLegacyPointQuestions,
  getAIConfiguration,
  getAnalyticsDashboard,
  getAuthToken,
  getCatalogNode,
  getTeacherMediaUploadPolicy,
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
  updateAIConfiguration,
  updateCatalogNode,
  updateGlobalAssessmentReportPrompts,
  uploadTeacherMediaAsset,
  type AIConfigurationResponse,
  type AIEnabledFeatureScopes,
  type AnalyticsDashboard,
  type AnalyticsPointScore,
  type AnalyticsScoreCell,
  type CatalogNodeDetail,
  type CatalogNodeKind,
  type CatalogPointMediaBinding,
  type CatalogQuestionBankNode,
  type CatalogQuestionBankResponse,
  type Question,
  type QuestionDraft,
  type TeacherMediaUploadPolicy,
  type StudentAssessmentReportSummary,
  type StudentReport,
  type TeacherClassSummary,
  type TeacherStudentSummary,
  type User,
} from "./api";
import {
  TeacherAlert,
  TeacherButton,
  TeacherCard,
  TeacherContent,
  TeacherDrawer,
  TeacherEmptyState,
  TeacherForm,
  TeacherHeader,
  TeacherInput,
  TeacherLoadingState,
  TeacherMain,
  TeacherMetricGrid,
  TeacherModal,
  TeacherPage,
  TeacherShell,
  TeacherSidebar,
  TeacherSwitch,
  TeacherTooltip,
  TeacherUpload,
  TeacherUiProvider,
} from "./ui/TeacherUI";

const logoSrc = `${import.meta.env.BASE_URL}assets/sysu-lockup-red.svg`;
const forbiddenPathSegments = [
  "/videos",
  "/evaluation",
  "/learning-assistant",
  "/monitoring",
  "/rag",
  "/agent",
  "/provider",
  "/recommend",
  "/question-bank",
  "/scores",
  "/workbench",
  "/import",
];

type RouteKey = "experiments" | "classes" | "questions" | "analytics" | "reports";
type ObjectiveQuestionType = Question["question_type"];

const navItems: Array<{ key: RouteKey; label: string; path: string }> = [
  { key: "experiments", label: "实验管理", path: "/experiments" },
  { key: "classes", label: "班级管理", path: "/classes" },
  { key: "questions", label: "AI 出题", path: "/questions" },
  { key: "analytics", label: "学情分析", path: "/analytics" },
  { key: "reports", label: "评价报告", path: "/reports" },
];

const objectiveQuestionTypeOptions: Array<{ value: ObjectiveQuestionType; label: string }> = [
  { value: "single_choice", label: "选择题" },
  { value: "true_false", label: "判断题" },
  { value: "fill_blank", label: "填空题" },
];
const deepSeekDefaultBaseUrl = "https://api.deepseek.com";
const deepSeekDefaultModel = "deepseek-v4-flash";
const aiConfigFeatureOptions: Array<{ key: keyof AIEnabledFeatureScopes; label: string }> = [
  { key: "question_bank_assistant", label: "AI 出题" },
  { key: "student_learning_analytics", label: "AI 报告" },
];

function catalogContentStatusLabel(status?: string | null, fallback = "未填写资料"): string {
  if (!status) return fallback;
  const labels: Record<string, string> = {
    archived: "已归档",
    draft: "草稿",
    pending: "待发布",
    published: "已发布",
    rejected: "已退回",
    reviewing: "待审核",
  };
  return labels[status] || status;
}

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
  if (path.startsWith("/classes")) return "classes";
  if (path.startsWith("/questions")) return "questions";
  if (path.startsWith("/analytics")) return "analytics";
  if (path.startsWith("/reports")) return "reports";
  return "experiments";
}

export function LegacyTeacherApp() {
  return (
    <TeacherUiProvider>
      <LegacyTeacherAppContent />
    </TeacherUiProvider>
  );
}

function LegacyTeacherAppContent() {
  const path = usePath();
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(getAuthToken()));
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [aiConfigOpen, setAiConfigOpen] = useState(false);

  useEffect(() => {
    if (!getAuthToken()) return;
    let active = true;
    setCheckingSession(true);
    loadCurrentUser()
      .then((value) => {
        if (active && value.role === "teacher") setUser(value);
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

  useEffect(() => {
    if (!path.startsWith("/ai-config")) return;
    setAiConfigOpen(true);
    navigate("/experiments");
  }, [path]);

  useEffect(() => {
    if (!userMenuOpen) return;
    const closeMenu = () => setUserMenuOpen(false);
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setUserMenuOpen(false);
    };
    window.addEventListener("click", closeMenu);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [userMenuOpen]);

  if (checkingSession) return <div className="legacy-teacher-loading">正在载入后台...</div>;
  if (!user) return <LoginScreen onLogin={setUser} />;

  const activeRoute = routeFromPath(isForbiddenPath(path) ? "/experiments" : path);
  const activeLabel = navItems.find((item) => item.key === activeRoute)?.label || "实验管理";
  const logout = () => {
    setAuthToken("");
    window.location.assign("/");
  };

  return (
    <TeacherShell testId="teacher-shell">
      <TeacherSidebar>
        <div className="legacy-sidebar-brand">
          <img src={logoSrc} alt="实验平台标识" className="legacy-sidebar-logo" />
          <strong>无机化学实验教学后台</strong>
        </div>
        <nav aria-label="后台导航">
          {navItems.map((item) => (
            <NavButton key={item.key} active={activeRoute === item.key} label={item.label} path={item.path} testId={`teacher-nav-${item.key}`} />
          ))}
        </nav>
      </TeacherSidebar>
      <TeacherMain>
        <TeacherHeader>
          <nav className="legacy-breadcrumb" aria-label="当前位置">
            <span>后台工作台</span>
            <span aria-hidden="true">&gt;</span>
            <strong>{activeLabel}</strong>
          </nav>
          <div className="legacy-user-menu" onClick={(event) => event.stopPropagation()}>
            <button
              type="button"
              className="legacy-user-menu-button"
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              onClick={() => setUserMenuOpen((value) => !value)}
            >
              <span>{user.display_name || user.username}</span>
              <span aria-hidden="true">▾</span>
            </button>
            {userMenuOpen ? (
              <div className="legacy-user-menu-panel" role="menu">
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setSettingsOpen(true);
                    setUserMenuOpen(false);
                  }}
                >
                  设置
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setAiConfigOpen(true);
                    setUserMenuOpen(false);
                  }}
                >
                  AI 配置
                </button>
                <button type="button" role="menuitem" onClick={logout}>
                  登出
                </button>
              </div>
            ) : null}
          </div>
        </TeacherHeader>
        <SettingsSidebar user={user} open={settingsOpen} onClose={() => setSettingsOpen(false)} />
        <AIConfigurationSidebar open={aiConfigOpen} onClose={() => setAiConfigOpen(false)} />
        <TeacherContent>
          {activeRoute === "questions" ? (
            <QuestionsPage />
          ) : activeRoute === "classes" ? (
            <ClassesPage />
          ) : activeRoute === "analytics" ? (
            <AnalyticsPage />
          ) : activeRoute === "reports" ? (
            <ReportsPage />
          ) : (
            <ExperimentsPage />
          )}
        </TeacherContent>
      </TeacherMain>
    </TeacherShell>
  );
}

function NavButton({ active, label, path, testId }: { active: boolean; label: string; path: string; testId: string }) {
  return (
    <TeacherButton className={active ? "active" : ""} data-testid={testId} onClick={() => navigate(path)}>
      {label}
    </TeacherButton>
  );
}

function LoginScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (values: { username: string; password: string }) => {
    setSubmitting(true);
    setError("");
    try {
      const response = await teacherLogin(values.username, values.password);
      if (response.user.role !== "teacher") {
        throw new Error("该账号不能进入后台。");
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
      <section className="legacy-teacher-login-panel">
        <div className="legacy-teacher-login-identity">
          <img src={logoSrc} alt="实验平台标识" />
          <span>Teacher Backoffice</span>
          <h1>无机化学实验教学后台</h1>
          <p>管理实验目录与点位资料，基于点位内容出题，并查看学生学习与报告生成结果。</p>
        </div>
        <TeacherForm
          data-testid="teacher-login-form"
          className="legacy-teacher-login-card"
          layout="vertical"
          initialValues={{ username: "teacher" }}
          requiredMark={false}
          onFinish={submit}
        >
          <div className="legacy-teacher-login-card-head">
            <span>账号登录</span>
            <h2>教师入口</h2>
          </div>
          <TeacherForm.Item label="账号" name="username" rules={[{ required: true, message: "请输入账号。" }]}>
            <TeacherInput name="username" autoComplete="username" />
          </TeacherForm.Item>
          <TeacherForm.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码。" }]}>
            <TeacherInput.Password name="password" autoComplete="current-password" />
          </TeacherForm.Item>
          {error ? <TeacherAlert className="legacy-error" type="error" message={error} /> : null}
          <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={submitting}>
            {submitting ? "登录中..." : "进入后台"}
          </TeacherButton>
        </TeacherForm>
      </section>
    </div>
  );
}

function userRoleLabel(role: User["role"]): string {
  return role === "teacher" ? "教师" : "学生";
}

function SettingsSidebar({ user, open, onClose }: { user: User; open: boolean; onClose: () => void }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordNotice, setPasswordNotice] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [saving, setSaving] = useState(false);
  const [teacherUsername, setTeacherUsername] = useState("");
  const [teacherDisplayName, setTeacherDisplayName] = useState("");
  const [teacherPassword, setTeacherPassword] = useState("");
  const [teacherMustChangePassword, setTeacherMustChangePassword] = useState(true);
  const [teacherNotice, setTeacherNotice] = useState("");
  const [teacherError, setTeacherError] = useState("");
  const [creatingTeacher, setCreatingTeacher] = useState(false);

  useEffect(() => {
    if (!open) return;
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setPasswordNotice("");
    setPasswordError("");
    setSaving(false);
    setTeacherUsername("");
    setTeacherDisplayName("");
    setTeacherPassword("");
    setTeacherMustChangePassword(true);
    setTeacherNotice("");
    setTeacherError("");
    setCreatingTeacher(false);
  }, [open]);

  const submitPassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPasswordNotice("");
    setPasswordError("");
    if (!currentPassword) {
      setPasswordError("请输入当前密码。");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("新密码至少需要 8 位。");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("两次输入的新密码不一致。");
      return;
    }
    setSaving(true);
    try {
      await changeCurrentPassword({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordNotice("个人密码已更新。");
    } catch (caught) {
      setPasswordError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  const submitTeacher = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTeacherNotice("");
    setTeacherError("");
    const username = teacherUsername.trim();
    const displayName = teacherDisplayName.trim();
    if (!username) {
      setTeacherError("请输入教师账号。");
      return;
    }
    if (!displayName) {
      setTeacherError("请输入教师姓名。");
      return;
    }
    if (teacherPassword.length < 8) {
      setTeacherError("初始密码至少需要 8 位。");
      return;
    }

    setCreatingTeacher(true);
    try {
      await createTeacherAccount({
        username,
        display_name: displayName,
        password: teacherPassword,
        must_change_password: teacherMustChangePassword,
      });
      setTeacherUsername("");
      setTeacherDisplayName("");
      setTeacherPassword("");
      setTeacherMustChangePassword(true);
      setTeacherNotice("已添加教师账号。");
    } catch (caught) {
      const message = caught instanceof Error && caught.message === "Teacher username already exists" ? "教师账号已存在。" : legacyTeacherErrorMessage(caught);
      setTeacherError(message);
    } finally {
      setCreatingTeacher(false);
    }
  };

  const busy = saving || creatingTeacher;

  return (
    <TeacherDrawer
      className="legacy-profile-sidebar legacy-settings-sidebar"
      title="设置"
      open={open}
      onClose={onClose}
      placement="right"
      width="min(420px, calc(100vw - 24px))"
      maskClosable={!busy}
      keyboard={!busy}
      destroyOnHidden
    >
      <section className="legacy-profile-sidebar-body legacy-settings-sidebar-body" data-testid="teacher-settings-sidebar" aria-label="设置">
        <div className="legacy-profile-account-card" aria-label="当前账号">
          <div className="legacy-profile-avatar" aria-hidden="true">
            {(user.display_name || user.username).slice(0, 1).toUpperCase()}
          </div>
          <div>
            <span>当前账号</span>
            <strong>{user.display_name || user.username}</strong>
            <small>{user.username}</small>
          </div>
        </div>

        <dl className="legacy-profile-meta-list">
          <div>
            <dt>身份</dt>
            <dd>{userRoleLabel(user.role)}</dd>
          </div>
          <div>
            <dt>账号类型</dt>
            <dd>后台账号</dd>
          </div>
        </dl>

        <form className="legacy-profile-password-form" onSubmit={submitPassword}>
          <div className="legacy-profile-form-head">
            <strong>修改密码</strong>
            <span>保存后请使用新密码登录。</span>
          </div>
          <label>
            当前密码
            <TeacherInput.Password
              aria-label="当前密码"
              autoComplete="current-password"
              autoFocus={open}
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label>
            新密码
            <TeacherInput.Password
              aria-label="新密码"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <label>
            确认新密码
            <TeacherInput.Password
              aria-label="确认新密码"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </label>
          {passwordNotice ? <NoticeBlock>{passwordNotice}</NoticeBlock> : null}
          {passwordError ? <ErrorBlock compact>{passwordError}</ErrorBlock> : null}
          <div className="legacy-profile-sidebar-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={onClose} disabled={busy}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={saving}>
              {saving ? "保存中..." : "保存密码"}
            </TeacherButton>
          </div>
        </form>

        <form className="legacy-profile-password-form legacy-settings-teacher-form" onSubmit={submitTeacher}>
          <div className="legacy-profile-form-head">
            <strong>添加教师账号</strong>
            <span>新老师可使用初始密码进入后台。</span>
          </div>
          <label>
            教师账号
            <TeacherInput
              aria-label="教师账号"
              autoComplete="username"
              value={teacherUsername}
              onChange={(event) => setTeacherUsername(event.target.value)}
              placeholder="例如 teacher2"
            />
          </label>
          <label>
            教师姓名
            <TeacherInput
              aria-label="教师姓名"
              autoComplete="name"
              value={teacherDisplayName}
              onChange={(event) => setTeacherDisplayName(event.target.value)}
              placeholder="例如 李老师"
            />
          </label>
          <label>
            初始密码
            <TeacherInput.Password
              aria-label="初始密码"
              autoComplete="new-password"
              value={teacherPassword}
              onChange={(event) => setTeacherPassword(event.target.value)}
            />
          </label>
          <label className="legacy-settings-switch-row">
            <TeacherSwitch
              aria-label="首次登录必须修改密码"
              checked={teacherMustChangePassword}
              onChange={(checked) => setTeacherMustChangePassword(checked)}
            />
            <span>首次登录必须修改密码</span>
          </label>
          {teacherNotice ? <NoticeBlock>{teacherNotice}</NoticeBlock> : null}
          {teacherError ? <ErrorBlock compact>{teacherError}</ErrorBlock> : null}
          <div className="legacy-profile-sidebar-actions legacy-settings-single-action">
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={creatingTeacher}>
              {creatingTeacher ? "添加中..." : "添加教师"}
            </TeacherButton>
          </div>
        </form>
      </section>
    </TeacherDrawer>
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

function PageFrame({
  eyebrow,
  title,
  description,
  showHeader = true,
  testId,
  children,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  showHeader?: boolean;
  testId?: string;
  children: ReactNode;
}) {
  return (
    <TeacherPage testId={testId}>
      {showHeader ? (
        <section className="legacy-page-head">
          {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
          <h1>{title}</h1>
          {description ? <p>{description}</p> : null}
        </section>
      ) : null}
      {children}
    </TeacherPage>
  );
}

function StateBlock({ loading, error, children }: { loading: boolean; error: string; children: ReactNode }) {
  if (loading) return <TeacherLoadingState />;
  if (error) return <ErrorBlock>{error}</ErrorBlock>;
  return <>{children}</>;
}

function MetricGrid({ metrics }: { metrics: Array<{ label: string; value: ReactNode; unit?: string; description?: string }> }) {
  return <TeacherMetricGrid metrics={metrics} />;
}

function NoticeBlock({ children }: { children: ReactNode }) {
  return <TeacherAlert className="legacy-notice" type="success" message={children} />;
}

function ErrorBlock({ children, compact = false }: { children: ReactNode; compact?: boolean }) {
  return <TeacherAlert className={`legacy-error${compact ? " compact" : ""}`} type="error" message={children} />;
}

function aiConnectivityStatusLabel(status?: string | null): string {
  const labels: Record<string, string> = {
    authenticated: "启用",
    connected: "启用",
    failed: "连接失败",
    not_configured: "未配置",
    stale: "待复检",
    untested: "未检测",
  };
  return labels[status || ""] || "未检测";
}

function aiStatusMessageLabel(message?: string | null): string {
  const normalized = (message || "").trim().toLowerCase();
  if (normalized === "authenticated" || normalized === "connected") return "启用";
  return (message || "未检测").replaceAll("API Key", "API 密钥");
}

function formatDateTime(value?: string | null): string {
  if (!value) return "未记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "未记录";
  return date.toLocaleString("zh-CN", { hour12: false });
}

function normalizedScore(value?: number | string | null): number | null {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return Math.round((numeric > 0 && numeric <= 1 ? numeric * 100 : numeric) * 10) / 10;
}

function scoreLabel(value?: number | string | null, fallback = "-"): string {
  const score = normalizedScore(value);
  if (score === null) return fallback;
  return `${Number.isInteger(score) ? score.toFixed(0) : score.toFixed(1)} 分`;
}

function analyticsScoreCell(row: AnalyticsDashboard["matrix"][number], columnId: string): AnalyticsScoreCell | null {
  return row.experiment_groups?.[columnId] || row.experiments?.[columnId] || null;
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

type CatalogFileTreeNode = CatalogQuestionBankNode & { children: CatalogFileTreeNode[] };
type CatalogContextMenuState = { x: number; y: number; parentId: string; parentTitle: string; targetNode?: CatalogQuestionBankNode };
type CatalogCreateRequest = { kind: CatalogNodeKind; parentId: string; parentTitle: string };
type CatalogDeleteRequest = { node: CatalogQuestionBankNode };

function sortCatalogNodes(items: CatalogQuestionBankNode[]): CatalogQuestionBankNode[] {
  return [...items].sort((left, right) => Number(left.display_order || 0) - Number(right.display_order || 0) || left.title.localeCompare(right.title, "zh-Hans-CN"));
}

function buildCatalogFileTree(nodes: CatalogQuestionBankNode[]): CatalogFileTreeNode[] {
  const childrenByParent = new Map<string | null, CatalogQuestionBankNode[]>();
  nodes.forEach((node) => {
    const parentId = node.parent_id && nodes.some((item) => item.node_id === node.parent_id) ? node.parent_id : null;
    const current = childrenByParent.get(parentId) || [];
    current.push(node);
    childrenByParent.set(parentId, current);
  });

  const build = (parentId: string | null): CatalogFileTreeNode[] =>
    sortCatalogNodes(childrenByParent.get(parentId) || []).map((node) => ({
      ...node,
      children: build(node.node_id),
    }));

  return build(null);
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
  const rootDirectoryIds = useMemo(() => directoryNodes.filter((item) => !item.parent_id).map((item) => item.node_id), [directoryNodes]);
  const rootDirectoryKey = rootDirectoryIds.join("|");
  const [expandedNodeIds, setExpandedNodeIds] = useState<Set<string>>(new Set());
  const [contextMenu, setContextMenu] = useState<CatalogContextMenuState | null>(null);
  const [createRequest, setCreateRequest] = useState<CatalogCreateRequest | null>(null);
  const [deleteRequest, setDeleteRequest] = useState<CatalogDeleteRequest | null>(null);
  const currentChapterTitle = catalog.chapters.find((chapter) => chapter.chapter_id === chapterId)?.chapter_title || chapterId || "章节";
  const rootCreateTitle = `${currentChapterTitle} 根目录`;

  useEffect(() => {
    if (!selectedNodeId && selectedFallback?.node_id) setSelectedNodeId(selectedFallback.node_id);
    if (selectedNodeId && nodes.length && !nodes.some((item) => item.node_id === selectedNodeId)) setSelectedNodeId(selectedFallback?.node_id || "");
  }, [nodes, selectedFallback, selectedNodeId]);

  useEffect(() => {
    setExpandedNodeIds(new Set(rootDirectoryIds));
  }, [chapterId, rootDirectoryKey]);

  useEffect(() => {
    if (!contextMenu) return;
    const closeMenu = () => setContextMenu(null);
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setContextMenu(null);
    };
    window.addEventListener("click", closeMenu);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [contextMenu]);

  const detailState = useAsyncData<CatalogNodeDetail | null>(() => (selectedFallback?.node_id ? getCatalogNode(selectedFallback.node_id) : Promise.resolve(null)), [
    selectedFallback?.node_id,
    reloadKey,
  ]);
  const detail = detailState.data;
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [visibilitySubmitting, setVisibilitySubmitting] = useState(false);

  const refresh = () => setReloadKey((value) => value + 1);
  const toggleNodeVisibility = async (node: CatalogQuestionBankNode) => {
    const nodeEnabled = node.status === "published";
    setVisibilitySubmitting(true);
    setActionError("");
    try {
      await changeCatalogNodeStatus(node.node_id, nodeEnabled ? "unpublish" : "publish", { includeSubtree: true });
      setNotice(nodeEnabled ? "已关闭学生端展示。" : "已启用学生端展示。");
      refresh();
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setVisibilitySubmitting(false);
    }
  };
  const toggleExpandedNode = (nodeId: string) => {
    setExpandedNodeIds((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };
  const createParentFromNode = (node?: CatalogQuestionBankNode): Pick<CatalogContextMenuState, "parentId" | "parentTitle"> => {
    if (!node) return { parentId: "", parentTitle: rootCreateTitle };
    if (node.node_kind === "directory") return { parentId: node.node_id, parentTitle: node.title };
    const parent = nodes.find((item) => item.node_id === node.parent_id);
    return { parentId: node.parent_id || "", parentTitle: parent?.title || rootCreateTitle };
  };
  const openContextMenu = (event: ReactMouseEvent, node?: CatalogQuestionBankNode) => {
    event.preventDefault();
    event.stopPropagation();
    if (node) setSelectedNodeId(node.node_id);
    const parent = createParentFromNode(node);
    setContextMenu({
      ...parent,
      targetNode: node,
      x: Math.max(12, Math.min(event.clientX, window.innerWidth - 220)),
      y: Math.max(12, Math.min(event.clientY, window.innerHeight - 128)),
    });
  };

  return (
    <PageFrame title="实验管理" showHeader={false} testId="teacher-page-experiments">
      <StateBlock loading={catalog.loading && !catalog.data} error={catalog.error}>
        {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <div className="legacy-management-grid">
          <TeacherCard className="legacy-table-card">
            <header>
              <h2>章节目录与点位</h2>
              <span>目录 {directoryNodes.length} · 点位 {pointNodes.length}</span>
            </header>
            <label className="legacy-select-label">
              章节
              <select
                value={chapterId}
                onChange={(event) => {
                  setChapterId(event.target.value);
                  setSelectedNodeId("");
                  setContextMenu(null);
                  setCreateRequest(null);
                  setDeleteRequest(null);
                }}
              >
                {catalog.chapters.map((chapter) => (
                  <option key={chapter.chapter_id} value={chapter.chapter_id}>
                    {chapter.chapter_title}
                  </option>
                ))}
              </select>
            </label>
            <CatalogFileTree
              nodes={nodes}
              selectedNodeId={selectedFallback?.node_id || ""}
              expandedNodeIds={expandedNodeIds}
              onToggle={toggleExpandedNode}
              onSelect={(node) => {
                setSelectedNodeId(node.node_id);
                if (node.node_kind === "directory" && !expandedNodeIds.has(node.node_id)) toggleExpandedNode(node.node_id);
              }}
              onContextMenu={openContextMenu}
            />
            <CatalogContextMenu
              menu={contextMenu}
              onChoose={(kind) => {
                if (!contextMenu) return;
                setCreateRequest({ kind, parentId: contextMenu.parentId, parentTitle: contextMenu.parentTitle });
                setContextMenu(null);
              }}
              onDelete={() => {
                if (!contextMenu?.targetNode) return;
                setDeleteRequest({ node: contextMenu.targetNode });
                setContextMenu(null);
              }}
            />
            <CreateNodeDialog
              request={createRequest}
              chapterId={chapterId || catalog.chapters[0]?.chapter_id || ""}
              onClose={() => setCreateRequest(null)}
              onCreated={(parentId) => {
                if (parentId) {
                  setExpandedNodeIds((current) => new Set(current).add(parentId));
                }
                refresh();
              }}
              onNotice={setNotice}
              onError={setActionError}
            />
            <DeleteNodeDialog
              request={deleteRequest}
              onClose={() => setDeleteRequest(null)}
              onDeleted={() => {
                setSelectedNodeId("");
                refresh();
              }}
              onNotice={setNotice}
              onError={setActionError}
            />
          </TeacherCard>
          <TeacherCard className="legacy-table-card">
            <header>
              <h2>节点编辑</h2>
              {detail ? <NodeVisibilityControl node={detail.node} disabled={visibilitySubmitting} onToggle={toggleNodeVisibility} /> : null}
            </header>
            <StateBlock loading={detailState.loading && !detailState.data} error={detailState.error}>
              {detail ? (
                <NodeEditor
                  detail={detail}
                  onSaved={(message = "已保存节点资料。") => {
                    setNotice(message);
                    refresh();
                  }}
                  onError={setActionError}
                />
              ) : (
                <TeacherEmptyState message="请选择一个目录或点位。" compact />
              )}
            </StateBlock>
          </TeacherCard>
        </div>
      </StateBlock>
    </PageFrame>
  );
}

function CatalogFileTree({
  nodes,
  selectedNodeId,
  expandedNodeIds,
  onToggle,
  onSelect,
  onContextMenu,
}: {
  nodes: CatalogQuestionBankNode[];
  selectedNodeId: string;
  expandedNodeIds: Set<string>;
  onToggle: (nodeId: string) => void;
  onSelect: (node: CatalogQuestionBankNode) => void;
  onContextMenu: (event: ReactMouseEvent, node?: CatalogQuestionBankNode) => void;
}) {
  const tree = useMemo(() => buildCatalogFileTree(nodes), [nodes]);
  if (!tree.length) return <div onContextMenu={(event) => onContextMenu(event)}><TeacherEmptyState message="当前章节暂无目录或点位。" compact /></div>;
  return (
    <div className="legacy-file-tree" role="tree" aria-label="章节目录与点位" onContextMenu={(event) => onContextMenu(event)}>
      {tree.map((node) => (
        <CatalogFileTreeRow
          key={node.node_id}
          node={node}
          depth={0}
          selectedNodeId={selectedNodeId}
          expandedNodeIds={expandedNodeIds}
          onToggle={onToggle}
          onSelect={onSelect}
          onContextMenu={onContextMenu}
        />
      ))}
    </div>
  );
}

function CatalogFileTreeRow({
  node,
  depth,
  selectedNodeId,
  expandedNodeIds,
  onToggle,
  onSelect,
  onContextMenu,
}: {
  node: CatalogFileTreeNode;
  depth: number;
  selectedNodeId: string;
  expandedNodeIds: Set<string>;
  onToggle: (nodeId: string) => void;
  onSelect: (node: CatalogQuestionBankNode) => void;
  onContextMenu: (event: ReactMouseEvent, node?: CatalogQuestionBankNode) => void;
}) {
  const isDirectory = node.node_kind === "directory";
  const hasChildren = node.children.length > 0;
  const isExpanded = expandedNodeIds.has(node.node_id);
  const isSelected = selectedNodeId === node.node_id;
  const style = { "--tree-depth": depth } as CSSProperties;
  return (
    <div className="legacy-file-tree-branch">
      <div className={`legacy-file-tree-row${isSelected ? " selected" : ""}`} style={style}>
        <button
          type="button"
          className="legacy-file-tree-toggle"
          disabled={!hasChildren}
          aria-label={hasChildren ? (isExpanded ? `收起 ${node.title}` : `展开 ${node.title}`) : undefined}
          onClick={(event) => {
            event.stopPropagation();
            if (hasChildren) onToggle(node.node_id);
          }}
        >
          {hasChildren ? (isExpanded ? "▾" : "▸") : ""}
        </button>
        <button
          type="button"
          className={`legacy-file-tree-node is-${node.node_kind}`}
          role="treeitem"
          aria-selected={isSelected}
          aria-expanded={isDirectory && hasChildren ? isExpanded : undefined}
          onClick={() => onSelect(node)}
          onContextMenu={(event) => {
            onContextMenu(event, node);
          }}
        >
          <span className="legacy-file-tree-icon" aria-hidden="true" />
          <span className="legacy-file-tree-main">
            <strong>{node.title}</strong>
          </span>
        </button>
      </div>
      {hasChildren && isExpanded ? (
        <div className="legacy-file-tree-children" role="group">
          {node.children.map((child) => (
            <CatalogFileTreeRow
              key={child.node_id}
              node={child}
              depth={depth + 1}
              selectedNodeId={selectedNodeId}
              expandedNodeIds={expandedNodeIds}
              onToggle={onToggle}
              onSelect={onSelect}
              onContextMenu={onContextMenu}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function CatalogContextMenu({
  menu,
  onChoose,
  onDelete,
}: {
  menu: CatalogContextMenuState | null;
  onChoose: (kind: CatalogNodeKind) => void;
  onDelete: () => void;
}) {
  if (!menu) return null;
  const target = menu.targetNode;
  const canCreate = !target || target.node_kind === "directory";
  const deleteLabel = target?.node_kind === "directory" ? "删除目录" : "删除点位";
  return (
    <div className="legacy-catalog-context-menu" role="menu" style={{ left: menu.x, top: menu.y }} onClick={(event) => event.stopPropagation()}>
      <strong>{target?.title || menu.parentTitle}</strong>
      {canCreate ? (
        <>
          <button type="button" role="menuitem" onClick={() => onChoose("directory")}>
            新增目录
          </button>
          <button type="button" role="menuitem" onClick={() => onChoose("point")}>
            新增点位
          </button>
        </>
      ) : null}
      {target ? (
        <button type="button" role="menuitem" className="danger" onClick={onDelete}>
          {deleteLabel}
        </button>
      ) : null}
    </div>
  );
}

function CreateNodeDialog({
  request,
  chapterId,
  onClose,
  onCreated,
  onNotice,
  onError,
}: {
  request: CatalogCreateRequest | null;
  chapterId: string;
  onClose: () => void;
  onCreated: (parentId: string) => void;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}) {
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!request) return;
    setTitle("");
    setSubmitting(false);
  }, [request]);

  if (!request) return null;

  const submit = async (values: { title: string }) => {
    const nextTitle = values.title.trim();
    if (!chapterId || !nextTitle) {
      onError("请先选择章节并填写名称。");
      return;
    }
    setSubmitting(true);
    onNotice("");
    onError("");
    try {
      await createCatalogNode({
        chapter_id: chapterId,
        parent_id: request.parentId || null,
        node_kind: request.kind,
        title: nextTitle,
      });
      onNotice(request.kind === "point" ? "已新增点位。" : "已新增目录。");
      onCreated(request.parentId);
      onClose();
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <TeacherModal
      open
      className="legacy-create-dialog"
      title={request.kind === "directory" ? "新增目录" : "新增点位"}
      onCancel={onClose}
      footer={null}
      maskClosable={!submitting}
    >
      <span className="legacy-create-dialog-location">位置：{request.parentTitle}</span>
      <TeacherForm className="legacy-create-dialog-form" layout="vertical" initialValues={{ title }} onFinish={submit}>
        <TeacherForm.Item label="名称" name="title" rules={[{ required: true, message: "请输入名称。" }]}>
          <TeacherInput
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder={request.kind === "directory" ? "输入目录名称" : "输入实验点位名称"}
            autoFocus
          />
        </TeacherForm.Item>
        <div className="legacy-create-dialog-actions">
          <TeacherButton type="default" className="legacy-secondary-button" onClick={onClose}>
            取消
          </TeacherButton>
          <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={submitting}>
            {submitting ? "创建中..." : request.kind === "directory" ? "创建目录" : "创建点位"}
          </TeacherButton>
        </div>
      </TeacherForm>
    </TeacherModal>
  );
}

function DeleteNodeDialog({
  request,
  onClose,
  onDeleted,
  onNotice,
  onError,
}: {
  request: CatalogDeleteRequest | null;
  onClose: () => void;
  onDeleted: () => void;
  onNotice: (value: string) => void;
  onError: (value: string) => void;
}) {
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!request) return;
    setSubmitting(false);
  }, [request]);

  if (!request) return null;

  const isDirectory = request.node.node_kind === "directory";
  const submit = async () => {
    setSubmitting(true);
    onNotice("");
    onError("");
    try {
      await changeCatalogNodeStatus(request.node.node_id, "archive", { includeSubtree: true });
      onNotice(isDirectory ? "已删除目录及其下级内容。" : "已删除点位。");
      onDeleted();
      onClose();
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <TeacherModal
      open
      className="legacy-create-dialog"
      title={isDirectory ? "删除目录" : "删除点位"}
      onCancel={onClose}
      footer={null}
      maskClosable={!submitting}
    >
      <div className="legacy-delete-dialog-body">
        <strong>{request.node.title}</strong>
        <p>{isDirectory ? "删除目录会同时删除它下面的目录和点位。相关视频、题目和历史引用不会被物理清除。" : "删除点位会将它从章节目录中移除。相关视频、题目和历史引用不会被物理清除。"}</p>
      </div>
      <div className="legacy-create-dialog-actions">
        <TeacherButton type="default" className="legacy-secondary-button" onClick={onClose} disabled={submitting}>
          取消
        </TeacherButton>
        <TeacherButton type="primary" danger className="primary-button" disabled={submitting} onClick={submit}>
          {submitting ? "删除中..." : "确认删除"}
        </TeacherButton>
      </div>
    </TeacherModal>
  );
}

function NodeVisibilityControl({ node, disabled, onToggle }: { node: CatalogQuestionBankNode; disabled: boolean; onToggle: (node: CatalogQuestionBankNode) => void }) {
  const nodeEnabled = node.status === "published";
  const helpId = `legacy-visibility-help-${node.node_id}`;

  return (
    <div className="legacy-header-visibility">
      <TeacherSwitch
        className={`legacy-enable-switch${nodeEnabled ? " is-on" : ""}`}
        checked={nodeEnabled}
        aria-label="学生端可见"
        disabled={disabled}
        checkedChildren="启用"
        unCheckedChildren="关闭"
        onChange={() => onToggle(node)}
      />
      <span className="legacy-help-tooltip">
        <TeacherTooltip title="关闭后，该节点及下级不会展示给学生。">
          <button type="button" className="legacy-help-dot" aria-label="学生端展示说明" aria-describedby={helpId}>
            ?
          </button>
        </TeacherTooltip>
        <span id={helpId} className="legacy-help-bubble" role="tooltip">
          关闭后，该节点及下级不会展示给学生。
        </span>
      </span>
    </div>
  );
}

function NodeEditor({ detail, onSaved, onError }: { detail: CatalogNodeDetail; onSaved: (message?: string) => void; onError: (value: string) => void }) {
  const node = detail.node;
  const content = detail.point_content;
  const [title, setTitle] = useState(node.title || "");
  const [principle, setPrinciple] = useState(content?.principle_text || content?.principle_equation || "");
  const [phenomenon, setPhenomenon] = useState(content?.phenomenon_explanation || "");
  const [safety, setSafety] = useState(content?.safety_note || "");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setTitle(node.title || "");
    setPrinciple(content?.principle_text || content?.principle_equation || "");
    setPhenomenon(content?.phenomenon_explanation || "");
    setSafety(content?.safety_note || "");
  }, [node.node_id, node.title, content]);

  const save = async () => {
    if (!title.trim()) {
      onError("请填写节点名称。");
      return;
    }
    setSubmitting(true);
    onError("");
    try {
      await updateCatalogNode(node.node_id, {
        title: title.trim(),
      });
      if (node.node_kind === "point") {
        await saveCatalogPointContent(node.node_id, {
          point_title: title.trim(),
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

  return (
    <TeacherForm className="legacy-editor-form" layout="vertical" onFinish={save}>
      <TeacherForm.Item label="名称">
        <TeacherInput value={title} onChange={(event) => setTitle(event.target.value)} />
      </TeacherForm.Item>
      {node.node_kind === "point" ? (
        <div className="legacy-point-content-fields">
          <TeacherForm.Item label="原理">
            <TeacherInput.TextArea value={principle} onChange={(event) => setPrinciple(event.target.value)} rows={3} />
          </TeacherForm.Item>
          <TeacherForm.Item label="现象">
            <TeacherInput.TextArea value={phenomenon} onChange={(event) => setPhenomenon(event.target.value)} rows={3} />
          </TeacherForm.Item>
          <TeacherForm.Item label="安全">
            <TeacherInput.TextArea value={safety} onChange={(event) => setSafety(event.target.value)} rows={3} />
          </TeacherForm.Item>
          <PointVideoManager detail={detail} fallbackTitle={title.trim() || node.title} onSaved={onSaved} onError={onError} />
        </div>
      ) : null}
      <div className="legacy-editor-actions">
        <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={submitting}>
          {submitting ? "保存中..." : "保存"}
        </TeacherButton>
      </div>
    </TeacherForm>
  );
}

function uploadTitleFromFilename(filename: string): string {
  return filename.replace(/\.[^/.]+$/, "").trim() || "点位视频";
}

function formatMediaSize(value?: number | null): string | null {
  if (!value || value <= 0) return null;
  if (value < 1024 * 1024) return `${Math.ceil(value / 1024)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatMediaDuration(value?: number | null): string | null {
  if (!value || value <= 0) return null;
  const totalSeconds = Math.round(value);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes ? `${minutes}:${String(seconds).padStart(2, "0")}` : `${seconds}s`;
}

function pointVideoStatusLabel(binding: CatalogPointMediaBinding): string {
  if (binding.upload_status === "ready") return binding.binding_status === "published" ? "已发布" : "未发布";
  if (binding.upload_status === "processing") return "处理中";
  if (binding.upload_status === "failed") return "处理失败";
  if (binding.upload_status === "replaced") return "已替换";
  return binding.upload_status || "未知状态";
}

function VideoGlyph() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
      <path d="M5 5.5h9.4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
      <path d="m16.4 9.1 4.1-2.2c.7-.4 1.5.1 1.5.9v8.4c0 .8-.8 1.3-1.5.9l-4.1-2.2V9.1Z" />
    </svg>
  );
}

function UploadGlyph() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
      <path d="M12 3v11" />
      <path d="m7.5 7.5 4.5-4.5 4.5 4.5" />
      <path d="M5 14v3.5A2.5 2.5 0 0 0 7.5 20h9A2.5 2.5 0 0 0 19 17.5V14" />
    </svg>
  );
}

function FileGlyph() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
      <path d="M7 3.5h7l4 4V19a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V5A1.5 1.5 0 0 1 7.5 3.5Z" />
      <path d="M14 3.5V8h4" />
      <path d="M9 13h6" />
      <path d="M9 16h4" />
    </svg>
  );
}

function PointVideoManager({
  detail,
  fallbackTitle,
  onSaved,
  onError,
}: {
  detail: CatalogNodeDetail;
  fallbackTitle: string;
  onSaved: (message?: string) => void;
  onError: (value: string) => void;
}) {
  const node = detail.node;
  const binding = detail.media_bindings?.[0] || null;
  const [policy, setPolicy] = useState<TeacherMediaUploadPolicy | null>(null);
  const [videoTitle, setVideoTitle] = useState(binding?.title || fallbackTitle);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    let active = true;
    getTeacherMediaUploadPolicy()
      .then((value) => {
        if (active) setPolicy(value);
      })
      .catch(() => {
        if (active) setPolicy(null);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setVideoTitle(binding?.title || fallbackTitle);
    setVideoFile(null);
  }, [node.node_id, binding?.binding_id, binding?.title, fallbackTitle]);

  const uploadPointVideo = async () => {
    if (!videoFile) {
      onError("请选择要添加的视频文件。");
      return;
    }
    const nextTitle = videoTitle.trim() || fallbackTitle || uploadTitleFromFilename(videoFile.name);
    setSubmitting(true);
    onError("");
    try {
      const asset = await uploadTeacherMediaAsset({ title: nextTitle, file: videoFile });
      await bindCatalogPointMedia(node.node_id, {
        media_asset_id: asset.id,
        title: nextTitle,
        metadata: { source: "teacher_point_editor" },
      });
      setVideoFile(null);
      onSaved(asset.upload_status === "ready" ? "已添加点位视频。" : "已上传并绑定点位视频，处理完成后学生端可播放。");
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  const removePointVideo = async () => {
    if (!binding) return;
    setRemoving(true);
    onError("");
    try {
      await changeCatalogPointMediaBinding(binding.binding_id, "delete");
      onSaved("已移除点位视频。");
    } catch (caught) {
      onError(legacyTeacherErrorMessage(caught));
    } finally {
      setRemoving(false);
    }
  };

  const currentMeta = [
    binding?.original_file_name || null,
    formatMediaSize(binding?.playback_file_size_bytes || binding?.source_file_size_bytes),
    formatMediaDuration(binding?.playback_duration_seconds),
  ].filter(Boolean);
  const selectedFileMeta = [videoFile?.type || null, formatMediaSize(videoFile?.size)].filter(Boolean);
  const policyText = policy ? `支持 ${policy.allowed_extensions.join(" / ")}，单文件不超过 ${policy.max_media_upload_mb} MB。` : "支持常见视频格式，文件限制以后端校验为准。";

  return (
    <section className="legacy-point-video-panel" aria-labelledby="legacy-point-video-title">
      <header className="legacy-point-video-head">
        <div>
          <h3 id="legacy-point-video-title">点位视频</h3>
          <p>当前点位只保留一个学生端视频，上传新文件会替换现有绑定。</p>
        </div>
        {binding ? <span className={`legacy-point-video-status status-${binding.upload_status}`}>{pointVideoStatusLabel(binding)}</span> : <span className="legacy-point-video-status status-empty">未添加</span>}
      </header>
      {binding ? (
        <div className="legacy-point-video-current">
          <div className="legacy-point-video-preview">
            <VideoGlyph />
          </div>
          <div>
            <strong>{binding.title}</strong>
            {currentMeta.length ? (
              <span className="legacy-point-video-meta">
                {currentMeta.map((item) => (
                  <small key={item}>{item}</small>
                ))}
              </span>
            ) : null}
            {binding.error_reason ? <small>{binding.error_reason}</small> : null}
          </div>
          <TeacherButton htmlType="button" danger className="legacy-secondary-button" disabled={removing || submitting} onClick={removePointVideo}>
            {removing ? "移除中..." : "移除视频"}
          </TeacherButton>
        </div>
      ) : (
        <div className="legacy-point-video-empty">
          <div className="legacy-point-video-preview is-empty">
            <VideoGlyph />
          </div>
          <div>
            <strong>当前点位暂无视频。</strong>
            <span>添加后，学生端会在处理完成的可播放视频中读取这一条。</span>
          </div>
        </div>
      )}
      <div className="legacy-point-video-upload">
        <TeacherForm.Item label="视频标题">
          <TeacherInput value={videoTitle} onChange={(event) => setVideoTitle(event.target.value)} />
        </TeacherForm.Item>
        <div className="legacy-point-video-actions">
          <TeacherUpload
            accept={policy?.allowed_extensions?.join(",") || "video/*"}
            beforeUpload={(file) => {
              setVideoFile(file);
              if (!videoTitle.trim()) setVideoTitle(uploadTitleFromFilename(file.name));
              return false;
            }}
            maxCount={1}
            showUploadList={false}
          >
            <button type="button" className={`legacy-point-video-picker${videoFile ? " has-file" : ""}`} disabled={submitting || removing}>
              <span className="legacy-point-video-picker-icon">{videoFile ? <FileGlyph /> : <UploadGlyph />}</span>
              <span>
                <strong>{videoFile ? videoFile.name : "选择视频文件"}</strong>
                <small>{videoFile ? selectedFileMeta.join(" / ") || "已选择，等待上传" : policyText}</small>
              </span>
            </button>
          </TeacherUpload>
          <div className="legacy-point-video-command-stack">
            <TeacherButton type="primary" htmlType="button" className="primary-button" disabled={!videoFile || submitting || removing} onClick={uploadPointVideo}>
              {submitting ? "上传中..." : binding ? "上传并替换" : "上传并绑定"}
            </TeacherButton>
            {videoFile ? (
              <TeacherButton
                htmlType="button"
                className="legacy-secondary-button"
                disabled={submitting || removing}
                onClick={() => setVideoFile(null)}
              >
                清除选择
              </TeacherButton>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function AIConfigurationSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [reloadKey, setReloadKey] = useState(0);
  const state = useAsyncData<AIConfigurationResponse | null>(() => (open ? getAIConfiguration() : Promise.resolve(null)), [reloadKey, open]);
  const [baseUrl, setBaseUrl] = useState(deepSeekDefaultBaseUrl);
  const [model, setModel] = useState(deepSeekDefaultModel);
  const [apiKey, setApiKey] = useState("");
  const [checkInterval, setCheckInterval] = useState(30);
  const [enabledFeatures, setEnabledFeatures] = useState<AIEnabledFeatureScopes>({
    rag_access_enabled: true,
    student_ai_assistant: true,
    student_learning_analytics: true,
    question_bank_assistant: true,
    teacher_learning_analytics: true,
  });
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const config = state.data;
    if (!config) return;
    setBaseUrl(config.base_url || config.chat_provider?.base_url || deepSeekDefaultBaseUrl);
    setModel(config.model || config.chat_provider?.model || deepSeekDefaultModel);
    setCheckInterval(config.connection_check_interval_minutes || 30);
    setEnabledFeatures((current) => ({
      ...current,
      ...(config.enabled_features || {}),
      question_bank_assistant: config.enabled_features?.question_bank_assistant ?? true,
      student_learning_analytics: config.enabled_features?.student_learning_analytics ?? true,
    }));
    setApiKey("");
    setNotice("");
    setActionError("");
  }, [state.data]);

  const toggleFeature = (key: keyof AIEnabledFeatureScopes, enabled: boolean) => {
    setEnabledFeatures((current) => ({ ...current, [key]: enabled }));
  };

  const saveConfig = async (event: FormEvent) => {
    event.preventDefault();
    const nextBaseUrl = baseUrl.trim().replace(/\/+$/, "");
    const nextModel = model.trim();
    const nextApiKey = apiKey.trim();
    if (!nextBaseUrl || !nextModel) {
      setActionError("请填写接口地址和模型名称。");
      return;
    }
    setSaving(true);
    setNotice("");
    setActionError("");
    try {
      await updateAIConfiguration({
        provider: "openai",
        base_url: nextBaseUrl,
        model: nextModel,
        ...(nextApiKey ? { api_key: nextApiKey } : {}),
        connection_check_interval_minutes: checkInterval,
        enabled_features: enabledFeatures,
        chat_provider: {
          provider: "openai",
          base_url: nextBaseUrl,
          model: nextModel,
          ...(nextApiKey ? { api_key: nextApiKey } : {}),
        },
      });
      setApiKey("");
      setNotice("AI 模型配置已保存。");
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  const status = state.data?.status;
  const configuredKey = state.data?.api_key_configured ? state.data.api_key_fingerprint || "已保存" : "未保存";

  return (
    <TeacherDrawer
      className="legacy-ai-config-sidebar"
      title="AI 模型配置"
      open={open}
      onClose={onClose}
      placement="right"
      width="min(520px, calc(100vw - 24px))"
      maskClosable={!saving}
      keyboard={!saving}
      destroyOnHidden
    >
      <section className="legacy-ai-config-sidebar-body" data-testid="teacher-ai-config-sidebar" aria-label="AI 配置">
        {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <StateBlock loading={state.loading && !state.data} error={state.error}>
          <div className="legacy-ai-config-provider-card">
            <div>
              <span>模型服务</span>
              <strong>DeepSeek 接入</strong>
              <small>OpenAI 兼容接口，用于 AI 出题和 AI 报告。</small>
            </div>
            <em>{aiConnectivityStatusLabel(status?.connectivity_status)}</em>
          </div>
          <form className="legacy-ai-config-form" onSubmit={saveConfig}>
            <label>
              接口地址
              <TeacherInput value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
            </label>
            <label>
              模型名称
              <TeacherInput list="legacy-deepseek-models" value={model} onChange={(event) => setModel(event.target.value)} />
              <datalist id="legacy-deepseek-models">
                <option value="deepseek-v4-flash" />
                <option value="deepseek-v4-pro" />
              </datalist>
            </label>
            <label>
              API 密钥
              <TeacherInput.Password
                aria-label="API 密钥"
                autoComplete="off"
                value={apiKey}
                placeholder={state.data?.api_key_configured ? "留空则保留已保存密钥" : ""}
                onChange={(event) => setApiKey(event.target.value)}
              />
            </label>
            <label>
              连接检测间隔
              <select value={checkInterval} onChange={(event) => setCheckInterval(Number(event.target.value) || 30)}>
                <option value={5}>5 分钟</option>
                <option value={15}>15 分钟</option>
                <option value={30}>30 分钟</option>
                <option value={60}>60 分钟</option>
                <option value={180}>180 分钟</option>
              </select>
            </label>
            <fieldset className="legacy-ai-feature-fieldset">
              <legend>启用范围</legend>
              {aiConfigFeatureOptions.map((item) => (
                <label key={item.key}>
                  <TeacherSwitch checked={Boolean(enabledFeatures[item.key])} onChange={(checked) => toggleFeature(item.key, checked)} />
                  <span>{item.label}</span>
                </label>
              ))}
            </fieldset>
            <dl className="legacy-ai-status-list">
              <div>
                <dt>模型</dt>
                <dd>{state.data?.model || deepSeekDefaultModel}</dd>
              </div>
              <div>
                <dt>密钥</dt>
                <dd>{configuredKey}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>{aiStatusMessageLabel(status?.message)}</dd>
              </div>
              <div>
                <dt>上次检测</dt>
                <dd>{formatDateTime(status?.last_checked_at)}</dd>
              </div>
              <div>
                <dt>近期调用</dt>
                <dd>
                  请求 {status?.recent_request_count ?? 0} 次，错误 {status?.recent_error_count ?? 0} 次
                </dd>
              </div>
            </dl>
            <div className="legacy-ai-config-sidebar-actions">
              <TeacherButton
                type="default"
                className="legacy-secondary-button"
                disabled={saving}
                onClick={() => {
                  setBaseUrl(deepSeekDefaultBaseUrl);
                  setModel(deepSeekDefaultModel);
                }}
              >
                使用默认值
              </TeacherButton>
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={saving}>
                {saving ? "保存中..." : "保存配置"}
              </TeacherButton>
            </div>
          </form>
        </StateBlock>
      </section>
    </TeacherDrawer>
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
  const workbenchMetrics = [
    { label: "题目总数", value: Number(catalog.data?.totals.question_count || 0), unit: "题" },
    { label: "已发布", value: Number(catalog.data?.totals.published_count || 0), unit: "题" },
    { label: "待审题", value: Number(draftsState.data?.items.filter((item) => item.status === "draft").length || 0), unit: "题" },
    { label: "点位", value: points.length, unit: "项" },
  ];

  return (
    <PageFrame
      title="AI 出题"
      showHeader={false}
      testId="teacher-page-questions"
    >
      <StateBlock loading={catalog.loading && !catalog.data} error={catalog.error}>
        {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <TeacherCard className="legacy-table-card legacy-question-workbench">
          <header className="legacy-question-workbench-head">
            <div>
              <span className="legacy-section-kicker">点位资料直接命题</span>
              <h2>命题工作区</h2>
            </div>
            <div className="legacy-question-summary-strip" aria-label="AI 出题概览">
              {workbenchMetrics.map((metric) => (
                <article key={metric.label}>
                  <span>{metric.label}</span>
                  <strong>
                    {metric.value}
                    <small>{metric.unit}</small>
                  </strong>
                </article>
              ))}
            </div>
          </header>
          <div className="legacy-question-demo-grid">
            <aside className="legacy-question-point-panel" aria-label="点位来源">
              <div className="legacy-question-panel-head">
                <div>
                  <span className="legacy-section-kicker">01</span>
                  <h3>点位来源</h3>
                </div>
                <span>{points.length} 项</span>
              </div>
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
                    <span>{catalogContentStatusLabel(point.content_status)} · 题目 {point.counts?.question_count || 0}</span>
                  </button>
                ))}
              </div>
            </aside>
            <form className="legacy-question-prompt-panel" onSubmit={generate}>
              <div className="legacy-question-panel-head">
                <div>
                  <span className="legacy-section-kicker">02</span>
                  <h3>生成配置</h3>
                </div>
                <div className="legacy-question-panel-actions">
                  <span>{questionTypes.length} 类题型</span>
                  <TeacherButton type="primary" htmlType="submit" className="primary-button legacy-question-generate-button" disabled={generating || !selectedPoint}>
                    {generating ? "生成中..." : "生成待审题"}
                  </TeacherButton>
                </div>
              </div>
              <PointContentSummary detail={detailState.data} loading={detailState.loading} />
              <fieldset className="legacy-question-type-row">
                <legend>题型与数量</legend>
                {objectiveQuestionTypeOptions.map((item) => (
                  <label key={item.value} className={questionTypes.includes(item.value) ? "selected" : ""}>
                    <input type="checkbox" checked={questionTypes.includes(item.value)} onChange={(event) => toggleQuestionType(item.value, event.target.checked)} />
                    <span>{item.label}</span>
                  </label>
                ))}
                <label className="legacy-question-count-control">
                  <span>数量</span>
                  <select value={count} onChange={(event) => setCount(Number(event.target.value) || 1)}>
                    {[1, 2, 3].map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
              </fieldset>
              <label className="legacy-textarea-label">
                教师要求
                <TeacherInput.TextArea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} />
              </label>
            </form>
            <section className="legacy-question-review-panel" aria-label="待审队列">
              <div className="legacy-question-review-head">
                <div>
                  <span className="legacy-section-kicker">03</span>
                  <strong>待审题</strong>
                </div>
                <span>{draftsState.loading ? "读取中" : `${draftsState.data?.items.length || 0} 条`}</span>
              </div>
              <StateBlock loading={draftsState.loading && !draftsState.data} error={draftsState.error}>
                {draftsState.data?.items.length ? (
                  <div className="legacy-question-candidate-list">
                    {draftsState.data.items.slice(0, 5).map((draft) => (
                      <DraftReviewCard key={draft.id} draft={draft} onReview={reviewDraft} />
                    ))}
                  </div>
                ) : (
                  <TeacherEmptyState message="暂无待审题。" compact />
                )}
              </StateBlock>
            </section>
          </div>
        </TeacherCard>
        <TeacherCard className="legacy-table-card">
          <header>
            <h2>正式题库</h2>
            <span>{questionsState.data?.total || 0} 题</span>
          </header>
          <StateBlock loading={questionsState.loading && !questionsState.data} error={questionsState.error}>
            <div className="legacy-resource-list">
              {(questionsState.data?.items || []).slice(0, 12).map((question) => (
                <QuestionRow key={question.id} question={question} />
              ))}
            </div>
          </StateBlock>
        </TeacherCard>
      </StateBlock>
    </PageFrame>
  );
}

function PointContentSummary({ detail, loading }: { detail: CatalogNodeDetail | null; loading: boolean }) {
  if (loading) return <TeacherLoadingState message="正在读取点位资料..." />;
  const content = detail?.point_content;
  return (
    <div className="legacy-question-selected">
      <div className="legacy-question-selected-head">
        <span className="legacy-row-label">{catalogContentStatusLabel(content?.content_status, "点位资料")}</span>
        <strong>{content?.point_title || detail?.node.title || "请选择实验点位"}</strong>
      </div>
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
        <TeacherButton className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "publish")}>
          通过入库
        </TeacherButton>
        <TeacherButton className="legacy-secondary-button" disabled={draft.status !== "draft"} onClick={() => onReview(draft.id, "reject")}>
          退回修改
        </TeacherButton>
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
        <span>{catalogContentStatusLabel(question.status, "未知")}</span>
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

function classStatusLabel(status?: string | null): string {
  if (status === "active") return "启用中";
  if (status === "archived") return "已归档";
  if (status === "disabled") return "已停用";
  return status || "未知";
}

function studentStatusLabel(status?: string | null): string {
  if (status === "pending") return "待激活";
  if (status === "active") return "已激活";
  if (status === "disabled") return "已停用";
  return status || "未知";
}

function activationModeLabel(value?: string | null): string {
  if (value === "default_password") return "默认密码";
  if (value === "self_registration") return "自助注册";
  return value || "默认密码";
}

function ClassesPage() {
  const [reloadKey, setReloadKey] = useState(0);
  const [studentReloadKey, setStudentReloadKey] = useState(0);
  const classState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, [reloadKey]);
  const classes = classState.data || [];
  const [selectedClassId, setSelectedClassId] = useState("");
  const selectedClass = classes.find((item) => item.id === selectedClassId) || classes[0] || null;
  const [className, setClassName] = useState("");
  const [classDescription, setClassDescription] = useState("");
  const [studentId, setStudentId] = useState("");
  const [studentName, setStudentName] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [creatingClass, setCreatingClass] = useState(false);
  const [creatingStudent, setCreatingStudent] = useState(false);

  useEffect(() => {
    if (!selectedClassId && selectedClass?.id) setSelectedClassId(selectedClass.id);
    if (selectedClassId && classes.length && !classes.some((item) => item.id === selectedClassId)) setSelectedClassId(classes[0]?.id || "");
  }, [classes, selectedClass, selectedClassId]);

  const studentsState = useAsyncData<TeacherStudentSummary[]>(
    () => (selectedClass?.id ? listTeacherClassStudents(selectedClass.id) : Promise.resolve([])),
    [selectedClass?.id, studentReloadKey],
  );
  const students = studentsState.data || [];
  const classStudentTotal = classes.reduce((total, item) => total + Number(item.student_count || 0), 0);
  const activeStudentTotal = students.filter((item) => item.activated || item.status === "active").length;

  const createClass = async (event: FormEvent) => {
    event.preventDefault();
    const nextName = className.trim();
    if (!nextName) {
      setActionError("请填写班级名称。");
      return;
    }
    setCreatingClass(true);
    setNotice("");
    setActionError("");
    try {
      const response = await createTeacherClass({ class_name: nextName, description: classDescription.trim() || undefined });
      setClassName("");
      setClassDescription("");
      setSelectedClassId(response.id);
      setReloadKey((value) => value + 1);
      setNotice("已创建班级。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingClass(false);
    }
  };

  const createStudent = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedClass?.id) {
      setActionError("请先选择班级。");
      return;
    }
    const nextStudentId = studentId.trim();
    const nextStudentName = studentName.trim();
    if (!nextStudentId || !nextStudentName) {
      setActionError("请填写学号和姓名。");
      return;
    }
    setCreatingStudent(true);
    setNotice("");
    setActionError("");
    try {
      await createTeacherClassStudent(selectedClass.id, {
        student_id: nextStudentId,
        student_name: nextStudentName,
        status: "pending",
        activation_mode: "default_password",
      });
      setStudentId("");
      setStudentName("");
      setStudentReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice("已添加学生。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingStudent(false);
    }
  };

  return (
    <PageFrame
      eyebrow="班级与学生"
      title="班级管理"
      description="维护教师后台可管理的班级与学生名单；学生使用账号密码登录后，会关联到对应班级。"
      showHeader={false}
      testId="teacher-page-classes"
    >
      {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
      {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
      <StateBlock loading={classState.loading && !classState.data} error={classState.error}>
        <MetricGrid
          metrics={[
            { label: "班级总数", value: classes.length, unit: "个" },
            { label: "学生总数", value: classStudentTotal, unit: "人" },
            { label: "当前班级", value: selectedClass?.student_count || students.length || 0, unit: "人" },
            { label: "已激活", value: activeStudentTotal, unit: "人" },
          ]}
        />
        <div className="legacy-class-management-grid">
          <TeacherCard className="legacy-table-card">
            <header>
              <h2>班级列表</h2>
              <span>{classes.length} 个班级</span>
            </header>
            <form className="legacy-inline-form" onSubmit={createClass}>
              <label>
                班级名称
                <TeacherInput value={className} onChange={(event) => setClassName(event.target.value)} placeholder="例如：2026 级无机化学 1 班" />
              </label>
              <label>
                备注
                <TeacherInput.TextArea value={classDescription} onChange={(event) => setClassDescription(event.target.value)} rows={3} placeholder="选填，用于区分教学班或实验分组。" />
              </label>
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={creatingClass}>
                {creatingClass ? "创建中..." : "新增班级"}
              </TeacherButton>
            </form>
            <div className="legacy-class-grid management" aria-label="班级列表">
              {classes.length ? (
                classes.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`legacy-module-card legacy-class-card-button${item.id === selectedClass?.id ? " selected" : ""}`}
                    onClick={() => setSelectedClassId(item.id)}
                  >
                    <span className="legacy-row-label">{classStatusLabel(item.status)}</span>
                    <strong>{item.class_name}</strong>
                    <span>{item.description || "暂无班级备注。"}</span>
                    <div className="legacy-card-stats">
                      <span>学生 {item.student_count || 0}</span>
                      {typeof item.active_students === "number" ? <span>已激活 {item.active_students}</span> : null}
                    </div>
                  </button>
                ))
              ) : (
                <TeacherEmptyState message="暂无班级，请先新增班级。" compact />
              )}
            </div>
          </TeacherCard>
          <TeacherCard className="legacy-table-card">
            <header>
              <h2>学生名单</h2>
              <span>{selectedClass?.class_name || "未选择班级"}</span>
            </header>
            <form className="legacy-inline-form two-column" onSubmit={createStudent}>
              <label>
                学号
                <TeacherInput value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="例如：20260001" disabled={!selectedClass} />
              </label>
              <label>
                姓名
                <TeacherInput value={studentName} onChange={(event) => setStudentName(event.target.value)} placeholder="学生姓名" disabled={!selectedClass} />
              </label>
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={!selectedClass || creatingStudent}>
                {creatingStudent ? "添加中..." : "添加学生"}
              </TeacherButton>
            </form>
            <StateBlock loading={studentsState.loading && !studentsState.data} error={studentsState.error}>
              {selectedClass ? (
                students.length ? (
                  <div className="legacy-student-table legacy-student-table-management" aria-label="学生名单">
                    <article className="legacy-student-table-head">
                      <strong>学生</strong>
                      <span>学号</span>
                      <span>状态</span>
                      <span>登录方式</span>
                    </article>
                    {students.map((student) => (
                      <article key={`${student.student_id}-${student.id || student.class_id || selectedClass.id}`}>
                        <strong>{student.student_name || student.display_name || student.username || student.student_id}</strong>
                        <span>{student.student_id}</span>
                        <span>{student.activated ? "已激活" : studentStatusLabel(student.status)}</span>
                        <span>{activationModeLabel(student.activation_mode)}</span>
                      </article>
                    ))}
                  </div>
                ) : (
                  <TeacherEmptyState message="当前班级暂无学生。" compact />
                )
              ) : (
                <TeacherEmptyState message="请选择或新增班级。" compact />
              )}
            </StateBlock>
          </TeacherCard>
        </div>
      </StateBlock>
    </PageFrame>
  );
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
  const columns = (dashboard?.experiment_groups?.length ? dashboard.experiment_groups : dashboard?.experiments || []).slice(0, 8);
  const [selectedFamilyId, setSelectedFamilyId] = useState("");

  useEffect(() => {
    if (!selectedStudentId && rows[0]?.student_id) setSelectedStudentId(rows[0].student_id);
  }, [rows, selectedStudentId]);
  useEffect(() => {
    if (!selectedFamilyId && columns[0]?.id) setSelectedFamilyId(columns[0].id);
    if (selectedFamilyId && columns.length && !columns.some((item) => item.id === selectedFamilyId)) setSelectedFamilyId(columns[0]?.id || "");
  }, [columns, selectedFamilyId]);

  const reportState = useAsyncData<StudentReport | null>(
    () => (selectedClassId && selectedStudentId ? getStudentReport(selectedClassId, selectedStudentId) : Promise.resolve(null)),
    [selectedClassId, selectedStudentId],
  );
  const selectedStudent = rows.find((row) => row.student_id === selectedStudentId) || rows[0] || null;
  const selectedFamily = columns.find((item) => item.id === selectedFamilyId) || columns[0] || null;
  const selectedFamilyCell = selectedStudent && selectedFamily ? analyticsScoreCell(selectedStudent, selectedFamily.id) : null;
  const selectedPointScores = selectedFamilyCell?.points || [];
  const familyGridStyle = useMemo<CSSProperties>(() => {
    const familyTracks = columns.length ? ` repeat(${columns.length}, minmax(118px, 1fr))` : "";
    return { gridTemplateColumns: `minmax(176px, 1.25fr) 92px${familyTracks}` };
  }, [columns.length]);

  return (
    <PageFrame
      eyebrow="学生学习情况"
      title="学情分析"
      description="按班级展示每个学生的参与、得分、掌握度证据和薄弱点位，数据来自新版学情接口。"
      showHeader={false}
      testId="teacher-page-analytics"
    >
      <StateBlock loading={classState.loading && !classState.data} error={classState.error}>
        <TeacherCard className="legacy-card">
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
        </TeacherCard>
        <StateBlock loading={dashboardState.loading && !dashboardState.data} error={dashboardState.error}>
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
              <TeacherCard className="legacy-table-card">
                <header>
                  <h2>各族元素得分</h2>
                  <span>{rows.length} 名学生</span>
                </header>
                <div className="legacy-family-score-table" role="table" aria-label="各族元素得分">
                  <div className="legacy-family-score-head" role="row" style={familyGridStyle}>
                    <span role="columnheader">学生</span>
                    <span role="columnheader">平均分</span>
                    {columns.map((item) => (
                      <span role="columnheader" key={item.id}>
                        {item.title}
                      </span>
                    ))}
                  </div>
                  {rows.map((student) => (
                    <div className={`legacy-family-score-row${student.student_id === selectedStudentId ? " selected" : ""}`} key={student.student_id} role="row" style={familyGridStyle}>
                      <button type="button" className="legacy-family-student-cell" onClick={() => setSelectedStudentId(student.student_id)}>
                        <strong>{student.student_name}</strong>
                        <small>{student.student_id}</small>
                      </button>
                      <span className="legacy-family-average-cell">{scoreLabel(student.average_score)}</span>
                      {columns.map((item) => {
                        const state = analyticsScoreCell(student, item.id);
                        const selected = student.student_id === selectedStudentId && item.id === selectedFamilyId;
                        return (
                          <button
                            type="button"
                            className={`legacy-family-score-cell${selected ? " selected" : ""}`}
                            key={item.id}
                            aria-label={`${student.student_name} ${item.title} ${scoreLabel(state?.score ?? state?.mastery_score)}`}
                            onClick={() => {
                              setSelectedStudentId(student.student_id);
                              setSelectedFamilyId(item.id);
                            }}
                          >
                            <strong>{scoreLabel(state?.score ?? state?.mastery_score)}</strong>
                            <small>{state ? `${state.evidence_count || 0} 证据` : "无记录"}</small>
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </TeacherCard>
              <TeacherCard className="legacy-table-card">
                <header>
                  <h2>点位得分明细</h2>
                  <span>
                    {selectedStudent?.student_name || "未选择学生"} · {selectedFamily?.title || "未选择族元素"}
                  </span>
                </header>
                {selectedPointScores.length ? (
                  <PointScoreList points={selectedPointScores} />
                ) : (
                  <TeacherEmptyState message="当前学生在该族元素下暂无点位得分。" compact />
                )}
              </TeacherCard>
              <TeacherCard className="legacy-table-card">
                <header>
                  <h2>学生报告摘要</h2>
                  <span>{selectedStudentId || "未选择学生"}</span>
                </header>
                <StateBlock loading={reportState.loading && !reportState.data} error={reportState.error}>
                  {reportState.data ? <StudentReportPanel report={reportState.data} /> : <TeacherEmptyState message="请选择学生。" compact />}
                </StateBlock>
              </TeacherCard>
            </>
          ) : null}
        </StateBlock>
      </StateBlock>
    </PageFrame>
  );
}

function PointScoreList({ points }: { points: AnalyticsPointScore[] }) {
  return (
    <div className="legacy-point-score-list">
      {points.map((point, index) => {
        const score = normalizedScore(point.score ?? point.mastery_score) ?? 0;
        return (
          <article className="legacy-point-score-item" key={point.point_node_id || `${point.experiment_id || "point"}-${index}`}>
            <div>
              <strong>{point.point_title || "未命名点位"}</strong>
              <span>{point.experiment_title || "未关联实验"}</span>
            </div>
            <div className="legacy-point-score-bar" aria-label={`${point.point_title} ${scoreLabel(score)}`}>
              <span style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
            </div>
            <em>{scoreLabel(score)}</em>
            <small>{point.evidence_count || 0} 条证据</small>
          </article>
        );
      })}
    </div>
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
      showHeader={false}
      testId="teacher-page-reports"
    >
      {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
      {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
      <StateBlock loading={(promptState.loading && !promptState.data) || (classState.loading && !classState.data)} error={promptState.error || classState.error}>
        <div className="legacy-management-grid">
          <TeacherCard className="legacy-table-card">
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
                <TeacherInput.TextArea value={summaryPrompt} onChange={(event) => setSummaryPrompt(event.target.value)} rows={7} />
              </label>
              <label className="legacy-textarea-label">
                错题讲解 Prompt
                <TeacherInput.TextArea value={mistakePrompt} onChange={(event) => setMistakePrompt(event.target.value)} rows={7} />
              </label>
              <div className="legacy-editor-actions">
                <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={saving}>
                  {saving ? "保存中..." : "保存 Prompt"}
                </TeacherButton>
                <TeacherButton type="default" className="legacy-secondary-button" disabled={saving} onClick={resetPrompts}>
                  恢复默认
                </TeacherButton>
              </div>
            </form>
          </TeacherCard>
          <TeacherCard className="legacy-table-card">
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
            <StateBlock loading={(studentsState.loading && !studentsState.data) || (reportsState.loading && !reportsState.data)} error={studentsState.error || reportsState.error}>
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
              <StateBlock loading={reportDetailState.loading && !reportDetailState.data} error={reportDetailState.error}>
                {reportDetailState.data ? (
                  <article className="legacy-report-detail">
                    <h2>{reportDetailState.data.title}</h2>
                    <strong>学习总结</strong>
                    <p>{reportDetailState.data.summary.text}</p>
                    <strong>错题讲解</strong>
                    <p>{reportDetailState.data.mistake_explanation.text}</p>
                  </article>
                ) : (
                  <TeacherEmptyState message="当前学生暂无报告。" compact />
                )}
              </StateBlock>
            </StateBlock>
          </TeacherCard>
        </div>
      </StateBlock>
    </PageFrame>
  );
}
