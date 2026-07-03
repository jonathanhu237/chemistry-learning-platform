import { FormEvent, type CSSProperties, type DependencyList, type MouseEvent as ReactMouseEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  changeCatalogNodeStatus,
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
  TeacherUiProvider,
} from "./ui/TeacherUI";

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
  "/recommend",
  "/question-bank",
  "/scores",
  "/workbench",
  "/import",
];

type RouteKey = "experiments" | "questions" | "analytics" | "reports";
type ObjectiveQuestionType = Question["question_type"];

const navItems: Array<{ key: RouteKey; label: string; path: string }> = [
  { key: "experiments", label: "实验管理", path: "/experiments" },
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
        <img src={logoSrc} alt="实验平台标识" className="legacy-sidebar-logo" />
        <strong>无机化学实验教学后台</strong>
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
      <section className="legacy-teacher-login-card">
        <img src={logoSrc} alt="实验平台标识" />
        <span className="eyebrow">Teacher</span>
        <h1>无机化学实验教学后台</h1>
        <p>管理实验目录与点位资料，基于点位内容出题，并查看学生学习与报告生成结果。</p>
        <TeacherForm data-testid="teacher-login-form" className="legacy-teacher-login-form" layout="vertical" initialValues={{ username: "teacher" }} onFinish={submit}>
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
type CatalogCreateMenuState = { x: number; y: number; parentId: string; parentTitle: string };
type CatalogCreateRequest = { kind: CatalogNodeKind; parentId: string; parentTitle: string };

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
  const [createMenu, setCreateMenu] = useState<CatalogCreateMenuState | null>(null);
  const [createRequest, setCreateRequest] = useState<CatalogCreateRequest | null>(null);
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
    if (!createMenu) return;
    const closeMenu = () => setCreateMenu(null);
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setCreateMenu(null);
    };
    window.addEventListener("click", closeMenu);
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [createMenu]);

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
  const createParentFromNode = (node?: CatalogQuestionBankNode): Pick<CatalogCreateMenuState, "parentId" | "parentTitle"> => {
    if (!node) return { parentId: "", parentTitle: rootCreateTitle };
    if (node.node_kind === "directory") return { parentId: node.node_id, parentTitle: node.title };
    const parent = nodes.find((item) => item.node_id === node.parent_id);
    return { parentId: node.parent_id || "", parentTitle: parent?.title || rootCreateTitle };
  };
  const openCreateMenu = (event: ReactMouseEvent, node?: CatalogQuestionBankNode) => {
    event.preventDefault();
    event.stopPropagation();
    if (node) setSelectedNodeId(node.node_id);
    const parent = createParentFromNode(node);
    setCreateMenu({
      ...parent,
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
                  setCreateMenu(null);
                  setCreateRequest(null);
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
              onContextMenu={openCreateMenu}
            />
            <CatalogCreateContextMenu
              menu={createMenu}
              onChoose={(kind) => {
                if (!createMenu) return;
                setCreateRequest({ kind, parentId: createMenu.parentId, parentTitle: createMenu.parentTitle });
                setCreateMenu(null);
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
                  onSaved={() => {
                    setNotice("已保存节点资料。");
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
            if (isDirectory) onContextMenu(event, node);
            else {
              event.preventDefault();
              event.stopPropagation();
            }
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

function CatalogCreateContextMenu({
  menu,
  onChoose,
}: {
  menu: CatalogCreateMenuState | null;
  onChoose: (kind: CatalogNodeKind) => void;
}) {
  if (!menu) return null;
  return (
    <div className="legacy-catalog-context-menu" role="menu" style={{ left: menu.x, top: menu.y }} onClick={(event) => event.stopPropagation()}>
      <strong>{menu.parentTitle}</strong>
      <button type="button" role="menuitem" onClick={() => onChoose("directory")}>
        新增目录
      </button>
      <button type="button" role="menuitem" onClick={() => onChoose("point")}>
        新增点位
      </button>
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
        checkedChildren="已启用"
        unCheckedChildren="未启用"
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

function NodeEditor({ detail, onSaved, onError }: { detail: CatalogNodeDetail; onSaved: () => void; onError: (value: string) => void }) {
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
      testId="teacher-page-questions"
    >
      <StateBlock loading={catalog.loading && !catalog.data} error={catalog.error}>
        <MetricGrid
          metrics={[
            { label: "题目总数", value: Number(catalog.data?.totals.question_count || 0), unit: "题" },
            { label: "已发布", value: Number(catalog.data?.totals.published_count || 0), unit: "题" },
            { label: "待审题", value: Number(draftsState.data?.items.filter((item) => item.status === "draft").length || 0), unit: "题" },
            { label: "点位", value: points.length, unit: "项" },
          ]}
        />
        {notice ? <NoticeBlock>{notice}</NoticeBlock> : null}
        {actionError ? <ErrorBlock>{actionError}</ErrorBlock> : null}
        <TeacherCard className="legacy-table-card legacy-question-demo">
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
                <TeacherInput.TextArea value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={5} />
              </label>
              <TeacherButton type="primary" htmlType="submit" className="primary-button" disabled={generating || !selectedPoint}>
                {generating ? "生成中..." : "生成待审题"}
              </TeacherButton>
            </form>
            <section className="legacy-question-review-panel">
              <div className="legacy-question-review-head">
                <strong>待审题</strong>
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
