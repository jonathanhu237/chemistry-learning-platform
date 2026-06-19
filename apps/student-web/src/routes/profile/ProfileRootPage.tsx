import { useNavigate } from "@tanstack/react-router";
import { ClipboardList, LogOut, MessageSquarePlus, UserRound } from "lucide-react";
import { navigateToFeedback } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";

export function ProfileRootPage() {
  const navigate = useNavigate();
  const { user, canUseFeedback, onLogout } = useStudentRuntime();

  return (
    <section className="learning-panel profile-tab-panel" aria-label="我的">
      <section className="profile-card">
        <span className="panel-icon">
          <UserRound size={20} />
        </span>
        <div>
          <p>{user.student_id || user.username}</p>
          <h2>{user.display_name}</h2>
          {user.class_name ? <small>{user.class_name}</small> : null}
        </div>
      </section>
      {canUseFeedback ? (
        <button className="profile-entry-card" type="button" onClick={() => navigateToFeedback(navigate, "profile")}>
          <MessageSquarePlus size={20} />
          <span>
            <strong>提交反馈</strong>
            <small>课程内容、实验资源、系统问题都可以在这里反馈。</small>
          </span>
        </button>
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
          <span>反馈入口已关闭</span>
        </MobileEmptyState>
      )}
      <MobileButton className="secondary-action full profile-logout-action" type="button" variant="secondary" onClick={onLogout}>
        <LogOut size={18} />
        <span>退出登录</span>
      </MobileButton>
    </section>
  );
}
