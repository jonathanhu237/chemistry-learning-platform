import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { Check, ChevronRight, ClipboardList, LoaderCircle, RotateCcw, Search, X } from "lucide-react";
import {
  errorMessage,
  getStudentCustomAssessmentOptions,
  startStudentCustomAssessment,
  type CustomAssessmentScopeNode,
  type StudentCustomAssessmentOptionsResponse,
} from "../../api";
import { storePosttestSession } from "../../app/router/assessmentSessionStore";
import { navigateToAssessmentSession } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { MobileButton, MobileEmptyState, MobileField } from "../../mobile/primitives";

type QuestionsPerPoint = 1 | 2 | 3;

export function assessmentScopeKindLabel(kind: CustomAssessmentScopeNode["kind"]): string {
  if (kind === "chapter") return "章节";
  if (kind === "directory") return "目录";
  return "点位";
}

export function filterAssessmentScopeTree(nodes: CustomAssessmentScopeNode[], keyword: string): CustomAssessmentScopeNode[] {
  const normalizedKeyword = keyword.trim().toLowerCase();
  if (!normalizedKeyword) return nodes;
  return nodes
    .map((node) => {
      const children = filterAssessmentScopeTree(node.children || [], normalizedKeyword);
      const selfMatches = `${node.title} ${assessmentScopeKindLabel(node.kind)}`.toLowerCase().includes(normalizedKeyword);
      if (!selfMatches && !children.length) return null;
      return { ...node, children };
    })
    .filter((node): node is CustomAssessmentScopeNode => Boolean(node));
}

export function selectedAssessmentPointIds(nodes: CustomAssessmentScopeNode[], selectedIds: Set<string>): string[] {
  const result = new Set<string>();
  const walk = (node: CustomAssessmentScopeNode, inheritedSelected: boolean) => {
    const selected = inheritedSelected || selectedIds.has(node.id);
    if (node.kind === "point" && selected && node.question_count > 0) result.add(node.id);
    node.children.forEach((child) => walk(child, selected));
  };
  nodes.forEach((node) => walk(node, false));
  return Array.from(result);
}

function descendantScopeIds(node: CustomAssessmentScopeNode): string[] {
  return node.children.flatMap((child) => [child.id, ...descendantScopeIds(child)]);
}

function findAssessmentScopeNode(nodes: CustomAssessmentScopeNode[], nodeId: string): CustomAssessmentScopeNode | null {
  for (const node of nodes) {
    if (node.id === nodeId) return node;
    const descendant = findAssessmentScopeNode(node.children, nodeId);
    if (descendant) return descendant;
  }
  return null;
}

export function toggleAssessmentScopeSelection(
  nodes: CustomAssessmentScopeNode[],
  selectedIds: Set<string>,
  nodeId: string,
): Set<string> {
  const next = new Set(selectedIds);
  if (next.has(nodeId)) {
    next.delete(nodeId);
    return next;
  }
  const completeNode = findAssessmentScopeNode(nodes, nodeId);
  if (!completeNode) return next;
  descendantScopeIds(completeNode).forEach((id) => next.delete(id));
  next.add(nodeId);
  return next;
}

function selectedScopes(nodes: CustomAssessmentScopeNode[], selectedIds: Set<string>): Array<{ id: string; title: string }> {
  return nodes.flatMap((node) => [
    ...(selectedIds.has(node.id) ? [{ id: node.id, title: node.title }] : []),
    ...selectedScopes(node.children, selectedIds),
  ]);
}

