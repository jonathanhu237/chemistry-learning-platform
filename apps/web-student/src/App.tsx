import { useEffect, useMemo, useState } from "react";
import { LoaderCircle } from "lucide-react";
import logoUrl from "./assets/sysu-logo.svg";
import { StudentPreviewRouterProvider, StudentRouterProvider } from "./app/router/StudentRouterProvider";
import { storePreviewInputHandshake } from "./app/preview/input/previewInputProtocol";
import type { ViewState } from "./app/router/routeTypes";
import { LoginPanel } from "./features/auth/LoginPanel";
import { PasswordPanel } from "./features/auth/PasswordPanel";
import { isStudent } from "./features/auth/authUtils";
import { AssessmentPanel, type AnswerMap } from "./features/pretest/AssessmentPanel";
import { PretestErrorPanel, TEMP_PRETEST_SKIP_BARRIER, TEMP_PRETEST_SKIP_TITLE } from "./features/pretest/PretestErrorPanel";
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
  startStudentPretest,
  submitStudentPretest,
} from "./api";

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [previewRuntime, setPreviewRuntime] = useState(() => isPreviewAuthSession());
  const [pretest, setPretest] = useState<Awaited<ReturnType<typeof startStudentPretest>> | null>(null);
  const [pretestLoading, setPretestLoading] = useState(false);
  const [pretestError, setPretestError] = useState("");
  const [pretestSkipped, setPretestSkipped] = useState(false);
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
        setPretestSkipped(true);
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
        setUser(currentUser);
      })
      .catch(() => {
        setAuthToken("");
        setPreviewRuntime(false);
      })
      .finally(() => setChecking(false));
  }, [previewCatalogRoute, previewRuntime, previewSessionRoute, user]);

  useEffect(() => {
    if (!user || user.must_change_password) {
      setPretest(null);
      setPretestLoading(false);
      setPretestError("");
      setPretestSkipped(false);
      return;
    }

    if (previewRuntime || user.preview_mode) {
      setPretest(null);
      setPretestLoading(false);
      setPretestError("");
      setPretestSkipped(true);
      return;
    }

    if (TEMP_PRETEST_SKIP_BARRIER) {
      setPretest(null);
      setPretestLoading(false);
      setPretestError(TEMP_PRETEST_SKIP_TITLE);
      setPretestSkipped(false);
      return;
    }

    let cancelled = false;
    setPretestLoading(true);
    setPretestError("");
    setPretestSkipped(false);
    startStudentPretest()
      .then((response) => {
        if (cancelled) return;
        setPretest(response);
      })
      .catch((requestError) => {
        if (cancelled) return;
        setPretestError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setPretestLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [previewRuntime, user?.id, user?.must_change_password, user?.password_version, user?.preview_mode]);

  const view: ViewState = useMemo(() => {
    if (checking) return "checking";
    if (!user) return "login";
    if (user.must_change_password) return "password";
    if (previewRuntime || user.preview_mode) return "home";
    if (pretestLoading && !pretest) return "pretest-loading";
    if (pretestError && !pretestSkipped) return "pretest-error";
    if (pretest?.status === "in_progress" && pretest.stage && pretest.questions.length) return "pretest";
    if (pretestLoading) return "pretest-loading";
    return "home";
  }, [checking, pretest, pretestError, pretestLoading, pretestSkipped, previewRuntime, user]);

  const acceptLogin = (response: LoginResponse) => {
    if (!isStudent(response)) {
      setAuthToken("");
      setSessionError("请使用学生账号登录");
      return;
    }
    setSessionError("");
    setPreviewRuntime(false);
    setAuthToken(response.access_token);
    setUser(response.user);
  };

  const handleLogout = async () => {
    await logout();
    setPretest(null);
    setPretestError("");
    setPretestSkipped(false);
    setPreviewRuntime(false);
    setUser(null);
  };

  const handlePretestSubmit = async (answers: AnswerMap) => {
    if (!pretest?.stage) return;
    setPretestLoading(true);
    setPretestError("");
    try {
      const response = await submitStudentPretest(
        pretest.stage,
        Object.entries(answers).map(([questionId, answer]) => ({ question_id: questionId, answer })),
      );
      setPretest(response);
      if (response.status === "completed" && response.report?.id) {
        window.history.replaceState({}, "", `/assessment/reports/${response.report.id}?from=assessment`);
        setPretestSkipped(true);
      }
    } catch (requestError) {
      setPretestError(errorMessage(requestError));
    } finally {
      setPretestLoading(false);
    }
  };

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
    <main className={view === "pretest" ? "app-shell assessment-shell" : view === "home" ? "app-shell learning-shell" : "app-shell"}>
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
      {view === "pretest-loading" ? <LoadingPanel text="正在准备课前摸底" /> : null}
      {view === "pretest-error" ? (
        <PretestErrorPanel message={pretestError} onSkip={() => setPretestSkipped(true)} onLogout={handleLogout} />
      ) : null}
      {view === "pretest" && pretest ? (
        <>
          <AssessmentPanel
            eyebrow="课前摸底"
            title="请完成以下题目"
            questions={pretest.questions}
            submitting={pretestLoading}
            onSubmit={handlePretestSubmit}
          />
        </>
      ) : null}
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
