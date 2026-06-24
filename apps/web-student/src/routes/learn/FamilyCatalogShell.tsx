import type { CSSProperties } from "react";
import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ChevronRight, FlaskConical, FolderOpen, LoaderCircle, MoreHorizontal, Search } from "lucide-react";

import {
  errorMessage,
  getStudentCatalogNode,
  getStudentChapterCatalog,
  getStudentLearningPage,
  type StudentCatalogBreadcrumb,
  type StudentCatalogChapterResponse,
  type StudentCatalogNodeCard,
  type StudentCatalogNodeResponse,
  type StudentLearningElementBadge,
  type StudentLearningPageResponse,
  type StudentLearningProfile,
} from "../../api";
import { navigateToElement, navigateToPoint, navigateToSearch } from "../../app/router/navigation";
import { CatalogNodeCards, catalogPathLabel } from "../../features/catalog/CatalogNodeCards";
import { formatChapterEntryTitle } from "../../features/learning/learningFormat";
import { ElementTileContent } from "../../features/periodic-table/PeriodicElementCell";
import { elementEnglishName, elementTileStyle } from "../../features/periodic-table/periodicHelpers";
import { MobileEmptyState } from "../../mobile/primitives";
import { LearningState } from "../../shared/mobile/LearningState";

export function FamilyCatalogShell({
  profileId,
  directoryNodeId,
  initialElementSymbol,
  initialPage,
  loadLearningPage = getStudentLearningPage,
  loadChapterCatalog = getStudentChapterCatalog,
  loadCatalogNode = getStudentCatalogNode,
  onOpenDirectoryOverride,
  onOpenPointOverride,
  onOpenSearchOverride,
  onOpenElementDetailOverride,
  onTitleChange,
}: {
  profileId: string;
  directoryNodeId?: string | null;
  initialElementSymbol?: string | null;
  initialPage?: StudentLearningPageResponse | null;
  loadLearningPage?: (profileId: string) => Promise<StudentLearningPageResponse>;
  loadChapterCatalog?: (chapterId: string) => Promise<StudentCatalogChapterResponse>;
  loadCatalogNode?: (nodeId: string) => Promise<StudentCatalogNodeResponse>;
  onOpenDirectoryOverride?: (node: StudentCatalogNodeCard) => void;
  onOpenPointOverride?: (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => void;
  onOpenSearchOverride?: (sourceNodeId: string, catalogPath: string) => void;
  onOpenElementDetailOverride?: (profile: StudentLearningProfile, element: StudentLearningElementBadge) => void;
  onTitleChange?: (title: string) => void;
}) {
  const navigate = useNavigate();
  const seededPage = initialPage?.active_profile?.profile_id === profileId ? initialPage : null;
  const [page, setPage] = useState<StudentLearningPageResponse | null>(seededPage);
  const [selectedElementSymbol, setSelectedElementSymbol] = useState(initialElementSymbol || "");
  const [activeDirectoryId, setActiveDirectoryId] = useState(directoryNodeId || "");
  const [loading, setLoading] = useState(Boolean(profileId) && !seededPage);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialPage?.active_profile?.profile_id === profileId) {
      setPage(initialPage);
      setLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    loadLearningPage(profileId)
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
  }, [initialPage, loadLearningPage, profileId]);

  const profile = page?.active_profile || null;

  useEffect(() => {
    setActiveDirectoryId(directoryNodeId || "");
  }, [directoryNodeId]);

  useEffect(() => {
    if (profile) onTitleChange?.(formatChapterEntryTitle(profile));
  }, [profile, onTitleChange]);

  useEffect(() => {
    if (initialElementSymbol) setSelectedElementSymbol(initialElementSymbol);
  }, [initialElementSymbol]);

  useEffect(() => {
    if (!profile) return;
    const symbols = profile.elements.map((element) => element.symbol);
    const preferred =
      initialElementSymbol && symbols.includes(initialElementSymbol)
        ? initialElementSymbol
        : selectedElementSymbol || profile.default_element_symbol || symbols[0] || "";
    if (!preferred || !symbols.includes(preferred)) {
      setSelectedElementSymbol(profile.default_element_symbol && symbols.includes(profile.default_element_symbol) ? profile.default_element_symbol : symbols[0] || "");
    }
  }, [profile, initialElementSymbol, selectedElementSymbol]);

  const selectedElement = useMemo(() => {
    if (!profile) return null;
    return (
      profile.elements.find((element) => element.symbol === selectedElementSymbol) ||
      profile.elements.find((element) => element.symbol === profile.default_element_symbol) ||
      profile.elements[0] ||
      null
    );
  }, [profile, selectedElementSymbol]);

  const openDirectory = useCallback(
    (node: StudentCatalogNodeCard) => {
      if (onOpenDirectoryOverride) {
        onOpenDirectoryOverride(node);
        return;
      }
      setActiveDirectoryId(node.node_id);
    },
    [onOpenDirectoryOverride],
  );

  const openPoint = useCallback(
    (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => {
      if (onOpenPointOverride) {
        onOpenPointOverride(node, breadcrumbs);
        return;
      }
      const nextPath = catalogPathLabel([...breadcrumbs, breadcrumbForNode(node)]);
      navigateToPoint(navigate, node.node_id, {
        from: "chapter",
        profileId: profile?.profile_id || profileId,
        chapterId: node.chapter_id || profile?.chapter_id,
        sourceNodeId: activeDirectoryId || "",
        catalogPath: nextPath,
        elementSymbol: selectedElement?.symbol || "",
        pointTitle: node.title,
      });
    },
    [activeDirectoryId, navigate, onOpenPointOverride, profile?.chapter_id, profile?.profile_id, profileId, selectedElement?.symbol],
  );

  if (loading) {
    return <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载章节学习" />;
  }

  if (error) {
    return <LearningState icon={<FlaskConical size={23} />} text={error} />;
  }

  if (!profile) {
    return <LearningState icon={<FlaskConical size={23} />} text="没有找到学习章节" />;
  }

  return (
    <section className="family-catalog-shell" aria-label="族学习目录">
      <FamilyCatalogHeader
        profile={profile}
        selectedElement={selectedElement}
        onSelectElement={setSelectedElementSymbol}
        onOpenElementDetail={() => {
          if (!selectedElement) return;
          if (onOpenElementDetailOverride) {
            onOpenElementDetailOverride(profile, selectedElement);
            return;
          }
          navigateToElement(navigate, profile.profile_id, selectedElement.symbol, { from: "chapter" });
        }}
      />
      <div className="family-catalog-collapse-marker" aria-hidden="true" />
      <div className="family-catalog-body">
        <section className="family-catalog-sheet" aria-label="章节学习目录工作区">
          <FamilyCatalogBrowser
            chapterId={profile.chapter_id}
            rootLabel={formatChapterEntryTitle(profile)}
            activeDirectoryId={activeDirectoryId}
            loadChapterCatalog={loadChapterCatalog}
            loadCatalogNode={loadCatalogNode}
            onChangeDirectory={setActiveDirectoryId}
            onOpenDirectory={openDirectory}
            onOpenPoint={openPoint}
            onOpenSearch={(sourceNodeId, catalogPath) => {
              if (onOpenSearchOverride) {
                onOpenSearchOverride(sourceNodeId, catalogPath);
                return;
              }
              navigateToSearch(navigate, {
                from: "chapter",
                profileId: profile.profile_id,
                chapterId: profile.chapter_id,
                sourceNodeId,
                catalogPath,
                elementSymbol: selectedElement?.symbol || "",
              });
            }}
          />
        </section>
      </div>
    </section>
  );
}

