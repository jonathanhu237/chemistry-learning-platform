import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Outlet, useLocation } from "@tanstack/react-router";
import { LockKeyhole } from "lucide-react";
import { assistantEnabled, defaultStudentAppConfig, feedbackEnabled, previewRouteBlocked } from "../appConfig";
import { errorMessage, getStudentAppConfig, startStudentPosttest, type StudentAppConfigResponse } from "../../api";
import { storePosttestSession } from "../router/assessmentSessionStore";
import { rootIdForPath, routeRoleForPath } from "../router/routeVisibility";
import type { StudentRootRouteId } from "../router/routeTypes";
import { StudentRuntimeProvider, useStudentShellBase } from "./studentAppContext";
import { StudentAppHeader } from "./StudentAppHeader";
import { StudentBottomNav } from "./StudentBottomNav";
import { PreviewInputRuntime } from "../preview/input/PreviewInputRuntime";
import { MobileEmptyState } from "../../mobile/primitives";

const rootHeaderMeta: Record<StudentRootRouteId, { title: string; subtitle: string }> = {
  home: { title: "首页", subtitle: "今日学习" },
  learn: { title: "学习", subtitle: "章节与元素周期表" },
  ai: { title: "AI", subtitle: "学习助手中心" },
  assessment: { title: "测评", subtitle: "练习与学习报告" },
  profile: { title: "我的", subtitle: "账号与反馈" },
};

export function AuthenticatedAppLayout() {
  const baseContext = useStudentShellBase();
  const location = useLocation();
  const activeRoot = rootIdForPath(location.pathname);
  const routeRole = routeRoleForPath(location.pathname);
  const isRootRoute = routeRole === "root";
  const [appConfig, setAppConfig] = useState<StudentAppConfigResponse>(defaultStudentAppConfig);
  const [configError, setConfigError] = useState("");
  const [posttestLoading, setPosttestLoading] = useState(false);
  const [posttestError, setPosttestError] = useState("");
  const [navCompressed, setNavCompressed] = useState(false);
  const lastScrollY = useRef(0);
  const routeBlocked = previewRouteBlocked(appConfig, location.pathname);
  const previewMode = Boolean(baseContext.user.preview_mode || appConfig.preview_mode);

  useEffect(() => {
    let cancelled = false;
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

  const startAssessmentSession = useCallback(async () => {
    setPosttestLoading(true);
    setPosttestError("");
    try {
      const response = await startStudentPosttest();
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

  return (
    <StudentRuntimeProvider value={runtime}>
      <section
        className={[
          "student-app-shell",
          isRootRoute ? "root-route" : "detail-route",
          navCompressed && isRootRoute ? "nav-compressed" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="学生学习应用"
      >
        {headerMeta ? <StudentAppHeader title={headerMeta.title} subtitle={headerMeta.subtitle} /> : null}
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
