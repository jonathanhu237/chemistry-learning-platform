import { useEffect, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { BarChart3, ChevronRight, ClipboardList, LoaderCircle } from "lucide-react";
import { errorMessage, getStudentAssessmentReports, type StudentAssessmentReportSummary } from "../../api";
import { navigateToAssessmentReport } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { formatPercent, formatScore } from "../../features/assessment/assessmentFormat";
import { MobileEmptyState } from "../../mobile/primitives";

function reportTypeLabel(type: StudentAssessmentReportSummary["report_type"]): string {
  if (type === "pretest") return "课前测试";
  if (type === "custom") return "自主测评";
  if (type === "point") return "点位测评";
  if (type === "posttest") return "学习后测";
  return "智能测评";
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

export function ProfileReportsPage() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [reports, setReports] = useState<StudentAssessmentReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentAssessmentReports()
      .then((response) => {
        if (!cancelled) setReports(response.reports || []);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <DetailPageFrame title="测评报告" source={search.from || "profile"}>
      <section className="learning-panel profile-report-list-page" aria-label="测评报告列表">
        {loading ? (
          <MobileEmptyState className="empty-learning-card" icon={<LoaderCircle className="spin" size={20} />}>
            <span>正在加载报告</span>
          </MobileEmptyState>
        ) : error ? (
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>{error}</span>
          </MobileEmptyState>
        ) : reports.length ? (
          <div className="profile-report-list">
            {reports.map((report) => (
              <button
                key={report.id}
                className="profile-report-card"
                type="button"
                onClick={() => navigateToAssessmentReport(navigate, report.id, "profile-reports")}
              >
                <span className="profile-report-icon">
                  <BarChart3 size={18} />
                </span>
                <span className="profile-report-copy">
                  <strong>{report.title || reportTypeLabel(report.report_type)}</strong>
                  <small>
                    {formatDate(report.completed_at)} · {reportTypeLabel(report.report_type)} · {formatScore(report.score)} 分
                  </small>
                  <em>
                    正确率 {formatPercent(report.correct_rate)} · 错题 {report.wrong_count}
                  </em>
                </span>
                <ChevronRight size={18} />
              </button>
            ))}
          </div>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>暂无测评报告，完成一次测评后会显示在这里。</span>
          </MobileEmptyState>
        )}
      </section>
    </DetailPageFrame>
  );
}
