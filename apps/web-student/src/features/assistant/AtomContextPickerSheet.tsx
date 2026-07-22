import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Atom, ChevronRight, FolderOpen, LoaderCircle, Search, X } from "lucide-react";

import type {
  StudentCatalogBreadcrumb,
  StudentCatalogChapterResponse,
  StudentCatalogNodeCard,
  StudentCatalogNodeResponse,
  StudentLearningPageResponse,
  StudentLearningProfileSummary,
  StudentHomeVideoFeedItem,
  StudentHomeVideoFeedResponse,
} from "../../api";
import {
  errorMessage,
  getStudentCatalogNode,
  getStudentChapterCatalog,
  getStudentHomeVideoFeed,
  getStudentLearningPage,
} from "../../api";
import { formatChapterEntryTitle } from "../learning/learningFormat";
import {
  assistantContextFromCatalogNode,
  assistantContextFromHomeFeedItem,
  isBindableHomeFeedItem,
  type AssistantContext,
} from "./assistantContext";

const PICKER_SEARCH_DEBOUNCE_MS = 240;
const PICKER_SEARCH_LIMIT = 12;

function contextIdentity(context: AssistantContext | null | undefined): string {
  if (!context) return "";
  return [context.point_node_id, context.source_node_id, context.chapter_id, context.context_title].filter(Boolean).join("::");
}

function catalogNodeMatchesContext(node: StudentCatalogNodeCard, context: AssistantContext | null | undefined): boolean {
  if (!context) return false;
  const selectedIds = [context.point_node_id, context.source_node_id].filter((id): id is string => Boolean(id));
  if (selectedIds.length) {
    return [node.node_id, node.placement_node_id, node.canonical_point_id].some((id) => Boolean(id && selectedIds.includes(id)));
  }
  const nodeTitle = node.canonical_point_title || node.title;
  return Boolean(nodeTitle && context.context_title && nodeTitle === context.context_title && (!context.chapter_id || node.chapter_id === context.chapter_id));
}

function profileTitle(profile: StudentLearningProfileSummary): string {
  return formatChapterEntryTitle(profile) || profile.title || profile.subtitle || profile.chapter_id;
}

function compactResultPath(item: StudentHomeVideoFeedItem, profiles: StudentLearningProfileSummary[] = []): string {
  const target = item.target;
  const path = (target.catalog_path?.length ? target.catalog_path : item.catalog_path).map((part) => part.trim()).filter(Boolean);
  const profile = profiles.find((entry) => entry.chapter_id === (target.chapter_id || item.chapter_id));
  const chapterTitle = profile ? profileTitle(profile) : target?.chapter_id || "";
  const fullPath: string[] = [];
  for (const part of [chapterTitle, ...path]) {
    const text = part.trim();
    if (!text || fullPath[fullPath.length - 1] === text) continue;
    fullPath.push(text);
  }
  if (fullPath.length) return fullPath.join(" / ");
  return item.summary;
}

function pointResultItems(response: StudentHomeVideoFeedResponse | null): StudentHomeVideoFeedItem[] {
  if (!response) return [];
  const seen = new Set<string>();
  const items: StudentHomeVideoFeedItem[] = [];
  for (const item of response.items) {
    if (!isBindableHomeFeedItem(item)) continue;
    const key = item.target.node_id || item.target.placement_node_id || item.id;
    if (seen.has(key)) continue;
    seen.add(key);
    items.push(item);
  }
  return items;
}

function PickerState({ children }: { children: ReactNode }) {
  return <div className="atom-context-picker-state">{children}</div>;
}

