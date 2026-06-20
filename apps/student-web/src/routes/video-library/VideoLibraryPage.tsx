import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { Bot, ChevronRight, FlaskConical, LoaderCircle, Search, Sparkles, Video, X } from "lucide-react";
import type {
  StudentVideoLibraryResultItem,
  StudentVideoLibraryRouteTarget,
  StudentVideoLibrarySearchResponse,
} from "../../api";
import { errorMessage, searchStudentVideoLibrary } from "../../api";
import { navigateToAiChat, navigateToChapter, navigateToPoint } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { type AssistantContext } from "../../features/assistant/assistantContext";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";

function compactSearch(search: Record<string, string | null | undefined>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(search)
      .map(([key, value]) => [key, String(value || "").trim()] as const)
      .filter(([, value]) => value.length > 0),
  );
}

function aiContextFromResult(item: StudentVideoLibraryResultItem, target: StudentVideoLibraryRouteTarget): AssistantContext {
  return {
    context_type: target.node_id ? "learning_point" : "learning_home",
    context_title: target.context_title || item.title,
    context_summary: target.context_summary || item.snippet || item.subtitle,
    chapter_id: target.chapter_id || undefined,
    point_node_id: target.node_id || undefined,
    source_node_id: target.source_node_id || undefined,
    catalog_path: target.catalog_path || undefined,
    prompts: [
      target.prompt || `解释“${item.title}”这个实验现象`,
      "这个现象对应哪些反应原理？",
      "我应该先看哪个实验点位？",
    ],
  };
}

export function VideoLibraryPage() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const query = search.q || "";
  const [draft, setDraft] = useState(query);
  const [payload, setPayload] = useState<StudentVideoLibrarySearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => setDraft(query), [query]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const nextQuery = draft.trim();
      if (nextQuery === query) return;
      void navigate({
        to: "/video-library",
        search: compactSearch({ from: search.from || "home", q: nextQuery }),
        replace: true,
      });
    }, 240);
    return () => window.clearTimeout(timer);
  }, [draft, navigate, query, search.from]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    searchStudentVideoLibrary(query)
      .then((response) => {
        if (!cancelled) setPayload(response);
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
  }, [query]);

  const hasQuery = query.trim().length > 0;
  const groupedResultCount = useMemo(
    () => payload?.groups.reduce((total, group) => total + group.items.length, 0) || 0,
    [payload],
  );

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextQuery = draft.trim();
    void navigate({
      to: "/video-library",
      search: compactSearch({ from: search.from || "home", q: nextQuery }),
      replace: false,
    });
  };

  const openResult = (item: StudentVideoLibraryResultItem) => {
    const target = item.target;
    if (!target) return;
    if (target.kind === "point_detail" && target.node_id) {
      navigateToPoint(navigate, target.node_id, {
        from: "video-library",
        profileId: target.profile_id,
        chapterId: target.chapter_id,
        sourceNodeId: target.source_node_id,
        catalogPath: target.catalog_path?.join(" / "),
        propertyKey: target.property_key,
        propertyTitle: target.property_title,
        elementSymbol: target.element_symbol,
        pointTitle: target.point_title || item.title,
      });
      return;
    }
    if (target.kind === "chapter_detail" && target.profile_id) {
      navigateToChapter(navigate, target.profile_id, {
        from: "video-library",
        propertyKey: target.property_key,
        elementSymbol: target.element_symbol,
      });
      return;
    }
    if (target.kind === "ai_chat") {
      navigateToAiChat(navigate, aiContextFromResult(item, target), "video-library");
    }
  };

  const searchBox = (
    <form className="video-library-search" role="search" onSubmit={submitSearch}>
      <Search size={18} />
      <input
        value={draft}
        onChange={(event) => setDraft(event.currentTarget.value)}
        placeholder="搜实验现象、试剂、点位"
        aria-label="搜索实验视频库"
      />
      {draft ? (
        <button type="button" aria-label="清空搜索" onClick={() => setDraft("")}>
          <X size={16} />
        </button>
      ) : null}
    </form>
  );

  return (
    <DetailPageFrame title="实验视频库" source={search.from || "home"}>
      <section className="video-library-page" aria-label="实验视频库">
        <section className="video-library-hero">
          <div>
            <p>实验视频学习</p>
            <h2>从现象、试剂和观察点进入实验</h2>
            <span>结果都会跳转到可学习的章节、点位或 AI 解释，不停在纯文本列表。</span>
          </div>
          <Video size={28} />
        </section>

        {searchBox}

        {payload?.message ? <div className={`video-library-banner ${payload.status}`}>{payload.message}</div> : null}
        {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在检索实验视频库" /> : null}
        {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}

        {!loading && !error && payload && !hasQuery ? (
          <DefaultBrowse payload={payload} onChip={(nextQuery) => setDraft(nextQuery)} onOpenResult={openResult} />
        ) : null}

        {!loading && !error && payload && hasQuery ? (
          <section className="video-library-results" aria-live="polite">
            <div className="video-library-section-head">
              <div>
                <p>搜索结果</p>
                <h3>{groupedResultCount ? `${groupedResultCount} 个可跳转结果` : "没有匹配结果"}</h3>
              </div>
              <span>{payload.backend === "elasticsearch" ? "ES" : payload.backend === "local" ? "本地" : "关闭"}</span>
            </div>
            {payload.groups.length ? (
              payload.groups.map((group) => (
                <section key={group.key} className="video-result-group">
                  <div className="video-result-group-head">
                    <strong>{group.title}</strong>
                    <small>{group.summary}</small>
                  </div>
                  <div className="video-result-list">
                    {group.items.map((item) => (
                      <VideoResultButton key={item.id} item={item} onClick={() => openResult(item)} />
                    ))}
                  </div>
                </section>
              ))
            ) : (
              <MobileEmptyState className="empty-learning-card" icon={<Search size={20} />}>
                <span>换一个现象、试剂或章节关键词试试。</span>
              </MobileEmptyState>
            )}
          </section>
        ) : null}
      </section>
    </DetailPageFrame>
  );
}

