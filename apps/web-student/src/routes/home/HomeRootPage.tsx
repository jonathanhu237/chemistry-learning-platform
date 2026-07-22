import { type FormEvent, type RefObject, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { FlaskConical, LoaderCircle, Search, Sparkles, Video, X } from "lucide-react";
import {
  errorMessage,
  getStudentHomeVideoFeed,
  studentMediaUrl,
  type StudentHomeVideoFeedItem,
  type StudentHomeVideoFeedReason,
  type StudentHomeVideoFeedResponse,
} from "../../api";
import { navigateToPoint } from "../../app/router/navigation";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";

const reasonLabels: Record<StudentHomeVideoFeedReason, string> = {
  catalog: "目录实验",
  recommended: "推荐观看",
};

const genericHomeMetadata = new Set(["experiment video", "video point", "实验视频"]);
const homeMetadataSeparator = " · ";
const HOME_FEED_BATCH_SIZE = 20;

function uniqueHomeFeedItems(items: StudentHomeVideoFeedItem[]) {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.instance_id)) return false;
    seen.add(item.instance_id);
    return true;
  });
}

function isStaleHomeFeedCursor(error: unknown) {
  return typeof error === "object" && error !== null && "status" in error && (error as { status?: unknown }).status === 400;
}

type HomeFeedCandidate = {
  id: string;
  ratio: number;
  centerDistance: number;
};

function pushHomeMetadataPart(parts: string[], value: string | null | undefined, title: string, options?: { skipGeneric?: boolean }) {
  const part = value?.trim();
  if (!part) return;
  const normalized = part.toLocaleLowerCase();
  if (part === title.trim()) return;
  if (options?.skipGeneric && genericHomeMetadata.has(normalized)) return;
  const duplicate = parts.some((current) => current.toLocaleLowerCase() === normalized);
  if (!duplicate) parts.push(part);
}

function buildHomeVideoMetadata(item: StudentHomeVideoFeedItem): string {
  const parts: string[] = [];
  item.badges.forEach((badge) => pushHomeMetadataPart(parts, badge, item.title, { skipGeneric: true }));
  pushHomeMetadataPart(parts, item.snippet, item.title);

  const path = item.target.catalog_path?.length ? item.target.catalog_path : item.catalog_path;
  path.forEach((part, index) => {
    if (index === path.length - 1 && part.trim() === item.title.trim()) return;
    pushHomeMetadataPart(parts, part, item.title);
  });

  if (!parts.length) pushHomeMetadataPart(parts, reasonLabels[item.reason], item.title);
  return parts.slice(0, 3).join(homeMetadataSeparator);
}

function homePreviewViewportBounds() {
  const visualTop = window.visualViewport?.offsetTop ?? 0;
  const visualHeight = window.visualViewport?.height || window.innerHeight || document.documentElement.clientHeight || 0;
  let top = visualTop;
  let bottom = visualTop + visualHeight;
  const headerRect = document.querySelector<HTMLElement>(".student-app-shell.root-home .student-app-header")?.getBoundingClientRect();
  const bottomNavRect = document.querySelector<HTMLElement>(".student-bottom-nav")?.getBoundingClientRect();

  if (headerRect && headerRect.bottom > top && headerRect.bottom < bottom) top = headerRect.bottom;
  if (bottomNavRect && bottomNavRect.top > top && bottomNavRect.top < bottom) bottom = bottomNavRect.top;
  if (bottom <= top) {
    top = visualTop;
    bottom = visualTop + visualHeight;
  }
  return { top, bottom, center: (top + bottom) / 2 };
}

function homeFeedCandidateForNode(id: string, node: HTMLElement, viewport: ReturnType<typeof homePreviewViewportBounds>): HomeFeedCandidate | null {
  const rect = node.getBoundingClientRect();
  const height = Math.max(1, rect.height);
  const visibleHeight = Math.max(0, Math.min(rect.bottom, viewport.bottom) - Math.max(rect.top, viewport.top));
  if (!visibleHeight && (rect.bottom <= viewport.top || rect.top >= viewport.bottom)) return null;
  return {
    id,
    ratio: Math.min(1, visibleHeight / height),
    centerDistance: Math.abs((rect.top + rect.bottom) / 2 - viewport.center),
  };
}

