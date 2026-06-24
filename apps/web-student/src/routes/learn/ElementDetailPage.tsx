import { useEffect, useMemo, useState } from "react";
import { useParams, useSearch } from "@tanstack/react-router";
import { FlaskConical, LoaderCircle, Search } from "lucide-react";
import type { StudentLearningPageResponse } from "../../api";
import { errorMessage, getStudentLearningPage } from "../../api";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { LearningAtomModelCard } from "../../features/atom-viewer/LearningAtomModelCard";
import { LearningState } from "../../shared/mobile/LearningState";
import { MobileEmptyState } from "../../mobile/primitives";

export function ElementDetailPage() {
  const params = useParams({ strict: false }) as { profileId?: string; symbol?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const profileId = params.profileId || "";
  const symbol = params.symbol || "";
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (!profileId) {
      setLoading(false);
      setError("缺少章节信息");
      return () => {
        cancelled = true;
      };
    }

    setLoading(true);
    setError("");
    getStudentLearningPage(profileId)
      .then((payload) => {
        if (!cancelled) setPage(payload);
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
  }, [profileId]);

  const profile = page?.active_profile || null;
  const element = useMemo(() => {
    const normalizedSymbol = symbol.trim().toLowerCase();
    return profile?.elements.find((candidate) => candidate.symbol.toLowerCase() === normalizedSymbol) || null;
  }, [profile, symbol]);
  const title = element ? `${element.name} ${element.symbol}` : "元素详情";

  return (
    <DetailPageFrame title={title} source={search.from || "chapter"}>
      <section className="element-detail-page" aria-label="元素详情">
        {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载元素详情" /> : null}
        {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
        {!loading && !error && profile && element ? <LearningAtomModelCard profile={profile} element={element} /> : null}
        {!loading && !error && profile && !element ? (
          <MobileEmptyState className="empty-learning-card" icon={<Search size={20} />}>
            <span>没有找到这个元素</span>
          </MobileEmptyState>
        ) : null}
      </section>
    </DetailPageFrame>
  );
}