function FamilyCatalogBrowser({
  chapterId,
  rootLabel,
  activeDirectoryId,
  loadChapterCatalog = getStudentChapterCatalog,
  loadCatalogNode = getStudentCatalogNode,
  onChangeDirectory,
  onOpenDirectory,
  onOpenPoint,
  onOpenSearch,
}: {
  chapterId?: string | null;
  rootLabel: string;
  activeDirectoryId: string;
  loadChapterCatalog?: (chapterId: string) => Promise<StudentCatalogChapterResponse>;
  loadCatalogNode?: (nodeId: string) => Promise<StudentCatalogNodeResponse>;
  onChangeDirectory: (nodeId: string) => void;
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => void;
  onOpenSearch: (sourceNodeId: string, catalogPath: string) => void;
}) {
  const [chapterCatalog, setChapterCatalog] = useState<StudentCatalogChapterResponse | null>(null);
  const [directoryDetail, setDirectoryDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const [rootLoading, setRootLoading] = useState(Boolean(chapterId));
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [moreOpen, setMoreOpen] = useState(false);
  const activeCrumbRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!chapterId) {
      setChapterCatalog(null);
      setRootLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setRootLoading(true);
    setError("");
    loadChapterCatalog(chapterId)
      .then((payload) => {
        if (!cancelled) setChapterCatalog(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setRootLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [chapterId, loadChapterCatalog]);

  useEffect(() => {
    if (!activeDirectoryId) {
      setDirectoryDetail(null);
      setDirectoryLoading(false);
      return;
    }
    let cancelled = false;
    setDirectoryLoading(true);
    setError("");
    loadCatalogNode(activeDirectoryId)
      .then((payload) => {
        if (!cancelled) setDirectoryDetail(payload);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setDirectoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeDirectoryId, loadCatalogNode]);

  const breadcrumbs = activeDirectoryId ? directoryDetail?.breadcrumbs || [] : [];
  const nodes = activeDirectoryId ? directoryDetail?.children || [] : chapterCatalog?.nodes || [];
  const loading = rootLoading || directoryLoading;
  const fullPathText = breadcrumbs.length ? catalogPathLabel(breadcrumbs) : rootLabel;
  const childBreadcrumbItems = useMemo(() => breadcrumbs.map((item) => ({ nodeId: item.node_id, title: item.title })), [breadcrumbs]);

  useEffect(() => {
    if (typeof activeCrumbRef.current?.scrollIntoView === "function") {
      activeCrumbRef.current.scrollIntoView({ block: "nearest", inline: "end" });
    }
  }, [childBreadcrumbItems.length, activeDirectoryId]);

  const goRoot = useCallback(() => {
    onChangeDirectory("");
    setMoreOpen(false);
  }, [onChangeDirectory]);

  return (
    <section className="family-catalog-browser catalog-browser-body" aria-label="章节学习目录">
      <div className="family-catalog-browser-head">
        <div className="family-catalog-browser-topline">
          <div className="family-catalog-root-path">
            <button
              className={`family-catalog-crumb family-catalog-root-crumb${childBreadcrumbItems.length ? "" : " is-active"}`}
              type="button"
              aria-current={childBreadcrumbItems.length ? undefined : "page"}
              onClick={() => onChangeDirectory("")}
              title={rootLabel}
            >
              {rootLabel}
            </button>
            {childBreadcrumbItems.length ? <span className="family-catalog-crumb-separator" aria-hidden="true">›</span> : null}
          </div>
          <div className="family-catalog-browser-actions" aria-label="目录操作">
            <button className="family-catalog-search-action" type="button" onClick={() => onOpenSearch(activeDirectoryId, fullPathText)}>
              <Search size={14} />
              搜索
            </button>
            <button className="family-catalog-more-action" type="button" onClick={() => setMoreOpen(true)}>
              <MoreHorizontal size={14} />
              更多
            </button>
          </div>
        </div>
        {childBreadcrumbItems.length ? (
          <nav className="family-catalog-breadcrumbs" aria-label="目录路径">
            <div className="family-catalog-breadcrumb-track">
              {childBreadcrumbItems.map((item, index) => {
                const active = index === childBreadcrumbItems.length - 1;
                return (
                  <Fragment key={`${item.nodeId}-${index}`}>
                    {index ? <span className="family-catalog-crumb-separator" aria-hidden="true">›</span> : null}
                    <button
                      ref={active ? activeCrumbRef : null}
                      className={`family-catalog-crumb${active ? " is-active" : ""}`}
                      type="button"
                      aria-current={active ? "page" : undefined}
                      onClick={() => onChangeDirectory(item.nodeId)}
                      title={item.title}
                    >
                      {item.title}
                    </button>
                  </Fragment>
                );
              })}
            </div>
          </nav>
        ) : null}
      </div>

      {loading ? (
        <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载目录" />
      ) : error ? (
        <LearningState icon={<FolderOpen size={23} />} text={error} />
      ) : nodes.length ? (
        <CatalogNodeCards
          nodes={nodes}
          breadcrumbs={breadcrumbs}
          showSummaryFooter
          onOpenDirectory={onOpenDirectory}
          onOpenPoint={(node) => onOpenPoint(node, breadcrumbs)}
        />
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<FolderOpen size={20} />}>
          <span>当前目录暂无内容</span>
        </MobileEmptyState>
      )}

      {moreOpen ? (
        <div
          className="family-catalog-more-backdrop"
          role="presentation"
          onPointerDown={(event) => {
            if (event.target === event.currentTarget) setMoreOpen(false);
          }}
        >
          <section className="family-catalog-more-sheet" role="dialog" aria-modal="true" aria-label="目录更多">
            <div className="family-catalog-more-head">
              <h3>更多</h3>
            </div>
            <button type="button" onClick={goRoot} disabled={!activeDirectoryId}>
              回到章节目录
              <ChevronRight size={16} />
            </button>
          </section>
        </div>
      ) : null}
    </section>
  );
}

function FamilyCatalogHeader({
  profile,
  selectedElement,
  onSelectElement,
  onOpenElementDetail,
}: {
  profile: StudentLearningProfile;
  selectedElement: StudentLearningElementBadge | null;
  onSelectElement: (symbol: string) => void;
  onOpenElementDetail: () => void;
}) {
  const title = formatChapterEntryTitle(profile);
  const focus = selectedElement?.card_focus || (selectedElement?.common_valence ? `常见价态 ${selectedElement.common_valence}` : "观察元素性质");
  const relevance = selectedElement?.card_relevance || "查看这个元素在本章实验与观察任务中的作用。";
  const tags = selectedElement
    ? compactElementTags(selectedElement.card_tags?.length ? selectedElement.card_tags : fallbackElementTags(selectedElement, profile.family_name || title))
    : [];
  const selectedEnglishName = selectedElement ? elementEnglishName(selectedElement) : "";
  const selectedNameLine =
    selectedElement && selectedEnglishName && selectedEnglishName !== selectedElement.name ? (
      <>
        {selectedElement.name} <span>{selectedEnglishName}</span>
      </>
    ) : (
      selectedElement?.name || selectedEnglishName
    );

  return (
    <header className="family-catalog-context" aria-label={`${title} 元素上下文`}>
      <div className={profile.elements.length > 5 ? "family-element-rail has-overflow" : "family-element-rail"} aria-label="同族元素">
        {profile.elements.map((element) => {
          const active = element.symbol === selectedElement?.symbol;
          return (
            <button
              className={active ? "family-element-rail-button active" : "family-element-rail-button"}
              key={element.symbol}
              type="button"
              style={elementTileStyle(element) as CSSProperties}
              aria-label={`${element.symbol} ${elementEnglishName(element)} ${element.name}`}
              aria-pressed={active}
              onClick={() => onSelectElement(element.symbol)}
            >
              <ElementTileContent element={element} />
            </button>
          );
        })}
      </div>
      {selectedElement ? (
        <div className="chapter-element-summary family-context-summary" style={elementTileStyle(selectedElement) as CSSProperties}>
          <div className="family-context-summary-copy">
            <div className="family-context-summary-head">
              <h3>{selectedNameLine}</h3>
              <button className="chapter-element-detail-action family-element-detail-action" type="button" onClick={onOpenElementDetail}>
                <span>元素详情</span>
                <ChevronRight size={15} />
              </button>
            </div>
            <strong>{focus}</strong>
            <span className="family-context-summary-note">{relevance}</span>
          </div>
          <div className="family-context-tag-row">
            {tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        </div>
      ) : null}
    </header>
  );
}

function breadcrumbForNode(node: StudentCatalogNodeCard): StudentCatalogBreadcrumb {
  return {
    node_id: node.node_id,
    title: node.title,
    node_kind: node.node_kind,
    chapter_id: node.chapter_id,
  };
}

function fallbackElementTags(element: StudentLearningElementBadge, familyLabel: string): string[] {
  return [
    element.group_label || element.group || familyLabel,
    typeof element.period === "number" ? `${element.period}周期` : "",
    element.state_at_20c || element.state || "",
    element.common_valence ? `常见${element.common_valence}价` : "",
  ];
}

function compactElementTags(tags: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const tag of tags) {
    const text = tag.trim();
    if (!text || seen.has(text)) continue;
    seen.add(text);
    result.push(text);
    if (result.length >= 3) break;
  }
  return result;
}
