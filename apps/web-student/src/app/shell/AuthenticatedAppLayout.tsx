import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Outlet, useLocation, useNavigate } from "@tanstack/react-router";
import { LockKeyhole, Search } from "lucide-react";
import { assistantEnabled, defaultStudentAppConfig, feedbackEnabled, previewRouteBlocked } from "../appConfig";
import { errorMessage, getStudentAppConfig, startStudentSmartAssessment, type StudentAppConfigResponse } from "../../api";
import { storePosttestSession } from "../router/assessmentSessionStore";
import { navigateToVideoLibrary } from "../router/navigation";
import { rootIdForPath, routeRoleForPath } from "../router/routeVisibility";
import type { StudentRootRouteId } from "../router/routeTypes";
import { StudentRuntimeProvider, useStudentShellBase } from "./studentAppContext";
import { StudentAppHeader } from "./StudentAppHeader";
import { StudentBottomNav } from "./StudentBottomNav";
import { PreviewInputRuntime } from "../preview/input/PreviewInputRuntime";
import { MobileEmptyState } from "../../mobile/primitives";
import { debugAtomKeyboardSnapshot, installStudentMobileDebugConsole } from "../../debug/mobileDebug";
import sysuLogoNameGreenUrl from "../../assets/sysu-logo/sysu-logo-name-green.svg";

const rootHeaderMeta: Record<StudentRootRouteId, { title: string; subtitle: string }> = {
  home: { title: "首页", subtitle: "今日学习" },
  learn: { title: "学习", subtitle: "章节与元素周期表" },
  ai: { title: "Atom", subtitle: "学习助手中心" },
  assessment: { title: "测评", subtitle: "练习与学习报告" },
  profile: { title: "我的", subtitle: "账号与反馈" },
};

const homeVideoTopics = ["推荐", "全部", "最新", "颜色变化", "沉淀", "气体", "分层", "褪色", "火焰", "放热", "卤素", "酸碱", "氧化还原"];

const ROOT_AI_COMPOSER_SELECTOR = ".ai-chat-panel.root .ai-chat-compose";

function getVisualViewportHeight() {
  if (typeof window === "undefined") return 0;
  return Math.round(window.visualViewport?.height || window.innerHeight || document.documentElement.clientHeight || 0);
}

function getVisualViewportTop() {
  if (typeof window === "undefined") return 0;
  return Math.round(window.visualViewport?.offsetTop || 0);
}

function getKeyboardBottomInset(viewportHeight: number, viewportTop = 0) {
  if (typeof window === "undefined" || !window.visualViewport) return 0;
  const layoutHeight = Math.round(window.innerHeight || document.documentElement.clientHeight || viewportHeight);
  return Math.max(0, Math.round(layoutHeight - viewportHeight - viewportTop));
}

function isRootAiComposerTarget(target: EventTarget | null) {
  return typeof HTMLElement !== "undefined" && target instanceof HTMLElement && Boolean(target.closest(ROOT_AI_COMPOSER_SELECTOR));
}