function rankHomeFeedCandidates(left: HomeFeedCandidate, right: HomeFeedCandidate) {
  const ratioDelta = right.ratio - left.ratio;
  if (Math.abs(ratioDelta) > 0.08) return ratioDelta;
  return left.centerDistance - right.centerDistance;
}

function clampHomeProgress(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

function homeMediaDuration(video: HTMLVideoElement) {
  const duration = video.duration;
  return Number.isFinite(duration) && duration > 0 ? duration : 0;
}

function homeLoadedRatio(video: HTMLVideoElement, duration: number) {
  if (!duration || !video.buffered?.length) return 0;
  let loadedEnd = 0;
  for (let index = 0; index < video.buffered.length; index += 1) {
    try {
      loadedEnd = Math.max(loadedEnd, video.buffered.end(index));
    } catch {
      return 0;
    }
  }
  return clampHomeProgress(loadedEnd / duration);
}

function readHomeVideoProgress(video: HTMLVideoElement) {
  const duration = homeMediaDuration(video);
  const currentTime = Number.isFinite(video.currentTime) ? video.currentTime : 0;
  return {
    playedPercent: duration ? clampHomeProgress(currentTime / duration) * 100 : 0,
    loadedPercent: homeLoadedRatio(video, duration) * 100,
  };
}

function useHomeVideoProgress(videoRef: RefObject<HTMLVideoElement | null>, enabled: boolean) {
  const [progress, setProgress] = useState({ playedPercent: 0, loadedPercent: 0 });

  useEffect(() => {
    if (!enabled) {
      setProgress({ playedPercent: 0, loadedPercent: 0 });
      return undefined;
    }
    const video = videoRef.current;
    if (!video) return undefined;

    const sync = () => setProgress(readHomeVideoProgress(video));
    sync();

    const events = ["loadedmetadata", "durationchange", "timeupdate", "progress", "seeking", "seeked", "play"] as const;
    events.forEach((eventName) => video.addEventListener(eventName, sync));
    return () => events.forEach((eventName) => video.removeEventListener(eventName, sync));
  }, [enabled, videoRef]);

  return progress;
}

function useActiveFeedItem(items: StudentHomeVideoFeedItem[]) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeIdRef = useRef<string | null>(null);
  const itemIdsRef = useRef<string[]>([]);
  const nodesRef = useRef(new Map<string, HTMLElement>());
  const observerRef = useRef<IntersectionObserver | null>(null);
  const frameRef = useRef<number | null>(null);

  const setStableActiveId = useCallback((next: string | null) => {
    activeIdRef.current = next;
    setActiveId((current) => (current === next ? current : next));
  }, []);

  const updateActive = useCallback(() => {
    const itemIds = itemIdsRef.current;
    if (!itemIds.length) {
      setStableActiveId(null);
      return;
    }

    const itemSet = new Set(itemIds);
    const viewport = homePreviewViewportBounds();
    const candidates = Array.from(nodesRef.current.entries())
      .filter(([id]) => itemSet.has(id))
      .map(([id, node]) => homeFeedCandidateForNode(id, node, viewport))
      .filter((candidate): candidate is HomeFeedCandidate => Boolean(candidate));

    if (!candidates.length) {
      const current = activeIdRef.current;
      setStableActiveId(current && itemSet.has(current) ? current : itemIds[0]);
      return;
    }

    candidates.sort(rankHomeFeedCandidates);
    const best = candidates[0];
    const current = activeIdRef.current;
    const currentCandidate = candidates.find((candidate) => candidate.id === current);
    if (
      currentCandidate &&
      currentCandidate.ratio >= 0.24 &&
      best.id !== current &&
      best.ratio < currentCandidate.ratio + 0.18 &&
      best.centerDistance > currentCandidate.centerDistance - 36
    ) {
      return;
    }
    setStableActiveId(best.id);
  }, [setStableActiveId]);

  const scheduleActiveUpdate = useCallback(() => {
    if (frameRef.current !== null) return;
    frameRef.current = window.requestAnimationFrame(() => {
      frameRef.current = null;
      updateActive();
    });
  }, [updateActive]);

  const registerCard = useCallback(
    (id: string, node: HTMLElement | null) => {
      const previous = nodesRef.current.get(id);
      if (previous && observerRef.current) observerRef.current.unobserve(previous);
      if (!node) {
        nodesRef.current.delete(id);
        scheduleActiveUpdate();
        return;
      }
      nodesRef.current.set(id, node);
      if (observerRef.current) observerRef.current.observe(node);
      scheduleActiveUpdate();
    },
    [scheduleActiveUpdate],
  );

  useEffect(() => {
    itemIdsRef.current = items.map((item) => item.instance_id);
    if (!items.length) {
      setStableActiveId(null);
      return;
    }
    const current = activeIdRef.current;
    if (!current || !itemIdsRef.current.includes(current)) setStableActiveId(items[0].instance_id);
    scheduleActiveUpdate();
  }, [items, scheduleActiveUpdate, setStableActiveId]);

  useEffect(() => {
    if (!items.length || !("IntersectionObserver" in window)) return undefined;

    const observer = new IntersectionObserver(
      () => scheduleActiveUpdate(),
      {
        root: null,
        rootMargin: "-10% 0px -18% 0px",
        threshold: [0, 0.12, 0.25, 0.42, 0.6, 0.82, 1],
      },
    );

    observerRef.current = observer;
    nodesRef.current.forEach((node) => observer.observe(node));

    return () => {
      observer.disconnect();
      observerRef.current = null;
    };
  }, [items, scheduleActiveUpdate]);

  useEffect(() => {
    window.addEventListener("scroll", scheduleActiveUpdate, { passive: true });
    window.addEventListener("resize", scheduleActiveUpdate);
    window.addEventListener("orientationchange", scheduleActiveUpdate);
    window.visualViewport?.addEventListener("scroll", scheduleActiveUpdate);
    window.visualViewport?.addEventListener("resize", scheduleActiveUpdate);
    return () => {
      window.removeEventListener("scroll", scheduleActiveUpdate);
      window.removeEventListener("resize", scheduleActiveUpdate);
      window.removeEventListener("orientationchange", scheduleActiveUpdate);
      window.visualViewport?.removeEventListener("scroll", scheduleActiveUpdate);
      window.visualViewport?.removeEventListener("resize", scheduleActiveUpdate);
    };
  }, [scheduleActiveUpdate]);

  useEffect(
    () => () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    },
    [],
  );

  return { activeId, registerCard };
}

