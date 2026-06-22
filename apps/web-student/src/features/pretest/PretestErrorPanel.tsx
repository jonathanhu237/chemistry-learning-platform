import { BookOpenCheck, ClipboardList, LogOut } from "lucide-react";
import { MobileButton } from "../../mobile/primitives";

export const TEMP_PRETEST_SKIP_BARRIER = false;
export const TEMP_PRETEST_SKIP_TITLE = "课前摸底暂未接入";

export function PretestErrorPanel({ message, onSkip, onLogout }: { message: string; onSkip: () => void; onLogout: () => void }) {
  const title = TEMP_PRETEST_SKIP_BARRIER ? TEMP_PRETEST_SKIP_TITLE : message || "暂时无法开始";

  return (
    <section className="auth-panel success-panel">
      <div className="success-mark warning-mark">
        <ClipboardList size={30} />
      </div>
      <div className="success-copy">
        <p>课前摸底</p>
        <h2>{title}</h2>
      </div>
      <div className="form-hint">临时跳过屏障：课前摸底由后续分支继续完善，本轮可先进入学习页检查学习体验。</div>
      <MobileButton className="primary-action" type="button" onClick={onSkip}>
        <BookOpenCheck size={18} />
        <span>跳过课前摸底</span>
      </MobileButton>
      <MobileButton variant="secondary" className="secondary-action" type="button" onClick={onLogout}>
        <LogOut size={18} />
        <span>退出登录</span>
      </MobileButton>
    </section>
  );
}
