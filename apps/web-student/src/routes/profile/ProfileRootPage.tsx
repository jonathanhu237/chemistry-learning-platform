import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { BarChart3, Bookmark, ClipboardList, LoaderCircle, LogOut, MessageSquarePlus, Trash2, UserRound, Video } from "lucide-react";
import {
  errorMessage,
  getStudentFavoriteVideoFeed,
  removeStudentVideoSave,
  studentMediaUrl,
  type StudentHomeVideoFeedItem,
  type StudentVideoSaveRequest,
} from "../../api";
import { getFeedbackCapability, getStudentProfilePresentation } from "../../app/preview/previewSandbox";
import { navigateToFeedback, navigateToPoint, navigateToProfileReports } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";

const PROFILE_FAVORITE_BATCH_SIZE = 20;

function favoriteSavePayload(item: StudentHomeVideoFeedItem): StudentVideoSaveRequest {
  return {
    placement_node_id: item.placement_node_id || item.target.placement_node_id || item.node_id,
    canonical_point_id: item.canonical_point_id || item.target.canonical_point_id,
    media_id: item.video.media_id,
    source: "profile_favorites",
  };
}

function sameFavoriteItem(left: StudentHomeVideoFeedItem, right: StudentHomeVideoFeedItem) {
  return (
    left.video.media_id === right.video.media_id &&
    (left.placement_node_id || left.target.placement_node_id || left.node_id) ===
      (right.placement_node_id || right.target.placement_node_id || right.node_id)
  );
}

export function ProfileRootPage() {
  const navigate = useNavigate();
  const runtime = useStudentRuntime();
  const profile = getStudentProfilePresentation(runtime);
  const feedbackCapability = getFeedbackCapability(runtime);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [favoriteItems, setFavoriteItems] = useState<StudentHomeVideoFeedItem[]>([]);
  const [favoriteNextCursor, setFavoriteNextCursor] = useState<string | null>(null);
  const [favoriteHasMore, setFavoriteHasMore] = useState(false);
  const [favoritesLoading, setFavoritesLoading] = useState(false);
  const [favoritesLoadingMore, setFavoritesLoadingMore] = useState(false);
  const [favoritesLoaded, setFavoritesLoaded] = useState(false);
  const [favoritesError, setFavoritesError] = useState("");
  const [favoritesStatus, setFavoritesStatus] = useState("");

  const loadFavorites = useCallback((cursor?: string | null) => {
    const append = Boolean(cursor);
    if (append) setFavoritesLoadingMore(true);
    else setFavoritesLoading(true);
    setFavoritesError("");
    getStudentFavoriteVideoFeed(PROFILE_FAVORITE_BATCH_SIZE, cursor)
      .then((response) => {
        setFavoriteItems((current) => (append ? [...current, ...response.items] : response.items));
        setFavoriteNextCursor(response.next_cursor || null);
        setFavoriteHasMore(response.has_more);
        setFavoritesLoaded(true);
      })
      .catch((requestError) => setFavoritesError(errorMessage(requestError)))
      .finally(() => {
        if (append) setFavoritesLoadingMore(false);
        else setFavoritesLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!favoritesOpen || favoritesLoaded || favoritesLoading) return;
    loadFavorites(null);
  }, [favoritesLoaded, favoritesLoading, favoritesOpen, loadFavorites]);

  const openFavoriteItem = useCallback(
    (item: StudentHomeVideoFeedItem) => {
      const target = item.target;
      const nodeId = target.node_id || item.placement_node_id || item.node_id;
      navigateToPoint(navigate, nodeId, {
        from: "profile",
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

  const removeFavorite = useCallback((item: StudentHomeVideoFeedItem) => {
    setFavoritesStatus("");
    void removeStudentVideoSave("favorite", favoriteSavePayload(item))
      .then(() => {
        setFavoriteItems((current) => current.filter((candidate) => !sameFavoriteItem(candidate, item)));
        setFavoriteNextCursor(null);
        setFavoriteHasMore(false);
        setFavoritesStatus(`已取消收藏：${item.title}`);
        loadFavorites(null);
      })
      .catch((requestError) => setFavoritesStatus(errorMessage(requestError)));
  }, [loadFavorites]);

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
      <button className="profile-entry-card" type="button" onClick={() => setFavoritesOpen((value) => !value)} aria-expanded={favoritesOpen}>
        <Bookmark size={20} />
        <span>
          <strong>我的收藏</strong>
          <small>查看保存在“我的”里的实验视频。</small>
        </span>
      </button>
      {favoritesOpen ? (
        <section className="profile-favorites-panel" aria-label="我的收藏">
          {favoritesLoading ? <LearningState icon={<LoaderCircle className="spin" size={21} />} text="正在加载收藏" /> : null}
          {favoritesError ? <LearningState icon={<Video size={21} />} text={favoritesError} /> : null}
          {!favoritesLoading && !favoritesError && favoriteItems.length ? (
            <div className="profile-favorite-list">
              {favoriteItems.map((item) => {
                const posterUrl = item.video.thumbnail_path ? studentMediaUrl(item.video.thumbnail_path) : "";
                return (
                  <article className="profile-favorite-item" key={item.instance_id}>
                    <button type="button" className="profile-favorite-open" onClick={() => openFavoriteItem(item)} aria-label={`打开收藏视频：${item.title}`}>
                      <span className="profile-favorite-thumb">
                        {posterUrl ? <img src={posterUrl} alt="" loading="lazy" /> : <Video size={20} />}
                      </span>
                      <span className="profile-favorite-copy">
                        <strong>{item.title}</strong>
                        <small>{(item.target.catalog_path || item.catalog_path).join(" · ")}</small>
                      </span>
                    </button>
                    <button type="button" className="profile-favorite-remove" onClick={() => removeFavorite(item)} aria-label={`取消收藏：${item.title}`}>
                      <Trash2 size={18} />
                    </button>
                  </article>
                );
              })}
            </div>
          ) : null}
          {!favoritesLoading && !favoritesError && !favoriteItems.length ? (
            <MobileEmptyState className="empty-learning-card" icon={<Bookmark size={20} />}>
              <span>还没有收藏的实验视频</span>
            </MobileEmptyState>
          ) : null}
          {favoritesStatus ? <div className="profile-favorites-status">{favoritesStatus}</div> : null}
          {!favoritesLoading && !favoritesError && favoriteHasMore && favoriteNextCursor ? (
            <MobileButton className="secondary-action full" type="button" variant="secondary" disabled={favoritesLoadingMore} onClick={() => loadFavorites(favoriteNextCursor)}>
              {favoritesLoadingMore ? <LoaderCircle className="spin" size={18} /> : <Bookmark size={18} />}
              <span>{favoritesLoadingMore ? "加载中" : "继续加载收藏"}</span>
            </MobileButton>
          ) : null}
        </section>
      ) : null}
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
