import { useNavigate } from "@tanstack/react-router";
import { BarChart3, ClipboardList, LogOut, MessageSquarePlus, UserRound } from "lucide-react";
import { getFeedbackCapability, getStudentProfilePresentation } from "../../app/preview/previewSandbox";
import { navigateToFeedback, navigateToProfileReports } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";

export function ProfileRootPage() {
  const navigate = useNavigate();
  const runtime = useStudentRuntime();
  const profile = getStudentProfilePresentation(runtime);
  const feedbackCapability = getFeedbackCapability(runtime);

  return (
    <section className="learning-panel profile-tab-panel" aria-label="我的">
      <section className="profile-card">
        <span className="panel-icon">
          <UserRound size={20} />
        </span>
        <div>
          <p>{profile.studentId}</p>
          <h2>{profile.displayName}</h2>
          {profile.className ? <small>{profile.className}</small> : null}
        </div>
      </section>
      <button className="profile-entry-card" type="button" onClick={() => navigateToProfileReports(navigate, "profile")}>
        <BarChart3 size={20} />
        <span>
          <strong>测评报告</strong>
          <small>查看课前测试、自主测评和智能测评的历史报告。</small>
        </span>
      </button>
      {feedbackCapability.canOpenEntry ? (
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
      <MobileButton className="secondary-action full profile-logout-action" type="button" variant="secondary" onClick={runtime.onLogout}>
        <LogOut size={18} />
        <span>退出登录</span>
      </MobileButton>
    </section>
  );
}
