import { useEffect, useMemo, useState } from "react";
import { LoaderCircle } from "lucide-react";
import logoUrl from "./assets/sysu-logo.svg";
import { StudentRouterProvider } from "./app/router/StudentRouterProvider";
import type { ViewState } from "./app/router/routeTypes";
import { LoginPanel } from "./features/auth/LoginPanel";
import { PasswordPanel } from "./features/auth/PasswordPanel";
import { isStudent } from "./features/auth/authUtils";
import { AssessmentPanel, type AnswerMap } from "./features/pretest/AssessmentPanel";
import { PretestErrorPanel, TEMP_PRETEST_SKIP_BARRIER, TEMP_PRETEST_SKIP_TITLE } from "./features/pretest/PretestErrorPanel";
import {
  AuthUser,
  LoginResponse,
  errorMessage,
  getAuthToken,
  loadCurrentUser,
  logout,
  setAuthToken,
  startStudentPretest,
  submitStudentPretest,
} from "./api";

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [pretest, setPretest] = useState<Awaited<ReturnType<typeof startStudentPretest>> | null>(null);
  const [pretestLoading, setPretestLoading] = useState(false);
  const [pretestError, setPretestError] = useState("");
  const [pretestSkipped, setPretestSkipped] = useState(false);

  useEffect(() => {
    if (!getAuthToken()) {
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
        setUser(currentUser);
      })
      .catch(() => {
        setAuthToken("");
      })
      .finally(() => setChecking(false));
  }, []);

  useEffect(() => {
    if (!user || user.must_change_password) {
      setPretest(null);
      setPretestLoading(false);
      setPretestError("");
      setPretestSkipped(false);
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
  }, [user?.id, user?.must_change_password, user?.password_version]);

  const view: ViewState = useMemo(() => {
    if (checking) return "checking";
    if (!user) return "login";
    if (user.must_change_password) return "password";
    if (pretestLoading && !pretest) return "pretest-loading";
    if (pretestError && !pretestSkipped) return "pretest-error";
    if (pretest?.status === "in_progress" && pretest.stage && pretest.questions.length) return "pretest";
    if (pretestLoading) return "pretest-loading";
    return "home";
  }, [checking, pretest, pretestError, pretestLoading, pretestSkipped, user]);

  const acceptLogin = (response: LoginResponse) => {
    if (!isStudent(response)) {
      setAuthToken("");
      setSessionError("请使用学生账号登录");
      return;
    }
    setSessionError("");
    setAuthToken(response.access_token);
    setUser(response.user);
  };

  const handleLogout = async () => {
    await logout();
    setPretest(null);
    setPretestError("");
    setPretestSkipped(false);
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
    } catch (requestError) {
      setPretestError(errorMessage(requestError));
    } finally {
      setPretestLoading(false);
    }
  };

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

export default App;