type HomeVideoFeedCardProps = {
  item: StudentHomeVideoFeedItem;
  isActive: boolean;
  registerCard: (id: string, node: HTMLElement | null) => void;
  onOpen: (item: StudentHomeVideoFeedItem) => void;
};

function HomeVideoFeedCard({ item, isActive, registerCard, onOpen }: HomeVideoFeedCardProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaUrl = item.video.stream_path ? studentMediaUrl(item.video.stream_path) : "";
  const posterUrl = item.video.thumbnail_path ? studentMediaUrl(item.video.thumbnail_path) : "";
  const metadata = buildHomeVideoMetadata(item);
  const titleId = `home-video-title-${item.instance_id.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
  const progress = useHomeVideoProgress(videoRef, isActive && Boolean(mediaUrl));

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

  return (
    <article
      ref={(node) => registerCard(item.instance_id, node)}
      data-feed-id={item.instance_id}
      className={`home-video-card${isActive ? " is-active" : ""}`}
      aria-labelledby={titleId}
    >
      <div className="home-video-media">
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
        </button>
        {item.reason === "recommended" ? (
          <span className="home-video-recommendation-badge">
            <Sparkles size={13} aria-hidden="true" />
            老师推荐
          </span>
        ) : null}
        <div className="home-video-inactive-progress" aria-hidden="true">
          <span className="home-video-progress-loaded" style={{ width: `${progress.loadedPercent}%` }} />
          <span className="home-video-progress-played" style={{ width: `${progress.playedPercent}%` }} />
        </div>
      </div>

      <div className="home-video-body">
        <button
          type="button"
          className="home-video-text-button"
          onClick={() => onOpen(item)}
          aria-label={`打开实验详情：${item.title}`}
        >
          <h2 id={titleId}>{item.title}</h2>
          {metadata ? <p className="home-video-metadata">{metadata}</p> : null}
        </button>
      </div>
    </article>
  );
}

export function HomeRootPage() {
  const navigate = useNavigate();
  const [draftQuery, setDraftQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [items, setItems] = useState<StudentHomeVideoFeedItem[]>([]);
  const [feedMeta, setFeedMeta] = useState<Pick<StudentHomeVideoFeedResponse, "status" | "message" | "query" | "pool_size"> | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");
  const [feedNotice, setFeedNotice] = useState("");
  const [reloadToken, setReloadToken] = useState(0);
  const queryRef = useRef(activeQuery);
  const requestSeqRef = useRef(0);
  const loadingMoreRef = useRef(false);
  const staleCursorRecoveryRef = useRef(false);
  const { activeId, registerCard } = useActiveFeedItem(items);

  useEffect(() => {
    const requestId = requestSeqRef.current + 1;
    requestSeqRef.current = requestId;
    queryRef.current = activeQuery;
    const recoveringStaleCursor = staleCursorRecoveryRef.current;
    let cancelled = false;
    loadingMoreRef.current = false;
    setLoadingInitial(true);
    setLoadingMore(false);
    setError("");
    setItems([]);
    setNextCursor(null);
    setHasMore(false);
    setFeedMeta(null);
    getStudentHomeVideoFeed({ limit: HOME_FEED_BATCH_SIZE, q: activeQuery })
      .then((response) => {
        if (cancelled || requestSeqRef.current !== requestId || queryRef.current !== activeQuery) return;
        setItems(uniqueHomeFeedItems(response.items));
        setNextCursor(response.next_cursor || null);
        setHasMore(response.has_more);
        setFeedMeta({
          status: response.status,
          message: response.message,
          query: response.query,
          pool_size: response.pool_size,
        });
        if (recoveringStaleCursor) {
          staleCursorRecoveryRef.current = false;
          setFeedNotice("视频列表已更新，已从第一页重新加载。");
        } else {
          setFeedNotice("");
        }
      })
      .catch((requestError) => {
        if (!cancelled && requestSeqRef.current === requestId) {
          if (recoveringStaleCursor) staleCursorRecoveryRef.current = false;
          setFeedNotice("");
          setError(
            recoveringStaleCursor
              ? `视频列表已更新，但重新加载失败：${errorMessage(requestError)}`
              : errorMessage(requestError),
          );
        }
      })
      .finally(() => {
        if (!cancelled && requestSeqRef.current === requestId) setLoadingInitial(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeQuery, reloadToken]);

  const retryFirstPage = useCallback(() => {
    staleCursorRecoveryRef.current = false;
    setFeedNotice("");
    setReloadToken((current) => current + 1);
  }, []);

  const loadMore = useCallback(() => {
    if (loadingMoreRef.current || loadingInitial || !hasMore || !nextCursor) return;
    const requestId = requestSeqRef.current + 1;
    requestSeqRef.current = requestId;
    const query = activeQuery;
    const cursor = nextCursor;
    loadingMoreRef.current = true;
    setLoadingMore(true);
    setError("");
    getStudentHomeVideoFeed({ limit: HOME_FEED_BATCH_SIZE, q: query, cursor })
      .then((response) => {
        if (requestSeqRef.current !== requestId || queryRef.current !== query) return;
        setItems((current) => uniqueHomeFeedItems([...current, ...response.items]));
        setNextCursor(response.next_cursor || null);
        setHasMore(response.has_more);
        setFeedMeta({
          status: response.status,
          message: response.message,
          query: response.query,
          pool_size: response.pool_size,
        });
      })
      .catch((requestError) => {
        if (requestSeqRef.current !== requestId || queryRef.current !== query) return;
        if (isStaleHomeFeedCursor(requestError)) {
          staleCursorRecoveryRef.current = true;
          setNextCursor(null);
          setHasMore(false);
          setFeedNotice("视频列表已更新，正在从第一页重新加载……");
          setReloadToken((current) => current + 1);
          return;
        }
        setError(errorMessage(requestError));
      })
      .finally(() => {
        if (requestSeqRef.current === requestId) {
          loadingMoreRef.current = false;
          setLoadingMore(false);
        }
      });
  }, [activeQuery, hasMore, loadingInitial, nextCursor]);

  const submitSearch = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const nextQuery = draftQuery.trim();
      if (nextQuery !== activeQuery) {
        staleCursorRecoveryRef.current = false;
        setFeedNotice("");
        setActiveQuery(nextQuery);
      }
    },
    [activeQuery, draftQuery],
  );

  const clearSearch = useCallback(() => {
    staleCursorRecoveryRef.current = false;
    setFeedNotice("");
    setDraftQuery("");
    setActiveQuery("");
  }, []);

  const openItem = useCallback(
    (item: StudentHomeVideoFeedItem) => {
      const target = item.target;
      const nodeId = target.node_id || item.placement_node_id || item.node_id;
      navigateToPoint(navigate, nodeId, {
        from: "home",
        chapterId: target.chapter_id || item.chapter_id,
        sourceNodeId: target.source_node_id,
        catalogPath: (target.catalog_path || item.catalog_path).join(" / "),
        pointTitle: target.point_title || item.title,
      });
    },
    [navigate],
  );

  return (
    <section className="learning-panel home-root-page" aria-label="实验视频首页">
      <form className="home-feed-search" role="search" aria-label="搜索实验视频" onSubmit={submitSearch}>
        <label className="home-feed-search-field">
          <Search size={18} aria-hidden="true" />
          <input
            type="search"
            value={draftQuery}
            maxLength={120}
            placeholder="搜索实验、现象或试剂"
            aria-label="搜索实验视频"
            onChange={(event) => setDraftQuery(event.target.value)}
          />
          {draftQuery || activeQuery ? (
            <button type="button" className="home-feed-search-clear" aria-label="清空实验视频搜索" onClick={clearSearch}>
              <X size={17} />
            </button>
          ) : null}
        </label>
        <button type="submit" className="home-feed-search-submit" disabled={loadingInitial && draftQuery.trim() === activeQuery}>
          搜索
        </button>
      </form>

      {loadingInitial ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载实验视频" /> : null}
      {!loadingInitial && feedNotice ? <div className="home-feed-banner" role="status">{feedNotice}</div> : null}
      {!loadingInitial && error && !items.length ? (
        <div className="home-feed-retry">
          <LearningState icon={<FlaskConical size={23} />} text={error} />
          <button type="button" className="home-feed-search-submit" onClick={retryFirstPage}>重新加载</button>
        </div>
      ) : null}
      {!loadingInitial && error && items.length ? (
        <div className="home-feed-banner error" role="alert">
          <span>{error}</span>
          <button type="button" className="home-feed-search-submit" onClick={nextCursor ? loadMore : retryFirstPage}>重试</button>
        </div>
      ) : null}
      {!loadingInitial && !error && activeQuery && feedMeta ? (
        <div className="home-feed-result-summary" aria-live="polite">
          <span>“{feedMeta.query || activeQuery}”</span>
          <strong>{feedMeta.pool_size} 个结果</strong>
        </div>
      ) : null}

      {!loadingInitial && items.length ? (
        <div className="home-video-feed" aria-live="polite">
          {items.map((item) => (
            <HomeVideoFeedCard
              key={item.instance_id}
              item={item}
              isActive={activeId === item.instance_id}
              registerCard={registerCard}
              onOpen={openItem}
            />
          ))}
        </div>
      ) : null}

      {!loadingInitial && items.length ? (
        <div className="home-feed-pagination" aria-live="polite">
          {hasMore && nextCursor ? (
            <button type="button" onClick={loadMore} disabled={loadingMore}>
              {loadingMore ? <LoaderCircle className="spin" size={17} /> : null}
              <span>{loadingMore ? "正在加载" : "继续加载"}</span>
            </button>
          ) : (
            <span>已显示全部实验视频</span>
          )}
        </div>
      ) : null}

      {!loadingInitial && !error && !items.length ? (
        <MobileEmptyState className="empty-learning-card" icon={<Video size={20} />}>
          <span>{activeQuery ? `没有找到与“${feedMeta?.query || activeQuery}”匹配的实验视频，换个关键词试试。` : feedMeta?.message || "暂时没有可学习的实验视频。"}</span>
        </MobileEmptyState>
      ) : null}
    </section>
  );
}
