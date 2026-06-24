import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Atom, ChevronLeft, ChevronRight, FolderOpen, LoaderCircle, Search, X } from "lucide-react";

import type {
  StudentCatalogBreadcrumb,
  StudentCatalogChapterResponse,
  StudentCatalogNodeCard,
  StudentCatalogNodeResponse,
  StudentLearningPageResponse,
  StudentLearningProfileSummary,
  StudentVideoLibraryResultItem,
  StudentVideoLibrarySearchResponse,
} from "../../api";
import {
  errorMessage,
  getStudentCatalogNode,
  getStudentChapterCatalog,
  getStudentLearningPage,
  searchStudentVideoLibrary,
} from "../../api";
import { formatChapterEntryTitle } from "../learning/learningFormat";
import {
  assistantContextFromCatalogNode,
  assistantContextFromVideoLibraryResult,
  assistantContextPathLabel,
  isBindableVideoLibraryResult,
  type AssistantContext,
} from "./assistantContext";

const PICKER_SEARCH_DEBOUNCE_MS = 240;
const PICKER_SEARCH_LIMIT = 12;

function contextIdentity(context: AssistantContext | null | undefined): string {
  if (!context) return "";
  return [context.point_node_id, context.source_node_id, context.chapter_id, context.context_title].filter(Boolean).join("::");
}

function profileTitle(profile: StudentLearningProfileSummary): string {
  return formatChapterEntryTitle(profile) || profile.title || profile.subtitle || profile.chapter_id;
}

function compactResultPath(item: StudentVideoLibraryResultItem): string {
  const path = item.target?.catalog_path?.map((part) => part.trim()).filter(Boolean) || [];
  if (path.length) return path.join(" / ");
  return item.subtitle;
}

function pointResultItems(response: StudentVideoLibrarySearchResponse | null): StudentVideoLibraryResultItem[] {
  if (!response) return [];
  const seen = new Set<string>();
  const items: StudentVideoLibraryResultItem[] = [];
  for (const group of response.groups) {
    for (const item of group.items) {
      if (!isBindableVideoLibraryResult(item)) continue;
      const key = item.target?.node_id || item.target?.placement_node_id || item.id;
      if (seen.has(key)) continue;
      seen.add(key);
      items.push(item);
    }
  }
  return items;
}

function PickerState({ children }: { children: ReactNode }) {
  return <div className="atom-context-picker-state">{children}</div>;
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
  const [searchResponse, setSearchResponse] = useState<StudentVideoLibrarySearchResponse | null>(null);
  const [searchRequestVersion, setSearchRequestVersion] = useState(0);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");

  const trimmedQuery = query.trim();
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
  }, []);

  const closePicker = useCallback(() => {
    blurPickerFocus();
    clearShellPickerState();
    onClose();
  }, [blurPickerFocus, clearShellPickerState, onClose]);

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
    searchStudentVideoLibrary(debouncedQuery, PICKER_SEARCH_LIMIT)
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
    (item: StudentVideoLibraryResultItem) => {
      const context = assistantContextFromVideoLibraryResult(item);
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
        <div className="atom-context-picker-list" aria-label="学习目录根">
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
      <div className="atom-context-picker-list" aria-label="目录点位">
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
      <div className="atom-context-picker-list" aria-label="点位搜索结果">
        {searchItems.map((item) => {
          const context = assistantContextFromVideoLibraryResult(item);
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
              <span className="atom-context-picker-row-copy">
                <strong>{item.title}</strong>
                <small>{compactResultPath(item)}</small>
                {item.snippet ? <em>{item.snippet}</em> : null}
              </span>
              <ChevronRight size={17} />
            </button>
          );
        })}
      </div>
    );
  };

  const pathLabel = selectedContext ? assistantContextPathLabel(selectedContext) : "";
  const showSearchMode = Boolean(trimmedQuery);

  return (
    <div className="atom-context-picker-layer" role="dialog" aria-modal="true" aria-label="选择学习背景">
      <button type="button" className="atom-context-picker-backdrop" onClick={closePicker} aria-label="关闭学习背景选择" />
      <section className="atom-context-picker-sheet">
        <header className="atom-context-picker-head">
          <button
            type="button"
            className="atom-context-picker-nav"
            onClick={() => {
              if (activeDirectoryId) {
                const crumbs = directoryDetail?.breadcrumbs || [];
                const parent = crumbs[crumbs.length - 2];
                setActiveDirectoryId(parent?.node_id || "");
                return;
              }
              if (activeProfile) {
                setActiveProfile(null);
                setChapterCatalog(null);
              }
            }}
            disabled={!activeProfile || showSearchMode}
            aria-label="返回上一级目录"
          >
            <ChevronLeft size={18} />
          </button>
          <div>
            <p>{showSearchMode ? "搜索点位" : activeRootTitle || "目录选择"}</p>
            <h2>选择学习背景</h2>
            {pathLabel ? <small>当前：{selectedContext?.context_title} · {pathLabel}</small> : <small>一个对话只绑定一个点位</small>}
          </div>
          <button type="button" className="atom-context-picker-close" onClick={closePicker} aria-label="关闭学习背景选择">
            <X size={18} />
          </button>
        </header>

        <div className="atom-context-picker-body">{showSearchMode ? renderSearchMode() : renderCatalogMode()}</div>

        <footer className="atom-context-picker-search">
          <Search size={18} aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索点位、现象或试剂"
            aria-label="搜索可绑定点位"
          />
        </footer>
      </section>
    </div>
  );
}
