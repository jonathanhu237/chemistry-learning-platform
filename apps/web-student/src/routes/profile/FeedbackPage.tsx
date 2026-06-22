import { useSearch } from "@tanstack/react-router";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { getFeedbackCapability } from "../../app/preview/previewSandbox";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { StudentFeedbackForm } from "../../features/feedback/StudentFeedbackForm";
import { ClipboardList } from "lucide-react";
import { MobileEmptyState } from "../../mobile/primitives";

export function FeedbackPage() {
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const runtime = useStudentRuntime();
  const feedbackCapability = getFeedbackCapability(runtime);
  return (
    <DetailPageFrame title="提交反馈" source={search.from || "profile"}>
      {feedbackCapability.canOpenForm ? (
        <section className="learning-panel feedback-detail-page">
          <StudentFeedbackForm
            context={{
              pagePath: "/feedback/new",
              contextTitle: "学生端反馈",
              metadata: { route: "feedback_new", from: search.from || "profile" },
            }}
          />
        </section>
      ) : (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>反馈入口已关闭</span>
          </MobileEmptyState>
        </section>
      )}
    </DetailPageFrame>
  );
}
