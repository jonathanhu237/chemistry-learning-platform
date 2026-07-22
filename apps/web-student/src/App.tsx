import { useCallback, useEffect, useMemo, useState } from "react";
import { LoaderCircle } from "lucide-react";
import logoUrl from "./assets/sysu-logo.svg";
import { StudentPreviewRouterProvider, StudentRouterProvider } from "./app/router/StudentRouterProvider";
import { storePreviewInputHandshake } from "./app/preview/input/previewInputProtocol";
import type { ViewState } from "./app/router/routeTypes";
import { LoginPanel } from "./features/auth/LoginPanel";
import { PasswordPanel } from "./features/auth/PasswordPanel";
import { isStudent } from "./features/auth/authUtils";
import { StudentBaselineGate } from "./features/assessment/StudentBaselineGate";
import {
  AuthUser,
  LoginResponse,
  clearPreviewAuthToken,
  errorMessage,
  exchangeStudentPreviewTicket,
  getAuthToken,
  isPreviewAuthSession,
  loadCurrentUser,
  logout,
  setPreviewAuthToken,
  setAuthToken,
} from "./api";

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [previewRuntime, setPreviewRuntime] = useState(() => isPreviewAuthSession());
  const [baselineReady, setBaselineReady] = useState(false);
  const previewCatalogRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/preview/catalog/");
  const previewSessionRoute = typeof window !== "undefined" && window.location.pathname.startsWith("/preview/session");

  useEffect(() => {
    if (!previewSessionRoute) return;
    const ticket = new URLSearchParams(window.location.search).get("ticket") || "";
    const frameId = new URLSearchParams(window.location.search).get("previewFrameId") || "";
    const teacherOrigin = new URLSearchParams(window.location.search).get("previewTeacherOrigin") || "";
    if (!ticket) {
      setSessionError("Preview ticket is missing.");
      setChecking(false);
      return;
    }
    storePreviewInputHandshake(frameId, teacherOrigin);
    let cancelled = false;
    setChecking(true);
    exchangeStudentPreviewTicket(ticket)
      .then((response) => {
        if (cancelled) return;
        if (!isStudent(response)) {
          setSessionError("Preview session did not return a student account.");
          setChecking(false);
          return;
        }
        setSessionError("");
        setPreviewAuthToken(response.access_token);
        setPreviewRuntime(true);
        setUser(response.user);
        setBaselineReady(true);
        window.history.replaceState({}, "", "/home");
      })
      .catch((requestError) => {
        if (!cancelled) {
          clearPreviewAuthToken();
          setPreviewRuntime(false);
          setSessionError(errorMessage(requestError));
        }
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, [previewSessionRoute]);

  useEffect(() => {
    if (previewCatalogRoute) {
      setChecking(false);
      return;
    }
    if (previewSessionRoute) {
      return;
    }
    if ((previewRuntime || isPreviewAuthSession()) && user) {
      setChecking(false);
      return;
    }
    if (user) {
      setChecking(false);
      return;
    }
    if (!getAuthToken()) {
      setPreviewRuntime(false);
      setChecking(false);
      return;
    }
    loadCurrentUser()
      .then((currentUser) => {
        if (currentUser.role !== "student") {
          setAuthToken("");
          setSessionError("请使用学生账号登录");
          return;
        }
        setPreviewRuntime(Boolean(currentUser.preview_mode));
        setBaselineReady(Boolean(currentUser.preview_mode));
        setUser(currentUser);
      })
      .catch(() => {
        setAuthToken("");
        setPreviewRuntime(false);
      })
      .finally(() => setChecking(false));
  }, [previewCatalogRoute, previewRuntime, previewSessionRoute, user]);

  const view: ViewState = useMemo(() => {
    if (checking) return "checking";
    if (!user) return "login";
    if (user.must_change_password) return "password";
    if (previewRuntime || user.preview_mode) return "home";
    return baselineReady ? "home" : "baseline";
  }, [baselineReady, checking, previewRuntime, user]);

  const acceptLogin = (response: LoginResponse) => {
    if (!isStudent(response)) {
      setAuthToken("");
      setSessionError("请使用学生账号登录");
      return;
    }
    setSessionError("");
    setPreviewRuntime(false);
    setBaselineReady(false);
    setAuthToken(response.access_token);
    setUser(response.user);
  };

  const handleLogout = useCallback(async () => {
    await logout();
    setBaselineReady(false);
    setPreviewRuntime(false);
    setUser(null);
  }, []);

  const handleBaselineReady = useCallback(() => setBaselineReady(true), []);

  if (previewCatalogRoute) {
    return (
      <main className="app-shell learning-shell preview-shell">
        <StudentPreviewRouterProvider />
      </main>
    );
  }

  if (previewSessionRoute && (checking || sessionError)) {
    return (
      <main className="app-shell">
        {sessionError ? <PreviewSessionErrorPanel message={sessionError} /> : <LoadingPanel text="Loading preview session..." />}
      </main>
    );
  }

  return (
    <main className={view === "baseline" ? "app-shell assessment-shell" : view === "home" ? "app-shell learning-shell" : "app-shell"}>
      {view === "home" ? null : (
        <section className="brand-rail" aria-label="中山大学化学学院">
          <div className="brand-seal">
            <img src={logoUrl} alt="中山大学校徽" />
          </div>
          <div>
            <p>中山大学化学学院</p>
            <h1>元素实验</h1>
          </div>
        </section>
      )}

      {view === "checking" ? <LoadingPanel text="正在恢复登录状态" /> : null}
      {view === "login" ? <LoginPanel sessionError={sessionError} onLogin={acceptLogin} /> : null}
      {view === "password" && user ? <PasswordPanel user={user} onChanged={acceptLogin} /> : null}
      {view === "baseline" ? <StudentBaselineGate onReady={handleBaselineReady} onLogout={handleLogout} /> : null}
      {view === "home" && user ? <StudentRouterProvider user={user} onLogout={handleLogout} /> : null}
    </main>
  );
}

function LoadingPanel({ text }: { text: string }) {
  return (
    <section className="auth-panel compact-panel" aria-live="polite">
      <LoaderCircle className="spin" size={24} />
      <p>{text}</p>
    </section>
  );
}

function PreviewSessionErrorPanel({ message }: { message: string }) {
  return (
    <section className="auth-panel compact-panel" aria-live="polite">
      <p>{message}</p>
    </section>
  );
}

export default App;