function ScrollingLine({ text, className = "" }: { text: string; className?: string }) {
  const frameRef = useRef<HTMLSpanElement>(null);
  const textRef = useRef<HTMLSpanElement>(null);
  const [overflowing, setOverflowing] = useState(false);

  useEffect(() => {
    const measure = () => {
      const frame = frameRef.current;
      const textNode = textRef.current;
      setOverflowing(Boolean(frame && textNode && textNode.scrollWidth > frame.clientWidth + 2));
    };

    measure();
    const resizeObserver = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    if (frameRef.current) resizeObserver?.observe(frameRef.current);
    if (textRef.current) resizeObserver?.observe(textRef.current);
    window.addEventListener("resize", measure);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [text]);

  return (
    <span ref={frameRef} className={`atom-context-picker-marquee ${className}${overflowing ? " is-overflowing" : ""}`} title={text}>
      <span className="atom-context-picker-marquee-track">
        <span ref={textRef} className="atom-context-picker-marquee-text">
          {text}
        </span>
        {overflowing ? (
          <span className="atom-context-picker-marquee-text" aria-hidden="true">
            {text}
          </span>
        ) : null}
      </span>
    </span>
  );
}

export function AtomContextPickerSheet({
  selectedContext,
  onClose,
  onSelect,
}: {
  selectedContext?: AssistantContext | null;
  onClose: () => void;
  onSelect: (context: AssistantContext) => void;
}) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [learningPage, setLearningPage] = useState<StudentLearningPageResponse | null>(null);
  const [learningRequestVersion, setLearningRequestVersion] = useState(0);
  const [learningLoading, setLearningLoading] = useState(true);
  const [learningError, setLearningError] = useState("");
  const [activeProfile, setActiveProfile] = useState<StudentLearningProfileSummary | null>(null);
  const [chapterCatalog, setChapterCatalog] = useState<StudentCatalogChapterResponse | null>(null);
  const [chapterRequestVersion, setChapterRequestVersion] = useState(0);
  const [chapterLoading, setChapterLoading] = useState(false);
  const [chapterError, setChapterError] = useState("");
  const [activeDirectoryId, setActiveDirectoryId] = useState("");
  const [directoryDetail, setDirectoryDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const [directoryRequestVersion, setDirectoryRequestVersion] = useState(0);
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [directoryError, setDirectoryError] = useState("");
  const [searchResponse, setSearchResponse] = useState<StudentHomeVideoFeedResponse | null>(null);
  const [searchRequestVersion, setSearchRequestVersion] = useState(0);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);
  const selectedProfileAutoFocusRef = useRef("");
  const selectedDirectoryAutoFocusRef = useRef("");

  const trimmedQuery = query.trim();
  const showSearchMode = Boolean(trimmedQuery);
  const selectedIdentity = contextIdentity(selectedContext);
  const activeRootTitle = activeProfile ? profileTitle(activeProfile) : chapterCatalog?.chapter_title || "";
  const activeBreadcrumbs = activeDirectoryId ? directoryDetail?.breadcrumbs || [] : [];
  const activeNodes = activeDirectoryId ? directoryDetail?.children || [] : chapterCatalog?.nodes || [];
  const catalogLoading = learningLoading || chapterLoading || directoryLoading;
  const catalogError = learningError || chapterError || directoryError;
  const searchItems = useMemo(() => pointResultItems(searchResponse), [searchResponse]);
  const orderedProfiles = useMemo(() => {
    const profiles = learningPage?.profiles || [];
    const recommendedId = learningPage?.recommended_profile_id;
    return [...profiles].sort((left, right) => {
      if (left.profile_id === recommendedId) return -1;
      if (right.profile_id === recommendedId) return 1;
      return left.title.localeCompare(right.title, "zh-CN");
    });
  }, [learningPage]);

  const blurPickerFocus = useCallback(() => {
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement && activeElement.closest(".atom-context-picker-layer")) {
      activeElement.blur();
    }
  }, []);

  const clearShellPickerState = useCallback(() => {
    document.querySelector(".student-app-shell.context-picker-active")?.classList.remove("context-picker-active");
    document.documentElement.classList.remove("atom-context-picker-active");
    document.body.classList.remove("atom-context-picker-active");
  }, []);

  const closePicker = useCallback(() => {
    blurPickerFocus();
    clearShellPickerState();
    onClose();
  }, [blurPickerFocus, clearShellPickerState, onClose]);

  const clearSearch = useCallback(() => {
    setQuery("");
    setDebouncedQuery("");
    setSearchResponse(null);
    setSearchError("");
    setSearchLoading(false);
    window.setTimeout(() => searchInputRef.current?.focus(), 0);
  }, []);

  const findSelectedParentDirectory = useCallback(
    async (nodes: StudentCatalogNodeCard[], parentDirectoryId: string, visitedDirectoryIds: Set<string>): Promise<string | null> => {
      if (nodes.some((node) => node.node_kind === "point" && catalogNodeMatchesContext(node, selectedContext))) {
        return parentDirectoryId;
      }

      for (const node of nodes) {
        if (node.node_kind !== "directory" || visitedDirectoryIds.has(node.node_id)) continue;
        visitedDirectoryIds.add(node.node_id);
        const detail = await getStudentCatalogNode(node.node_id);
        const foundDirectoryId = await findSelectedParentDirectory(detail.children, node.node_id, visitedDirectoryIds);
        if (foundDirectoryId !== null) return foundDirectoryId;
      }

      return null;
    },
    [selectedContext],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQuery(trimmedQuery), PICKER_SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [trimmedQuery]);

  useEffect(() => {
    let cancelled = false;
    setLearningLoading(true);
    setLearningError("");
    getStudentLearningPage(null)
      .then((payload) => {
        if (!cancelled) setLearningPage(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setLearningError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLearningLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [learningRequestVersion]);

  useEffect(() => {
    if (!selectedContext || !selectedIdentity || selectedProfileAutoFocusRef.current === selectedIdentity || activeProfile || !orderedProfiles.length) {
      return;
    }
    const selectedChapterId = selectedContext.chapter_id;
    if (!selectedChapterId) return;
    const matchingProfile = orderedProfiles.find((profile) => profile.chapter_id === selectedChapterId);
    if (!matchingProfile) return;
    selectedProfileAutoFocusRef.current = selectedIdentity;
    setActiveProfile(matchingProfile);
  }, [activeProfile, orderedProfiles, selectedContext, selectedIdentity]);

  useEffect(() => {
    if (!activeProfile) {
      setChapterCatalog(null);
      setChapterError("");
      setChapterLoading(false);
      setActiveDirectoryId("");
      setDirectoryDetail(null);
      return;
    }
    let cancelled = false;
    setChapterLoading(true);
    setChapterError("");
    setActiveDirectoryId("");
    setDirectoryDetail(null);
    getStudentChapterCatalog(activeProfile.chapter_id)
      .then((payload) => {
        if (!cancelled) setChapterCatalog(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setChapterError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setChapterLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeProfile, chapterRequestVersion]);

  useEffect(() => {
    if (
      !selectedContext ||
      !selectedIdentity ||
      selectedDirectoryAutoFocusRef.current === selectedIdentity ||
      !activeProfile ||
      !chapterCatalog ||
      chapterLoading
    ) {
      return;
    }
    if (selectedContext.chapter_id && activeProfile.chapter_id !== selectedContext.chapter_id) return;

    let cancelled = false;
    const visitedDirectoryIds = new Set<string>();
    findSelectedParentDirectory(chapterCatalog.nodes, "", visitedDirectoryIds)
      .then((directoryId) => {
        if (cancelled) return;
        if (directoryId !== null) setActiveDirectoryId(directoryId);
        selectedDirectoryAutoFocusRef.current = selectedIdentity;
      })
      .catch(() => {
        if (!cancelled) selectedDirectoryAutoFocusRef.current = selectedIdentity;
      });

    return () => {
      cancelled = true;
    };
  }, [activeProfile, chapterCatalog, chapterLoading, findSelectedParentDirectory, selectedContext, selectedIdentity]);

  useEffect(() => {
    if (!activeDirectoryId) {
      setDirectoryDetail(null);
      setDirectoryError("");
      setDirectoryLoading(false);
      return;
    }
    let cancelled = false;
    setDirectoryLoading(true);
    setDirectoryError("");
    getStudentCatalogNode(activeDirectoryId)
      .then((payload) => {
        if (!cancelled) setDirectoryDetail(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setDirectoryError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setDirectoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeDirectoryId, directoryRequestVersion]);

  useEffect(() => {
    if (!debouncedQuery) {
      setSearchResponse(null);
      setSearchLoading(false);
      setSearchError("");
      return;
    }
    let cancelled = false;
    setSearchLoading(true);
    setSearchError("");
    getStudentHomeVideoFeed({ q: debouncedQuery, limit: PICKER_SEARCH_LIMIT })
      .then((payload) => {
        if (!cancelled) setSearchResponse(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setSearchError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setSearchLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQuery, searchRequestVersion]);

  useEffect(() => {
    if (!selectedIdentity || catalogLoading || searchLoading) return;
    const timer = window.setTimeout(() => {
      const selectedRow = document.querySelector<HTMLElement>(".atom-context-picker-row.selected");
      if (typeof selectedRow?.scrollIntoView === "function") selectedRow.scrollIntoView({ block: "center" });
    }, 0);
    return () => window.clearTimeout(timer);
  }, [activeDirectoryId, activeNodes.length, catalogLoading, searchItems.length, searchLoading, selectedIdentity, showSearchMode]);

  const openDirectory = useCallback((node: StudentCatalogNodeCard) => {
    if (node.node_kind === "directory") setActiveDirectoryId(node.node_id);
  }, []);

  const selectCatalogPoint = useCallback(
    (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => {
      if (node.node_kind !== "point") return;
      blurPickerFocus();
      clearShellPickerState();
      onSelect(assistantContextFromCatalogNode(node, breadcrumbs, activeRootTitle));
    },
    [activeRootTitle, blurPickerFocus, clearShellPickerState, onSelect],
  );

  const selectSearchPoint = useCallback(
    (item: StudentHomeVideoFeedItem) => {
      const context = assistantContextFromHomeFeedItem(item);
      if (!context) return;
      blurPickerFocus();
      clearShellPickerState();
      onSelect(context);
    },
    [blurPickerFocus, clearShellPickerState, onSelect],
  );

  const renderCatalogMode = () => {
    if (!activeProfile) {
      if (learningLoading) {
        return (
          <PickerState>
            <LoaderCircle className="spin" size={20} />
            <span>正在加载学习目录</span>
          </PickerState>
        );
      }
      if (learningError) {
        return (
          <PickerState>
            <span>{learningError}</span>
            <button type="button" onClick={() => setLearningRequestVersion((value) => value + 1)}>
              重试
            </button>
          </PickerState>
        );
      }
      if (!orderedProfiles.length) {
        return (
          <PickerState>
            <span>暂时没有可选择的学习目录</span>
          </PickerState>
        );
      }
      return (
        <div className="atom-context-picker-list kind-catalog" aria-label="学习目录根">
          {orderedProfiles.map((profile) => (
            <button
              type="button"
              className="atom-context-picker-row kind-directory"
              key={profile.profile_id}
              onClick={() => setActiveProfile(profile)}
            >
              <span className="atom-context-picker-row-icon">
                <FolderOpen size={19} />
              </span>
              <span className="atom-context-picker-row-copy">
                <strong>{profileTitle(profile)}</strong>
                <small>{profile.subtitle || profile.family_name || profile.chapter_id}</small>
              </span>
              <ChevronRight size={17} />
            </button>
          ))}
        </div>
      );
    }

    if (catalogLoading) {
      return (
        <PickerState>
          <LoaderCircle className="spin" size={20} />
          <span>正在加载这一级目录</span>
        </PickerState>
      );
    }
    if (catalogError) {
      return (
        <PickerState>
          <span>{catalogError}</span>
          <button
            type="button"
            onClick={() => (activeDirectoryId ? setDirectoryRequestVersion((value) => value + 1) : setChapterRequestVersion((value) => value + 1))}
          >
            重试
          </button>
        </PickerState>
      );
    }
    if (!activeNodes.length) {
      return (
        <PickerState>
          <span>这一级里没有可选择的点位</span>
        </PickerState>
      );
    }

    return (
      <div className="atom-context-picker-list kind-catalog" aria-label="目录点位">
        {activeNodes.map((node) => {
          const pointContext = node.node_kind === "point" ? assistantContextFromCatalogNode(node, activeBreadcrumbs, activeRootTitle) : null;
          const selected = pointContext ? contextIdentity(pointContext) === selectedIdentity : false;
          return (
            <button
              type="button"
              className={`atom-context-picker-row kind-${node.node_kind}${selected ? " selected" : ""}`}
              key={node.node_id}
              onClick={() => (node.node_kind === "directory" ? openDirectory(node) : selectCatalogPoint(node, activeBreadcrumbs))}
            >
              <span className="atom-context-picker-row-icon">{node.node_kind === "directory" ? <FolderOpen size={19} /> : <Atom size={18} />}</span>
              <span className="atom-context-picker-row-copy">
                <strong>{node.canonical_point_title || node.title}</strong>
                <small>{node.summary || (node.node_kind === "directory" ? "继续展开目录" : activeRootTitle)}</small>
              </span>
              <ChevronRight size={17} />
            </button>
          );
        })}
      </div>
    );
  };

  const renderSearchMode = () => {
    if (searchLoading) {
      return (
        <PickerState>
          <LoaderCircle className="spin" size={20} />
          <span>正在搜索可绑定点位</span>
        </PickerState>
      );
    }
    if (searchError) {
      return (
        <PickerState>
          <span>{searchError}</span>
          <button type="button" onClick={() => setSearchRequestVersion((value) => value + 1)}>
            重试
          </button>
        </PickerState>
      );
    }
    if (!searchItems.length) {
      return (
        <PickerState>
          <span>没有找到可绑定的点位</span>
        </PickerState>
      );
    }
    return (
      <div className="atom-context-picker-list kind-search" aria-label="点位搜索结果">
        {searchItems.map((item) => {
          const context = assistantContextFromHomeFeedItem(item);
          const selected = context ? contextIdentity(context) === selectedIdentity : false;
          return (
            <button
              type="button"
              className={`atom-context-picker-row kind-point${selected ? " selected" : ""}`}
              key={item.id}
              onClick={() => selectSearchPoint(item)}
            >
              <span className="atom-context-picker-row-icon">
                <Atom size={18} />
              </span>
              <span className="atom-context-picker-search-copy">
                <ScrollingLine text={item.title} className="is-title" />
                <ScrollingLine text={compactResultPath(item, orderedProfiles)} className="is-path" />
              </span>
              <ChevronRight size={17} />
            </button>
          );
        })}
      </div>
    );
  };

  const catalogBreadcrumbItems = activeBreadcrumbs.map((item) => ({ nodeId: item.node_id, title: item.title }));
  const catalogItemCount = activeProfile ? activeNodes.length : orderedProfiles.length;
  const catalogItemUnit = activeProfile && activeNodes.some((node) => node.node_kind === "point") ? "项" : "目录";

  const goCatalogHome = () => {
    setActiveProfile(null);
    setChapterCatalog(null);
    setActiveDirectoryId("");
    setDirectoryDetail(null);
  };

  const renderCatalogPath = () => {
    if (showSearchMode) return null;
    return (
      <nav className="atom-context-picker-path" aria-label="目录路径">
        <div className="atom-context-picker-path-row">
          <div className="atom-context-picker-root-path">
            <button
              type="button"
              className={`atom-context-picker-crumb${activeProfile ? "" : " is-active"}`}
              aria-current={activeProfile ? undefined : "page"}
              onClick={goCatalogHome}
            >
              全章节
            </button>
            {activeProfile ? (
              <span className="atom-context-picker-crumb-separator" aria-hidden="true">
                ›
              </span>
            ) : null}
          </div>
          <span className="atom-context-picker-count" aria-label={`当前共${catalogItemCount}${catalogItemUnit}`}>
            共{catalogItemCount}{catalogItemUnit}
          </span>
        </div>
        {activeProfile ? (
          <div className="atom-context-picker-breadcrumbs">
            <div className="atom-context-picker-path-track">
              <button
                type="button"
                className={`atom-context-picker-crumb${catalogBreadcrumbItems.length ? "" : " is-active"}`}
                aria-current={catalogBreadcrumbItems.length ? undefined : "page"}
                onClick={() => setActiveDirectoryId("")}
                title={activeRootTitle}
              >
                {activeRootTitle}
              </button>
              {catalogBreadcrumbItems.map((item, index) => {
                const active = index === catalogBreadcrumbItems.length - 1;
                return (
                  <span className="atom-context-picker-crumb-piece" key={`${item.nodeId}-${index}`}>
                    <span className="atom-context-picker-crumb-separator" aria-hidden="true">
                      ›
                    </span>
                    <button
                      type="button"
                      className={`atom-context-picker-crumb${active ? " is-active" : ""}`}
                      aria-current={active ? "page" : undefined}
                      onClick={() => setActiveDirectoryId(item.nodeId)}
                      title={item.title}
                    >
                      {item.title}
                    </button>
                  </span>
                );
              })}
            </div>
          </div>
        ) : null}
      </nav>
    );
  };

  return (
    <div className="atom-context-picker-layer" role="dialog" aria-modal="true" aria-label="选择学习背景">
      <button type="button" className="atom-context-picker-backdrop" onClick={closePicker} aria-label="关闭学习背景选择" />
      <section className="atom-context-picker-sheet">
        <header className={`atom-context-picker-head${showSearchMode ? " is-search" : " is-catalog"}`}>
          <p className="atom-context-picker-mode-label">{showSearchMode ? "直接搜索实验点位" : "从目录选择实验点位"}</p>
          {showSearchMode ? (
            null
          ) : (
            renderCatalogPath()
          )}
        </header>

        <div className="atom-context-picker-body">{showSearchMode ? renderSearchMode() : renderCatalogMode()}</div>

        <footer className="atom-context-picker-search">
          <Search size={18} aria-hidden="true" />
          <input
            ref={searchInputRef}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="直接搜索实验点位"
            aria-label="搜索可绑定点位"
          />
          <button
            type="button"
            className="atom-context-picker-search-clear"
            onClick={clearSearch}
            aria-label="清空实验点位搜索"
            hidden={!query}
          >
            <X size={18} />
          </button>
        </footer>
      </section>
    </div>
  );
}