function AssessmentScopeTree({
  nodes,
  selectedIds,
  disabled,
  onToggle,
  depth = 0,
  inheritedSelected = false,
}: {
  nodes: CustomAssessmentScopeNode[];
  selectedIds: Set<string>;
  disabled: boolean;
  onToggle: (node: CustomAssessmentScopeNode) => void;
  depth?: number;
  inheritedSelected?: boolean;
}) {
  return (
    <div className={depth === 0 ? "custom-scope-tree" : "custom-scope-children"} aria-label={depth === 0 ? "可选测评范围" : undefined}>
      {nodes.map((node) => {
        const selected = selectedIds.has(node.id);
        const covered = inheritedSelected && !selected;
        const unavailable = disabled || node.question_count <= 0;
        return (
          <div className="custom-scope-node" key={node.id}>
            <button
              type="button"
              className={[selected ? "selected" : "", covered ? "covered" : ""].filter(Boolean).join(" ")}
              disabled={unavailable || covered}
              aria-pressed={selected}
              onClick={() => onToggle(node)}
              style={{ paddingLeft: `${12 + depth * 18}px` }}
            >
              <span className="custom-scope-branch" aria-hidden="true">
                {depth ? <ChevronRight size={13} /> : null}
              </span>
              <span className="custom-scope-check" aria-hidden="true">
                {selected || covered ? <Check size={16} /> : null}
              </span>
              <span className="custom-scope-copy">
                <strong>{node.title}</strong>
                <small>{covered ? `随上级${assessmentScopeKindLabel(node.kind)}纳入` : assessmentScopeKindLabel(node.kind)}</small>
              </span>
              <em>{node.question_count} 题</em>
            </button>
            {node.children.length ? (
              <AssessmentScopeTree
                nodes={node.children}
                selectedIds={selectedIds}
                disabled={disabled}
                onToggle={onToggle}
                depth={depth + 1}
                inheritedSelected={inheritedSelected || selected}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function safeQuestionsPerPointOptions(data: StudentCustomAssessmentOptionsResponse | null): QuestionsPerPoint[] {
  const options = data?.settings.questions_per_point_options?.filter(
    (value): value is QuestionsPerPoint => value === 1 || value === 2 || value === 3,
  );
  return options?.length ? Array.from(new Set(options)).sort((left, right) => left - right) : [1, 2, 3];
}

export function AssessmentCustomPage() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [data, setData] = useState<StudentCustomAssessmentOptionsResponse | null>(null);
  const [query, setQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [questionsPerPoint, setQuestionsPerPoint] = useState<QuestionsPerPoint>(1);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [startError, setStartError] = useState("");
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError("");
    getStudentCustomAssessmentOptions()
      .then((response) => {
        if (cancelled) return;
        setData(response);
        const fallback = safeQuestionsPerPointOptions(response)[0];
        const defaultValue = response.settings.default_questions_per_point;
        setQuestionsPerPoint(defaultValue === 1 || defaultValue === 2 || defaultValue === 3 ? defaultValue : fallback);
      })
      .catch((requestError) => {
        if (!cancelled) {
          setData(null);
          setLoadError(errorMessage(requestError));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [retryKey]);

  const scopeTree = data?.scope_tree || [];
  const filteredScopeTree = useMemo(() => filterAssessmentScopeTree(scopeTree, query), [query, scopeTree]);
  const perPointOptions = useMemo(() => safeQuestionsPerPointOptions(data), [data]);
  const selectedPointCount = useMemo(() => selectedAssessmentPointIds(scopeTree, selectedIds).length, [scopeTree, selectedIds]);
  const selectedScopeItems = useMemo(() => selectedScopes(scopeTree, selectedIds), [scopeTree, selectedIds]);
  const estimatedQuestionCount = selectedPointCount * questionsPerPoint;
  const disabled = data?.settings.enabled === false;

  const toggleScope = (node: CustomAssessmentScopeNode) => {
    if (disabled || node.question_count <= 0) return;
    setStartError("");
    setSelectedIds((current) => toggleAssessmentScopeSelection(scopeTree, current, node.id));
  };

  const startCustomAssessment = async () => {
    if (disabled) return;
    if (!selectedIds.size || !selectedPointCount) {
      setStartError("请先选择至少 1 个有可用题目的章节、目录或点位。");
      return;
    }
    setStarting(true);
    setStartError("");
    try {
      const response = await startStudentCustomAssessment(Array.from(selectedIds), questionsPerPoint);
      storePosttestSession(response);
      navigateToAssessmentSession(navigate, response.session_id, "assessment-custom");
    } catch (requestError) {
      setStartError(errorMessage(requestError));
    } finally {
      setStarting(false);
    }
  };

  return (
    <DetailPageFrame title="自主测评" source={search.from || "assessment"}>
      <section className="learning-panel custom-assessment-page" aria-label="自主测评">
        {loading ? (
          <MobileEmptyState className="empty-learning-card" icon={<LoaderCircle className="spin" size={20} />}>
            <span>正在加载可选测评范围</span>
          </MobileEmptyState>
        ) : data ? (
          <>
            <section className="posttest-context">
              <div>
                <p>自主测评</p>
                <h2>按章节、目录或点位选择范围</h2>
                <div className="assessment-composition">
                  <span>已选 {selectedPointCount} 个点位</span>
                  <span>每点位 {questionsPerPoint} 题</span>
                  <span>预计最多 {estimatedQuestionCount} 题</span>
                </div>
              </div>
              <span>{scopeTree.length} 章</span>
            </section>

            {disabled ? <div className="form-hint">老师暂未开放自主测评，请返回使用智能组卷。</div> : null}
            {startError ? <div className="form-error">{startError}</div> : null}

            <div className="custom-assessment-toolbar">
              <label className="custom-search-field">
                <Search size={18} />
                <MobileField
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="搜索章节、目录或点位"
                  aria-label="搜索测评范围"
                />
                {query ? (
                  <button type="button" className="custom-search-clear" aria-label="清空范围搜索" onClick={() => setQuery("")}>
                    <X size={16} />
                  </button>
                ) : null}
              </label>
              <div className="custom-count-field">
                <span>每个点位抽题数</span>
                <div className="custom-count-row" role="group" aria-label="每个点位抽题数">
                  {perPointOptions.map((count) => (
                    <button
                      type="button"
                      key={count}
                      className={questionsPerPoint === count ? "selected" : ""}
                      disabled={disabled}
                      aria-pressed={questionsPerPoint === count}
                      onClick={() => setQuestionsPerPoint(count)}
                    >
                      {count}
                    </button>
                  ))}
                </div>
              </div>
              <div className="custom-selection-toolbar">
                <div className="custom-selection-summary" aria-label="已选测评范围">
                  {selectedScopeItems.slice(0, 4).map((item) => (
                    <span key={item.id}>{item.title}</span>
                  ))}
                  {selectedScopeItems.length > 4 ? <span>+{selectedScopeItems.length - 4}</span> : null}
                  {!selectedScopeItems.length ? <small>可直接选择上级范围，系统会展开到其中可用点位。</small> : null}
                </div>
                {selectedIds.size ? (
                  <button type="button" className="custom-selection-clear" onClick={() => setSelectedIds(new Set())}>
                    清空
                  </button>
                ) : null}
              </div>
            </div>

            {filteredScopeTree.length ? (
              <AssessmentScopeTree nodes={filteredScopeTree} selectedIds={selectedIds} disabled={disabled} onToggle={toggleScope} />
            ) : (
              <MobileEmptyState className="empty-learning-card" icon={<Search size={20} />}>
                <span>没有匹配的测评范围</span>
              </MobileEmptyState>
            )}

            <MobileButton
              className="primary-action full custom-start-action"
              type="button"
              loading={starting}
              disabled={disabled || !selectedPointCount}
              onClick={() => void startCustomAssessment()}
            >
              {starting ? <LoaderCircle className="spin" size={18} /> : <ClipboardList size={18} />}
              <span>{starting ? "正在组卷" : "开始自主测评"}</span>
            </MobileButton>
          </>
        ) : (
          <MobileEmptyState className="empty-learning-card custom-assessment-load-error" icon={<ClipboardList size={20} />}>
            <span>{loadError || "暂时无法加载自主测评范围。"}</span>
            <MobileButton variant="secondary" type="button" onClick={() => setRetryKey((key) => key + 1)}>
              <RotateCcw size={17} />
              <span>重新加载</span>
            </MobileButton>
          </MobileEmptyState>
        )}
      </section>
    </DetailPageFrame>
  );
}
