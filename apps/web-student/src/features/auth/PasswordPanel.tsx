import { FormEvent, useState } from "react";
import { LoaderCircle, LockKeyhole, ShieldCheck } from "lucide-react";
import { AuthUser, LoginResponse, changeStudentPassword, errorMessage } from "../../api";
import { MobileButton, MobileField } from "../../mobile/primitives";

export function PasswordPanel({ user, onChanged }: { user: AuthUser; onChanged: (response: LoginResponse) => void }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = newPassword.length >= 8 && newPassword === confirmPassword;

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;
    setLoading(true);
    setError("");
    try {
      const response = await changeStudentPassword(newPassword);
      onChanged(response);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-panel">
      <div className="panel-heading">
        <span className="panel-icon warning">
          <LockKeyhole size={19} />
        </span>
        <div>
          <p>{user.student_id || user.username}</p>
          <h2>修改初始密码</h2>
        </div>
      </div>

      <form onSubmit={submit} className="auth-form">
        <div className="form-hint">首次登录已完成身份校验，只需要设置新密码。</div>
        <label>
          <span>新密码</span>
          <MobileField
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            placeholder="至少 8 位"
            type="password"
            autoComplete="new-password"
          />
        </label>
        <label>
          <span>确认新密码</span>
          <MobileField
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="再次输入新密码"
            type="password"
            autoComplete="new-password"
          />
        </label>
        {newPassword && newPassword.length < 8 ? <div className="form-hint">新密码至少 8 位</div> : null}
        {confirmPassword && newPassword !== confirmPassword ? <div className="form-hint">两次输入的新密码不一致</div> : null}
        {error ? <div className="form-error">{error}</div> : null}
        <MobileButton className="primary-action" type="submit" loading={loading} disabled={!canSubmit}>
          {loading ? <LoaderCircle className="spin" size={18} /> : <ShieldCheck size={18} />}
          <span>{loading ? "正在保存" : "保存并继续"}</span>
        </MobileButton>
      </form>
    </section>
  );
}
