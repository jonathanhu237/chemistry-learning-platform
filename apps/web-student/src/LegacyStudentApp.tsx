import { FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import { BookOpenCheck, ChevronRight, ClipboardList, FileText, Folder, Home, PlayCircle, Video, type LucideIcon } from "lucide-react";

import {
  getAuthToken,
  legacyStudentErrorMessage,
  loadCustomAssessmentOptions,
  loadCatalogNode,
  loadChapterCatalog,
  loadCurrentUser,
  loadLegacyAssessmentReport,
  loadLegacyAssessmentReports,
  loadLegacyVideoPoints,
  loadLearningPage,
  loadPointDetail,
  mediaUrl,
  setAuthToken,
  startCustomAssessment,
  startPointAssessment,
  startSmartAssessment,
  submitSmartAssessment,
  studentLogin,
  type AssessmentReportSummary,
  type AuthUser,
  type CustomAssessmentExperimentOption,
  type CustomAssessmentOptionsResponse,
  type LegacyAssessmentReportDetail,
  type LegacyVideoPointItem,
  type PointDetail,
  type PublicSmartAssessmentQuestion,
  type SmartAssessmentAnswer,
  type SmartAssessmentReport,
  type SmartAssessmentResponse,
  type StudentCatalogNodeCard,
  type StudentCatalogNodeResponse,
  type StudentLearningElementBadge,
  type StudentLearningPageResponse,
  type StudentLearningProfile,
} from "./api";
import {
  findProfileForElement,
  formatProfileShortTitle,
  formatProfileTitle,
  legacyAreaColors,
  legacyAreaInk,
  legacyAreaLabels,
  legacyAreaOrder,
  periodicMetaForSymbol,
  profileHasArea,
  periodicAreaIdForElement,
  periodicGridColumn,
  periodicGridRow,
  type LegacyAreaId,
  type LegacyPeriodicElement,
} from "./legacyLearning";
import { periodicElements } from "./legacyPeriodic";

const logoSrc = `${import.meta.env.BASE_URL}assets/sysu-lockup-red.svg`;
const emblemSrc = `${import.meta.env.BASE_URL}assets/sysu-emblem-red.svg`;
const forbiddenPathSegments = ["/ai", "/assistant", "/artifact", "/learning-assistant", "/monitoring", "/ai-config"];
const legacyAssessmentSessionPrefix = "chem_student_old_assessment_session:";
const legacyAssessmentReportPrefix = "chem_student_old_assessment_report:";

type LegacyRootTab = "home" | "learn" | "assessment" | "reports";

const legacyNavItems: Array<{ id: LegacyRootTab; label: string; path: string; Icon: LucideIcon }> = [
  { id: "home", label: "主页", path: "/", Icon: Home },
  { id: "learn", label: "学习", path: "/learn", Icon: BookOpenCheck },
  { id: "assessment", label: "评测", path: "/assessment", Icon: ClipboardList },
  { id: "reports", label: "报告", path: "/reports", Icon: FileText },
];

function currentLocation(): string {
  const path = window.location.pathname || "/";
  return `${path}${window.location.search || ""}`;
}

function pathOnly(location: string): string {
  return location.split("?")[0] || "/";
}

function queryFor(location: string): URLSearchParams {
  return new URLSearchParams(location.includes("?") ? location.slice(location.indexOf("?") + 1) : "");
}

function navigate(path: string): void {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

function routeWithQuery(path: string, params: Record<string, string | null | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const text = query.toString();
  return text ? `${path}?${text}` : path;
}

function useLocation(): string {
  const [location, setLocation] = useState(currentLocation);
  useEffect(() => {
    const update = () => setLocation(currentLocation());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return location;
}

function isForbiddenPath(path: string): boolean {
  return forbiddenPathSegments.some((segment) => path.startsWith(segment));
}

function decodePathTail(path: string, prefix: string): string {
  return decodeURIComponent(path.replace(prefix, ""));
}

function safeBackPath(value: string | null, fallback = "/"): string {
  if (!value || !value.startsWith("/") || isForbiddenPath(pathOnly(value))) return fallback;
  return value;
}

function activeTabFor(location: string): LegacyRootTab {
  const path = pathOnly(location);
  if (path.startsWith("/assessment")) return "assessment";
  if (path.startsWith("/profile") || path.startsWith("/reports")) return "reports";
  if (path.startsWith("/learn")) return "learn";
  if (path.startsWith("/videos/")) {
    const from = queryFor(location).get("from");
    return from?.startsWith("/learn") ? "learn" : "home";
  }
  return "home";
}

function chapterRoute(profileId: string, elementSymbol?: string | null): string {
  return routeWithQuery(`/learn/chapter/${encodeURIComponent(profileId)}`, { element: elementSymbol || "" });
}

function catalogRoute(nodeId: string, profileId: string, chapterId?: string | null, elementSymbol?: string | null): string {
  return routeWithQuery(`/learn/catalog/${encodeURIComponent(nodeId)}`, {
    profile: profileId,
    chapter: chapterId || "",
    element: elementSymbol || "",
  });
}

function pointRoute(nodeId: string, from: string): string {
  return routeWithQuery(`/videos/${encodeURIComponent(nodeId)}`, { from });
}

type LearningRouteContext = {
  profileId: string;
  chapterId: string;
  elementSymbol: string;
};

function learningContextFromPath(path: string): LearningRouteContext {
  const params = queryFor(path);
  const cleanPath = pathOnly(path);
  let profileId = params.get("profile") || "";
  if (!profileId && cleanPath.startsWith("/learn/chapter/")) {
    profileId = decodePathTail(cleanPath, "/learn/chapter/");
  }
  return {
    profileId,
    chapterId: params.get("chapter") || "",
    elementSymbol: params.get("element") || "",
  };
}

function pointOwningCatalogRoute(detail: PointDetail | null, sourceBackPath: string): string {
  const context = learningContextFromPath(sourceBackPath);
  const path = detail?.assessment_context?.catalog_path?.length ? detail.assessment_context.catalog_path : detail?.breadcrumbs || [];
  const currentPointId = detail?.node_id || detail?.placement_node_id || detail?.assessment_context?.point_node_id || "";
  const parentDirectory = [...path].reverse().find((item) => item.node_kind === "directory" && item.node_id !== currentPointId);

  if (parentDirectory?.node_id) {
    return catalogRoute(parentDirectory.node_id, context.profileId, parentDirectory.chapter_id || detail?.chapter_id || context.chapterId, context.elementSymbol);
  }
  if (context.profileId) return chapterRoute(context.profileId, context.elementSymbol);
  return routeWithQuery("/learn", { chapter: detail?.chapter_id || context.chapterId });
}

function pointBackAction(detail: PointDetail | null, sourceBackPath: string): { label: string; path: string } {
  const sourcePath = pathOnly(sourceBackPath);
  if (sourcePath === "/") return { label: "返回首页", path: "/" };
  if (sourcePath.startsWith("/learn")) return { label: "返回学习目录", path: pointOwningCatalogRoute(detail, sourceBackPath) };
  if (sourcePath.startsWith("/videos/")) {
    const nestedSource = safeBackPath(queryFor(sourceBackPath).get("from"), "/");
    return pointBackAction(detail, nestedSource);
  }
  return { label: "返回首页", path: "/" };
}

function sortLegacyVideoPoints(items: LegacyVideoPointItem[]): LegacyVideoPointItem[] {
  return items
    .map((item, index) => ({ item, index }))
    .sort((left, right) => {
      const leftMediaCount = left.item.published_media_count ?? left.item.media_count ?? 0;
      const rightMediaCount = right.item.published_media_count ?? right.item.media_count ?? 0;
      const leftHasVideo = leftMediaCount > 0 ? 0 : 1;
      const rightHasVideo = rightMediaCount > 0 ? 0 : 1;
      if (leftHasVideo !== rightHasVideo) return leftHasVideo - rightHasVideo;

      const leftRecommended = left.item.is_recommended ? 0 : 1;
      const rightRecommended = right.item.is_recommended ? 0 : 1;
      if (leftRecommended !== rightRecommended) return leftRecommended - rightRecommended;

      const leftOrder = left.item.is_recommended ? left.item.recommended_order ?? 0 : 0;
      const rightOrder = right.item.is_recommended ? right.item.recommended_order ?? 0 : 0;
      if (leftOrder !== rightOrder) return leftOrder - rightOrder;

      return left.index - right.index;
    })
    .map(({ item }) => item);
}

function oldStorage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function readOldJson<T>(key: string): T | null {
  try {
    const raw = oldStorage()?.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function storeLegacyAssessmentSession(assessment: SmartAssessmentResponse): void {
  try {
    oldStorage()?.setItem(`${legacyAssessmentSessionPrefix}${assessment.session_id}`, JSON.stringify(assessment));
  } catch {
    // The route transition still works if sessionStorage is unavailable.
  }
}

function readLegacyAssessmentSession(sessionId: string): SmartAssessmentResponse | null {
  if (!sessionId) return null;
  return readOldJson<SmartAssessmentResponse>(`${legacyAssessmentSessionPrefix}${sessionId}`);
}

function storeLegacyAssessmentReport(report: SmartAssessmentReport): void {
  try {
    oldStorage()?.setItem(`${legacyAssessmentReportPrefix}${report.session_id}`, JSON.stringify(report));
  } catch {
    // Reports are still returned in-memory after submit if storage is unavailable.
  }
}

function assessmentSessionRoute(sessionId: string, from = "assessment"): string {
  return routeWithQuery(`/assessment/session/${encodeURIComponent(sessionId)}`, { from });
}

export function LegacyStudentApp() {
  const location = useLocation();
  const activePath = pathOnly(location);
  const activeTab = activeTabFor(location);
  const params = queryFor(location);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checkingSession, setCheckingSession] = useState(Boolean(getAuthToken()));

  useEffect(() => {
    if (!getAuthToken()) return;
    let active = true;
    setCheckingSession(true);
    loadCurrentUser()
      .then((value) => {
        if (active && value.role === "student") setUser(value);
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
    if (isForbiddenPath(activePath)) navigate("/");
  }, [activePath]);

  const safePath = isForbiddenPath(activePath) ? "/" : activePath;

  if (checkingSession) {
    return <ShellFrame>正在载入实验学习平台...</ShellFrame>;
  }

  if (!user) {
    return <LoginScreen onLogin={setUser} />;
  }

  const logout = () => {
    setAuthToken("");
    setUser(null);
    navigate("/");
  };

  return (
    <ShellFrame onLogout={logout}>
      <LegacyBottomNav activeTab={activeTab} />
      {safePath.startsWith("/videos/") ? (
        <PointPage nodeId={decodePathTail(safePath, "/videos/")} backPath={safeBackPath(params.get("from"))} />
      ) : safePath.startsWith("/learn/catalog/") ? (
        <LearningDirectoryPage
          nodeId={decodePathTail(safePath, "/learn/catalog/")}
          profileId={params.get("profile") || ""}
          chapterId={params.get("chapter") || ""}
          elementSymbol={params.get("element") || ""}
        />
      ) : safePath.startsWith("/learn/chapter/") ? (
        <LearningChapterPage profileId={decodePathTail(safePath, "/learn/chapter/")} initialElementSymbol={params.get("element") || ""} />
      ) : safePath.startsWith("/learn") ? (
        <LearningRootPage />
      ) : safePath.startsWith("/assessment/session/") ? (
        <AssessmentSessionPage sessionId={decodePathTail(safePath, "/assessment/session/")} />
      ) : safePath.startsWith("/assessment") ? (
        <AssessmentPage />
      ) : safePath.startsWith("/reports/") ? (
        <ReportDetailPage reportId={decodePathTail(safePath, "/reports/")} />
      ) : safePath.startsWith("/profile") || safePath.startsWith("/reports") ? (
        <ReportsPage user={user} />
      ) : (
        <HomeVideoLibraryPage />
      )}
    </ShellFrame>
  );
}

function LegacyBottomNav({ activeTab }: { activeTab: LegacyRootTab }) {
  return (
    <nav className="legacy-tabbar" aria-label="旧版学生底部导航">
      {legacyNavItems.map(({ id, label, path, Icon }) => (
        <button key={id} className={activeTab === id ? "active" : ""} aria-current={activeTab === id ? "page" : undefined} aria-label={label} onClick={() => navigate(path)}>
          <span className="legacy-tabbar-icon" aria-hidden="true">
            <Icon />
          </span>
          <span className="legacy-tabbar-label">{label}</span>
        </button>
      ))}
    </nav>
  );
}

function ShellFrame({ children, onLogout }: { children: ReactNode; onLogout?: () => void }) {
  return (
    <div className="legacy-student-shell">
      <header className="legacy-student-header">
        <div className="legacy-brand">
          <img src={logoSrc} alt="中山大学" />
          <span>无机化学实验学习平台</span>
        </div>
        {onLogout ? (
          <button className="legacy-header-logout" type="button" onClick={onLogout}>
            退出登录
          </button>
        ) : null}
      </header>
      <main>{children}</main>
    </div>
  );
}

function LoginScreen({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const response = await studentLogin(studentId, password);
      setAuthToken(response.access_token);
      onLogin(response.user);
    } catch (caught) {
      setError(legacyStudentErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="legacy-login-page">
      <section className="legacy-login-panel">
        <img className="legacy-login-emblem" src={emblemSrc} alt="" />
        <img className="legacy-login-logo" src={logoSrc} alt="中山大学" />
        <h1>无机化学实验学习平台</h1>
        <p>以实验为知识单元，结合 BKT 掌握度跟踪、视频学习和测评反馈，支持学生开展自主实验学习。</p>
        <form onSubmit={submit}>
          <label>
            学号
            <input value={studentId} onChange={(event) => setStudentId(event.target.value)} autoComplete="username" />
          </label>
          <label>
            密码
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          {error ? <div className="legacy-error">{error}</div> : null}
          <button className="primary-button" disabled={submitting}>
            {submitting ? "登录中..." : "进入学习"}
          </button>
        </form>
      </section>
    </div>
  );
}

function HomeVideoLibraryPage() {
  const [items, setItems] = useState<LegacyVideoPointItem[]>([]);
  const [searchResults, setSearchResults] = useState<LegacyVideoPointItem[]>([]);
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const trimmedQuery = query.trim();

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    if (trimmedQuery) {
      loadLegacyVideoPoints(trimmedQuery, 200)
        .then((response) => {
          if (!active) return;
          setSearchResults(sortLegacyVideoPoints(response.items || []));
          setItems([]);
        })
        .catch((caught) => {
          if (active) setError(legacyStudentErrorMessage(caught));
        })
        .finally(() => {
          if (active) setLoading(false);
        });
      return () => {
        active = false;
      };
    }

    loadLegacyVideoPoints("", 500)
      .then((response) => {
        if (!active) return;
        setItems(sortLegacyVideoPoints(response.items || []));
        setSearchResults([]);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [trimmedQuery]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setQuery(draft.trim());
  };

  const clearSearch = () => {
    setDraft("");
    setQuery("");
  };

  return (
    <section className="legacy-page" data-testid="student-video-feed">
      <div className="legacy-hero-band">
        <div>
          <span className="eyebrow">全部实验视频</span>
          <h1>实验视频库</h1>
          <p>按已发布实验点位汇总全部可学习视频点位，学生可直接检索实验现象、试剂或点位名称，进入对应实验知识单元学习。默认显示全部视频点位，不管当前是否已绑定视频。搜索后显示搜索结果内容。</p>
        </div>
      </div>

      <form className="legacy-video-search" role="search" onSubmit={submit}>
        <label>
          <span>搜索实验视频</span>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="输入实验、试剂、现象或点位名称" />
        </label>
        <button className="primary-button" type="submit">
          搜索
        </button>
      </form>
      {trimmedQuery ? (
        <div className="legacy-search-summary">
          <span>当前共 {searchResults.length} 个搜索结果</span>
          <button className="text-button" type="button" onClick={clearSearch}>
            返回全部视频库
          </button>
        </div>
      ) : null}

      {loading ? <div className="legacy-state">正在载入实验视频库...</div> : null}
      {error ? <div className="legacy-error">{error}</div> : null}
      {!loading && !error && trimmedQuery && !searchResults.length ? <div className="legacy-state">未找到匹配的实验视频。</div> : null}
      {!loading && !error && !trimmedQuery && !items.length ? <div className="legacy-state">暂无已发布的实验点位。</div> : null}

      {trimmedQuery ? (
        <div className="legacy-feed-list" aria-label="实验视频搜索结果">
          {searchResults.map((item) => (
            <SearchResultCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <>
          <div className="legacy-feed-list" aria-label="全部实验视频">
            {items.map((item) => (
              <HomeVideoCard key={item.id} item={item} />
            ))}
          </div>
          {!loading && !error && items.length ? (
            <div className="legacy-list-footer">
              <span>没有更多视频了</span>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

function HomeVideoCard({ item }: { item: LegacyVideoPointItem }) {
  const location = item.catalog_path?.slice(0, -1).slice(-2).join(" / ") || "实验点位";
  return (
    <article className="legacy-video-card">
      {item.is_recommended ? <span className="legacy-recommend-badge">推荐学习</span> : null}
      <button className="legacy-video-button" onClick={() => navigate(pointRoute(item.node_id, "/"))} aria-label={`打开 ${item.title}`}>
        {item.thumbnail_path ? <img src={mediaUrl(item.thumbnail_path)} alt="" /> : <span className="poster-fallback">实验点位</span>}
      </button>
      <div className="legacy-video-body">
        <h2>{item.title}</h2>
        <p>{item.summary || item.snippet || "围绕该实验点位完成现象观察、原理理解和操作注意事项学习。"}</p>
        <div className="legacy-meta-row">
          <span>{location}</span>
        </div>
      </div>
    </article>
  );
}

function SearchResultCard({ item }: { item: LegacyVideoPointItem }) {
  const location = item.catalog_path?.slice(0, -1).slice(-2).join(" / ") || "实验视频库";
  return (
    <article className="legacy-video-card search-result">
      {item.is_recommended ? <span className="legacy-recommend-badge">推荐学习</span> : null}
      <button className="legacy-video-button result-icon" onClick={() => navigate(pointRoute(item.node_id, "/"))} aria-label={`打开 ${item.title}`}>
        {item.thumbnail_path ? <img src={mediaUrl(item.thumbnail_path)} alt="" /> : <span>视频</span>}
      </button>
      <div className="legacy-video-body">
        <h2>{item.title}</h2>
        <p>{item.snippet || item.summary || "来自实验视频库的匹配点位。"}</p>
        <div className="legacy-meta-row">
          <span>{location}</span>
        </div>
      </div>
    </article>
  );
}

function LearningRootPage() {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectionMessage, setSelectionMessage] = useState("");
  const [selectedArea, setSelectedArea] = useState<LegacyAreaId | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loadLearningPage(null)
      .then((value) => {
        if (active) setPage(value);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const profiles = page?.profiles || [];
  const filteredProfiles = useMemo(() => (selectedArea ? profiles.filter((profile) => profileHasArea(profile, selectedArea)) : profiles), [profiles, selectedArea]);
  const selectElement = (element: LegacyPeriodicElement) => {
    const profile = findProfileForElement(element, profiles);
    if (!profile) {
      setSelectionMessage(`${element.symbol} ${element.name} 暂无已发布学习章节。`);
      return;
    }
    navigate(chapterRoute(profile.profile_id, element.symbol));
  };

  return (
    <section className="legacy-page legacy-learning-page legacy-drilldown-page">
      <div className="legacy-section-head">
        <span className="eyebrow">实验知识图谱式导航</span>
        <h1>元素周期表学习入口</h1>
        <p>从元素出发进入对应元素族和实验章节，再逐层打开目录、子目录与实验点位。</p>
      </div>
      {loading ? <div className="legacy-state">正在载入元素学习入口...</div> : null}
      {error ? <div className="legacy-error">{error}</div> : null}
      {!loading && !error ? (
        <>
          <PeriodicTableSelector
            selectedArea={selectedArea}
            onSelectArea={(areaId) => {
              setSelectedArea((current) => (current === areaId ? null : areaId));
              setSelectionMessage("");
            }}
            onSelectElement={selectElement}
          />
          {selectionMessage ? <div className="legacy-state compact">{selectionMessage}</div> : null}
          <LearningProfileIndex profiles={filteredProfiles} selectedArea={selectedArea} />
        </>
      ) : null}
    </section>
  );
}

function PeriodicTableSelector({
  selectedArea,
  onSelectArea,
  onSelectElement,
}: {
  selectedArea: LegacyAreaId | null;
  onSelectArea: (areaId: LegacyAreaId) => void;
  onSelectElement: (element: LegacyPeriodicElement) => void;
}) {
  return (
    <section className="legacy-periodic-card" aria-label="元素周期表">
      <div className="legacy-periodic-head">
        <div>
          <span className="eyebrow">选择元素</span>
          <h2>元素周期表</h2>
        </div>
        <div className="legacy-area-legend" aria-label="元素分区">
          {legacyAreaOrder.map((areaId) => (
            <button
              key={areaId}
              className={selectedArea === areaId ? "active" : ""}
              type="button"
              style={{ borderColor: legacyAreaColors[areaId], color: legacyAreaInk[areaId] }}
              aria-pressed={selectedArea === areaId}
              onClick={() => onSelectArea(areaId)}
            >
              <i style={{ background: legacyAreaColors[areaId] }} />
              {legacyAreaLabels[areaId]}
            </button>
          ))}
        </div>
      </div>
      <div className="legacy-periodic-scroll" aria-label="完整元素周期表，可横向滑动">
        <div className="legacy-periodic-grid">
          {Array.from({ length: 18 }, (_, index) => (
            <span className="legacy-group-number" key={index} style={{ gridColumn: index + 1, gridRow: 1 }}>
              {index + 1}
            </span>
          ))}
          {periodicElements.map((element) => {
            const areaId = periodicAreaIdForElement(element);
            return (
              <button
                key={element.atomicNumber}
                className={`legacy-element-cell${selectedArea && selectedArea !== areaId ? " is-muted" : ""}${selectedArea === areaId ? " is-area-selected" : ""}`}
                type="button"
                style={{
                  gridColumn: periodicGridColumn(element),
                  gridRow: periodicGridRow(element),
                  background: legacyAreaColors[areaId],
                  color: legacyAreaInk[areaId],
                }}
                title={`${element.symbol} ${element.name}`}
                aria-label={`${element.symbol} ${element.name}`}
                onClick={() => onSelectElement(element)}
              >
                <strong>{element.symbol}</strong>
                <small>{element.name}</small>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function LearningProfileIndex({ profiles, selectedArea }: { profiles: StudentLearningPageResponse["profiles"]; selectedArea: LegacyAreaId | null }) {
  if (!profiles.length) return <div className="legacy-state">{selectedArea ? `暂无${legacyAreaLabels[selectedArea]}学习章节。` : "暂无已发布的元素学习章节。"}</div>;
  return (
    <section className="legacy-profile-index" aria-label="可学习章节">
      <h2>可学习章节</h2>
      <div className="legacy-profile-grid">
        {profiles.map((profile) => (
          <button key={profile.profile_id} type="button" title={formatProfileTitle(profile)} onClick={() => navigate(chapterRoute(profile.profile_id, profile.element_symbols[0]))}>
            <strong>{formatProfileShortTitle(profile)}</strong>
          </button>
        ))}
      </div>
    </section>
  );
}

function LearningChapterPage({ profileId, initialElementSymbol }: { profileId: string; initialElementSymbol: string }) {
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [catalog, setCatalog] = useState<StudentCatalogNodeCard[]>([]);
  const [selectedElementSymbol, setSelectedElementSymbol] = useState(initialElementSymbol);
  const [loading, setLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loadLearningPage(profileId)
      .then((value) => {
        if (!active) return;
        setPage(value);
        const profile = value.active_profile;
        const preferred = initialElementSymbol || profile?.default_element_symbol || profile?.element_symbols?.[0] || "";
        setSelectedElementSymbol(preferred);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [initialElementSymbol, profileId]);

  const profile = page?.active_profile || null;

  useEffect(() => {
    if (!profile?.chapter_id) return;
    let active = true;
    setCatalogLoading(true);
    setError("");
    loadChapterCatalog(profile.chapter_id)
      .then((value) => {
        if (active) setCatalog(value.nodes || []);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setCatalogLoading(false);
      });
    return () => {
      active = false;
    };
  }, [profile?.chapter_id]);

  if (loading) return <section className="legacy-page"><div className="legacy-state">正在载入学习章节...</div></section>;
  if (error) return <section className="legacy-page"><div className="legacy-error">{error}</div></section>;
  if (!profile) return <section className="legacy-page"><div className="legacy-state">没有找到学习章节。</div></section>;

  const selectedElement = findSelectedProfileElement(profile, selectedElementSymbol);
  const currentRoute = chapterRoute(profile.profile_id, selectedElement?.symbol || selectedElementSymbol);

  return (
    <section className="legacy-page legacy-learning-page legacy-drilldown-page">
      <DrilldownTopbar title={`当前章节：${formatProfileShortTitle(profile)}`} actionLabel="返回上一级目录" onAction={() => navigate("/learn")} />
      <section className="legacy-learning-chapter">
        <ElementRail profile={profile} selectedSymbol={selectedElement?.symbol || ""} onSelect={setSelectedElementSymbol} />
        {selectedElement ? <SelectedElementSummary element={selectedElement} /> : null}
      </section>
      <section className="legacy-catalog-panel">
        {catalogLoading ? <div className="legacy-state">正在载入目录...</div> : null}
        {!catalogLoading ? (
          <CatalogNodeList
            nodes={catalog}
            profileId={profile.profile_id}
            chapterId={profile.chapter_id}
            elementSymbol={selectedElement?.symbol || selectedElementSymbol}
            from={currentRoute}
          />
        ) : null}
      </section>
    </section>
  );
}

function LearningDirectoryPage({ nodeId, profileId, chapterId, elementSymbol }: { nodeId: string; profileId: string; chapterId: string; elementSymbol: string }) {
  const [detail, setDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const [profileTitle, setProfileTitle] = useState("学习章节");
  const [activeProfile, setActiveProfile] = useState<StudentLearningProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    Promise.all([loadCatalogNode(nodeId), profileId ? loadLearningPage(profileId).catch(() => null) : Promise.resolve(null)])
      .then(([nodeResponse, learningPage]) => {
        if (!active) return;
        setDetail(nodeResponse);
        if (learningPage?.active_profile) {
          setActiveProfile(learningPage.active_profile);
          setProfileTitle(formatProfileTitle(learningPage.active_profile));
        }
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [nodeId, profileId]);

  if (loading) return <section className="legacy-page"><div className="legacy-state">正在载入目录...</div></section>;
  if (error) return <section className="legacy-page"><div className="legacy-error">{error}</div></section>;
  if (!detail) return <section className="legacy-page"><div className="legacy-state">没有找到目录。</div></section>;

  const currentRoute = catalogRoute(nodeId, profileId, detail.node.chapter_id || chapterId, elementSymbol);
  const rootRoute = profileId ? chapterRoute(profileId, elementSymbol) : "/learn";
  const selectedElement = activeProfile ? findSelectedProfileElement(activeProfile, elementSymbol) : null;

  return (
    <section className="legacy-page legacy-learning-page legacy-drilldown-page">
      <DrilldownTopbar title={`当前章节：${activeProfile ? formatProfileShortTitle(activeProfile) : profileTitle}`} actionLabel="返回上一级目录" onAction={() => navigate(rootRoute)} />
      {activeProfile ? (
        <section className="legacy-learning-chapter">
          <ElementRail profile={activeProfile} selectedSymbol={selectedElement?.symbol || ""} onSelect={(symbol) => navigate(chapterRoute(activeProfile.profile_id, symbol))} />
          {selectedElement ? <SelectedElementSummary element={selectedElement} /> : null}
        </section>
      ) : null}
      <section className="legacy-catalog-panel">
        <CatalogNodeList
          nodes={detail.children}
          profileId={profileId}
          chapterId={detail.node.chapter_id || chapterId}
          elementSymbol={elementSymbol}
          from={currentRoute}
        />
      </section>
    </section>
  );
}

function DrilldownTopbar({ title, actionLabel, onAction }: { title: string; actionLabel: string; onAction: () => void }) {
  return (
    <div className="legacy-drilldown-topbar">
      <div className="legacy-drilldown-breadcrumb" aria-label="学习路径">
        <button type="button" className="legacy-breadcrumb-link" onClick={() => navigate("/learn")}>
          元素周期表
        </button>
        <span aria-hidden="true">/</span>
        <strong>{title}</strong>
      </div>
      <button className="text-button" onClick={onAction}>
        {actionLabel}
      </button>
    </div>
  );
}

function ElementRail({
  profile,
  selectedSymbol,
  onSelect,
}: {
  profile: StudentLearningProfile;
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}) {
  return (
    <div className="legacy-element-rail" aria-label="同族元素">
      {profile.elements.map((element) => {
        const active = element.symbol === selectedSymbol;
        const periodicMeta = periodicMetaForSymbol(element.symbol);
        const areaId = periodicAreaIdForElement(periodicMeta || element);
        return (
          <button
            key={element.symbol}
            className={active ? "active" : ""}
            type="button"
            style={{ background: legacyAreaColors[areaId], color: legacyAreaInk[areaId] }}
            onClick={() => onSelect(element.symbol)}
          >
            <strong>{element.symbol}</strong>
            <span>{element.name}</span>
          </button>
        );
      })}
    </div>
  );
}

function SelectedElementSummary({ element }: { element: StudentLearningElementBadge }) {
  const groupTag = element.group ? `第${element.group}族` : "";
  const tags = [element.atomic_number ? `原子序数 ${element.atomic_number}` : groupTag, element.period ? `${element.period}周期` : "", element.common_valence ? `常见${element.common_valence}价` : ""]
    .filter(Boolean)
    .slice(0, 3);
  return (
    <div className="legacy-element-summary">
      <div>
        <span>当前元素</span>
        <strong>
          {element.symbol} {element.name}
        </strong>
      </div>
      <p>{element.card_focus || element.card_relevance || "结合本族元素性质观察相关实验现象。"}</p>
      <div className="legacy-meta-row">
        {tags.map((tag) => (
          <span key={tag}>{tag}</span>
        ))}
      </div>
    </div>
  );
}

function findSelectedProfileElement(profile: StudentLearningProfile, symbol: string): StudentLearningElementBadge | null {
  return profile.elements.find((element) => element.symbol === symbol) || profile.elements.find((element) => element.symbol === profile.default_element_symbol) || profile.elements[0] || null;
}

function CatalogNodeList({
  nodes,
  profileId,
  chapterId,
  elementSymbol,
  from,
}: {
  nodes: StudentCatalogNodeCard[];
  profileId: string;
  chapterId: string;
  elementSymbol: string;
  from: string;
}) {
  if (!nodes.length) return <div className="legacy-state">当前目录暂无已发布内容。</div>;
  return (
    <div className="legacy-catalog-list">
      {nodes.map((node) => {
        const isPoint = node.node_kind === "point";
        const EntryIcon = isPoint ? Video : Folder;
        return (
          <article className={`legacy-catalog-row kind-${node.node_kind}`} key={node.node_id}>
            <button
              type="button"
              onClick={() => {
                if (isPoint) navigate(pointRoute(node.node_id, from));
                else navigate(catalogRoute(node.node_id, profileId, node.chapter_id || chapterId, elementSymbol));
              }}
            >
              <span className="legacy-catalog-icon" aria-hidden="true">
                <EntryIcon />
              </span>
              <span className="legacy-catalog-copy">
                <strong>{node.title}</strong>
                {node.summary ? <small>{node.summary}</small> : null}
              </span>
              <ChevronRight className="legacy-catalog-arrow" aria-hidden="true" />
            </button>
          </article>
        );
      })}
    </div>
  );
}

function PointPage({ nodeId, backPath }: { nodeId: string; backPath: string }) {
  const [detail, setDetail] = useState<PointDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    loadPointDetail(nodeId)
      .then((value) => {
        if (active) setDetail(value);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [nodeId]);

  const video = detail?.videos?.[0];
  const backAction = pointBackAction(detail, backPath);
  const relatedPoints = detail?.related_points || [];

  const startPointPosttest = async () => {
    const pointNodeId = detail?.assessment_context?.point_node_id || detail?.placement_node_id || detail?.node_id || nodeId;
    setAssessmentError("");
    setAssessmentLoading(true);
    try {
      const response = await startPointAssessment(pointNodeId);
      storeLegacyAssessmentSession(response);
      navigate(assessmentSessionRoute(response.session_id, "point"));
    } catch (caught) {
      setAssessmentError(legacyStudentErrorMessage(caught));
    } finally {
      setAssessmentLoading(false);
    }
  };

  return (
    <section className="legacy-page">
      <button className="text-button" onClick={() => navigate(backAction.path)}>
        {backAction.label}
      </button>
      {loading ? <div className="legacy-state">正在载入实验点位...</div> : null}
      {error ? <div className="legacy-error">{error}</div> : null}
      {detail ? (
        <article className="legacy-detail-card">
          <div className="legacy-detail-title">
            <span className="eyebrow">实验知识单元</span>
            <h1>{detail.title}</h1>
            <p>{detail.breadcrumbs?.map((item) => item.title).join(" / ")}</p>
          </div>
          {video?.stream_path ? (
            <video className="native-video" controls preload="metadata" poster={mediaUrl(video.thumbnail_path)} src={mediaUrl(video.stream_path)}>
              当前浏览器不支持实验视频播放。
            </video>
          ) : (
            <div className="legacy-state">该点位尚未发布可播放视频。</div>
          )}
          <div className="legacy-two-column">
            <section>
              <h2>实验原理</h2>
              <PrincipleBlock text={detail.principle_equation || detail.principle_text || detail.summary || "暂无原理说明。"} />
            </section>
            <section>
              <h2>现象解释</h2>
              <p>{detail.phenomenon_explanation || "完成视频学习后，可结合测评结果继续巩固该实验点位。"}</p>
            </section>
            <section>
              <h2>安全提示</h2>
              <p>{detail.safety_note || "按教师要求完成观察记录，注意试剂和装置安全。"}</p>
            </section>
          </div>
          <RelatedPointLinks points={relatedPoints} currentRoute={pointRoute(detail.node_id || nodeId, backPath)} />
          <button className="primary-button legacy-point-assessment-button" type="button" disabled={assessmentLoading} onClick={startPointPosttest}>
            <ClipboardList size={20} />
            <span>{assessmentLoading ? "正在组卷..." : "进行学后测评"}</span>
          </button>
          {assessmentError ? <div className="legacy-error">{assessmentError}</div> : null}
        </article>
      ) : null}
    </section>
  );
}

function RelatedPointLinks({ points, currentRoute }: { points: NonNullable<PointDetail["related_points"]>; currentRoute: string }) {
  if (!points.length) return null;
  return (
    <section className="legacy-related-section" aria-label="相关实验链接">
      <h2>相关实验链接</h2>
      <div className="legacy-related-list">
        {points.map((point) => (
          <button key={point.node_id} className="legacy-related-link" type="button" onClick={() => navigate(pointRoute(point.node_id, currentRoute))}>
            <span className="legacy-related-thumb" aria-hidden="true">
              <PlayCircle size={22} />
            </span>
            <span className="legacy-related-copy">
              <strong>{point.title}</strong>
              <small>{relatedPointRelationLabel(point.relation_type)}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function relatedPointRelationLabel(relationType?: string | null): string {
  if (relationType === "default" || relationType === "default_override" || relationType === "generated_default") return "推荐实验";
  return "相关实验";
}

function PrincipleBlock({ text }: { text: string }) {
  const lines = formatPrincipleLines(text);
  return (
    <div className="legacy-principle-block">
      {lines.map((line, index) => (
        <div className="legacy-principle-line" key={`${line.equation}-${line.note}-${index}`}>
          <code>{line.equation}</code>
          {line.note ? <span>{line.note}</span> : null}
        </div>
      ))}
    </div>
  );
}

function formatPrincipleLines(text: string): Array<{ equation: string; note: string }> {
  const normalized = text.replace(/\r/g, "\n").replace(/->/g, "→").replace(/=>/g, "→");
  return normalized
    .split(/\n+|；|;/)
    .flatMap((segment) => splitPrincipleSegment(segment))
    .filter((line) => line.equation || line.note);
}

function splitPrincipleSegment(segment: string): Array<{ equation: string; note: string }> {
  const trimmed = segment.trim();
  if (!trimmed) return [];
  if (!trimmed.includes("//")) return [{ equation: trimmed, note: "" }];
  const lines: Array<{ equation: string; note: string }> = [];
  for (const part of trimmed.split(/\s*\/\/\s*/).map((value) => value.trim()).filter(Boolean)) {
    if (isEquationLike(part)) {
      lines.push({ equation: part, note: "" });
      continue;
    }
    const previous = lines[lines.length - 1];
    if (previous) previous.note = previous.note ? `${previous.note}；${part}` : part;
    else lines.push({ equation: "", note: part });
  }
  return lines;
}

function isEquationLike(value: string): boolean {
  const arrowIndex = value.indexOf("→");
  return arrowIndex > 0 && arrowIndex < value.length - 1;
}

type AssessmentSetupMode = "smart" | "selected" | "random" | "all";
type AnswerMap = Record<string, string>;

const assessmentSetupModes: Array<{ id: AssessmentSetupMode; label: string; summary: string }> = [
  { id: "smart", label: "智能薄弱项测试", summary: "由 BKT 掌握度优先覆盖薄弱和未充分测量点位。" },
  { id: "selected", label: "自选实验范围", summary: "勾选本轮要练习的实验范围后组卷。" },
  { id: "random", label: "随机练习", summary: "从当前可选实验中随机抽取范围后组卷。" },
  { id: "all", label: "全部范围", summary: "覆盖全部有题实验范围后组卷。" },
];

function AssessmentQuestionCountSelector({
  countOptions,
  questionCount,
  onChange,
}: {
  countOptions: number[];
  questionCount: number;
  onChange: (count: number) => void;
}) {
  return (
    <div className="legacy-assessment-count-panel">
      <span>目标题数</span>
      <div className="legacy-question-count-row" aria-label="选择题数">
        {countOptions.map((count) => (
          <button key={count} type="button" className={questionCount === count ? "active" : ""} onClick={() => onChange(count)}>
            {count} 题
          </button>
        ))}
      </div>
    </div>
  );
}

function AssessmentPage() {
  const [data, setData] = useState<CustomAssessmentOptionsResponse | null>(null);
  const [mode, setMode] = useState<AssessmentSetupMode>("smart");
  const [selectingRange, setSelectingRange] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [questionCount, setQuestionCount] = useState(10);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const [optionError, setOptionError] = useState("");

  useEffect(() => {
    let active = true;
    setLoadingOptions(true);
    setOptionError("");
    loadCustomAssessmentOptions()
      .then((response) => {
        if (!active) return;
        setData(response);
        setQuestionCount(response.settings.default_question_count || response.settings.question_count_options?.[0] || 10);
      })
      .catch((caught) => {
        if (active) setOptionError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoadingOptions(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const experiments = data?.experiments || [];
  const eligibleExperiments = useMemo(() => experiments.filter((item) => item.question_count > 0), [experiments]);
  const filteredExperiments = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return experiments.filter((item) => {
      if (!keyword) return true;
      return assessmentOptionSearchText(item).includes(keyword);
    });
  }, [experiments, query]);
  const filteredEligible = useMemo(() => filteredExperiments.filter((item) => item.question_count > 0), [filteredExperiments]);
  const selectedExperiments = useMemo(() => experiments.filter((item) => selectedIds.has(item.id)), [experiments, selectedIds]);
  const countOptions = useMemo(() => {
    const values = data?.settings.question_count_options?.length ? data.settings.question_count_options : [5, 10, 15, 20];
    return Array.from(new Set(values)).sort((left, right) => left - right);
  }, [data?.settings.question_count_options]);
  const selectedCount = mode === "all" ? eligibleExperiments.length : selectedIds.size;
  const availableQuestionCount = eligibleExperiments.reduce((sum, item) => sum + item.question_count, 0);
  const customDisabled = data?.settings.enabled === false;
  const canStartCustom = Boolean(data && eligibleExperiments.length && !customDisabled);

  const toggleExperiment = (option: CustomAssessmentExperimentOption) => {
    if (option.question_count <= 0) return;
    setMode("selected");
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(option.id)) next.delete(option.id);
      else next.add(option.id);
      return next;
    });
  };

  const selectCurrent = () => {
    setMode("selected");
    setSelectedIds((current) => {
      const next = new Set(current);
      filteredEligible.forEach((item) => next.add(item.id));
      return next;
    });
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const chooseMode = (nextMode: AssessmentSetupMode) => {
    setError("");
    setMode(nextMode);
    setSelectingRange(false);
  };

  const start = async () => {
    setError("");
    setStarting(true);
    try {
      let response: SmartAssessmentResponse;
      if (mode === "smart") {
        response = await startSmartAssessment();
      } else {
        if (!data) {
          setError("暂时无法读取实验范围，请稍后再试。");
          return;
        }
        if (customDisabled) {
          setError("教师暂未开放自选范围测评，请使用智能薄弱项测试。");
          return;
        }
        let experimentIds: string[] = [];
        if (mode === "selected") experimentIds = Array.from(selectedIds);
        if (mode === "random") {
          experimentIds = randomExperimentIds(eligibleExperiments, questionCount, data.settings.max_questions_per_experiment || 3);
          setSelectedIds(new Set(experimentIds));
        }
        if (mode === "all") experimentIds = eligibleExperiments.map((item) => item.id);
        if (!experimentIds.length) {
          setError("请先选择至少 1 个有题实验范围。");
          if (mode === "selected") setSelectingRange(true);
          return;
        }
        response = await startCustomAssessment(experimentIds, questionCount);
      }
      storeLegacyAssessmentSession(response);
      navigate(assessmentSessionRoute(response.session_id, "assessment"));
    } catch (caught) {
      setError(legacyStudentErrorMessage(caught));
    } finally {
      setStarting(false);
    }
  };

  if (selectingRange) {
    return (
      <section className="legacy-page legacy-assessment-page">
        <div className="legacy-assessment-subbar legacy-page-topbar">
          <strong>自选实验范围</strong>
          <button
            className="text-button"
            type="button"
            onClick={() => {
              setError("");
              setSelectingRange(false);
            }}
          >
            返回测评方式
          </button>
        </div>

        <section className="legacy-assessment-setup" aria-label="自选实验范围">
          <AssessmentQuestionCountSelector countOptions={countOptions} questionCount={questionCount} onChange={setQuestionCount} />

          {optionError ? <div className="legacy-error">实验范围暂时无法加载；请稍后再试。</div> : null}
          {error ? <div className="legacy-error">{error}</div> : null}

          <div className="legacy-assessment-toolbar">
            <label>
              <span>搜索实验范围</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索实验名称、章节或编号" />
            </label>
            <button type="button" onClick={selectCurrent} disabled={!filteredEligible.length || customDisabled}>
              全选当前列表
            </button>
            <button type="button" onClick={clearSelection} disabled={!selectedIds.size}>
              清空
            </button>
          </div>

          {loadingOptions ? <div className="legacy-state">正在载入可选实验范围...</div> : null}
          {!loadingOptions && !filteredExperiments.length ? <div className="legacy-state">没有匹配的实验范围。</div> : null}
          {!loadingOptions && filteredExperiments.length ? (
            <div className="legacy-assessment-option-list" aria-label="可选实验范围">
              {filteredExperiments.map((option) => {
                const disabled = option.question_count <= 0 || customDisabled;
                const selected = selectedIds.has(option.id);
                return (
                  <button
                    key={option.id}
                    type="button"
                    className={selected ? "selected" : ""}
                    disabled={disabled}
                    aria-pressed={selected}
                    onClick={() => toggleExperiment(option)}
                  >
                    <span className="legacy-checkbox" aria-hidden="true">
                      {selected ? "✓" : ""}
                    </span>
                    <span className="legacy-assessment-option-copy">
                      <strong>{option.title}</strong>
                      <small>{option.parent_title || option.code}</small>
                    </span>
                    <em>{option.question_count} 道可用题</em>
                  </button>
                );
              })}
            </div>
          ) : null}

          <button className="primary-button legacy-assessment-start" type="button" disabled={starting || !canStartCustom} onClick={start}>
            {starting ? "正在组卷..." : "开始测评"}
          </button>
        </section>
      </section>
    );
  }

  return (
    <section className="legacy-page legacy-assessment-page">
      <div className="legacy-section-head">
        <span className="eyebrow">BKT 实验测评</span>
        <h1>按掌握度与范围出题</h1>
        <p>学生可选择智能薄弱项测试，也可按实验范围自选、随机或全选组卷；测评结果将回写掌握度，形成视频学习、测评巩固和学情反馈闭环。</p>
      </div>

      <section className="legacy-assessment-setup" aria-label="测评设置">
        <AssessmentQuestionCountSelector countOptions={countOptions} questionCount={questionCount} onChange={setQuestionCount} />

        <div className="legacy-assessment-mode-grid" aria-label="出题方式">
          {assessmentSetupModes.map((item) => (
            <button key={item.id} type="button" className={mode === item.id ? "active" : ""} onClick={() => chooseMode(item.id)}>
              <strong>{item.label}</strong>
              <small>{item.summary}</small>
            </button>
          ))}
        </div>

        {optionError ? <div className="legacy-error">实验范围暂时无法加载；仍可使用智能薄弱项测试。</div> : null}
        {error ? <div className="legacy-error">{error}</div> : null}
        {loadingOptions && mode !== "smart" ? <div className="legacy-state compact">正在读取可用题库...</div> : null}

        {mode === "selected" ? (
          <button className="primary-button legacy-assessment-start" type="button" onClick={() => setSelectingRange(true)}>
            {selectedCount ? "继续选择实验范围" : "进入选择实验范围"}
          </button>
        ) : (
          <button className="primary-button legacy-assessment-start" type="button" disabled={starting || (mode !== "smart" && !canStartCustom)} onClick={start}>
            {starting ? "正在组卷..." : "开始测评"}
          </button>
        )}
      </section>
    </section>
  );
}

function AssessmentSessionPage({ sessionId }: { sessionId: string }) {
  const [assessment] = useState<SmartAssessmentResponse | null>(() => readLegacyAssessmentSession(sessionId));
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<SmartAssessmentReport | null>(null);
  const [resultReportId, setResultReportId] = useState<string | null>(null);

  if (!assessment) {
    return (
      <section className="legacy-page legacy-assessment-page">
        <button className="text-button" onClick={() => navigate("/assessment")}>
          返回测评
        </button>
        <div className="legacy-state">本轮测评信息已失效，请返回测评主页重新开始。</div>
      </section>
    );
  }

  if (report) return <AssessmentResultPage report={report} reportId={resultReportId} />;

  const questions = assessment.questions || [];
  const allAnswered = questions.length > 0 && questions.every((question) => isAnswered(answers[question.id]));
  const answeredCount = questions.filter((question) => isAnswered(answers[question.id])).length;
  const modeLabel = assessmentModeLabel(assessment.assessment_mode);
  const targetCount = assessment.composition?.requested_question_count || assessment.composition?.target_question_count || assessment.composition?.total_questions || questions.length;
  const actualCount = questions.length || assessment.composition?.total_questions || 0;
  const underfilled = Boolean(assessment.composition?.warnings?.underfilled) || (targetCount > 0 && actualCount > 0 && actualCount < targetCount);

  const submit = async () => {
    if (!allAnswered) {
      setError("请完成全部题目后再提交。");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const response = await submitSmartAssessment(
        assessment.session_id,
        Object.entries(answers).map(([questionId, answer]) => ({ question_id: questionId, answer })),
      );
      storeLegacyAssessmentReport(response.report);
      setResultReportId(response.assessment_report?.id || null);
      setReport(response.report);
    } catch (caught) {
      setError(legacyStudentErrorMessage(caught));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="legacy-page legacy-assessment-page legacy-assessment-session-page">
      <div className="legacy-exam-topbar">
        <strong>{modeLabel}</strong>
        <button className="text-button" onClick={() => navigate("/assessment")}>
          返回评测
        </button>
      </div>
      <article className="legacy-exam-paper" aria-label="旧版实验测评试卷">
        <header className="legacy-exam-head">
          <div>
            <h1>{assessmentSessionTitle(assessment)}</h1>
            <p>{assessmentExperimentNames(assessment) || "按本轮测评策略生成实验题目。"}</p>
          </div>
        </header>

        <div className="legacy-meta-row legacy-exam-meta">
          <span>共 {actualCount} 题</span>
          <span className={allAnswered ? "is-complete" : undefined}>已完成 {answeredCount} 题</span>
        </div>
        {underfilled ? <div className="legacy-state compact">题库可用题量不足，系统已按当前题库生成 {actualCount} 题。</div> : null}
        {error ? <div className="legacy-error">{error}</div> : null}

        <div className="legacy-question-list">
          {questions.map((question, index) => (
            <AssessmentQuestionCard
              key={question.id}
              question={question}
              index={index}
              answer={answers[question.id] || ""}
              onAnswer={(answer) => setAnswers((current) => ({ ...current, [question.id]: answer }))}
            />
          ))}
        </div>
        {!questions.length ? <div className="legacy-state">本轮测评暂无可答题目，请返回后重新开始。</div> : null}
        <button className="primary-button legacy-assessment-start" type="button" disabled={!allAnswered || submitting} onClick={submit}>
          {submitting ? "正在提交..." : allAnswered ? "提交答案" : "请完成全部题目"}
        </button>
      </article>
    </section>
  );
}

function AssessmentQuestionCard({
  question,
  index,
  answer,
  onAnswer,
}: {
  question: PublicSmartAssessmentQuestion;
  index: number;
  answer: string;
  onAnswer: (answer: string) => void;
}) {
  return (
    <article className="legacy-question-card">
      <div className="legacy-question-head">
        <span>第 {index + 1} 题</span>
        <em>{questionTypeLabel(question.question_type)}</em>
      </div>
      <h2>{question.stem}</h2>
      {question.question_type === "fill_blank" ? (
        <input className="legacy-fill-answer" value={answer} onChange={(event) => onAnswer(event.target.value)} placeholder="请输入答案" />
      ) : (
        <div className="legacy-option-list">
          {assessmentOptions(question).map((option) => (
            <button key={`${question.id}-${option.value}`} type="button" className={answer === option.value ? "selected" : ""} aria-pressed={answer === option.value} onClick={() => onAnswer(option.value)}>
              <b>{option.marker}</b>
              <span>{option.text}</span>
            </button>
          ))}
        </div>
      )}
    </article>
  );
}

function AssessmentResultPage({ report, reportId }: { report: SmartAssessmentReport; reportId: string | null }) {
  return (
    <section className="legacy-page legacy-assessment-page">
      <article className="legacy-detail-card">
        <span className="eyebrow">测评结果</span>
        <h1>{assessmentModeLabel(report.assessment_mode)}完成</h1>
        <div className="legacy-metrics">
          <Metric label="得分" value={Number(report.score || 0).toFixed(1)} />
          <Metric label="答对" value={`${report.correct_count}/${report.total_count}`} />
          <Metric label="正确率" value={`${Math.round((report.correct_rate || 0) * 100)}%`} />
        </div>
        <p>{report.next_recommendation || "请根据错题和掌握度变化继续复盘薄弱实验点。"}</p>
        {report.wrong_answers?.length ? <div className="legacy-error">本次共有 {report.wrong_answers.length} 道题需要复盘。</div> : null}
        <div className="legacy-result-actions">
          <button className="secondary-button legacy-assessment-start" type="button" onClick={() => navigate("/assessment")}>
            返回测评
          </button>
          <button className="primary-button legacy-assessment-start" type="button" onClick={() => navigate(reportId ? `/reports/${encodeURIComponent(reportId)}` : "/reports")}>
            查看报告
          </button>
        </div>
      </article>
    </section>
  );
}

function assessmentOptionSearchText(option: CustomAssessmentExperimentOption): string {
  return [option.title, option.parent_title, option.parent_code, option.code].filter(Boolean).join(" ").toLowerCase();
}

function randomExperimentIds(options: CustomAssessmentExperimentOption[], questionCount: number, maxQuestionsPerExperiment: number): string[] {
  const eligible = options.filter((item) => item.question_count > 0);
  if (!eligible.length) return [];
  const targetExperimentCount = Math.max(1, Math.ceil(questionCount / Math.max(1, maxQuestionsPerExperiment)));
  return eligible
    .map((item) => ({ item, sort: Math.random() }))
    .sort((left, right) => left.sort - right.sort)
    .slice(0, Math.min(targetExperimentCount, eligible.length))
    .map(({ item }) => item.id);
}

function isAnswered(value?: string): boolean {
  return Boolean(String(value || "").trim());
}

function assessmentModeLabel(mode?: string): string {
  if (mode === "custom") return "自选范围测评";
  if (mode === "point") return "学后点位测评";
  return "智能薄弱项测试";
}

function assessmentSessionTitle(assessment: SmartAssessmentResponse): string {
  if (assessment.assessment_mode === "custom") return "请完成本轮自选实验测评";
  if (assessment.assessment_mode === "point") return "请完成本轮学后测评";
  return "请完成本轮智能组卷";
}

function assessmentExperimentNames(assessment: SmartAssessmentResponse): string {
  const names = (assessment.experiments || []).slice(0, 3).map((item) => item.title).filter(Boolean);
  if (!names.length) return "";
  const suffix = (assessment.experiments || []).length > names.length ? ` 等 ${(assessment.experiments || []).length} 个实验` : "";
  return `${names.join("、")}${suffix}`;
}

function questionTypeLabel(type: string): string {
  if (type === "true_false") return "判断题";
  if (type === "fill_blank") return "填空题";
  return "单项选择题";
}

function optionValue(option: Record<string, unknown>, index: number): string {
  const raw = option.label ?? option.key ?? option.value ?? String.fromCharCode(65 + index);
  return String(raw);
}

function optionText(option: Record<string, unknown>, index: number): string {
  const fallback = optionValue(option, index);
  return String(option.text ?? fallback);
}

function assessmentOptions(question: PublicSmartAssessmentQuestion): Array<{ value: string; marker: string; text: string }> {
  if (question.question_type === "true_false") {
    return [
      { value: "true", marker: "对", text: "正确" },
      { value: "false", marker: "错", text: "错误" },
    ];
  }
  return (question.options || []).map((option, index) => {
    const value = optionValue(option, index);
    return { value, marker: value, text: optionText(option, index) };
  });
}

function ReportsPage({ user }: { user: AuthUser }) {
  const [reports, setReports] = useState<AssessmentReportSummary[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    loadLegacyAssessmentReports()
      .then((value) => {
        if (active) setReports(value.reports || []);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const average = useMemo(() => {
    if (!reports.length) return 0;
    return reports.reduce((sum, item) => sum + Number(item.score || 0), 0) / reports.length;
  }, [reports]);
  const wrongTotal = useMemo(() => reports.reduce((sum, item) => sum + Number(item.wrong_count || 0), 0), [reports]);
  const studentId = user.student_id || user.username || "未登记学号";
  const className = user.class_name || user.class_id || "未分班";

  return (
    <section className="legacy-page">
      <section className="legacy-profile-info-card" aria-label="学生信息">
        <dl>
          <div>
            <dt>学号</dt>
            <dd>{studentId}</dd>
          </div>
          <div>
            <dt>姓名</dt>
            <dd>{user.display_name || user.username}</dd>
          </div>
          <div>
            <dt>班级</dt>
            <dd>{className}</dd>
          </div>
        </dl>
      </section>

      <div className="legacy-section-head">
        <span className="eyebrow">学习报告</span>
        <h1>报告</h1>
        <p>每次测评完成后生成一份学习报告，查看本轮得分、AI 学情总结和错题解析，继续复盘薄弱实验点。</p>
      </div>
      {loading ? <div className="legacy-state">正在载入报告...</div> : null}
      {error ? <div className="legacy-error">{error}</div> : null}
      <div className="legacy-metrics">
        <Metric label="报告数" value={reports.length} />
        <Metric label="平均分" value={average.toFixed(1)} />
        <Metric label="待复盘错题" value={wrongTotal} />
      </div>
      <div className="legacy-report-list">
        {reports.map((report) => (
          <button className="legacy-report-card" key={report.id} type="button" onClick={() => navigate(`/reports/${encodeURIComponent(report.id)}`)}>
            <strong>{report.title}</strong>
            <span>{formatReportDate(report.completed_at)}</span>
            <p>
              得分 {formatScore(report.score)}，答对 {report.correct_count}/{report.total_count}，错题 {report.wrong_count || 0} 道。
            </p>
            <em>查看报告</em>
          </button>
        ))}
        {!loading && !reports.length ? <div className="legacy-state">暂无测评报告。</div> : null}
      </div>
    </section>
  );
}

function ReportDetailPage({ reportId }: { reportId: string }) {
  const [report, setReport] = useState<LegacyAssessmentReportDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    loadLegacyAssessmentReport(reportId)
      .then((value) => {
        if (active) setReport(value);
      })
      .catch((caught) => {
        if (active) setError(legacyStudentErrorMessage(caught));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reportId]);

  const mistakeExplanationText = report?.mistake_explanation?.text?.trim() || "";
  const hasAiMistakeExplanation = report?.mistake_explanation?.source === "ai" && mistakeExplanationText.length > 0;

  return (
    <section className="legacy-page legacy-report-detail-page">
      <div className="legacy-exam-topbar">
        <strong>学习报告</strong>
        <button className="text-button" onClick={() => navigate("/reports")}>
          返回报告
        </button>
      </div>

      {loading ? <div className="legacy-state">正在载入报告...</div> : null}
      {error ? <div className="legacy-error">{error}</div> : null}
      {!loading && !error && !report ? <div className="legacy-state">没有找到这份报告。</div> : null}

      {report ? (
        <>
          <article className="legacy-report-detail-head">
            <span className="eyebrow">{reportTypeLabel(report.report_type)}</span>
            <h1>{report.title}</h1>
            <p>{formatReportDate(report.completed_at)}</p>
            <div className="legacy-metrics">
              <Metric label="得分" value={formatScore(report.score)} />
              <Metric label="答对" value={`${report.correct_count}/${report.total_count}`} />
              <Metric label="错题" value={report.wrong_count || report.wrong_questions.length} />
            </div>
          </article>

          <section className="legacy-ai-summary">
            <h2>AI 学情总结</h2>
            <p>{report.ai_summary?.text || "本次报告暂无总结，请继续完成测评以获得学习反馈。"}</p>
            {report.next_steps ? <p className="legacy-report-next">{report.next_steps}</p> : null}
          </section>

          <section className="legacy-wrong-section">
            <h2>错题解析</h2>
            {mistakeExplanationText ? (
              <section className="legacy-answer-explanation legacy-ai-mistake-overview">
                <h4>AI 错题解析</h4>
                <p>{mistakeExplanationText}</p>
              </section>
            ) : null}
            {report.wrong_questions.length ? (
              <div className="legacy-wrong-list">
                {report.wrong_questions.map((question, index) => (
                  <article className="legacy-wrong-question" key={`${question.question_id || "question"}-${index}`}>
                    <div className="legacy-question-head">
                      <span>第 {index + 1} 题</span>
                      {question.experiment_title ? <em>{question.experiment_title}</em> : null}
                    </div>
                    <h3>{question.stem}</h3>
                    {question.options?.length ? (
                      <ul className="legacy-report-options">
                        {question.options.map((option) => (
                          <li key={option}>{option}</li>
                        ))}
                      </ul>
                    ) : null}
                    {!hasAiMistakeExplanation ? (
                      <>
                        <div className="legacy-answer-grid">
                          <div>
                            <span>你的答案</span>
                            <strong>{question.submitted_answer}</strong>
                          </div>
                          <div>
                            <span>参考答案</span>
                            <strong>{question.correct_answer}</strong>
                          </div>
                        </div>
                        <section className="legacy-answer-explanation">
                          <h4>解析</h4>
                          <p>{question.explanation}</p>
                        </section>
                      </>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="legacy-state">本次没有错题。</div>
            )}
          </section>
        </>
      ) : null}
    </section>
  );
}

function reportTypeLabel(type?: string): string {
  if (type === "custom") return "自选范围测评";
  if (type === "point") return "学后测评";
  if (type === "pretest") return "课前测评";
  if (type === "posttest") return "课后测评";
  return "智能薄弱项测试";
}

function formatReportDate(value?: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="legacy-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatScore(value?: number | null): string {
  if (value === null || value === undefined) return "50.0";
  return Number(value).toFixed(1);
}
