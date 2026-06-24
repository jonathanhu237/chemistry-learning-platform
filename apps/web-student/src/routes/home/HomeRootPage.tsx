import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Atom, Bookmark, ChevronRight, FlaskConical, LoaderCircle, MoreHorizontal, Share2, ThumbsUp, Video } from "lucide-react";
import {
  errorMessage,
  getStudentHomeVideoFeed,
  studentMediaUrl,
  type StudentHomeVideoFeedItem,
  type StudentHomeVideoFeedReason,
  type StudentHomeVideoFeedResponse,
} from "../../api";
import { navigateToAiChat, navigateToPoint } from "../../app/router/navigation";
import { type AssistantContext } from "../../features/assistant/assistantContext";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";
import { useStudentRuntime } from "../../app/shell/studentAppContext";

const reasonLabels: Record<StudentHomeVideoFeedReason, string> = {
  catalog: "目录实验",
  recommended: "推荐观看",
  recent: "最近更新",
  weakness: "薄弱章节",
};

function formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return "";
  const total = Math.round(seconds);
  const minutes = Math.floor(total / 60);
  const rest = total % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

function compactCatalogPath(path: string[]): string {
  const cleanPath = path.map((part) => part.trim()).filter(Boolean);
  if (cleanPath.length <= 2) return cleanPath.join(" / ");
  return `${cleanPath[0]} / ${cleanPath[cleanPath.length - 1]}`;
}

function feedItemAssistantContext(item: StudentHomeVideoFeedItem): AssistantContext {
  const target = item.target;
  return {
    context_type: "learning_point",
    context_title: item.title,
    context_summary: item.snippet || item.summary || compactCatalogPath(item.catalog_path),
    chapter_id: target.chapter_id || item.chapter_id || undefined,
    point_node_id: target.node_id || item.placement_node_id || item.node_id || undefined,
    source_node_id: target.source_node_id || undefined,
    catalog_path: target.catalog_path || item.catalog_path,
    prompts: [
      `帮我解释“${item.title}”这个实验视频的现象`,
      "这个实验和课本目录里的哪一节有关？",
      "看这个视频时我应该重点观察什么？",
    ],
  };
}

function useActiveFeedItem(items: StudentHomeVideoFeedItem[]) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const nodesRef = useRef(new Map<string, HTMLElement>());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const visibilityRef = useRef(new Map<string, { ratio: number; top: number }>());

  const updateActive = useCallback(() => {
    const viewportCenter = window.innerHeight / 2;
    const next =
      Array.from(visibilityRef.current.entries())
        .filter(([, state]) => state.ratio >= 0.48)
        .sort(([, left], [, right]) => right.ratio - left.ratio || Math.abs(left.top - viewportCenter) - Math.abs(right.top - viewportCenter))[0]?.[0] || null;
    setActiveId((current) => (current === next ? current : next));
  }, []);

  const registerCard = useCallback(
    (id: string, node: HTMLElement | null) => {
      const previous = nodesRef.current.get(id);
      if (previous && observerRef.current) observerRef.current.unobserve(previous);
      if (!node) {
        nodesRef.current.delete(id);
        visibilityRef.current.delete(id);
        updateActive();
        return;
      }
      nodesRef.current.set(id, node);
      if (observerRef.current) observerRef.current.observe(node);
    },
    [updateActive],
  );

  useEffect(() => {
    if (!items.length) {
      setActiveId(null);
      return;
    }
    if (!("IntersectionObserver" in window)) {
      setActiveId(items[0].id);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = (entry.target as HTMLElement).dataset.feedId || "";
          if (!id) continue;
          if (entry.isIntersecting) {
            visibilityRef.current.set(id, {
              ratio: entry.intersectionRatio,
              top: entry.boundingClientRect.top,
            });
          } else {
            visibilityRef.current.delete(id);
          }
        }
        updateActive();
      },
      {
        root: null,
        rootMargin: "-18% 0px -26% 0px",
        threshold: [0, 0.25, 0.48, 0.65, 0.82, 1],
      },
    );

    observerRef.current = observer;
    nodesRef.current.forEach((node) => observer.observe(node));

    return () => {
      observer.disconnect();
      observerRef.current = null;
      visibilityRef.current.clear();
    };
  }, [items, updateActive]);

  useEffect(() => {
    if (!activeId || items.some((item) => item.id === activeId)) return;
    setActiveId(items[0]?.id || null);
  }, [activeId, items]);

  return { activeId, registerCard };
}

type HomeVideoFeedCardProps = {
  item: StudentHomeVideoFeedItem;
  isActive: boolean;
  canUseAssistant: boolean;
  registerCard: (id: string, node: HTMLElement | null) => void;
  onOpen: (item: StudentHomeVideoFeedItem) => void;
  onAsk: (item: StudentHomeVideoFeedItem) => void;
};