function DefaultBrowse({
  payload,
  onChip,
  onOpenResult,
}: {
  payload: StudentVideoLibrarySearchResponse;
  onChip: (query: string) => void;
  onOpenResult: (item: StudentVideoLibraryResultItem) => void;
}) {
  return (
    <section className="video-library-default">
      {payload.browse.chips.length ? (
        <section className="video-chip-panel">
          <div className="video-library-section-head">
            <div>
              <p>按现象浏览</p>
              <h3>常见实验线索</h3>
            </div>
            <Sparkles size={18} />
          </div>
          <div className="video-library-chip-grid">
            {payload.browse.chips.map((chip) => (
              <button key={`${chip.kind}-${chip.label}`} type="button" onClick={() => onChip(chip.query)}>
                <span>{chip.label}</span>
                <small>{chip.kind === "element_family" ? "章节" : chip.kind === "reagent" ? "试剂" : "现象"}</small>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      <section className="video-recommended-panel">
        <div className="video-library-section-head">
          <div>
            <p>推荐实验</p>
            <h3>直接进入可学习点位</h3>
          </div>
          <Video size={18} />
        </div>
        {payload.browse.recommended.length ? (
          <div className="video-result-list">
            {payload.browse.recommended.map((item) => (
              <VideoResultButton key={item.id} item={item} onClick={() => onOpenResult(item)} />
            ))}
          </div>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<FlaskConical size={20} />}>
            <span>暂无可展示的实验视频内容。</span>
          </MobileEmptyState>
        )}
      </section>
    </section>
  );
}

function VideoResultButton({ item, onClick }: { item: StudentVideoLibraryResultItem; onClick: () => void }) {
  const icon = item.type === "ai_prompt" ? <Bot size={20} /> : item.type === "chapter_experiment" ? <FlaskConical size={20} /> : <Video size={20} />;
  return (
    <button className="video-result-card" type="button" onClick={onClick} disabled={!item.target}>
      <span className="video-result-icon">{icon}</span>
      <span className="video-result-copy">
        <strong>{item.title}</strong>
        {item.subtitle ? <small>{item.subtitle}</small> : null}
        {item.snippet ? <em>{item.snippet}</em> : null}
        {item.badges.length ? (
          <span className="video-result-badges">
            {item.badges.slice(0, 3).map((badge) => (
              <b key={badge}>{badge}</b>
            ))}
          </span>
        ) : null}
      </span>
      <span className="video-result-action">
        <small>{item.action_label || "打开"}</small>
        <ChevronRight size={17} />
      </span>
    </button>
  );
}
