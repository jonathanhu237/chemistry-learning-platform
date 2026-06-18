import { FormEvent, useEffect, useState } from "react";
import { LoaderCircle, LogIn, UserRound } from "lucide-react";
import { errorMessage, studentLogin, type LoginResponse } from "../../api";
import { MobileButton, MobileField } from "../../mobile/primitives";
import { normalizeStudentId } from "./authUtils";

export function LoginPanel({
  sessionError,
  onLogin,
}: {
  sessionError: string;
  onLogin: (response: LoginResponse) => void;
}) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(sessionError);

  useEffect(() => setError(sessionError), [sessionError]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedId = normalizeStudentId(studentId);
    if (!normalizedId || !password) return;
    setLoading(true);
    setError("");
    try {
      const response = await studentLogin(normalizedId, password);
      onLogin(response);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-panel">
      <div className="panel-heading">
        <span className="panel-icon">
          <UserRound size={19} />
        </span>
        <div>
          <p>学生入口</p>
          <h2>学号登录</h2>
        </div>
      </div>

      <form onSubmit={submit} className="auth-form">
        <label>
          <span>学号</span>
          <MobileField
            value={studentId}
            onChange={(event) => setStudentId(event.target.value)}
            placeholder="请输入学号"
            autoComplete="username"
            inputMode="text"
          />
        </label>
        <label>
          <span>密码</span>
          <MobileField
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="请输入密码"
            type="password"
            autoComplete="current-password"
          />
        </label>
        {error ? <div className="form-error">{error}</div> : null}
        <MobileButton className="primary-action" type="submit" loading={loading} disabled={!studentId.trim() || !password}>
          {loading ? <LoaderCircle className="spin" size={18} /> : <LogIn size={18} />}
          <span>{loading ? "正在登录" : "登录"}</span>
        </MobileButton>
      </form>
    </section>
  );
}
