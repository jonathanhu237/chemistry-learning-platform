import { FormEvent, type CSSProperties, type DependencyList, type MouseEvent as ReactMouseEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import katex from "katex";
import { ArrowLeft, ArrowRight } from "lucide-react";
import "katex/dist/katex.min.css";

import {
  bindCatalogPointMedia,
  changeCatalogNodeStatus,
  changeCurrentPassword,
  changeCatalogPointMediaBinding,
  clearTeacherClassSmartAssessmentStrategy,
  createCatalogNode,
  createTeacherAccount,
  createTeacherClass,
  createTeacherClassStudent,
  deleteTeacherClass,
  deleteTeacherClassStudent,
  generateLegacyPointQuestions,
  getAIConfiguration,
  getAnalyticsDashboard,
  getAuthToken,
  getCatalogNode,
  getTeacherClassRegistrationSettings,
  getTeacherClassSmartAssessmentStrategy,
  getTeacherMediaUploadPolicy,
  getGlobalAssessmentReportPrompts,
  getTeacherStudentAssessmentReport,
  importTeacherClassRoster,
  legacyTeacherErrorMessage,
  listTeacherAccounts,
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
  resetTeacherClassStudentPassword,
  revokeQuestionToDraft,
  saveCatalogPointContent,
  setAuthToken,
  teacherLogin,
  updateAIConfiguration,
  updateCatalogNode,
  updateGlobalAssessmentReportPrompts,
  updateQuestionDraft,
  updateTeacherClassStudent,
  updateTeacherAccount,
  uploadTeacherMediaAsset,
  type AIConfigurationResponse,
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
  type SmartAssessmentSettings,
  type SmartAssessmentStrategyResponse,
  type TeacherMediaUploadPolicy,
  type StudentAssessmentReportSummary,
  type TeacherAccount,
  type TeacherClassRegistrationSettings,
  type TeacherClassSummary,
  type TeacherStudentSummary,
  type User,
  updateTeacherClassSmartAssessmentStrategy,
  updateTeacherClassRegistrationSettings,
} from "./api";
import {
  TeacherAlert,
  TeacherButton,
  TeacherCard,
  TeacherContent,
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

type RouteKey = "experiments" | "classes" | "questions" | "paper" | "analytics" | "aiConfig" | "settings";
type ObjectiveQuestionType = Question["question_type"];

const navItems: Array<{ key: RouteKey; label: string; path: string }> = [
  { key: "experiments", label: "实验管理", path: "/experiments" },
  { key: "classes", label: "班级管理", path: "/classes" },
  { key: "questions", label: "AI 出题", path: "/questions" },
  { key: "paper", label: "组卷管理", path: "/paper" },
  { key: "analytics", label: "学情分析", path: "/analytics" },
  { key: "aiConfig", label: "AI 配置", path: "/ai-config" },
  { key: "settings", label: "设置", path: "/settings" },
];

const objectiveQuestionTypeOptions: Array<{ value: ObjectiveQuestionType; label: string }> = [
  { value: "single_choice", label: "选择题" },
  { value: "true_false", label: "判断题" },
  { value: "fill_blank", label: "填空题" },
];
const deepSeekDefaultBaseUrl = "https://api.deepseek.com";
const deepSeekDefaultModel = "deepseek-v4-flash";

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
  if (path.startsWith("/paper")) return "paper";
  if (path.startsWith("/analytics")) return "analytics";
  if (path.startsWith("/ai-config")) return "aiConfig";
  if (path.startsWith("/reports")) return "analytics";
  if (path.startsWith("/settings")) return "settings";
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
    if (!path.startsWith("/reports")) return;
    navigate("/analytics");
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
            <ol>
              <li>
                <span>后台工作台</span>
              </li>
              <li className="legacy-breadcrumb-separator" aria-hidden="true" />
              <li>
                <strong>{activeLabel}</strong>
              </li>
            </ol>
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
                <button type="button" role="menuitem" onClick={logout}>
                  登出
                </button>
              </div>
            ) : null}
          </div>
        </TeacherHeader>
        <TeacherContent>
          {activeRoute === "questions" ? (
            <QuestionsPage />
          ) : activeRoute === "classes" ? (
            <ClassesPage />
          ) : activeRoute === "paper" ? (
            <PaperManagementPage />
          ) : activeRoute === "analytics" ? (
            <AnalyticsPage />
          ) : activeRoute === "aiConfig" ? (
            <AIConfigurationPage />
          ) : activeRoute === "settings" ? (
            <SettingsPage currentUser={user} />
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

function SettingsPage({ currentUser }: { currentUser: User }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordNotice, setPasswordNotice] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [saving, setSaving] = useState(false);
  const [accountUsername, setAccountUsername] = useState("");
  const [accountDisplayName, setAccountDisplayName] = useState("");
  const [accountPassword, setAccountPassword] = useState("");
  const [accountMustChangePassword, setAccountMustChangePassword] = useState(true);
  const [accountNotice, setAccountNotice] = useState("");
  const [accountError, setAccountError] = useState("");
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [updatingAccountId, setUpdatingAccountId] = useState("");
  const [accountReloadKey, setAccountReloadKey] = useState(0);
  const accountState = useAsyncData<TeacherAccount[]>(listTeacherAccounts, [accountReloadKey]);
  const accounts = accountState.data || [];

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

  const accountErrorMessage = (caught: unknown): string => {
    if (caught instanceof Error && caught.message === "Teacher username already exists") return "后台账号已存在。";
    if (caught instanceof Error && caught.message === "Current teacher account cannot be disabled") return "不能停用当前登录账号。";
    return legacyTeacherErrorMessage(caught);
  };

  const submitAccount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAccountNotice("");
    setAccountError("");
    const username = accountUsername.trim();
    const displayName = accountDisplayName.trim();
    if (!username) {
      setAccountError("请输入后台账号。");
      return;
    }
    if (!displayName) {
      setAccountError("请输入显示姓名。");
      return;
    }
    if (accountPassword.length < 8) {
      setAccountError("初始密码至少需要 8 位。");
      return;
    }

    setCreatingAccount(true);
    try {
      await createTeacherAccount({
        username,
        display_name: displayName,
        password: accountPassword,
        must_change_password: accountMustChangePassword,
      });
      setAccountUsername("");
      setAccountDisplayName("");
      setAccountPassword("");
      setAccountMustChangePassword(true);
      setAccountNotice("已新增后台账号。");
      setAccountReloadKey((value) => value + 1);
    } catch (caught) {
      setAccountError(accountErrorMessage(caught));
    } finally {
      setCreatingAccount(false);
    }
  };

  const updateAccountStatus = async (account: TeacherAccount) => {
    const nextStatus = account.status === "active" ? "disabled" : "active";
    setAccountNotice("");
    setAccountError("");
    setUpdatingAccountId(account.id);
    try {
      await updateTeacherAccount(account.id, { status: nextStatus });
      setAccountNotice(`${account.display_name || account.username}已${nextStatus === "active" ? "启用" : "停用"}。`);
      setAccountReloadKey((value) => value + 1);
    } catch (caught) {
      setAccountError(accountErrorMessage(caught));
    } finally {
      setUpdatingAccountId("");
    }
  };

  return (
    <PageFrame title="设置" showHeader={false} testId="teacher-page-settings">
      <section className="legacy-settings-page-grid" data-testid="teacher-settings-page" aria-label="设置">
        <div className="legacy-settings-security-column">
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
            <div className="legacy-profile-sidebar-actions legacy-settings-single-action">
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={saving}>
                {saving ? "保存中..." : "保存密码"}
              </TeacherButton>
            </div>
          </form>
        </div>

        <div className="legacy-settings-account-column">
          <section className="legacy-account-management-card" data-testid="teacher-account-management" aria-label="账号管理">
            <div className="legacy-profile-form-head">
              <strong>账号管理</strong>
              <span>查看和管理可进入后台的账号。</span>
            </div>

            {accountNotice ? <NoticeBlock>{accountNotice}</NoticeBlock> : null}
            {accountError ? <ErrorBlock compact>{accountError}</ErrorBlock> : null}

            <StateBlock loading={accountState.loading} error={accountState.error}>
              {accounts.length ? (
                <div className="legacy-account-table-scroll">
                  <table className="legacy-account-table">
                    <thead>
                      <tr>
                        <th>后台账号</th>
                        <th>状态</th>
                        <th>首次改密</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accounts.map((account) => {
                        const active = account.status === "active";
                        const isCurrent = account.id === currentUser.id;
                        return (
                          <tr key={account.id}>
                            <td>
                              <strong>{account.display_name || account.username}</strong>
                              <span>
                                {account.username}
                                {isCurrent ? <em>本人</em> : null}
                              </span>
                            </td>
                            <td>
                              <span className={`legacy-account-status ${active ? "active" : "disabled"}`}>{active ? "已启用" : "已停用"}</span>
                            </td>
                            <td>{account.must_change_password ? "需要" : "不需要"}</td>
                            <td>
                              {isCurrent ? (
                                <span className="legacy-account-action-note">不可停用</span>
                              ) : (
                                <TeacherButton danger={active} disabled={updatingAccountId === account.id} onClick={() => updateAccountStatus(account)}>
                                  {updatingAccountId === account.id ? "处理中..." : active ? "停用" : "启用"}
                                </TeacherButton>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="legacy-account-empty">暂无后台账号。</div>
              )}
            </StateBlock>

            <form className="legacy-account-create-form" onSubmit={submitAccount}>
              <div className="legacy-account-create-head">
                <strong>新增后台账号</strong>
                <span>新账号可使用初始密码进入后台。</span>
              </div>
              <div className="legacy-account-create-grid">
                <label>
                  后台账号
                  <TeacherInput
                    aria-label="后台账号"
                    autoComplete="username"
                    value={accountUsername}
                    onChange={(event) => setAccountUsername(event.target.value)}
                    placeholder="例如 teacher2"
                  />
                </label>
                <label>
                  显示姓名
                  <TeacherInput
                    aria-label="显示姓名"
                    autoComplete="name"
                    value={accountDisplayName}
                    onChange={(event) => setAccountDisplayName(event.target.value)}
                    placeholder="例如 李老师"
                  />
                </label>
                <label>
                  初始密码
                  <TeacherInput.Password
                    aria-label="初始密码"
                    autoComplete="new-password"
                    value={accountPassword}
                    onChange={(event) => setAccountPassword(event.target.value)}
                  />
                </label>
                <label className="legacy-account-switch-field">
                  首次登录
                  <span className="legacy-account-switch-control">
                    <TeacherSwitch
                      aria-label="首次登录必须修改密码"
                      className={`legacy-enable-switch${accountMustChangePassword ? " is-on" : ""}`}
                      checked={accountMustChangePassword}
                      onChange={(checked) => setAccountMustChangePassword(checked)}
                    />
                    <span>必须修改密码</span>
                  </span>
                </label>
              </div>
              <div className="legacy-profile-sidebar-actions legacy-settings-single-action">
                <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={creatingAccount}>
                  {creatingAccount ? "新增中..." : "新增账号"}
                </TeacherButton>
              </div>
            </form>
          </section>

        </div>
      </section>
    </PageFrame>
  );
}

const smartAssessmentDefaults: SmartAssessmentSettings = {
  enabled: true,
  question_count: 10,
  untested_ratio_percent: 20,
  weak_tendency_percent: 70,
  max_questions_per_experiment: 2,
  weak_curve: 2,
  weak_max_bonus: 9,
};
const smartQuestionCountOptions = [5, 10, 15, 20];
const paperStrategyTicketsFormulaLatex = String.raw`T_i = 1 + w_i \cdot B \cdot \left(\frac{100-s_i}{100}\right)^\gamma`;

function normalizeSmartAssessmentSettings(value?: Partial<SmartAssessmentSettings> | null): SmartAssessmentSettings {
  return { ...smartAssessmentDefaults, ...(value || {}), enabled: true };
}

function smartAssessmentTickets(settings: SmartAssessmentSettings, mastery: number): number {
  const weakness = Math.max(0, Math.min(1, (100 - mastery) / 100));
  return 1 + (settings.weak_tendency_percent / 100) * settings.weak_max_bonus * Math.pow(weakness, settings.weak_curve);
}

function LatexFormula({ formula, label, className = "" }: { formula: string; label: string; className?: string }) {
  const html = useMemo(
    () =>
      katex.renderToString(formula, {
        output: "htmlAndMathml",
        strict: "ignore",
        throwOnError: false,
      }),
    [formula],
  );

  return <span className={`legacy-latex-formula ${className}`.trim()} role="img" aria-label={label} dangerouslySetInnerHTML={{ __html: html }} />;
}

function PaperManagementPage() {
  const classesState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, []);
  const classes = classesState.data || [];
  const [selectedClassId, setSelectedClassId] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SmartAssessmentSettings>(smartAssessmentDefaults);
  const selectedClass = classes.find((item) => item.id === selectedClassId) || classes[0] || null;
  const effectiveClassId = selectedClass?.id || "";
  const strategyState = useAsyncData<SmartAssessmentStrategyResponse | null>(
    () => (effectiveClassId ? getTeacherClassSmartAssessmentStrategy(effectiveClassId) : Promise.resolve(null)),
    [effectiveClassId, reloadKey],
  );
  const strategy = strategyState.data;

  useEffect(() => {
    if (!selectedClassId && classes[0]?.id) setSelectedClassId(classes[0].id);
  }, [classes, selectedClassId]);

  useEffect(() => {
    if (strategy?.strategy) setSettings(normalizeSmartAssessmentSettings(strategy.strategy));
  }, [strategy]);

  const setSetting = (key: keyof SmartAssessmentSettings, value: boolean | number) => {
    setSettings((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!effectiveClassId) return;
    setSaving(true);
    setNotice("");
    setError("");
    try {
      const saved = await updateTeacherClassSmartAssessmentStrategy(effectiveClassId, { ...settings, enabled: true });
      setSettings(normalizeSmartAssessmentSettings(saved.strategy));
      setNotice("智能组卷策略已保存。");
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  const reset = async () => {
    if (!effectiveClassId) return;
    setSaving(true);
    setNotice("");
    setError("");
    try {
      const saved = await clearTeacherClassSmartAssessmentStrategy(effectiveClassId);
      setSettings(normalizeSmartAssessmentSettings(saved.strategy));
      setNotice("已恢复默认智能组卷策略。");
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageFrame title="组卷管理" showHeader={false} testId="teacher-page-paper">
      <StateBlock loading={classesState.loading && !classesState.data} error={classesState.error}>
        {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
        {error ? <ErrorBlock>{error}</ErrorBlock> : null}
        {classes.length ? (
          <div className="legacy-paper-workbench" data-testid="teacher-paper-management">
            <TeacherCard className="legacy-paper-control-card">
              <label className="legacy-paper-class-control">
                <span>当前班级</span>
                <select
                  className="legacy-paper-class-select"
                  aria-label="选择班级"
                  value={effectiveClassId}
                  onChange={(event) => {
                    setSelectedClassId(event.target.value);
                    setNotice("");
                    setError("");
                  }}
                >
                  {classes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.class_name}
                    </option>
                  ))}
                </select>
              </label>
            </TeacherCard>

            <form className="legacy-paper-board-form" onSubmit={submit}>
              <TeacherCard className="legacy-table-card legacy-paper-board">
                <header>
                  <div>
                    <h2>智能组卷策略</h2>
                    <span>{strategy?.has_override ? "当前班级使用独立策略" : "当前班级继承默认策略"}</span>
                  </div>
                  <div className="legacy-paper-board-actions">
                    <TeacherButton type="default" onClick={reset} disabled={saving || !strategy?.has_override}>
                      恢复默认
                    </TeacherButton>
                    <TeacherButton type="primary" htmlType="submit" className="primary-button compact" disabled={saving || !effectiveClassId}>
                      {saving ? "保存中..." : "保存策略"}
                    </TeacherButton>
                  </div>
                </header>

                <div className="legacy-paper-board-grid">
                  <section className="legacy-paper-section" aria-label="策略参数">
                    <h3>策略参数</h3>
                    <table className="legacy-paper-settings-table">
                      <thead>
                        <tr>
                          <th scope="col">参数</th>
                          <th scope="col">当前值</th>
                          <th scope="col">调整</th>
                        </tr>
                      </thead>
                      <tbody>
                        <PaperChoiceField
                          label="每次题量"
                          value={settings.question_count}
                          options={smartQuestionCountOptions}
                          unit="题"
                          onChange={(value) => setSetting("question_count", value)}
                        />
                        <PaperNumberField
                          label="薄弱点位倾向"
                          symbol="w_i"
                          value={settings.weak_tendency_percent}
                          min={0}
                          max={100}
                          step={5}
                          unit="%"
                          onChange={(value) => setSetting("weak_tendency_percent", value)}
                        />
                        <PaperNumberField
                          label="单实验最多题数"
                          value={settings.max_questions_per_experiment}
                          min={1}
                          max={10}
                          unit="题"
                          onChange={(value) => setSetting("max_questions_per_experiment", value)}
                        />
                        <PaperNumberField
                          label="薄弱曲线"
                          symbol="γ"
                          value={settings.weak_curve}
                          min={0.5}
                          max={4}
                          step={0.5}
                          unit=""
                          onChange={(value) => setSetting("weak_curve", value)}
                        />
                        <PaperNumberField
                          label="薄弱加权上限"
                          symbol="B"
                          value={settings.weak_max_bonus}
                          min={1}
                          max={20}
                          step={1}
                          unit="倍"
                          onChange={(value) => setSetting("weak_max_bonus", value)}
                        />
                      </tbody>
                    </table>
                  </section>

                  <section className="legacy-paper-section" aria-label="薄弱权重曲线">
                    <h3>薄弱权重曲线</h3>
                    <div className="legacy-paper-formula-panel" aria-label="策略参数公式">
                      <div className="legacy-paper-formula-expression">
                        <span>票数公式</span>
                        <div className="legacy-paper-formula-lines">
                          <LatexFormula formula={paperStrategyTicketsFormulaLatex} label="tickets 公式" />
                        </div>
                      </div>
                      <p>票数越高，抽中概率越大。</p>
                    </div>
                    <PaperWeakCurve settings={settings} />
                  </section>
                </div>
              </TeacherCard>
            </form>
          </div>
        ) : (
          <TeacherEmptyState message="暂无班级，请先在班级管理中创建班级。" />
        )}
      </StateBlock>
    </PageFrame>
  );
}

function PaperNumberField({
  label,
  symbol,
  value,
  min,
  max,
  step = 1,
  unit,
  onChange,
}: {
  label: string;
  symbol?: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit: string;
  onChange: (value: number) => void;
}) {
  const update = (next: number) => onChange(Math.max(min, Math.min(max, Number.isFinite(next) ? next : min)));
  return (
    <tr>
      <th scope="row">
        <span className="legacy-paper-param-label">
          <span>{label}</span>
          {symbol ? <LatexFormula formula={symbol} label={symbol} className="legacy-paper-param-symbol" /> : null}
        </span>
      </th>
      <td>
        <strong>{value}</strong>
        {unit ? <em>{unit}</em> : null}
      </td>
      <td>
        <div className="legacy-paper-field-control">
          <input aria-label={`${label}滑块`} type="range" min={min} max={max} step={step} value={value} onChange={(event) => update(Number(event.target.value))} />
          <input aria-label={`${label}数值`} type="number" min={min} max={max} step={step} value={value} onChange={(event) => update(Number(event.target.value))} />
        </div>
      </td>
    </tr>
  );
}

function PaperChoiceField({
  label,
  value,
  options,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  options: number[];
  unit: string;
  onChange: (value: number) => void;
}) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td>
        <strong>{value}</strong>
        {unit ? <em>{unit}</em> : null}
      </td>
      <td>
        <div className="legacy-paper-choice-control" aria-label={`${label}选项`}>
          {options.map((option) => (
            <button key={option} type="button" className={value === option ? "active" : ""} onClick={() => onChange(option)}>
              {option}
              {unit}
            </button>
          ))}
        </div>
      </td>
    </tr>
  );
}

function PaperWeakCurve({ settings }: { settings: SmartAssessmentSettings }) {
  const marks = [0, 25, 50, 75, 100];
  const max = Math.max(...marks.map((mastery) => smartAssessmentTickets(settings, mastery)));
  return (
    <table className="legacy-paper-mini-table" aria-label="薄弱权重曲线">
      <thead>
        <tr>
          <th scope="col">
            掌握度 <LatexFormula formula="s_i" label="s_i" className="legacy-paper-param-symbol" />
          </th>
          <th scope="col">
            票数 <LatexFormula formula="T_i" label="T_i" className="legacy-paper-param-symbol" />
          </th>
        </tr>
      </thead>
      <tbody>
        {marks.map((mastery) => {
          const tickets = smartAssessmentTickets(settings, mastery);
          return (
            <tr key={mastery}>
              <th scope="row">{mastery} 分</th>
              <td>
                <b style={{ width: `${Math.max(8, (tickets / max) * 100)}%` }} />
                <span>{tickets.toFixed(1)} 票</span>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
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

function NoticeBlock(_props: { children: ReactNode }) {
  return null;
}

function ErrorBlock({ children, compact = false }: { children: ReactNode; compact?: boolean }) {
  return <TeacherAlert className={`legacy-error${compact ? " compact" : ""}`} type="error" message={children} />;
}

function ReportIcon() {
  return (
    <svg className="legacy-student-report-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none">
      <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7Z" />
      <path d="M14 2v5h5" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </svg>
  );
}

function ScoreDetailIcon() {
  return (
    <svg className="legacy-student-report-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none">
      <path d="M5 7h10" />
      <path d="M5 12h8" />
      <path d="M5 17h10" />
      <path d="m16 10 3 3-3 3" />
    </svg>
  );
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

function formatShortDateTime(value?: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

type AnalyticsFamilyColumn = {
  id: string;
  title: string;
  sourceIds: string[];
  experiment_count?: number;
};

type AnalyticsScoreDetailDialog = {
  student: AnalyticsDashboard["matrix"][number];
  family: AnalyticsFamilyColumn;
  cell: AnalyticsScoreCell | null;
};

type AnalyticsStudentReportDialog = {
  classId: string;
  student: AnalyticsDashboard["matrix"][number];
};

const elementFamilyTitleByChapter: Record<string, string> = {
  CH13: "卤族元素",
  CH14: "氧族元素",
  CH15: "氮族元素",
  CH16: "碳族元素",
  CH17: "硼族元素",
  CH18: "碱金属和碱土金属",
  CH19: "铜锌副族元素",
  CH20: "d 区过渡金属元素",
  CH21: "镧系和锕系元素",
  CH22: "氢和稀有气体",
};
const DEFAULT_ANALYTICS_SCORE = 50;
const ANALYTICS_STUDENT_PAGE_SIZE = 8;
const ANALYTICS_POINT_PAGE_SIZE = 8;

function chapterIdFromText(value?: string | null): string {
  const textValue = String(value || "");
  const chapterCode = textValue.match(/\bCH\s*(\d{2})\b/i);
  if (chapterCode) return `CH${chapterCode[1]}`;
  const chapterNumber = textValue.match(/第\s*(\d{1,2})\s*章/);
  if (chapterNumber) return `CH${String(Number(chapterNumber[1])).padStart(2, "0")}`;
  return "";
}

function analyticsFamilyTitle(value?: string | null): string {
  const textValue = String(value || "").trim();
  const chapterId = chapterIdFromText(textValue);
  if (chapterId && elementFamilyTitleByChapter[chapterId]) return elementFamilyTitleByChapter[chapterId];
  return textValue.replace(/^第\s*\d+\s*章\s*/, "").replace(/^CH\d{2}\s*[-_—:：]?\s*/i, "").trim() || textValue;
}

function analyticsFamilyColumns(
  items: Array<{ id: string; code?: string; title: string; experiment_count?: number }>,
): AnalyticsFamilyColumn[] {
  const columns = new Map<string, AnalyticsFamilyColumn>();
  items.forEach((item) => {
    const chapterId = chapterIdFromText(item.id) || chapterIdFromText(item.code) || chapterIdFromText(item.title);
    const columnId = chapterId || item.id;
    const column = columns.get(columnId) || {
      id: columnId,
      title: chapterId ? elementFamilyTitleByChapter[chapterId] || analyticsFamilyTitle(item.title) : analyticsFamilyTitle(item.title),
      sourceIds: [],
      experiment_count: 0,
    };
    if (!column.sourceIds.includes(item.id)) column.sourceIds.push(item.id);
    column.experiment_count = Number(column.experiment_count || 0) + Number(item.experiment_count || 0);
    columns.set(columnId, column);
  });
  return Array.from(columns.values());
}

function analyticsScoreCell(row: AnalyticsDashboard["matrix"][number], columnId: string): AnalyticsScoreCell | null {
  return row.experiment_groups?.[columnId] || row.experiments?.[columnId] || null;
}

function analyticsScoreCellForColumn(row: AnalyticsDashboard["matrix"][number], column: AnalyticsFamilyColumn): AnalyticsScoreCell | null {
  const cells = column.sourceIds.map((sourceId) => analyticsScoreCell(row, sourceId)).filter((cell): cell is AnalyticsScoreCell => Boolean(cell));
  if (!cells.length) return null;
  if (cells.length === 1) return cells[0];
  const scores = cells.map((cell) => normalizedScore(cell.score ?? cell.mastery_score)).filter((score): score is number => score !== null);
  const score = scores.length ? Math.round((scores.reduce((sum, value) => sum + value, 0) / scores.length) * 10) / 10 : DEFAULT_ANALYTICS_SCORE;
  return {
    status: cells.some((cell) => cell.status === "needs_attention") ? "needs_attention" : cells.every((cell) => cell.status === "completed") ? "completed" : "in_progress",
    mastery_score: score,
    score,
    evidence_count: cells.reduce((sum, cell) => sum + Number(cell.evidence_count || 0), 0),
    attempt_count: cells.reduce((sum, cell) => sum + Number(cell.attempt_count || 0), 0),
    points: cells.flatMap((cell) => cell.points || []),
  };
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
      className="legacy-create-dialog legacy-delete-dialog"
      title={isDirectory ? "删除目录" : "删除点位"}
      onCancel={onClose}
      footer={null}
      maskClosable={!submitting}
    >
      <div className="legacy-delete-dialog-body">
        <strong>{request.node.title}</strong>
        <p>{isDirectory ? "删除目录会同时删除它下面的目录和点位。相关视频、题目和历史引用不会被物理清除。" : "删除点位会将它从章节目录中移除。相关视频、题目和历史引用不会被物理清除。"}</p>
      </div>
      <div className="legacy-delete-dialog-actions">
        <TeacherButton type="default" className="legacy-delete-dialog-cancel" onClick={onClose} disabled={submitting}>
          取消
        </TeacherButton>
        <TeacherButton type="primary" danger className="legacy-delete-dialog-confirm" disabled={submitting} onClick={submit}>
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
  const currentVideoBinding = pointVideoBindingFromDetail(detail);
  const [title, setTitle] = useState(node.title || "");
  const [principle, setPrinciple] = useState(content?.principle_text || content?.principle_equation || "");
  const [phenomenon, setPhenomenon] = useState(content?.phenomenon_explanation || "");
  const [safety, setSafety] = useState(content?.safety_note || "");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [removeVideo, setRemoveVideo] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setTitle(node.title || "");
    setPrinciple(content?.principle_text || content?.principle_equation || "");
    setPhenomenon(content?.phenomenon_explanation || "");
    setSafety(content?.safety_note || "");
  }, [node.node_id, node.title, content]);

  useEffect(() => {
    setVideoFile(null);
    setRemoveVideo(false);
  }, [node.node_id, currentVideoBinding?.binding_id]);

  const save = async () => {
    if (!title.trim()) {
      onError("请填写节点名称。");
      return;
    }
    setSubmitting(true);
    onError("");
    try {
      const nextTitle = title.trim();
      await updateCatalogNode(node.node_id, {
        title: nextTitle,
      });
      if (node.node_kind === "point") {
        await saveCatalogPointContent(node.node_id, {
          point_title: nextTitle,
          principle_mode: "text",
          principle_text: principle.trim() || null,
          phenomenon_explanation: phenomenon.trim() || null,
          safety_note: safety.trim() || null,
        });
        if (removeVideo && currentVideoBinding && !videoFile) {
          await changeCatalogPointMediaBinding(currentVideoBinding.binding_id, "delete");
        }
        if (videoFile) {
          const asset = await uploadTeacherMediaAsset({ title: nextTitle || uploadTitleFromFilename(videoFile.name), file: videoFile });
          await bindCatalogPointMedia(node.node_id, {
            media_asset_id: asset.id,
            title: nextTitle || uploadTitleFromFilename(videoFile.name),
            metadata: { source: "teacher_point_editor" },
          });
        }
      }
      setVideoFile(null);
      setRemoveVideo(false);
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
          <PointVideoManager
            binding={currentVideoBinding}
            selectedFile={videoFile}
            removeExisting={removeVideo}
            disabled={submitting}
            onSelectFile={(file) => {
              setVideoFile(file);
              setRemoveVideo(false);
            }}
            onRemove={() => {
              setVideoFile(null);
              setRemoveVideo(Boolean(currentVideoBinding));
            }}
          />
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
  return filename.replace(/\.[^/.]+$/, "").trim() || "视频";
}

function isPlaceholderPointVideoBinding(binding: CatalogPointMediaBinding): boolean {
  const metadata = binding.metadata || {};
  return (
    metadata.placeholder_video === true ||
    metadata.coverage_kind === "placeholder_video" ||
    binding.original_file_name === "no-video-placeholder.mp4" ||
    binding.title.includes("占位视频")
  );
}

function pointVideoBindingFromDetail(detail: CatalogNodeDetail): CatalogPointMediaBinding | null {
  const rawBinding = detail.media_bindings?.[0] || null;
  return rawBinding && !isPlaceholderPointVideoBinding(rawBinding) ? rawBinding : null;
}

function VideoGlyph() {
  return (
    <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24">
      <path d="M5 5.5h9.4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
      <path d="m16.4 9.1 4.1-2.2c.7-.4 1.5.1 1.5.9v8.4c0 .8-.8 1.3-1.5.9l-4.1-2.2V9.1Z" />
    </svg>
  );
}

function PointVideoManager({
  binding,
  selectedFile,
  removeExisting,
  disabled,
  onSelectFile,
  onRemove,
}: {
  binding: CatalogPointMediaBinding | null;
  selectedFile: File | null;
  removeExisting: boolean;
  disabled: boolean;
  onSelectFile: (file: File) => void;
  onRemove: () => void;
}) {
  const [policy, setPolicy] = useState<TeacherMediaUploadPolicy | null>(null);

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

  const activeBinding = removeExisting ? null : binding;
  const displayName = selectedFile?.name || activeBinding?.original_file_name || activeBinding?.title || "暂无视频";
  const canRemove = Boolean(selectedFile || activeBinding);
  const hasPendingChange = Boolean(selectedFile || removeExisting);

  return (
    <section className="legacy-point-video-field" aria-label="视频">
      <span className="legacy-point-video-field-label">视频</span>
      <div className={`legacy-point-video-row${canRemove ? "" : " is-empty"}`}>
        <div className="legacy-point-video-icon">
          <VideoGlyph />
        </div>
        <div className="legacy-point-video-summary">
          <strong>{displayName}</strong>
          {hasPendingChange ? <span>待保存</span> : null}
        </div>
        <div className="legacy-point-video-inline-actions">
          <button type="button" className="legacy-point-video-remove" disabled={disabled || !canRemove} onClick={onRemove}>
            移除
          </button>
          <TeacherUpload
            accept={policy?.allowed_extensions?.join(",") || "video/*"}
            beforeUpload={(file) => {
              onSelectFile(file);
              return false;
            }}
            maxCount={1}
            showUploadList={false}
          >
            <button type="button" className="legacy-point-video-upload-button" disabled={disabled}>
              上传
            </button>
          </TeacherUpload>
        </div>
      </div>
    </section>
  );
}

function AIConfigurationSettingsSection({ active }: { active: boolean }) {
  const [reloadKey, setReloadKey] = useState(0);
  const state = useAsyncData<AIConfigurationResponse | null>(() => (active ? getAIConfiguration() : Promise.resolve(null)), [reloadKey, active]);
  const [baseUrl, setBaseUrl] = useState(deepSeekDefaultBaseUrl);
  const [model, setModel] = useState(deepSeekDefaultModel);
  const [apiKey, setApiKey] = useState("");
  const [editingApiKey, setEditingApiKey] = useState(false);
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);
  const apiKeyConfigured = Boolean(state.data?.api_key_configured || state.data?.chat_provider?.api_key_configured);

  useEffect(() => {
    const config = state.data;
    if (!config) return;
    setBaseUrl(config.base_url || config.chat_provider?.base_url || deepSeekDefaultBaseUrl);
    setModel(config.model || config.chat_provider?.model || deepSeekDefaultModel);
    setApiKey("");
    setEditingApiKey(false);
    setActionError("");
  }, [state.data]);

  const saveConfig = async (event: FormEvent) => {
    event.preventDefault();
    const nextBaseUrl = baseUrl.trim().replace(/\/+$/, "");
    const nextModel = model.trim();
    const nextApiKey = editingApiKey || !apiKeyConfigured ? apiKey.trim() : "";
    if (!nextBaseUrl || !nextModel) {
      setActionError("请填写接口地址和模型名称。");
      return;
    }
    setSaving(true);
    setActionError("");
    try {
      await updateAIConfiguration({
        provider: "openai",
        base_url: nextBaseUrl,
        model: nextModel,
        ...(nextApiKey ? { api_key: nextApiKey } : {}),
        chat_provider: {
          provider: "openai",
          base_url: nextBaseUrl,
          model: nextModel,
          ...(nextApiKey ? { api_key: nextApiKey } : {}),
        },
      });
      setApiKey("");
      setEditingApiKey(false);
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="legacy-ai-config-sidebar legacy-ai-config-model-panel" data-testid="teacher-ai-config-model" aria-label="大语言模型配置">
      <div className="legacy-profile-form-head">
        <strong>大语言模型配置</strong>
        <span>配置 AI 出题和 AI 报告使用的大语言模型。</span>
      </div>
      <div className="legacy-ai-config-sidebar-body">
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <StateBlock loading={state.loading && !state.data} error={state.error}>
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
              {apiKeyConfigured && !editingApiKey && !apiKey ? (
                <TeacherInput
                  aria-label="API 密钥"
                  autoComplete="off"
                  className="legacy-ai-config-key-mask"
                  readOnly
                  value="********"
                  onMouseDown={() => setEditingApiKey(true)}
                  onFocus={() => setEditingApiKey(true)}
                />
              ) : (
                <TeacherInput.Password
                  aria-label="API 密钥"
                  autoComplete="off"
                  value={apiKey}
                  placeholder=""
                  onBlur={() => {
                    if (apiKeyConfigured && !apiKey.trim()) setEditingApiKey(false);
                  }}
                  onChange={(event) => {
                    if (!editingApiKey) setEditingApiKey(true);
                    setApiKey(event.target.value);
                  }}
                />
              )}
            </label>
            <div className="legacy-ai-config-sidebar-actions">
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={saving}>
                {saving ? "保存中..." : "保存配置"}
              </TeacherButton>
            </div>
          </form>
        </StateBlock>
      </div>
    </section>
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
    const params = new URLSearchParams({ limit: "200", point_node_id: selectedPoint.node_id, status_filter: "published" });
    if (selectedPoint.canonical_point_id) params.set("canonical_point_id", selectedPoint.canonical_point_id);
    return listQuestionBankQuestions(params);
  }, [selectedPoint?.node_id, reloadKey]);
  const [questionTypes, setQuestionTypes] = useState<ObjectiveQuestionType[]>(["single_choice"]);
  const [count, setCount] = useState(1);
  const [prompt, setPrompt] = useState("");
  const [actionError, setActionError] = useState("");
  const [generating, setGenerating] = useState(false);
  const [publishingDraftId, setPublishingDraftId] = useState("");
  const [deletingDraftId, setDeletingDraftId] = useState("");
  const [revokingQuestionId, setRevokingQuestionId] = useState("");
  const [selectedDraftId, setSelectedDraftId] = useState("");
  const [selectedBankQuestionId, setSelectedBankQuestionId] = useState("");
  const draftItems = (draftsState.data?.items || []).filter((item) => item.status === "draft");
  const bankQuestions = questionsState.data?.items || [];
  const selectedDraft = draftItems.find((item) => item.id === selectedDraftId) || draftItems[0] || null;
  const selectedBankQuestion = bankQuestions.find((item) => item.id === selectedBankQuestionId) || bankQuestions[0] || null;

  useEffect(() => {
    if (selectedPoint) {
      setPrompt(`请围绕“${selectedPoint.title}”生成 1 道课堂测评题，依据点位原理、现象和安全资料命题。`);
      setActionError("");
    }
  }, [selectedPoint?.node_id]);

  const toggleQuestionType = (value: ObjectiveQuestionType, checked: boolean) => {
    setQuestionTypes((current) => {
      const next = checked ? Array.from(new Set([...current, value])) : current.filter((item) => item !== value);
      return next.length ? next : current;
    });
  };

  useEffect(() => {
    if (!selectedDraftId && draftItems[0]?.id) setSelectedDraftId(draftItems[0].id);
    if (selectedDraftId && draftItems.length && !draftItems.some((item) => item.id === selectedDraftId)) setSelectedDraftId(draftItems[0]?.id || "");
    if (!draftItems.length && selectedDraftId) setSelectedDraftId("");
  }, [draftItems, selectedDraftId]);

  useEffect(() => {
    if (!selectedBankQuestionId && bankQuestions[0]?.id) setSelectedBankQuestionId(bankQuestions[0].id);
    if (selectedBankQuestionId && bankQuestions.length && !bankQuestions.some((item) => item.id === selectedBankQuestionId)) setSelectedBankQuestionId(bankQuestions[0]?.id || "");
    if (!bankQuestions.length && selectedBankQuestionId) setSelectedBankQuestionId("");
  }, [bankQuestions, selectedBankQuestionId]);

  const generate = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedPoint || !prompt.trim()) {
      setActionError("请选择点位并填写命题要求。");
      return;
    }
    setGenerating(true);
    setActionError("");
    try {
      await generateLegacyPointQuestions({
        experiment_id: selectedPoint.experiment_id,
        prompt: prompt.trim(),
        question_types: questionTypes,
        count,
        difficulty: "basic",
        chapter_ids: [selectedPoint.chapter_id],
        target_point_node_ids: [selectedPoint.node_id],
      });
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setGenerating(false);
    }
  };

  const publishDraft = async (draftId: string) => {
    setActionError("");
    setPublishingDraftId(draftId);
    try {
      const publishedQuestion = await publishQuestionDraft(draftId);
      setSelectedDraftId("");
      setSelectedBankQuestionId(publishedQuestion.id);
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setPublishingDraftId("");
    }
  };

  const saveDraft = async (draftId: string, payload: QuestionDraft["payload"]) => {
    setActionError("");
    try {
      await updateQuestionDraft(draftId, { payload, status: "draft" });
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
      throw caught;
    }
  };

  const deleteDraft = async (draftId: string) => {
    setActionError("");
    setDeletingDraftId(draftId);
    try {
      await rejectQuestionDraft(draftId);
      if (selectedDraftId === draftId) setSelectedDraftId("");
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setDeletingDraftId("");
    }
  };

  const revokeQuestion = async (questionId: string) => {
    setActionError("");
    setRevokingQuestionId(questionId);
    try {
      const draft = await revokeQuestionToDraft(questionId);
      setSelectedBankQuestionId("");
      setSelectedDraftId(draft.id);
      setReloadKey((value) => value + 1);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setRevokingQuestionId("");
    }
  };
  return (
    <PageFrame
      title="AI 出题"
      showHeader={false}
      testId="teacher-page-questions"
    >
      <StateBlock loading={catalog.loading && !catalog.data} error={catalog.error}>
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <TeacherCard className="legacy-table-card legacy-question-workbench">
          <header className="legacy-question-workbench-head">
            <div>
              <span className="legacy-section-kicker">点位资料直接命题</span>
              <h2>命题工作区</h2>
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
                <TeacherInput.TextArea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={3} />
              </label>
              <div className="legacy-question-submit-row">
                <TeacherButton type="primary" htmlType="submit" className="primary-button legacy-question-generate-button" disabled={generating || !selectedPoint}>
                  {generating ? "生成中..." : "生成待审题"}
                </TeacherButton>
              </div>
            </form>
            <section className="legacy-question-library-transfer" aria-label="题库流转">
              <section className="legacy-question-review-panel" aria-label="待审队列">
                <div className="legacy-question-review-head">
                  <div>
                    <span className="legacy-section-kicker">03</span>
                    <strong>待审题</strong>
                  </div>
                  <span>{draftsState.loading ? "读取中" : `${draftItems.length} 条`}</span>
                </div>
                <StateBlock loading={draftsState.loading && !draftsState.data} error={draftsState.error}>
                  {draftItems.length ? (
                    <div className="legacy-question-candidate-list">
                      {draftItems.slice(0, 5).map((draft) => (
                        <DraftReviewCard
                          key={draft.id}
                          draft={draft}
                          selected={selectedDraft?.id === draft.id}
                          onSelect={() => setSelectedDraftId(draft.id)}
                          onSave={saveDraft}
                          publishing={publishingDraftId === draft.id}
                          deleting={deletingDraftId === draft.id}
                          onPublish={() => publishDraft(draft.id)}
                          onDelete={() => deleteDraft(draft.id)}
                        />
                      ))}
                    </div>
                  ) : (
                    <TeacherEmptyState message="暂无待审题。" compact />
                  )}
                </StateBlock>
              </section>
              <section className="legacy-question-review-panel legacy-question-bank-panel" aria-label="正式题库">
                <div className="legacy-question-review-head">
                  <div>
                    <span className="legacy-section-kicker">04</span>
                    <strong>正式题库</strong>
                  </div>
                  <span>{questionsState.loading ? "读取中" : `${questionsState.data?.total || 0} 题`}</span>
                </div>
                <StateBlock loading={questionsState.loading && !questionsState.data} error={questionsState.error}>
                  {bankQuestions.length ? (
                    <div className="legacy-question-bank-list">
                      {bankQuestions.map((question) => (
                        <QuestionRow
                          key={question.id}
                          question={question}
                          selected={selectedBankQuestion?.id === question.id}
                          revoking={revokingQuestionId === question.id}
                          onSelect={() => setSelectedBankQuestionId(question.id)}
                          onRevoke={() => revokeQuestion(question.id)}
                        />
                      ))}
                    </div>
                  ) : (
                    <TeacherEmptyState message="当前点位暂无已审核题。" compact />
                  )}
                </StateBlock>
              </section>
            </section>
          </div>
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

type DraftEditState = {
  stem: string;
  options: Array<{ label: string; text: string }>;
  answerValue: string;
  explanation: string;
};

function draftEditStateFromPayload(payload: QuestionDraft["payload"] | undefined): DraftEditState {
  const options = Array.isArray(payload?.options)
    ? payload.options.map((option, index) => {
        if (option && typeof option === "object") {
          return {
            label: String((option as { label?: unknown }).label || String.fromCharCode(65 + index)),
            text: String((option as { text?: unknown }).text || ""),
          };
        }
        return { label: String.fromCharCode(65 + index), text: String(option || "") };
      })
    : [];
  return {
    stem: String(payload?.stem || ""),
    options,
    answerValue: answerSummary(payload?.answer),
    explanation: String(payload?.explanation || ""),
  };
}

function answerFromDraftEdit(original: unknown, value: string): Record<string, unknown> {
  const trimmed = value.trim();
  if (original && typeof original === "object" && !Array.isArray(original)) {
    if ("accepted_answers" in original) {
      return {
        ...(original as Record<string, unknown>),
        accepted_answers: trimmed ? trimmed.split(/[\/,，;；\n]+/).map((item) => item.trim()).filter(Boolean) : [],
      };
    }
    return { ...(original as Record<string, unknown>), value: trimmed };
  }
  return { value: trimmed };
}

function DraftReviewCard({
  draft,
  selected = false,
  onSelect,
  onSave,
  publishing = false,
  deleting = false,
  onPublish,
  onDelete,
}: {
  draft: QuestionDraft;
  selected?: boolean;
  onSelect?: () => void;
  onSave: (draftId: string, payload: QuestionDraft["payload"]) => Promise<void>;
  publishing?: boolean;
  deleting?: boolean;
  onPublish?: () => void;
  onDelete?: () => void;
}) {
  const payload = draft.payload || {};
  const validationErrors = draft.validation_errors || [];
  const publishable = draft.status === "draft" && !validationErrors.length;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editState, setEditState] = useState<DraftEditState>(() => draftEditStateFromPayload(payload));

  useEffect(() => {
    if (!editing) setEditState(draftEditStateFromPayload(draft.payload));
  }, [draft.id, draft.payload, editing]);

  const updateOptionText = (index: number, text: string) => {
    setEditState((current) => ({
      ...current,
      options: current.options.map((option, optionIndex) => (optionIndex === index ? { ...option, text } : option)),
    }));
  };

  const saveEdit = async () => {
    setSaving(true);
    const nextPayload: QuestionDraft["payload"] = {
      ...payload,
      stem: editState.stem.trim(),
      options: editState.options.map((option) => ({ label: option.label, text: option.text.trim() })).filter((option) => option.text),
      answer: answerFromDraftEdit(payload.answer, editState.answerValue),
      explanation: editState.explanation.trim(),
      status: "draft",
    };
    try {
      await onSave(draft.id, nextPayload);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  if (editing) {
    return (
      <article className={`legacy-question-candidate-card legacy-question-candidate-card-editing${selected ? " selected" : ""}`}>
        <div className="legacy-question-candidate-title">
          <span className="legacy-row-label">{questionTypeLabel(String(payload.question_type || ""))}</span>
          {validationErrors.length ? <span className="legacy-row-label">需复核</span> : null}
        </div>
        <div className="legacy-draft-edit-form">
          <label>
            题干
            <TeacherInput.TextArea value={editState.stem} onChange={(event) => setEditState((current) => ({ ...current, stem: event.target.value }))} rows={3} />
          </label>
          {editState.options.length ? (
            <div className="legacy-draft-option-editor" aria-label="选项">
              {editState.options.map((option, index) => (
                <label key={`${option.label}-${index}`}>
                  <span>{option.label}</span>
                  <TeacherInput value={option.text} onChange={(event) => updateOptionText(index, event.target.value)} />
                </label>
              ))}
            </div>
          ) : null}
          <label>
            答案
            <TeacherInput value={editState.answerValue} onChange={(event) => setEditState((current) => ({ ...current, answerValue: event.target.value }))} />
          </label>
          <label>
            解析
            <TeacherInput.TextArea value={editState.explanation} onChange={(event) => setEditState((current) => ({ ...current, explanation: event.target.value }))} rows={3} />
          </label>
        </div>
        {validationErrors.length ? <div className="legacy-error compact">{validationErrors.join("；")}</div> : null}
        <div className="legacy-question-card-actions">
          <TeacherButton className="legacy-secondary-button" disabled={saving} onClick={saveEdit}>
            {saving ? "保存中..." : "保存修改"}
          </TeacherButton>
          <TeacherButton className="legacy-secondary-button" disabled={saving} onClick={() => setEditing(false)}>
            取消
          </TeacherButton>
        </div>
      </article>
    );
  }

  return (
    <article
      className={`legacy-question-candidate-card${selected ? " selected" : ""}`}
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.();
        }
      }}
    >
      <div className="legacy-question-candidate-title">
        <div className="legacy-question-card-labels">
          <span className="legacy-row-label">{questionTypeLabel(String(payload.question_type || ""))}</span>
          {validationErrors.length ? <span className="legacy-row-label">需复核</span> : null}
        </div>
        <button
          type="button"
          className="legacy-question-card-flow-button"
          aria-label="入库"
          title="入库"
          disabled={!publishable || publishing}
          onClick={(event) => {
            event.stopPropagation();
            onPublish?.();
          }}
        >
          {publishing ? <span className="legacy-flow-loading">…</span> : <ArrowRight aria-hidden="true" className="legacy-flow-icon" />}
        </button>
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
        <TeacherButton
          className="legacy-secondary-button"
          disabled={draft.status !== "draft"}
          onClick={(event) => {
            event.stopPropagation();
            setEditing(true);
          }}
        >
          修改
        </TeacherButton>
        <TeacherButton
          danger
          className="legacy-secondary-button"
          disabled={draft.status !== "draft" || deleting}
          onClick={(event) => {
            event.stopPropagation();
            onDelete?.();
          }}
        >
          {deleting ? "删除中..." : "删除"}
        </TeacherButton>
      </div>
    </article>
  );
}

function QuestionRow({
  question,
  selected = false,
  revoking = false,
  onSelect,
  onRevoke,
}: {
  question: Question;
  selected?: boolean;
  revoking?: boolean;
  onSelect?: () => void;
  onRevoke?: () => void;
}) {
  return (
    <article
      className={`legacy-question-candidate-card legacy-question-bank-row${selected ? " selected" : ""}`}
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return;
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.();
        }
      }}
    >
      <div className="legacy-question-candidate-title">
        <div className="legacy-question-card-labels">
          <span className="legacy-row-label">{questionTypeLabel(question.question_type)}</span>
          <span className="legacy-row-label">{catalogContentStatusLabel(question.status, "未知")}</span>
        </div>
        <button
          type="button"
          className="legacy-question-card-flow-button"
          aria-label="撤销到待审"
          title="撤销到待审"
          disabled={revoking}
          onClick={(event) => {
            event.stopPropagation();
            onRevoke?.();
          }}
        >
          {revoking ? <span className="legacy-flow-loading">…</span> : <ArrowLeft aria-hidden="true" className="legacy-flow-icon" />}
        </button>
      </div>
      <strong>{question.stem}</strong>
      <QuestionOptions options={question.options} />
      <dl className="legacy-question-answer">
        <div>
          <dt>答案</dt>
          <dd>{answerSummary(question.answer)}</dd>
        </div>
        <div>
          <dt>解析</dt>
          <dd>{question.explanation || "暂无解析。"}</dd>
        </div>
      </dl>
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

function studentDisplayName(student: TeacherStudentSummary): string {
  return student.student_name || student.display_name || student.username || student.student_id;
}

function studentIsActive(student: TeacherStudentSummary): boolean {
  return student.status !== "disabled" && (student.activated || student.status === "active");
}

function ClassesPage() {
  const [reloadKey, setReloadKey] = useState(0);
  const [studentReloadKey, setStudentReloadKey] = useState(0);
  const [registrationReloadKey, setRegistrationReloadKey] = useState(0);
  const classState = useAsyncData<TeacherClassSummary[]>(listTeacherClasses, [reloadKey]);
  const classes = classState.data || [];
  const [selectedClassId, setSelectedClassId] = useState("");
  const selectedClass = classes.find((item) => item.id === selectedClassId) || classes[0] || null;
  const registrationState = useAsyncData<TeacherClassRegistrationSettings | null>(
    () => (selectedClass?.id ? getTeacherClassRegistrationSettings(selectedClass.id) : Promise.resolve(null)),
    [selectedClass?.id, registrationReloadKey],
  );
  const [className, setClassName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [studentName, setStudentName] = useState("");
  const [classDialogOpen, setClassDialogOpen] = useState(false);
  const [classDeleteDialogOpen, setClassDeleteDialogOpen] = useState(false);
  const [studentDialogOpen, setStudentDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<TeacherStudentSummary | null>(null);
  const [editingStudentName, setEditingStudentName] = useState("");
  const [passwordStudent, setPasswordStudent] = useState<TeacherStudentSummary | null>(null);
  const [studentPassword, setStudentPassword] = useState("");
  const [deletingStudent, setDeletingStudent] = useState<TeacherStudentSummary | null>(null);
  const [importMode, setImportMode] = useState<"upsert" | "overwrite">("upsert");
  const [passwordMode, setPasswordMode] = useState<"student_id" | "shared">("student_id");
  const [sharedPassword, setSharedPassword] = useState("");
  const [rosterFile, setRosterFile] = useState<File | null>(null);
  const [studentPage, setStudentPage] = useState(1);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const [creatingClass, setCreatingClass] = useState(false);
  const [deletingClass, setDeletingClass] = useState(false);
  const [creatingStudent, setCreatingStudent] = useState(false);
  const [importingRoster, setImportingRoster] = useState(false);
  const [savingStudentName, setSavingStudentName] = useState(false);
  const [resettingStudentPassword, setResettingStudentPassword] = useState(false);
  const [togglingStudentId, setTogglingStudentId] = useState("");
  const [deletingStudentId, setDeletingStudentId] = useState("");

  useEffect(() => {
    if (!selectedClassId && selectedClass?.id) setSelectedClassId(selectedClass.id);
    if (selectedClassId && classes.length && !classes.some((item) => item.id === selectedClassId)) setSelectedClassId(classes[0]?.id || "");
  }, [classes, selectedClass, selectedClassId]);

  const studentsState = useAsyncData<TeacherStudentSummary[]>(
    () => (selectedClass?.id ? listTeacherClassStudents(selectedClass.id) : Promise.resolve([])),
    [selectedClass?.id, studentReloadKey],
  );
  const students = studentsState.data || [];
  const studentPageSize = 10;
  const studentPageCount = Math.max(1, Math.ceil(students.length / studentPageSize));
  const pagedStudents = students.slice((studentPage - 1) * studentPageSize, studentPage * studentPageSize);
  const defaultPasswordMode = registrationState.data?.default_password_mode === "shared" ? "shared" : "student_id";
  const initialPasswordLabel = defaultPasswordMode === "shared" ? "统一初始密码" : "使用学号";

  useEffect(() => {
    setStudentPage(1);
  }, [selectedClass?.id, students.length]);

  useEffect(() => {
    if (!importDialogOpen) return;
    setPasswordMode(defaultPasswordMode);
    setSharedPassword("");
  }, [defaultPasswordMode, importDialogOpen]);

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
      const response = await createTeacherClass({ class_name: nextName });
      setClassName("");
      setClassDialogOpen(false);
      setSelectedClassId(response.id);
      setReloadKey((value) => value + 1);
      setNotice("已创建班级。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingClass(false);
    }
  };

  const deleteClass = async () => {
    if (!selectedClass?.id) return;
    setDeletingClass(true);
    setNotice("");
    setActionError("");
    try {
      await deleteTeacherClass(selectedClass.id);
      setClassDeleteDialogOpen(false);
      setSelectedClassId("");
      setStudentReloadKey((value) => value + 1);
      setRegistrationReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice("已删除班级。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setDeletingClass(false);
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
      setStudentDialogOpen(false);
      setStudentReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice("已添加学生。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setCreatingStudent(false);
    }
  };

  const openEditStudent = (student: TeacherStudentSummary) => {
    setEditingStudent(student);
    setEditingStudentName(studentDisplayName(student));
    setActionError("");
  };

  const saveStudentName = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedClass?.id || !editingStudent) return;
    const nextName = editingStudentName.trim();
    if (!nextName) {
      setActionError("请填写学生姓名。");
      return;
    }
    setSavingStudentName(true);
    setNotice("");
    setActionError("");
    try {
      await updateTeacherClassStudent(selectedClass.id, editingStudent.student_id, { student_name: nextName });
      setEditingStudent(null);
      setEditingStudentName("");
      setStudentReloadKey((value) => value + 1);
      setNotice("已更新学生姓名。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSavingStudentName(false);
    }
  };

  const openResetStudentPassword = (student: TeacherStudentSummary) => {
    setPasswordStudent(student);
    setStudentPassword("");
    setActionError("");
  };

  const resetStudentPassword = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedClass?.id || !passwordStudent) return;
    const nextPassword = studentPassword.trim();
    if (nextPassword.length < 8) {
      setActionError("新密码至少 8 位。");
      return;
    }
    setResettingStudentPassword(true);
    setNotice("");
    setActionError("");
    try {
      await resetTeacherClassStudentPassword(selectedClass.id, passwordStudent.student_id, nextPassword);
      setPasswordStudent(null);
      setStudentPassword("");
      setNotice(`已重置 ${studentDisplayName(passwordStudent)} 的密码。`);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setResettingStudentPassword(false);
    }
  };

  const toggleStudentStatus = async (student: TeacherStudentSummary) => {
    if (!selectedClass?.id) return;
    const nextStatus = student.status === "disabled" ? "active" : "disabled";
    setTogglingStudentId(student.student_id);
    setNotice("");
    setActionError("");
    try {
      await updateTeacherClassStudent(selectedClass.id, student.student_id, { status: nextStatus });
      setStudentReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice(nextStatus === "disabled" ? "已停用学生账号。" : "已启用学生账号。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setTogglingStudentId("");
    }
  };

  const deleteStudent = async () => {
    if (!selectedClass?.id || !deletingStudent) return;
    setDeletingStudentId(deletingStudent.student_id);
    setNotice("");
    setActionError("");
    try {
      await deleteTeacherClassStudent(selectedClass.id, deletingStudent.student_id);
      setDeletingStudent(null);
      setStudentReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice("已删除学生账号。");
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setDeletingStudentId("");
    }
  };

  const importRoster = async () => {
    if (!selectedClass?.id) {
      setActionError("请先选择班级。");
      return;
    }
    if (!rosterFile) {
      setActionError("请选择要导入的名单文件。");
      return;
    }
    if (passwordMode === "shared" && !sharedPassword.trim() && !registrationState.data?.has_default_password) {
      setActionError("请填写统一初始密码，或改为使用学号。");
      return;
    }
    setImportingRoster(true);
    setNotice("");
    setActionError("");
    try {
      await updateTeacherClassRegistrationSettings(selectedClass.id, {
        default_password_mode: passwordMode,
        default_password: passwordMode === "shared" ? sharedPassword.trim() || undefined : undefined,
      });
      const result = await importTeacherClassRoster(selectedClass.id, { file: rosterFile, mode: importMode });
      setRosterFile(null);
      setSharedPassword("");
      setImportDialogOpen(false);
      setStudentReloadKey((value) => value + 1);
      setRegistrationReloadKey((value) => value + 1);
      setReloadKey((value) => value + 1);
      setNotice(importMode === "overwrite" ? `覆盖导入完成：${result.valid_rows} 条有效，禁用 ${result.disabled_missing} 条缺失名单。` : `导入完成：${result.valid_rows} 条有效。`);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setImportingRoster(false);
    }
  };

  return (
    <PageFrame title="班级管理" showHeader={false} testId="teacher-page-classes">
      {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
      {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
      <StateBlock loading={classState.loading && !classState.data} error={classState.error}>
        <TeacherCard className="legacy-card legacy-class-control-card">
          <div className="legacy-class-control-row">
            <label className="legacy-select-label">
              当前班级
              <select value={selectedClass?.id || ""} onChange={(event) => setSelectedClassId(event.target.value)} disabled={!classes.length}>
                {classes.length ? (
                  classes.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.class_name}
                    </option>
                  ))
                ) : (
                  <option value="">暂无班级</option>
                )}
              </select>
            </label>
            <div className="legacy-class-control-actions">
              <TeacherButton type="primary" className="primary-button compact" onClick={() => setClassDialogOpen(true)}>
                新增班级
              </TeacherButton>
              <TeacherButton className="legacy-secondary-button legacy-danger-button" disabled={!selectedClass || deletingClass} onClick={() => setClassDeleteDialogOpen(true)}>
                删除班级
              </TeacherButton>
            </div>
          </div>
        </TeacherCard>
        <TeacherCard className="legacy-table-card legacy-roster-panel legacy-roster-panel-full">
          <div className="legacy-class-panel-head">
            <div>
              <h2>学生名单</h2>
              <span>{selectedClass?.class_name || "未选择班级"} · 初始密码：{initialPasswordLabel}</span>
            </div>
            <div className="legacy-class-toolbar">
              <TeacherButton className="legacy-secondary-button" disabled={!selectedClass} onClick={() => setStudentDialogOpen(true)}>
                添加学生
              </TeacherButton>
              <TeacherButton type="primary" className="primary-button compact" disabled={!selectedClass} onClick={() => setImportDialogOpen(true)}>
                导入名单
              </TeacherButton>
            </div>
          </div>
          <StateBlock loading={studentsState.loading && !studentsState.data} error={studentsState.error}>
            {selectedClass ? (
              students.length ? (
                <div className="legacy-student-table legacy-student-table-management compact" aria-label="学生名单">
                  <article className="legacy-student-table-head">
                    <span>学号</span>
                    <strong>姓名</strong>
                    <span>状态</span>
                    <span>操作</span>
                  </article>
                  {pagedStudents.map((student) => (
                    <article key={`${student.student_id}-${student.id || student.class_id || selectedClass.id}`}>
                      <span>{student.student_id}</span>
                      <strong>{studentDisplayName(student)}</strong>
                      <span className={`legacy-status-pill status-${studentIsActive(student) ? "active" : student.status}`}>
                        {studentIsActive(student) ? "已激活" : studentStatusLabel(student.status)}
                      </span>
                      <span className="legacy-student-actions">
                        <button type="button" onClick={() => openEditStudent(student)}>
                          编辑
                        </button>
                        <button type="button" onClick={() => openResetStudentPassword(student)}>
                          重置密码
                        </button>
                        <button type="button" disabled={togglingStudentId === student.student_id} onClick={() => toggleStudentStatus(student)}>
                          {student.status === "disabled" ? "启用" : "停用"}
                        </button>
                        <button type="button" className="danger" disabled={deletingStudentId === student.student_id} onClick={() => setDeletingStudent(student)}>
                          删除
                        </button>
                      </span>
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
          <div className="legacy-class-pagination" aria-label="学生分页">
            <span>第 {studentPage} / {studentPageCount} 页 · 共 {students.length} 人</span>
            <div>
              <button type="button" disabled={studentPage <= 1} onClick={() => setStudentPage((value) => Math.max(1, value - 1))}>
                上一页
              </button>
              <button type="button" disabled={studentPage >= studentPageCount} onClick={() => setStudentPage((value) => Math.min(studentPageCount, value + 1))}>
                下一页
              </button>
            </div>
          </div>
        </TeacherCard>
      </StateBlock>
      <TeacherModal
        open={classDialogOpen}
        className="legacy-create-dialog"
        title="新增班级"
        onCancel={() => setClassDialogOpen(false)}
        footer={null}
        maskClosable={!creatingClass}
      >
        <form className="legacy-dialog-form" onSubmit={createClass}>
          <label>
            班级名称
            <TeacherInput value={className} onChange={(event) => setClassName(event.target.value)} placeholder="例如：26 级本科 1 班" autoFocus />
          </label>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setClassDialogOpen(false)} disabled={creatingClass}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={creatingClass}>
              {creatingClass ? "创建中..." : "创建班级"}
            </TeacherButton>
          </div>
        </form>
      </TeacherModal>
      <TeacherModal
        open={classDeleteDialogOpen}
        className="legacy-create-dialog"
        title="删除班级"
        onCancel={() => setClassDeleteDialogOpen(false)}
        footer={null}
        maskClosable={!deletingClass}
      >
        <div className="legacy-dialog-form compact">
          <div className="legacy-dialog-warning danger">
            <strong>{selectedClass?.class_name || ""}</strong>
            <span>删除后该班级不再出现在后台列表中，已存在的学习和测评数据会保留。</span>
          </div>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setClassDeleteDialogOpen(false)} disabled={deletingClass}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" className="primary-button" onClick={deleteClass} disabled={!selectedClass || deletingClass}>
              {deletingClass ? "删除中..." : "确认删除"}
            </TeacherButton>
          </div>
        </div>
      </TeacherModal>
      <TeacherModal
        open={studentDialogOpen}
        className="legacy-create-dialog"
        title="添加学生"
        onCancel={() => setStudentDialogOpen(false)}
        footer={null}
        maskClosable={!creatingStudent}
      >
        <form className="legacy-dialog-form compact" onSubmit={createStudent}>
          <label>
            学号
            <TeacherInput value={studentId} onChange={(event) => setStudentId(event.target.value)} placeholder="例如：26320001" autoFocus disabled={!selectedClass} />
          </label>
          <label>
            姓名
            <TeacherInput value={studentName} onChange={(event) => setStudentName(event.target.value)} placeholder="学生姓名" disabled={!selectedClass} />
          </label>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setStudentDialogOpen(false)} disabled={creatingStudent}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={!selectedClass || creatingStudent}>
              {creatingStudent ? "添加中..." : "添加学生"}
            </TeacherButton>
          </div>
        </form>
      </TeacherModal>
      <TeacherModal
        open={Boolean(editingStudent)}
        className="legacy-create-dialog"
        title="编辑学生"
        onCancel={() => setEditingStudent(null)}
        footer={null}
        maskClosable={!savingStudentName}
      >
        <form className="legacy-dialog-form compact" onSubmit={saveStudentName}>
          <label>
            学号
            <TeacherInput value={editingStudent?.student_id || ""} disabled />
          </label>
          <label>
            姓名
            <TeacherInput value={editingStudentName} onChange={(event) => setEditingStudentName(event.target.value)} placeholder="学生姓名" autoFocus />
          </label>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setEditingStudent(null)} disabled={savingStudentName}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={savingStudentName}>
              {savingStudentName ? "保存中..." : "保存"}
            </TeacherButton>
          </div>
        </form>
      </TeacherModal>
      <TeacherModal
        open={Boolean(passwordStudent)}
        className="legacy-create-dialog"
        title="重置密码"
        onCancel={() => setPasswordStudent(null)}
        footer={null}
        maskClosable={!resettingStudentPassword}
      >
        <form className="legacy-dialog-form compact" onSubmit={resetStudentPassword}>
          <div className="legacy-dialog-warning">
            <strong>{passwordStudent ? studentDisplayName(passwordStudent) : ""}</strong>
            <span>{passwordStudent?.student_id}</span>
          </div>
          <label>
            新密码
            <TeacherInput.Password value={studentPassword} onChange={(event) => setStudentPassword(event.target.value)} placeholder="至少 8 位" autoFocus />
          </label>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setPasswordStudent(null)} disabled={resettingStudentPassword}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={resettingStudentPassword}>
              {resettingStudentPassword ? "重置中..." : "重置密码"}
            </TeacherButton>
          </div>
        </form>
      </TeacherModal>
      <TeacherModal
        open={Boolean(deletingStudent)}
        className="legacy-create-dialog"
        title="删除学生"
        onCancel={() => setDeletingStudent(null)}
        footer={null}
        maskClosable={!deletingStudentId}
      >
        <div className="legacy-dialog-form compact">
          <div className="legacy-dialog-warning danger">
            <strong>{deletingStudent ? studentDisplayName(deletingStudent) : ""}</strong>
            <span>删除后该学生账号将无法登录，名单中也不再展示该学生。</span>
          </div>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setDeletingStudent(null)} disabled={Boolean(deletingStudentId)}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" className="primary-button" onClick={deleteStudent} disabled={Boolean(deletingStudentId)}>
              {deletingStudentId ? "删除中..." : "确认删除"}
            </TeacherButton>
          </div>
        </div>
      </TeacherModal>
      <TeacherModal
        open={importDialogOpen}
        className="legacy-create-dialog legacy-roster-import-dialog"
        title="导入学生名单"
        onCancel={() => {
          setImportDialogOpen(false);
          setRosterFile(null);
        }}
        footer={null}
        maskClosable={!importingRoster}
      >
        <div className="legacy-roster-import-body">
          <div className="legacy-segmented-row" role="group" aria-label="导入方式">
            <button type="button" className={importMode === "upsert" ? "active" : ""} onClick={() => setImportMode("upsert")}>
              追加更新
            </button>
            <button type="button" className={importMode === "overwrite" ? "active" : ""} onClick={() => setImportMode("overwrite")}>
              覆盖名单
            </button>
          </div>
          <div className="legacy-segmented-row" role="group" aria-label="初始密码">
            <button type="button" className={passwordMode === "student_id" ? "active" : ""} onClick={() => setPasswordMode("student_id")}>
              使用学号
            </button>
            <button type="button" className={passwordMode === "shared" ? "active" : ""} onClick={() => setPasswordMode("shared")}>
              统一密码
            </button>
          </div>
          {passwordMode === "shared" ? (
            <label className="legacy-import-password-field">
              统一初始密码
              <TeacherInput.Password value={sharedPassword} onChange={(event) => setSharedPassword(event.target.value)} placeholder={registrationState.data?.has_default_password ? "留空则沿用当前密码" : "至少 8 位"} />
            </label>
          ) : null}
          <TeacherUpload
            accept=".csv,.xlsx"
            maxCount={1}
            beforeUpload={(file) => {
              setRosterFile(file);
              return false;
            }}
            onRemove={() => setRosterFile(null)}
          >
            <button type="button" className="legacy-roster-file-button">
              {rosterFile ? rosterFile.name : "选择 CSV/XLSX 文件"}
            </button>
          </TeacherUpload>
          <div className="legacy-create-dialog-actions">
            <TeacherButton type="default" className="legacy-secondary-button" onClick={() => setImportDialogOpen(false)} disabled={importingRoster}>
              取消
            </TeacherButton>
            <TeacherButton type="primary" className="primary-button" disabled={!selectedClass || !rosterFile || importingRoster} onClick={importRoster}>
              {importingRoster ? "导入中..." : "导入名单"}
            </TeacherButton>
          </div>
        </div>
      </TeacherModal>
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
  const rawColumns = dashboard?.experiment_groups?.length ? dashboard.experiment_groups : dashboard?.experiments || [];
  const columns = useMemo(() => analyticsFamilyColumns(rawColumns), [rawColumns]);
  const [scoreDetail, setScoreDetail] = useState<AnalyticsScoreDetailDialog | null>(null);
  const [reportDetail, setReportDetail] = useState<AnalyticsStudentReportDialog | null>(null);
  const [analyticsPage, setAnalyticsPage] = useState(1);
  const analyticsPageCount = Math.max(1, Math.ceil(rows.length / ANALYTICS_STUDENT_PAGE_SIZE));
  const clampedAnalyticsPage = Math.min(analyticsPage, analyticsPageCount);
  const pagedRows = rows.slice((clampedAnalyticsPage - 1) * ANALYTICS_STUDENT_PAGE_SIZE, clampedAnalyticsPage * ANALYTICS_STUDENT_PAGE_SIZE);

  useEffect(() => {
    if (!selectedStudentId && rows[0]?.student_id) setSelectedStudentId(rows[0].student_id);
  }, [rows, selectedStudentId]);
  useEffect(() => {
    setAnalyticsPage(1);
  }, [selectedClassId, rows.length]);
  useEffect(() => {
    if (analyticsPage > analyticsPageCount) setAnalyticsPage(analyticsPageCount);
  }, [analyticsPage, analyticsPageCount]);
  useEffect(() => {
    if (scoreDetail && (!rows.some((row) => row.student_id === scoreDetail.student.student_id) || !columns.some((item) => item.id === scoreDetail.family.id))) {
      setScoreDetail(null);
    }
  }, [columns, rows, scoreDetail]);
  useEffect(() => {
    if (reportDetail && (!rows.some((row) => row.student_id === reportDetail.student.student_id) || reportDetail.classId !== selectedClassId)) {
      setReportDetail(null);
    }
  }, [reportDetail, rows, selectedClassId]);

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
                  <h2>学生报告和各部分掌握度</h2>
                  <span>{rows.length} 名学生</span>
                </header>
                <div className="legacy-family-score-table-wrap">
                  <table className="legacy-family-score-table" aria-label="学生报告和各部分掌握度">
                    <thead>
                      <tr>
                        <th scope="col">学生</th>
                        {columns.map((item) => (
                          <th scope="col" key={item.id}>
                            {item.title}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {pagedRows.map((student) => (
                        <tr className={student.student_id === selectedStudentId ? "selected" : ""} key={student.student_id}>
                          <th scope="row">
                            <div className="legacy-family-student-entry">
                              <button type="button" className="legacy-family-student-cell" onClick={() => setSelectedStudentId(student.student_id)}>
                                <strong>{student.student_name}</strong>
                                <small>{student.student_id}</small>
                              </button>
                              <button
                                type="button"
                                className="legacy-student-report-button"
                                aria-label={`查看${student.student_name}测试报告`}
                                title="查看测试报告"
                                onClick={() => {
                                  setSelectedStudentId(student.student_id);
                                  setReportDetail({ classId: selectedClassId, student });
                                }}
                              >
                                <ReportIcon />
                              </button>
                            </div>
                          </th>
                          {columns.map((item) => {
                            const state = analyticsScoreCellForColumn(student, item);
                            const selected = scoreDetail?.student.student_id === student.student_id && scoreDetail.family.id === item.id;
                            const pointScores = state?.points || [];
                            const pointSummary = pointScores.length
                              ? pointScores.map((point) => `${point.point_title || "未命名点位"}：${scoreLabel(point.score ?? point.mastery_score)}`).join("\n")
                              : "暂无点位得分";
                            return (
                              <td key={item.id}>
                                <div className={`legacy-family-score-entry${selected ? " selected" : ""}`} title={pointSummary}>
                                  <div className="legacy-family-score-cell">
                                    <strong>{scoreLabel(state?.score ?? state?.mastery_score)}</strong>
                                  </div>
                                  <button
                                    type="button"
                                    className="legacy-score-detail-button"
                                    aria-label={`查看${student.student_name}${item.title}点位得分详情`}
                                    title="查看点位得分详情"
                                    onClick={() => {
                                      setSelectedStudentId(student.student_id);
                                      setScoreDetail({ student, family: item, cell: state });
                                    }}
                                  >
                                    <ScoreDetailIcon />
                                  </button>
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="legacy-class-pagination legacy-family-score-pagination" aria-label="学情分页">
                  <span>
                    第 {clampedAnalyticsPage} / {analyticsPageCount} 页 · 共 {rows.length} 名学生
                  </span>
                  <div>
                    <button type="button" disabled={clampedAnalyticsPage <= 1} onClick={() => setAnalyticsPage((value) => Math.max(1, value - 1))}>
                      上一页
                    </button>
                    <button type="button" disabled={clampedAnalyticsPage >= analyticsPageCount} onClick={() => setAnalyticsPage((value) => Math.min(analyticsPageCount, value + 1))}>
                      下一页
                    </button>
                  </div>
                </div>
              </TeacherCard>
              <TeacherModal
                open={Boolean(scoreDetail)}
                className="legacy-score-detail-dialog"
                title={scoreDetail ? `${scoreDetail.student.student_name} · ${scoreDetail.family.title}` : "点位得分"}
                onCancel={() => setScoreDetail(null)}
                footer={null}
                width={760}
              >
                {scoreDetail ? <AnalyticsScoreDetail detail={scoreDetail} /> : null}
              </TeacherModal>
              <StudentReportDialog reportDetail={reportDetail} onClose={() => setReportDetail(null)} />
            </>
          ) : null}
        </StateBlock>
      </StateBlock>
    </PageFrame>
  );
}

function AnalyticsScoreDetail({ detail }: { detail: AnalyticsScoreDetailDialog }) {
  const points = detail.cell?.points || [];
  const score = detail.cell?.score ?? detail.cell?.mastery_score;
  const [pointPage, setPointPage] = useState(1);
  const pointPageCount = Math.max(1, Math.ceil(points.length / ANALYTICS_POINT_PAGE_SIZE));
  const clampedPointPage = Math.min(pointPage, pointPageCount);
  const pagedPoints = points.slice((clampedPointPage - 1) * ANALYTICS_POINT_PAGE_SIZE, clampedPointPage * ANALYTICS_POINT_PAGE_SIZE);
  useEffect(() => {
    setPointPage(1);
  }, [detail.student.student_id, detail.family.id, points.length]);
  return (
    <div className="legacy-score-detail-content">
      <div className="legacy-score-detail-strip">
        <article>
          <span>族元素得分</span>
          <strong>{scoreLabel(score)}</strong>
        </article>
        <article>
          <span>点位数量</span>
          <strong>{points.length}</strong>
        </article>
        <article>
          <span>证据数量</span>
          <strong>{detail.cell?.evidence_count || 0}</strong>
        </article>
      </div>
      {points.length ? (
        <PointScoreTable points={pagedPoints} page={clampedPointPage} pageCount={pointPageCount} total={points.length} onPageChange={setPointPage} />
      ) : (
        <TeacherEmptyState message="当前族元素下暂无配置点位。" compact />
      )}
    </div>
  );
}

function PointScoreTable({
  points,
  page,
  pageCount,
  total,
  onPageChange,
}: {
  points: AnalyticsPointScore[];
  page: number;
  pageCount: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  return (
    <>
      <div className="legacy-point-score-table-wrap">
        <table className="legacy-point-score-table" aria-label="点位得分明细">
          <thead>
            <tr>
              <th scope="col">点位</th>
              <th scope="col">目录</th>
              <th scope="col">得分</th>
              <th scope="col">证据</th>
            </tr>
          </thead>
          <tbody>
            {points.map((point, index) => (
              <tr key={point.point_node_id || `${point.experiment_id || "point"}-${index}`}>
                <th scope="row">{point.point_title || "未命名点位"}</th>
                <td>{point.directory_title || point.experiment_title || "未关联目录"}</td>
                <td>{scoreLabel(point.score ?? point.mastery_score)}</td>
                <td>{point.evidence_count || 0} 条</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legacy-class-pagination legacy-point-score-pagination" aria-label="点位得分页">
        <span>
          第 {page} / {pageCount} 页 · 共 {total} 个点位
        </span>
        <div>
          <button type="button" disabled={page <= 1} onClick={() => onPageChange(Math.max(1, page - 1))}>
            上一页
          </button>
          <button type="button" disabled={page >= pageCount} onClick={() => onPageChange(Math.min(pageCount, page + 1))}>
            下一页
          </button>
        </div>
      </div>
    </>
  );
}

type AIConfigurationPanel = "prompts" | "model";

function AIConfigurationPage() {
  const [activePanel, setActivePanel] = useState<AIConfigurationPanel>("prompts");

  return (
    <PageFrame title="AI 配置" showHeader={false} testId="teacher-page-ai-config">
      <TeacherCard className="legacy-card legacy-ai-config-tabs-card">
        <div className="legacy-segmented-row legacy-ai-config-tabs" role="tablist" aria-label="AI 配置类型">
          <button
            type="button"
            role="tab"
            aria-selected={activePanel === "prompts"}
            className={activePanel === "prompts" ? "active" : ""}
            onClick={() => setActivePanel("prompts")}
          >
            报告生成 Prompt
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activePanel === "model"}
            className={activePanel === "model" ? "active" : ""}
            onClick={() => setActivePanel("model")}
          >
            大语言模型配置
          </button>
        </div>
      </TeacherCard>
      {activePanel === "prompts" ? <AssessmentReportPromptPanel /> : <AIConfigurationSettingsSection active />}
    </PageFrame>
  );
}

function AssessmentReportPromptPanel() {
  const promptState = useAsyncData(getGlobalAssessmentReportPrompts, []);
  const [summaryPrompt, setSummaryPrompt] = useState("");
  const [mistakePrompt, setMistakePrompt] = useState("");
  const [actionError, setActionError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (promptState.data) {
      setSummaryPrompt(promptState.data.settings.summary_prompt);
      setMistakePrompt(promptState.data.settings.mistake_prompt);
    }
  }, [promptState.data]);

  const savePrompts = async (event: FormEvent) => {
    event.preventDefault();
    if (!summaryPrompt.trim() || !mistakePrompt.trim()) {
      setActionError("请填写报告总结 Prompt 和错题讲解 Prompt。");
      return;
    }
    setSaving(true);
    setActionError("");
    try {
      await updateGlobalAssessmentReportPrompts({ summary_prompt: summaryPrompt, mistake_prompt: mistakePrompt });
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  const resetPrompts = async () => {
    setSaving(true);
    setActionError("");
    try {
      const response = await resetGlobalAssessmentReportPrompts();
      setSummaryPrompt(response.settings.summary_prompt);
      setMistakePrompt(response.settings.mistake_prompt);
    } catch (caught) {
      setActionError(legacyTeacherErrorMessage(caught));
    } finally {
      setSaving(false);
    }
  };

  return (
    <TeacherCard className="legacy-table-card legacy-report-prompt-card" data-testid="teacher-report-prompt-panel">
      <header>
        <h2>报告生成 Prompt</h2>
        <span>{promptState.data?.source === "global" ? "全局设置" : "班级设置"}</span>
      </header>
      {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
      <StateBlock loading={promptState.loading && !promptState.data} error={promptState.error}>
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
      </StateBlock>
    </TeacherCard>
  );
}

function StudentReportDialog({ reportDetail, onClose }: { reportDetail: AnalyticsStudentReportDialog | null; onClose: () => void }) {
  const [selectedReportId, setSelectedReportId] = useState("");
  const open = Boolean(reportDetail);
  const classId = reportDetail?.classId || "";
  const student = reportDetail?.student || null;
  const studentId = student?.student_id || "";

  useEffect(() => {
    setSelectedReportId("");
  }, [classId, studentId, open]);

  const reportsState = useAsyncData(
    () => (open && classId && studentId ? listTeacherStudentAssessmentReports(classId, studentId) : Promise.resolve({ reports: [] as StudentAssessmentReportSummary[] })),
    [open, classId, studentId],
  );
  const reports = reportsState.data?.reports || [];
  useEffect(() => {
    if (!selectedReportId && reports[0]?.id) setSelectedReportId(reports[0].id);
    if (selectedReportId && !reports.length) setSelectedReportId("");
    if (selectedReportId && reports.length && !reports.some((report) => report.id === selectedReportId)) setSelectedReportId(reports[0]?.id || "");
  }, [reports, selectedReportId]);

  const reportDetailState = useAsyncData(
    () => (open && classId && studentId && selectedReportId ? getTeacherStudentAssessmentReport(classId, studentId, selectedReportId) : Promise.resolve(null)),
    [open, classId, studentId, selectedReportId],
  );

  return (
    <TeacherModal
      open={open}
      className="legacy-student-report-dialog"
      title={student ? `${student.student_name} · 测试报告` : "测试报告"}
      onCancel={onClose}
      footer={null}
      width={900}
    >
      {student ? (
        <div className="legacy-student-report-dialog-body" data-testid="teacher-student-report-dialog">
          <div className="legacy-student-report-summary-strip">
            <article>
              <span>学生</span>
              <strong>{student.student_name}</strong>
              <small>{student.student_id}</small>
            </article>
            <article>
              <span>测试次数</span>
              <strong>{reports.length} 次</strong>
            </article>
            <article>
              <span>平均分</span>
              <strong>{scoreLabel(student.average_score)}</strong>
            </article>
          </div>
          <StateBlock loading={reportsState.loading && !reportsState.data} error={reportsState.error}>
            {reports.length ? (
              <div className="legacy-student-report-layout">
                <div className="legacy-report-list" aria-label="学生测试报告列表">
                  {reports.map((report) => (
                    <button
                      type="button"
                      key={report.id}
                      aria-pressed={report.id === selectedReportId}
                      className={report.id === selectedReportId ? "selected" : ""}
                      onClick={() => setSelectedReportId(report.id)}
                    >
                      <strong className="legacy-report-list-title">{report.title}</strong>
                      <strong className="legacy-report-list-score">{scoreLabel(report.score)}</strong>
                      <span className="legacy-report-list-meta">
                        {formatShortDateTime(report.completed_at)} · {report.correct_count}/{report.total_count} 题 · 错题 {report.wrong_count}
                      </span>
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
                    <TeacherEmptyState message="请选择一份报告。" compact />
                  )}
                </StateBlock>
              </div>
            ) : (
              <TeacherEmptyState message="当前学生暂无测试报告。" compact />
            )}
          </StateBlock>
        </div>
      ) : null}
    </TeacherModal>
  );
}
