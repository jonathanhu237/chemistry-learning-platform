import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, FocusEvent, KeyboardEvent, MouseEvent, PointerEvent, TouchEvent } from "react";
import Artplayer from "artplayer";
import type { Option } from "artplayer";
import { Maximize2, Pause, Play, Video } from "lucide-react";

import sysuEmblemGreenUrl from "../../assets/sysu-logo/sysu-emblem-green.svg";
import sysuEmblemRedUrl from "../../assets/sysu-logo/sysu-emblem-red.svg";
import { BackArrowIcon } from "../../shared/mobile/BackArrowIcon";

const sysuProgressLogos = [sysuEmblemGreenUrl, sysuEmblemRedUrl] as const;
const chromeHideDelayMs = 2800;

type PlayerShellState = {
  isReady: boolean;
  isPlaying: boolean;
  isSeeking: boolean;
  isWaiting: boolean;
  hasError: boolean;
  currentTime: number;
  duration: number;
  loadedRatio: number;
  isFullscreenWeb: boolean;
};

const initialShellState: PlayerShellState = {
  isReady: false,
  isPlaying: false,
  isSeeking: false,
  isWaiting: false,
  hasError: false,
  currentTime: 0,
  duration: 0,
  loadedRatio: 0,
  isFullscreenWeb: false,
};

function randomSysuProgressLogo() {
  return sysuProgressLogos[Math.floor(Math.random() * sysuProgressLogos.length)];
}

