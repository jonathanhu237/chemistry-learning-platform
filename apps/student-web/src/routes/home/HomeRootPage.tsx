import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { BookOpenCheck, ClipboardList, FlaskConical, LoaderCircle, MessageCircle, Sparkles } from "lucide-react";
import { errorMessage, getStudentLearningHome, getStudentLearningPage, type StudentLearningHomeResponse, type StudentLearningPageResponse } from "../../api";
import { navigateToAiChat, navigateToAssessmentSession, navigateToChapter, navigateToRoot } from "../../app/router/navigation";
import { defaultAssistantContext } from "../../features/assistant/assistantContext";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { useStudentRuntime } from "../../app/shell/studentAppContext";

export function HomeRootPage() {
  const navigate = useNavigate();
  const { canUseAssistant, startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();
  const [learningPage, setLearningPage] = useState<StudentLearningPageResponse | null>(null);
  const [learningHome, setLearningHome] = useState<StudentLearningHomeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([getStudentLearningPage(null), getStudentLearningHome()])
      .then(([page, home]) => {
        if (cancelled) return;
        setLearningPage(page);
        setLearningHome(home);
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

  const recommendedProfile = useMemo(() => {
    const profiles = learningPage?.profiles || [];
    const recommendedProfileId = learningPage?.recommended_profile_id || learningPage?.active_profile?.profile_id || profiles[0]?.profile_id || "";
    return profiles.find((profile) => profile.profile_id === recommendedProfileId) || profiles[0] || null;
  }, [learningPage]);
  const recommendedGroup = learningHome?.groups.find((group) => group.recommended) || learningHome?.groups[0] || null;

  const startAssessment = async () => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "home");
  };

  return (
    <section className="learning-panel home-root-page" aria-label="首页">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载今日学习" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error ? (
        <>
          <section className="home-hero-card">
            <span className="panel-icon">
              <Sparkles size={20} />
            </span>
            <div>
              <p>推荐学习</p>
              <h2>{recommendedProfile ? formatChapterEntryTitle(recommendedProfile) : "选择一个章节开始"}</h2>
              <small>{recommendedProfile?.subtitle || recommendedGroup?.parent_title || "从周期表、AI 或测评入口继续学习。"}</small>
            </div>
          </section>

          <div className="home-action-grid">
            {recommendedProfile ? (
              <button type="button" className="home-action-card primary" onClick={() => navigateToChapter(navigate, recommendedProfile.profile_id, { from: "home" })}>
                <BookOpenCheck size={20} />
                <span>继续章节</span>
                <strong>{recommendedProfile.element_symbols.join(" ") || recommendedProfile.family_name}</strong>
              </button>
            ) : (
              <button type="button" className="home-action-card primary" onClick={() => navigateToRoot(navigate, "learn")}>
                <BookOpenCheck size={20} />
                <span>选择章节</span>
                <strong>学习入口</strong>
              </button>
            )}
            <button type="button" className="home-action-card" onClick={() => navigateToRoot(navigate, "learn")}>
              <FlaskConical size={20} />
              <span>周期表</span>
              <strong>按元素族学习</strong>
            </button>
            <button type="button" className="home-action-card" disabled={!canUseAssistant} onClick={() => navigateToAiChat(navigate, defaultAssistantContext(), "home")}>
              <MessageCircle size={20} />
              <span>问 AI</span>
              <strong>{canUseAssistant ? "带着问题进入" : "暂未开放"}</strong>
            </button>
            <button type="button" className="home-action-card" onClick={startAssessment} disabled={posttestLoading}>
              <ClipboardList size={20} />
              <span>学习测评</span>
              <strong>{posttestLoading ? "正在创建" : "开始练习"}</strong>
            </button>
          </div>

          {posttestError ? <div className="form-error">{posttestError}</div> : null}
          {!recommendedProfile && !recommendedGroup ? (
            <MobileEmptyState className="empty-learning-card" icon={<BookOpenCheck size={20} />}>
              <span>暂无推荐内容，可以先从学习页选择章节。</span>
            </MobileEmptyState>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
