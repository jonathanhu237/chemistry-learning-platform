import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ChevronRight, ChevronUp, FlaskConical, FolderOpen, LoaderCircle, MoreHorizontal, Search, X } from "lucide-react";

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
import { navigateToElement, navigateToPoint } from "../../app/router/navigation";
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
  onTitleChange,
}: {
  profileId: string;
  directoryNodeId?: string | null;
  initialElementSymbol?: string | null;
  onTitleChange?: (title: string) => void;
}) {
  const navigate = useNavigate();
  const [page, setPage] = useState<StudentLearningPageResponse | null>(null);
  const [selectedElementSymbol, setSelectedElementSymbol] = useState(initialElementSymbol || "");
  const [activeDirectoryId, setActiveDirectoryId] = useState(directoryNodeId || "");
  const [catalogSearch, setCatalogSearch] = useState("");
  const [loading, setLoading] = useState(Boolean(profileId));
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
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
      setActiveDirectoryId(node.node_id);
    },
    [],
  );

  const openPoint = useCallback(
    (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => {
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
    [activeDirectoryId, navigate, profile?.chapter_id, profile?.profile_id, profileId, selectedElement?.symbol],
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
          if (selectedElement) navigateToElement(navigate, profile.profile_id, selectedElement.symbol, { from: "chapter" });
        }}
      />
      <div className="family-catalog-collapse-marker" aria-hidden="true" />
      <div className="family-catalog-body">
        <section className="family-catalog-sheet" aria-label="章节学习目录工作区">
          <span className="family-catalog-sheet-edge" aria-hidden="true" />
          <FamilyCatalogBrowser
            chapterId={profile.chapter_id}
            activeDirectoryId={activeDirectoryId}
            searchQuery={catalogSearch}
            onChangeDirectory={setActiveDirectoryId}
            onOpenDirectory={openDirectory}
            onOpenPoint={openPoint}
            onClearSearch={() => setCatalogSearch("")}
          />
          <label className="family-catalog-search">
            <Search size={16} />
            <input
              type="search"
              value={catalogSearch}
              onChange={(event) => setCatalogSearch(event.target.value)}
              placeholder="查找本章目录内容"
              aria-label="查找本章目录内容"
            />
            {catalogSearch ? (
              <button type="button" aria-label="清空目录搜索" onClick={() => setCatalogSearch("")}>
                <X size={14} />
              </button>
            ) : null}
          </label>
        </section>
      </div>
    </section>
  );
}

function FamilyCatalogBrowser({
  chapterId,
  activeDirectoryId,
  searchQuery,
  onChangeDirectory,
  onOpenDirectory,
  onOpenPoint,
  onClearSearch,
}: {
  chapterId?: string | null;
  activeDirectoryId: string;
  searchQuery: string;
  onChangeDirectory: (nodeId: string) => void;
  onOpenDirectory: (node: StudentCatalogNodeCard) => void;
  onOpenPoint: (node: StudentCatalogNodeCard, breadcrumbs: StudentCatalogBreadcrumb[]) => void;
  onClearSearch: () => void;
}) {
  const [chapterCatalog, setChapterCatalog] = useState<StudentCatalogChapterResponse | null>(null);
  const [directoryDetail, setDirectoryDetail] = useState<StudentCatalogNodeResponse | null>(null);
  const [rootLoading, setRootLoading] = useState(Boolean(chapterId));
  const [directoryLoading, setDirectoryLoading] = useState(false);
  const [error, setError] = useState("");
  const [moreOpen, setMoreOpen] = useState(false);

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
    getStudentChapterCatalog(chapterId)
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
  }, [chapterId]);

  useEffect(() => {
    if (!activeDirectoryId) {
      setDirectoryDetail(null);
      setDirectoryLoading(false);
      return;
    }
    let cancelled = false;
    setDirectoryLoading(true);
    setError("");
    getStudentCatalogNode(activeDirectoryId)
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
  }, [activeDirectoryId]);

  const breadcrumbs = activeDirectoryId ? directoryDetail?.breadcrumbs || [] : [];
  const nodes = activeDirectoryId ? directoryDetail?.children || [] : chapterCatalog?.nodes || [];
  const loading = rootLoading || directoryLoading;
  const pathText = breadcrumbs.length ? catalogPathLabel(breadcrumbs) : "根目录";
  const canGoUp = breadcrumbs.length > 0;

  const goUp = useCallback(() => {
    if (!breadcrumbs.length) return;
    const parent = breadcrumbs[breadcrumbs.length - 2];
    onChangeDirectory(parent?.node_id || "");
  }, [breadcrumbs, onChangeDirectory]);

  const goRoot = useCallback(() => {
    onChangeDirectory("");
    setMoreOpen(false);
  }, [onChangeDirectory]);

  return (
    <section className="family-catalog-browser catalog-browser-body" aria-label="章节学习目录">
      <div className="family-catalog-browser-head">
        <div>
          <p>章节学习目录下</p>
          <span>{pathText}</span>
        </div>
        <div className="family-catalog-browser-actions" aria-label="目录操作">
          <button className="family-catalog-up-action" type="button" disabled={!canGoUp} onClick={goUp}>
            <ChevronUp size={13} />
            上一级
          </button>
          <button className="family-catalog-more-action" type="button" onClick={() => setMoreOpen(true)}>
            <MoreHorizontal size={14} />
            更多
          </button>
        </div>
      </div>

      {loading ? (
        <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载目录" />
      ) : error ? (
        <LearningState icon={<FolderOpen size={23} />} text={error} />
      ) : nodes.length ? (
        <CatalogNodeCards
          nodes={nodes}
          breadcrumbs={breadcrumbs}
          searchQuery={searchQuery}
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
              <button type="button" onClick={() => setMoreOpen(false)} aria-label="关闭目录更多">
                <X size={16} />
              </button>
            </div>
            <button type="button" onClick={goRoot} disabled={!activeDirectoryId}>
              回到章节目录
              <ChevronRight size={16} />
            </button>
            <button type="button" onClick={onClearSearch} disabled={!searchQuery.trim()}>
              清空目录搜索
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