function clamp(value: number, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

function formatPlayerTime(value: number) {
  if (!Number.isFinite(value) || value < 0) return "--:--";
  const seconds = Math.floor(value);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}

function mediaDuration(art: Artplayer) {
  const videoDuration = art.video.duration;
  if (Number.isFinite(videoDuration) && videoDuration > 0) return videoDuration;
  const playerDuration = art.duration;
  return Number.isFinite(playerDuration) && playerDuration > 0 ? playerDuration : 0;
}

function loadedRatio(video: HTMLVideoElement, duration: number) {
  if (!duration || !video.buffered?.length) return 0;
  let loadedEnd = 0;
  for (let index = 0; index < video.buffered.length; index += 1) {
    try {
      loadedEnd = Math.max(loadedEnd, video.buffered.end(index));
    } catch {
      return 0;
    }
  }
  return clamp(loadedEnd / duration);
}

function readShellState(art: Artplayer, isSeeking: boolean): PlayerShellState {
  const duration = mediaDuration(art);
  const currentTime = Number.isFinite(art.video.currentTime) ? art.video.currentTime : 0;
  const isPlaying = Boolean(art.playing || (!art.video.paused && !art.video.ended));

  return {
    isReady: Boolean(art.isReady || duration > 0 || art.video.readyState > 0),
    isPlaying,
    isSeeking,
    isWaiting: art.video.readyState > 0 && art.video.readyState < 3 && isPlaying,
    hasError: Boolean(art.video.error),
    currentTime: duration ? clamp(currentTime, 0, duration) : Math.max(0, currentTime),
    duration,
    loadedRatio: loadedRatio(art.video, duration),
    isFullscreenWeb: Boolean(art.fullscreenWeb),
  };
}

function progressPercent(currentTime: number, duration: number) {
  if (!duration) return 0;
  return clamp(currentTime / duration) * 100;
}

export function PointVideoPlayer({
  src,
  poster,
  emptyReason,
  onBack,
}: {
  src?: string | null;
  poster?: string | null;
  emptyReason?: string | null;
  onBack: () => void;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const artRef = useRef<Artplayer | null>(null);
  const onBackRef = useRef(onBack);
  const progressLogoUrl = useMemo(() => randomSysuProgressLogo(), [src]);
  const hideTimerRef = useRef<number | null>(null);
  const seekingRef = useRef(false);
  const seekingPointerIdRef = useRef<number | null>(null);
  const [isChromeActive, setIsChromeActive] = useState(false);
  const [shellState, setShellState] = useState<PlayerShellState>(initialShellState);

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current !== null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const syncShellState = useCallback((art = artRef.current) => {
    if (!art) return;
    setShellState(readShellState(art, seekingRef.current));
  }, []);

  const scheduleChromeHide = useCallback(() => {
    clearHideTimer();
    const art = artRef.current;
    if (!art || seekingRef.current || art.video.paused || art.video.ended) return;
    hideTimerRef.current = window.setTimeout(() => {
      if (!seekingRef.current) {
        setIsChromeActive(false);
      }
    }, chromeHideDelayMs);
  }, [clearHideTimer]);

  const activateChrome = useCallback(
    ({ hold = false }: { hold?: boolean } = {}) => {
      setIsChromeActive(true);
      clearHideTimer();
      if (!hold) {
        scheduleChromeHide();
      }
    },
    [clearHideTimer, scheduleChromeHide],
  );

  useEffect(() => {
    onBackRef.current = onBack;
  }, [onBack]);

  useEffect(() => {
    return () => clearHideTimer();
  }, [clearHideTimer]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !src) return undefined;

    seekingRef.current = false;
    seekingPointerIdRef.current = null;
    setIsChromeActive(false);
    setShellState(initialShellState);
    clearHideTimer();

    const options: Option = {
      container,
      url: src,
      poster: poster || undefined,
      theme: "#006934",
      volume: 0.7,
      muted: true,
      autoplay: true,
      autoSize: false,
      backdrop: false,
      fullscreen: false,
      fullscreenWeb: false,
      miniProgressBar: false,
      setting: false,
      hotkey: true,
      lock: false,
      playsInline: true,
      gesture: true,
      fastForward: true,
      playbackRate: false,
      mutex: true,
      moreVideoAttr: {
        preload: "metadata",
        controls: false,
        playsInline: true,
      },
    };

    const art = new Artplayer(options);
    artRef.current = art;
    art.video.controls = false;
    art.video.removeAttribute("controls");
    art.video.setAttribute("playsinline", "");
    art.video.setAttribute("webkit-playsinline", "");

    const sync = () => syncShellState(art);
    const syncAndKeepActive = () => {
      syncShellState(art);
      setIsChromeActive(true);
      clearHideTimer();
    };
    const syncAndScheduleHide = () => {
      syncShellState(art);
      scheduleChromeHide();
    };
    const onWaiting = () => {
      setShellState((current) => ({ ...current, isWaiting: true }));
    };
    const onReady = () => {
      syncShellState(art);
      void art.play().catch(() => {
        syncShellState(art);
        setIsChromeActive(true);
        clearHideTimer();
      });
    };

    art.on("ready", onReady);
    art.on("video:loadedmetadata", sync);
    art.on("video:durationchange", sync);
    art.on("video:timeupdate", sync);
    art.on("video:progress", sync);
    art.on("video:seeked", sync);
    art.on("video:seeking", sync);
    art.on("video:waiting", onWaiting);
    art.on("video:playing", syncAndScheduleHide);
    art.on("video:play", syncAndScheduleHide);
    art.on("video:pause", syncAndKeepActive);
    art.on("video:error", syncAndKeepActive);
    art.on("seek", sync);
    art.on("fullscreenWeb", sync);
    syncShellState(art);

    return () => {
      art.off("ready", onReady);
      art.off("video:loadedmetadata", sync);
      art.off("video:durationchange", sync);
      art.off("video:timeupdate", sync);
      art.off("video:progress", sync);
      art.off("video:seeked", sync);
      art.off("video:seeking", sync);
      art.off("video:waiting", onWaiting);
      art.off("video:playing", syncAndScheduleHide);
      art.off("video:play", syncAndScheduleHide);
      art.off("video:pause", syncAndKeepActive);
      art.off("video:error", syncAndKeepActive);
      art.off("seek", sync);
      art.off("fullscreenWeb", sync);
      clearHideTimer();
      art.destroy(false);
      if (artRef.current === art) {
        artRef.current = null;
      }
      seekingRef.current = false;
      seekingPointerIdRef.current = null;
      setIsChromeActive(false);
      setShellState(initialShellState);
    };
  }, [clearHideTimer, poster, scheduleChromeHide, src, syncShellState]);

  const shouldIgnoreShellActivation = (target: EventTarget | null) =>
    target instanceof Element && target.closest(".point-youtube-control, .point-youtube-progress-hit");

  const handleShellPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (shouldIgnoreShellActivation(event.target)) {
      return;
    }
    activateChrome();
  };

  const handleShellTouchStart = (event: TouchEvent<HTMLDivElement>) => {
    if (shouldIgnoreShellActivation(event.target)) {
      return;
    }
    activateChrome();
  };

  const handleShellClick = (event: MouseEvent<HTMLDivElement>) => {
    if (shouldIgnoreShellActivation(event.target)) {
      return;
    }
    activateChrome();
  };

  const handleBackClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    clearHideTimer();
    onBackRef.current();
  };

  const handleTogglePlay = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const art = artRef.current;
    if (!art) return;
    activateChrome({ hold: true });
    if (shellState.isPlaying) {
      art.pause();
      syncShellState(art);
      return;
    }
    void art.play().then(() => syncShellState(art)).catch(() => {
      setIsChromeActive(true);
      syncShellState(art);
    });
  };

  const handleFullscreen = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    const art = artRef.current;
    if (!art) return;
    activateChrome();
    art.fullscreenWeb = !art.fullscreenWeb;
    syncShellState(art);
  };

  const seekFromClientX = useCallback(
    (clientX: number, target: HTMLElement) => {
      const art = artRef.current;
      if (!art || !shellState.duration) return;
      const rect = target.getBoundingClientRect();
      if (!rect.width) return;
      const ratio = clamp((clientX - rect.left) / rect.width);
      const nextTime = ratio * shellState.duration;
      art.seek = nextTime;
      setShellState((current) => ({
        ...current,
        isSeeking: true,
        currentTime: nextTime,
      }));
    },
    [shellState.duration],
  );

  const handleProgressPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    seekingRef.current = true;
    seekingPointerIdRef.current = event.pointerId;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    activateChrome({ hold: true });
    seekFromClientX(event.clientX, event.currentTarget);
  };

  const handleProgressPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!seekingRef.current || seekingPointerIdRef.current !== event.pointerId) return;
    event.preventDefault();
    event.stopPropagation();
    seekFromClientX(event.clientX, event.currentTarget);
  };

  const finishProgressSeek = (event: PointerEvent<HTMLDivElement>) => {
    if (seekingPointerIdRef.current !== event.pointerId) return;
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    seekingRef.current = false;
    seekingPointerIdRef.current = null;
    setShellState((current) => ({ ...current, isSeeking: false }));
    syncShellState();
    scheduleChromeHide();
  };

  const handleProgressKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const art = artRef.current;
    if (!art || !shellState.duration) return;
    const step = event.shiftKey ? 10 : 5;
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    event.stopPropagation();
    const direction = event.key === "ArrowRight" ? 1 : -1;
    const nextTime = clamp((shellState.currentTime + direction * step) / shellState.duration) * shellState.duration;
    art.seek = nextTime;
    setShellState((current) => ({ ...current, currentTime: nextTime }));
    activateChrome({ hold: true });
  };

  const handleShellFocus = () => {
    activateChrome({ hold: true });
  };

  const handleShellBlur = (event: FocusEvent<HTMLDivElement>) => {
    const nextTarget = event.relatedTarget;
    if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) return;
    scheduleChromeHide();
  };

  if (!src) {
    return (
      <section className="point-art-player point-art-player-empty" aria-label="点位视频播放器">
        <button type="button" className="point-player-empty-back" onClick={onBack} aria-label="返回">
          <BackArrowIcon className="point-player-back-icon" />
        </button>
        <div className="video-placeholder">
          <Video size={34} />
          <strong>暂无可播放视频</strong>
          <span>{emptyReason || "教师尚未绑定可播放内容，完成绑定后学生可在这里观看。"}</span>
        </div>
      </section>
    );
  }

  const playedPercent = progressPercent(shellState.currentTime, shellState.duration);
  const loadedPercent = shellState.loadedRatio * 100;
  const shellClassName = [
    "point-youtube-shell",
    isChromeActive ? "point-youtube-shell-active" : "",
    shellState.isPlaying ? "point-youtube-shell-playing" : "point-youtube-shell-paused",
    shellState.isSeeking ? "point-youtube-shell-seeking" : "",
    shellState.isWaiting ? "point-youtube-shell-waiting" : "",
    shellState.hasError ? "point-youtube-shell-error" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section
      className="point-art-player"
      aria-label="点位视频播放器"
      style={{ "--point-player-logo": `url("${progressLogoUrl}")` } as CSSProperties}
    >
      <div ref={containerRef} className="point-art-player-mount" />
      <div
        className={shellClassName}
        onBlurCapture={handleShellBlur}
        onClick={handleShellClick}
        onFocusCapture={handleShellFocus}
        onPointerDown={handleShellPointerDown}
        onTouchStart={handleShellTouchStart}
      >
        <div className="point-youtube-inactive-progress" aria-hidden="true">
          <span className="point-youtube-progress-loaded" style={{ width: `${loadedPercent}%` }} />
          <span className="point-youtube-progress-played" style={{ width: `${playedPercent}%` }} />
        </div>

        <div className="point-youtube-controls">
          <button
            type="button"
            className="point-youtube-control point-youtube-back"
            onClick={handleBackClick}
            aria-label="返回"
          >
            <BackArrowIcon className="point-player-back-icon" />
          </button>

          <button
            type="button"
            className="point-youtube-control point-youtube-play"
            onClick={handleTogglePlay}
            aria-label={shellState.isPlaying ? "暂停" : "播放"}
          >
            {shellState.isPlaying ? <Pause size={36} fill="currentColor" /> : <Play size={40} fill="currentColor" />}
          </button>

          <div className="point-youtube-bottom">
            <span className="point-youtube-time-capsule" aria-label="播放时间">
              {formatPlayerTime(shellState.currentTime)}
              <span aria-hidden="true"> / </span>
              {formatPlayerTime(shellState.duration)}
            </span>
            <button
              type="button"
              className="point-youtube-control point-youtube-fullscreen"
              onClick={handleFullscreen}
              aria-label={shellState.isFullscreenWeb ? "退出全屏" : "全屏"}
            >
              <Maximize2 size={25} />
            </button>
            <div
              className="point-youtube-progress-hit"
              role="slider"
              tabIndex={0}
              aria-label="播放进度"
              aria-valuemin={0}
              aria-valuemax={Math.round(shellState.duration)}
              aria-valuenow={Math.round(shellState.currentTime)}
              aria-disabled={!shellState.duration}
              onKeyDown={handleProgressKeyDown}
              onPointerCancel={finishProgressSeek}
              onPointerDown={handleProgressPointerDown}
              onPointerMove={handleProgressPointerMove}
              onPointerUp={finishProgressSeek}
            >
              <div className="point-youtube-active-progress" aria-hidden="true">
                <span className="point-youtube-progress-track" />
                <span className="point-youtube-progress-loaded" style={{ width: `${loadedPercent}%` }} />
                <span className="point-youtube-progress-played" style={{ width: `${playedPercent}%` }} />
                <span className="point-youtube-progress-thumb" style={{ left: `${playedPercent}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