export function AuthenticatedAppLayout() {
  const navigate = useNavigate();
  const baseContext = useStudentShellBase();
  const location = useLocation();
  const activeRoot = rootIdForPath(location.pathname);
  const routeRole = routeRoleForPath(location.pathname);
  const isRootRoute = routeRole === "root";
  const isCatalogDetailRoute = /^\/chapter\/[^/]+$/.test(location.pathname) || /^\/catalog\/[^/]+$/.test(location.pathname);
  const [appConfig, setAppConfig] = useState<StudentAppConfigResponse>(defaultStudentAppConfig);
  const [configError, setConfigError] = useState("");
  const [posttestLoading, setPosttestLoading] = useState(false);
  const [posttestError, setPosttestError] = useState("");
  const [navCompressed, setNavCompressed] = useState(false);
  const [homeVideoTopic, setHomeVideoTopic] = useState(homeVideoTopics[0]);
  const [rootComposerFocused, setRootComposerFocused] = useState(false);
  const [visualViewportHeight, setVisualViewportHeight] = useState(getVisualViewportHeight);
  const [visualViewportTop, setVisualViewportTop] = useState(getVisualViewportTop);
  const [keyboardBottomInset, setKeyboardBottomInset] = useState(() => getKeyboardBottomInset(getVisualViewportHeight(), getVisualViewportTop()));
  const lastScrollY = useRef(0);
  const focusDebugTimers = useRef<number[]>([]);
  const maxVisualViewportHeight = useRef(0);
  const rootKeyboardCompressed = useRef(false);
  const routeBlocked = previewRouteBlocked(appConfig, location.pathname);
  const previewMode = Boolean(baseContext.user.preview_mode || appConfig.preview_mode);
  const isRootAiRoute = isRootRoute && activeRoot === "ai";
  const keyboardActive = isRootAiRoute && rootComposerFocused;

  useEffect(() => {
    let cancelled = false;
    void installStudentMobileDebugConsole();
    const refreshConfig = async () => {
      try {
        const response = await getStudentAppConfig();
        if (!cancelled) {
          setAppConfig(response);
          setConfigError("");
        }
      } catch (requestError) {
        if (!cancelled) setConfigError(errorMessage(requestError));
      }
    };
    void refreshConfig();
    const handleVisible = () => {
      if (document.visibilityState !== "hidden") void refreshConfig();
    };
    window.addEventListener("focus", handleVisible);
    document.addEventListener("visibilitychange", handleVisible);
    const timer = window.setInterval(refreshConfig, 60_000);
    return () => {
      cancelled = true;
      window.removeEventListener("focus", handleVisible);
      document.removeEventListener("visibilitychange", handleVisible);
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    setNavCompressed(false);
    lastScrollY.current = window.scrollY;
    if (!isRootRoute) return;

    const handleScroll = () => {
      const nextScrollY = window.scrollY;
      const delta = nextScrollY - lastScrollY.current;
      if (nextScrollY < 64 || delta < -14) {
        setNavCompressed(false);
      } else if (delta > 18 && nextScrollY > 128) {
        setNavCompressed(true);
      }
      lastScrollY.current = nextScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, [isRootRoute, location.pathname]);

  useEffect(() => {
    rootKeyboardCompressed.current = false;
    setRootComposerFocused(false);
    debugAtomKeyboardSnapshot("route-change", { pathname: location.pathname, isRootAiRoute });
  }, [location.pathname]);

  useEffect(() => {
    const updateVisualViewport = () => {
      const nextHeight = getVisualViewportHeight();
      const nextTop = getVisualViewportTop();
      const nextBottomInset = getKeyboardBottomInset(nextHeight, nextTop);
      setVisualViewportHeight(nextHeight);
      setVisualViewportTop(nextTop);
      setKeyboardBottomInset(nextBottomInset);
      debugAtomKeyboardSnapshot("visual-viewport-update", {
        nextHeight,
        nextTop,
        nextBottomInset,
        isRootAiRoute,
        rootComposerFocused,
      });
      if (!nextHeight) return;

      maxVisualViewportHeight.current = Math.max(maxVisualViewportHeight.current, nextHeight);
      const restoredGap = maxVisualViewportHeight.current - nextHeight;
      if (isRootAiRoute && rootComposerFocused && window.visualViewport) {
        if (restoredGap > 80) rootKeyboardCompressed.current = true;
        if (rootKeyboardCompressed.current && restoredGap <= 24) {
          rootKeyboardCompressed.current = false;
          setRootComposerFocused(false);
        }
      }
    };

    updateVisualViewport();
    window.addEventListener("resize", updateVisualViewport);
    window.visualViewport?.addEventListener("resize", updateVisualViewport);
    window.visualViewport?.addEventListener("scroll", updateVisualViewport);
    return () => {
      window.removeEventListener("resize", updateVisualViewport);
      window.visualViewport?.removeEventListener("resize", updateVisualViewport);
      window.visualViewport?.removeEventListener("scroll", updateVisualViewport);
    };
  }, [isRootAiRoute, rootComposerFocused]);

  useEffect(() => {
    if (!isRootAiRoute) {
      setRootComposerFocused(false);
      return;
    }

    const clearFocusDebugTimers = () => {
      focusDebugTimers.current.forEach((timer) => window.clearTimeout(timer));
      focusDebugTimers.current = [];
    };
    let blurFrame = 0;
    const handleFocusIn = (event: FocusEvent) => {
      if (isRootAiComposerTarget(event.target)) {
        rootKeyboardCompressed.current = false;
        setRootComposerFocused(true);
        debugAtomKeyboardSnapshot("root-composer-focusin", { eventTarget: event.target instanceof HTMLElement ? event.target.tagName : "" });
        clearFocusDebugTimers();
        focusDebugTimers.current = [250, 600, 1000].map((delay) =>
          window.setTimeout(() => debugAtomKeyboardSnapshot(`root-composer-focusin+${delay}ms`), delay),
        );
      }
    };
    const handleFocusOut = () => {
      window.cancelAnimationFrame(blurFrame);
      blurFrame = window.requestAnimationFrame(() => {
        const stillInComposer = isRootAiComposerTarget(document.activeElement);
        rootKeyboardCompressed.current = stillInComposer ? rootKeyboardCompressed.current : false;
        setRootComposerFocused(stillInComposer);
        debugAtomKeyboardSnapshot("root-composer-focusout", { stillInComposer });
      });
    };

    document.addEventListener("focusin", handleFocusIn);
    document.addEventListener("focusout", handleFocusOut);
    return () => {
      clearFocusDebugTimers();
      window.cancelAnimationFrame(blurFrame);
      document.removeEventListener("focusin", handleFocusIn);
      document.removeEventListener("focusout", handleFocusOut);
    };
  }, [isRootAiRoute]);

  useEffect(() => {
    debugAtomKeyboardSnapshot("keyboard-active-change", {
      keyboardActive,
      visualViewportHeight,
      visualViewportTop,
      keyboardBottomInset,
    });
  }, [keyboardActive, keyboardBottomInset, visualViewportHeight, visualViewportTop]);

  const startAssessmentSession = useCallback(async () => {
    setPosttestLoading(true);
    setPosttestError("");
    try {
      const response = await startStudentSmartAssessment();
      storePosttestSession(response);
      return response;
    } catch (requestError) {
      setPosttestError(errorMessage(requestError));
      return null;
    } finally {
      setPosttestLoading(false);
    }
  }, []);

  const runtime = useMemo(
    () => ({
      ...baseContext,
      appConfig,
      configError,
      previewMode,
      previewPolicy: appConfig.preview_policy,
      canUseAssistant: assistantEnabled(appConfig.features),
      canUseFeedback: feedbackEnabled(appConfig.features),
      startAssessmentSession,
      posttestLoading,
      posttestError,
    }),
    [appConfig, baseContext, configError, posttestError, posttestLoading, previewMode, startAssessmentSession],
  );

  const headerMeta = activeRoot ? rootHeaderMeta[activeRoot] : null;
  const shouldRenderHeader = Boolean(headerMeta && !(isRootRoute && activeRoot === "ai"));
  const shellStyle = useMemo(
    () =>
      ({
        "--student-visual-viewport-height": visualViewportHeight ? `${visualViewportHeight}px` : "100dvh",
        "--student-visual-viewport-top": `${visualViewportTop}px`,
        "--student-keyboard-bottom-inset": `${keyboardBottomInset}px`,
        "--student-keyboard-welcome-offset": `${Math.round(Math.max(44, Math.min(96, visualViewportHeight * 0.16 || 64)))}px`,
      }) as CSSProperties,
    [keyboardBottomInset, visualViewportHeight, visualViewportTop],
  );

  return (
    <StudentRuntimeProvider value={runtime}>
      <section
        className={[
          "student-app-shell",
          isRootRoute ? "root-route" : "detail-route",
          isCatalogDetailRoute ? "catalog-detail-route" : "",
          activeRoot ? `root-${activeRoot}` : "",
          navCompressed && isRootRoute ? "nav-compressed" : "",
          keyboardActive ? "keyboard-active" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={shellStyle}
        aria-label="学生学习应用"
      >
        {shouldRenderHeader && headerMeta ? (
          activeRoot === "home" ? (
            <StudentAppHeader
              ariaLabel="学生端首页"
              brand={<img className="student-app-header-logo" src={sysuLogoNameGreenUrl} alt="中山大学" />}
              actions={
                <button
                  className="student-app-header-icon-action"
                  type="button"
                  aria-label="搜索实验视频"
                  onClick={() => navigateToVideoLibrary(navigate, { from: "home" })}
                >
                  <Search size={29} />
                </button>
              }
              below={
                <div className="home-video-topic-rail" aria-label="实验视频推荐标签">
                  {homeVideoTopics.map((topic) => (
                    <button
                      type="button"
                      key={topic}
                      className={topic === homeVideoTopic ? "active" : ""}
                      aria-pressed={topic === homeVideoTopic}
                      onClick={() => setHomeVideoTopic(topic)}
                    >
                      {topic}
                    </button>
                  ))}
                </div>
              }
            />
          ) : (
            <StudentAppHeader title={headerMeta.title} subtitle={headerMeta.subtitle} />
          )
        ) : null}
        {configError ? <div className="form-hint app-config-hint">配置刷新失败，当前页面会继续使用上一次配置：{configError}</div> : null}
        <div className="student-route-content">
          {routeBlocked ? (
            <section className="learning-panel">
              <MobileEmptyState className="empty-learning-card" icon={<LockKeyhole size={20} />}>
                <span>{appConfig.preview_policy?.message || "This feature is unavailable in teacher preview mode."}</span>
              </MobileEmptyState>
            </section>
          ) : (
            <Outlet />
          )}
        </div>
        {activeRoot ? <StudentBottomNav activeRoot={activeRoot} /> : null}
        <PreviewInputRuntime />
      </section>
    </StudentRuntimeProvider>
  );
}