function HomeVideoFeedCard({ item, isActive, canUseAssistant, registerCard, onOpen, onAsk }: HomeVideoFeedCardProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [liked, setLiked] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const mediaUrl = item.video.stream_path ? studentMediaUrl(item.video.stream_path) : "";
  const posterUrl = item.video.thumbnail_path ? studentMediaUrl(item.video.thumbnail_path) : "";
  const duration = formatDuration(item.video.duration_seconds);
  const pathLabel = compactCatalogPath(item.catalog_path);
  const description = item.snippet || item.summary;
  const badges = item.badges.length ? item.badges.slice(0, 3) : [reasonLabels[item.reason]];
  const titleId = `home-video-title-${item.id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (!isActive || !mediaUrl) {
      try {
        video.pause();
      } catch {
        // Some test environments do not implement media controls.
      }
      return;
    }
    video.muted = true;
    video.playsInline = true;
    try {
      const playPromise = video.play();
      if (playPromise) void playPromise.catch(() => undefined);
    } catch {
      // Autoplay can be blocked; the poster and action remain usable.
    }
  }, [isActive, mediaUrl]);

  const shareItem = useCallback(() => {
    if (typeof navigator.share !== "function") return;
    void navigator
      .share({
        title: item.title,
        text: description || pathLabel || item.title,
      })
      .catch(() => undefined);
  }, [description, item.title, pathLabel]);

  return (
    <article
      ref={(node) => registerCard(item.id, node)}
      data-feed-id={item.id}
      className={`home-video-card${isActive ? " is-active" : ""}`}
      aria-labelledby={titleId}
    >
      <button type="button" className="home-video-media-button" onClick={() => onOpen(item)} aria-label={`查看实验视频：${item.title}`}>
        {isActive && mediaUrl ? (
          <video ref={videoRef} src={mediaUrl} poster={posterUrl || undefined} muted playsInline loop preload="metadata" />
        ) : posterUrl ? (
          <img src={posterUrl} alt="" loading="lazy" />
        ) : (
          <span className="home-video-poster-fallback">
            <Video size={30} />
            <span>实验视频</span>
          </span>
        )}
        <span className="home-video-preview-state">{isActive ? "静音预览" : "滑到此处自动预览"}</span>
        {duration ? <span className="home-video-duration">{duration}</span> : null}
      </button>

      <div className="home-video-body">
        <p className="home-video-path">{pathLabel || "实验视频"}</p>
        <h2 id={titleId}>
          <button type="button" className="home-video-title-button" onClick={() => onOpen(item)}>
            {item.title}
          </button>
        </h2>
        {description ? <p className="home-video-description">{description}</p> : null}
        <div className="home-video-badges" aria-label="视频标签">
          {badges.map((badge) => (
            <span key={badge}>{badge}</span>
          ))}
        </div>
        <div className="home-video-actions" aria-label={`视频操作：${item.title}`}>
          <button type="button" className="home-video-open-action" onClick={() => onOpen(item)} aria-label={`查看实验：${item.title}`}>
            <span>查看实验</span>
            <ChevronRight size={16} />
          </button>
          <div className="home-video-icon-actions" aria-label="视频快捷操作">
            <button
              type="button"
              className={`home-video-icon-action${liked ? " active" : ""}`}
              aria-label={`${liked ? "取消点赞" : "点赞"}：${item.title}`}
              aria-pressed={liked}
              onClick={() => setLiked((current) => !current)}
            >
              <ThumbsUp size={20} />
            </button>
            <button
              type="button"
              className={`home-video-icon-action${bookmarked ? " active" : ""}`}
              aria-label={`${bookmarked ? "取消收藏" : "收藏"}：${item.title}`}
              aria-pressed={bookmarked}
              onClick={() => setBookmarked((current) => !current)}
            >
              <Bookmark size={20} />
            </button>
            <button type="button" className="home-video-icon-action" aria-label={`转发实验视频：${item.title}`} onClick={shareItem}>
              <Share2 size={20} />
            </button>
            <button
              type="button"
              className="home-video-icon-action atom"
              disabled={!canUseAssistant}
              onClick={() => onAsk(item)}
              aria-label={`问问Atom：${item.title}`}
            >
              <Atom size={18} />
              <span>Atom</span>
            </button>
            <button type="button" className="home-video-icon-action" aria-label={`更多操作：${item.title}`}>
              <MoreHorizontal size={21} />
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

export function HomeRootPage() {
  const navigate = useNavigate();
  const { canUseAssistant } = useStudentRuntime();
  const [feed, setFeed] = useState<StudentHomeVideoFeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const items = useMemo(() => feed?.items || [], [feed]);
  const { activeId, registerCard } = useActiveFeedItem(items);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentHomeVideoFeed(16)
      .then((response) => {
        if (!cancelled) setFeed(response);
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

  const openItem = useCallback(
    (item: StudentHomeVideoFeedItem) => {
      const target = item.target;
      const nodeId = target.node_id || item.placement_node_id || item.node_id;
      navigateToPoint(navigate, nodeId, {
        from: "home",
        profileId: target.profile_id,
        chapterId: target.chapter_id || item.chapter_id,
        sourceNodeId: target.source_node_id,
        catalogPath: (target.catalog_path || item.catalog_path).join(" / "),
        propertyKey: target.property_key,
        propertyTitle: target.property_title,
        elementSymbol: target.element_symbol,
        pointTitle: target.point_title || item.title,
      });
    },
    [navigate],
  );

  const askItem = useCallback(
    (item: StudentHomeVideoFeedItem) => {
      if (!canUseAssistant) return;
      navigateToAiChat(navigate, feedItemAssistantContext(item), "home");
    },
    [canUseAssistant, navigate],
  );

  return (
    <section className="learning-panel home-root-page" aria-label="实验视频首页">
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载实验视频" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {!loading && !error && feed?.message ? <div className={`home-feed-banner ${feed.status}`}>{feed.message}</div> : null}

      {!loading && !error && items.length ? (
        <div className="home-video-feed" aria-live="polite">
          {items.map((item) => (
            <HomeVideoFeedCard
              key={item.id}
              item={item}
              isActive={activeId === item.id}
              canUseAssistant={canUseAssistant}
              registerCard={registerCard}
              onOpen={openItem}
              onAsk={askItem}
            />
          ))}
        </div>
      ) : null}

      {!loading && !error && !items.length ? (
        <MobileEmptyState className="empty-learning-card" icon={<Video size={20} />}>
          <span>暂无已发布实验视频，可以先去学习页按元素分区浏览章节目录。</span>
        </MobileEmptyState>
      ) : null}
    </section>
  );
}
