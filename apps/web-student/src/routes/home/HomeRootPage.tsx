import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { BookOpenCheck, ClipboardList, FlaskConical, LoaderCircle, MessageCircle, Search, Sparkles } from "lucide-react";
import { errorMessage, getStudentLearningHome, getStudentLearningPage, type StudentLearningHomeResponse, type StudentLearningPageResponse } from "../../api";
import { navigateToAiChat, navigateToChapter, navigateToRoot, navigateToVideoLibrary } from "../../app/router/navigation";
import { defaultAssistantContext } from "../../features/assistant/assistantContext";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { useStudentRuntime } from "../../app/shell/studentAppContext";

export function HomeRootPage() {
  const navigate = useNavigate();
  const { canUseAssistant } = useStudentRuntime();
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
            <button type="button" className="home-action-card video-library-entry" onClick={() => navigateToVideoLibrary(navigate, { from: "home" })}>
              <Search size={20} />
              <span>实验视频库</span>
              <strong>搜现象、试剂、点位</strong>
            </button>
            <button type="button" className="home-action-card" disabled={!canUseAssistant} onClick={() => navigateToAiChat(navigate, defaultAssistantContext(), "home")}>
              <MessageCircle size={20} />
              <span>问 AI</span>
              <strong>{canUseAssistant ? "带着问题进入" : "暂未开放"}</strong>
            </button>
            <button type="button" className="home-action-card" onClick={() => navigateToRoot(navigate, "assessment")}>
              <ClipboardList size={20} />
              <span>学习测评</span>
              <strong>选择练习方式</strong>
            </button>
          </div>

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
