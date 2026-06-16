import { useEffect, useMemo, useState } from "react";
import type * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Empty, Flex, Progress, Segmented, Space, Statistic, Tag, Tooltip, Typography } from "antd";
import { DatabaseOutlined, ExperimentOutlined, QuestionCircleOutlined, TeamOutlined } from "@ant-design/icons";

import { api } from "../../api";
import type { LearningResourceOverview } from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { statusColor, statusLabel } from "../../lib/status";
import { areaMeta, countValue, questionTypeSummary, resourcePercent, shortResourceTitle } from "./resourceUtils";
import "./resources.css";

const { Text, Title } = Typography;

const periodicElementSymbols: Record<string, string> = {
  "1-1": "H",
  "1-18": "He",
  "2-1": "Li",
  "2-2": "Be",
  "2-13": "B",
  "2-14": "C",
  "2-15": "N",
  "2-16": "O",
  "2-17": "F",
  "2-18": "Ne",
  "3-1": "Na",
  "3-2": "Mg",
  "3-13": "Al",
  "3-14": "Si",
  "3-15": "P",
  "3-16": "S",
  "3-17": "Cl",
  "3-18": "Ar",
  "4-1": "K",
  "4-2": "Ca",
  "4-3": "Sc",
  "4-4": "Ti",
  "4-5": "V",
  "4-6": "Cr",
  "4-7": "Mn",
  "4-8": "Fe",
  "4-9": "Co",
  "4-10": "Ni",
  "4-11": "Cu",
  "4-12": "Zn",
  "4-13": "Ga",
  "4-14": "Ge",
  "4-15": "As",
  "4-16": "Se",
  "4-17": "Br",
  "4-18": "Kr",
  "5-1": "Rb",
  "5-2": "Sr",
  "5-3": "Y",
  "5-4": "Zr",
  "5-5": "Nb",
  "5-6": "Mo",
  "5-7": "Tc",
  "5-8": "Ru",
  "5-9": "Rh",
  "5-10": "Pd",
  "5-11": "Ag",
  "5-12": "Cd",
  "5-13": "In",
  "5-14": "Sn",
  "5-15": "Sb",
  "5-16": "Te",
  "5-17": "I",
  "5-18": "Xe",
  "6-1": "Cs",
  "6-2": "Ba",
  "6-3": "La",
  "6-4": "Hf",
  "6-5": "Ta",
  "6-6": "W",
  "6-7": "Re",
  "6-8": "Os",
  "6-9": "Ir",
  "6-10": "Pt",
  "6-11": "Au",
  "6-12": "Hg",
  "6-13": "Tl",
  "6-14": "Pb",
  "6-15": "Bi",
  "6-16": "Po",
  "6-17": "At",
  "6-18": "Rn",
  "7-1": "Fr",
  "7-2": "Ra",
  "7-3": "Ac",
  "7-4": "Rf",
  "7-5": "Db",
  "7-6": "Sg",
  "7-7": "Bh",
  "7-8": "Hs",
  "7-9": "Mt",
  "7-10": "Ds",
  "7-11": "Rg",
  "7-12": "Cn",
  "7-13": "Nh",
  "7-14": "Fl",
  "7-15": "Mc",
  "7-16": "Lv",
  "7-17": "Ts",
  "7-18": "Og",
};

const fBlockSymbols = [
  ["Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
  ["Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
];

const hydrogenNobleGasPositions = new Set(["1-1", "1-18", "2-18", "3-18", "4-18", "5-18", "6-18", "7-18"]);

function periodicAreaForPosition(defaultArea: string, period: number, group: number) {
  return hydrogenNobleGasPositions.has(`${period}-${group}`) ? "integrated" : defaultArea;
}

const periodicAreaCells = [
  ...Array.from({ length: 7 }, (_, index) => ({
    area: periodicAreaForPosition("s", index + 1, 1),
    group: 1,
    period: index + 1,
    symbol: periodicElementSymbols[`${index + 1}-1`],
  })),
  ...Array.from({ length: 6 }, (_, index) => ({ area: "s", group: 2, period: index + 2, symbol: periodicElementSymbols[`${index + 2}-2`] })),
  ...Array.from({ length: 4 }, (_, periodIndex) =>
    Array.from({ length: 8 }, (_, groupIndex) => ({
      area: "d",
      group: groupIndex + 3,
      period: periodIndex + 4,
      symbol: periodicElementSymbols[`${periodIndex + 4}-${groupIndex + 3}`],
    })),
  ).flat(),
  ...Array.from({ length: 4 }, (_, periodIndex) =>
    Array.from({ length: 2 }, (_, groupIndex) => ({
      area: "ds",
      group: groupIndex + 11,
      period: periodIndex + 4,
      symbol: periodicElementSymbols[`${periodIndex + 4}-${groupIndex + 11}`],
    })),
  ).flat(),
  ...Array.from({ length: 6 }, (_, periodIndex) =>
    Array.from({ length: 6 }, (_, groupIndex) => ({
      area: periodicAreaForPosition("p", periodIndex + 2, groupIndex + 13),
      group: groupIndex + 13,
      period: periodIndex + 2,
      symbol: periodicElementSymbols[`${periodIndex + 2}-${groupIndex + 13}`],
    })),
  ).flat(),
  ...Array.from({ length: 2 }, (_, periodIndex) =>
    Array.from({ length: 14 }, (_, groupIndex) => ({
      area: "f",
      group: groupIndex + 5,
      period: periodIndex + 8,
      symbol: fBlockSymbols[periodIndex][groupIndex],
    })),
  ).flat(),
  { area: "integrated", group: 18, period: 1, symbol: periodicElementSymbols["1-18"] },
];

function ResourceMiniStat({
  label,
  value,
  tone = "default",
  compact = false,
}: {
  label: string;
  value: string | number;
  tone?: "default" | "green" | "blue" | "amber";
  compact?: boolean;
}) {
  const className = ["resource-mini-stat", `resource-mini-stat-${tone}`, compact ? "compact" : ""].filter(Boolean).join(" ");
  return (
    <div className={className}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ResourceDomainCard({
  title,
  eyebrow,
  value,
  icon,
  children,
  tone = "green",
}: {
  title: string;
  eyebrow: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  children: React.ReactNode;
  tone?: "green" | "blue" | "amber" | "purple";
}) {
  return (
    <Card className={`resource-domain-card resource-domain-${tone}`}>
      <Flex align="flex-start" justify="space-between" gap={14}>
        <div className="resource-domain-copy">
          <Text type="secondary">{eyebrow}</Text>
          <strong>{title}</strong>
        </div>
        <span className="resource-domain-icon">{icon}</span>
      </Flex>
      <div className="resource-domain-value">{value}</div>
      {children}
    </Card>
  );
}

function ResourceOverviewNavigator({
  overview,
  selectedGroupId,
  onSelectGroup,
}: {
  overview?: LearningResourceOverview;
  selectedGroupId?: string;
  onSelectGroup: (groupId: string) => void;
}) {
  const groups = overview?.groups || [];
  const areas = overview?.areas || [];
  const selectedGroup = groups.find((group) => group.id === selectedGroupId) || groups[0];
  const selectedAreaId = selectedGroup?.area_id || areas[0]?.area_id;
  const selectedArea = areas.find((area) => area.area_id === selectedAreaId) || areas[0];
  const areaLookup = new Map(areas.map((area) => [area.area_id, area]));
  const generalArea = areaLookup.get("general");
  const specialAreas = ["other"]
    .map((areaId) => areaLookup.get(areaId))
    .filter((area): area is NonNullable<typeof area> => Boolean(area));
  const selectedAreaGroups = (selectedArea?.group_ids || [])
    .map((groupId) => groups.find((item) => item.id === groupId))
    .filter((group): group is NonNullable<typeof group> => Boolean(group));
  const showFamilyGrid = !(selectedArea?.area_id === "general" && selectedAreaGroups.length <= 1);

  const selectArea = (areaId: string) => {
    const area = areaLookup.get(areaId);
    const firstGroup = area?.group_ids.find((groupId) => groups.some((group) => group.id === groupId));
    if (firstGroup) onSelectGroup(firstGroup);
  };

  return (
    <Card className="resource-periodic-card">
      <Flex justify="space-between" align="flex-start" gap={16} className="resource-periodic-heading">
        <div>
          <Text type="secondary">资源目录</Text>
          <Title level={4}>按元素区选择章节</Title>
        </div>
        {selectedArea ? (
          <Tag color={areaMeta(selectedArea.area_id).ink}>
            {areaMeta(selectedArea.area_id).label} · {selectedArea.metrics.group_count}
          </Tag>
        ) : null}
      </Flex>

      <div className="resource-area-legend">
        {areas.map((area) => {
          const meta = areaMeta(area.area_id);
          const active = area.area_id === selectedArea?.area_id;
          return (
            <button
              key={area.area_id}
              type="button"
              className={active ? "selected" : ""}
              style={{ "--area-color": meta.color, "--area-ink": meta.ink } as React.CSSProperties}
              onClick={() => selectArea(area.area_id)}
            >
              <i />
              <span>{meta.label}</span>
              <b>{area.metrics.group_count}</b>
            </button>
          );
        })}
      </div>

      <div className="resource-periodic-grid" aria-label="元素周期表式资源区选择">
        {Array.from({ length: 18 }, (_, index) => (
          <div className="resource-periodic-group-number" key={index + 1} style={{ gridColumn: index + 2, gridRow: 1 }}>
            {index + 1}
          </div>
        ))}
        {["一", "二", "三", "四", "五", "六", "七", "镧系", "锕系"].map((period, index) => (
          <div className="resource-periodic-period-number" key={period} style={{ gridColumn: 1, gridRow: index + 2 }}>
            {period}
          </div>
        ))}
        {generalArea ? (
          <button
            type="button"
            aria-label={`选择通识资源，${generalArea.metrics.knowledge_point_count} 个知识点`}
            className={
              selectedArea?.area_id === "general"
                ? "resource-periodic-general-zone active"
                : "resource-periodic-general-zone"
            }
            style={
              {
                "--area-color": areaMeta("general").color,
                "--area-ink": areaMeta("general").ink,
              } as React.CSSProperties
            }
            onClick={() => selectArea("general")}
          />
        ) : null}
        {periodicAreaCells.map((cell, index) => {
          const meta = areaMeta(cell.area);
          const available = areaLookup.has(cell.area);
          const active = selectedArea?.area_id === cell.area;
          return (
            <button
              key={`${cell.area}-${cell.group}-${cell.period}-${index}`}
              type="button"
              disabled={!available}
              className={active ? "resource-element-cell selected-area" : "resource-element-cell"}
              style={{
                gridColumn: cell.group + 1,
                gridRow: cell.period + 1,
                background: active ? meta.selected : meta.color,
                "--cell-ink": meta.ink,
              } as React.CSSProperties}
              title={`${cell.symbol || meta.label} · ${meta.label}`}
              onClick={() => selectArea(cell.area)}
            >
              <span>{cell.symbol}</span>
            </button>
          );
        })}
      </div>

      {specialAreas.length ? (
        <div className="resource-periodic-specials">
          {specialAreas.map((area) => {
            const meta = areaMeta(area.area_id);
            const active = area.area_id === selectedArea?.area_id;
            return (
              <button
                key={area.area_id}
                type="button"
                className={active ? "active" : ""}
                style={{ "--area-color": meta.color, "--area-ink": meta.ink } as React.CSSProperties}
                onClick={() => selectArea(area.area_id)}
              >
                <span>{meta.label}</span>
                <strong>{area.area_id === "general" ? "通识/跨章节" : area.area_name}</strong>
                <small>
                  知识点 {area.metrics.knowledge_point_count} · 实验 {area.metrics.experiment_count} · 题目 {area.metrics.question_count}
                </small>
              </button>
            );
          })}
        </div>
      ) : null}

      {showFamilyGrid ? (
        <div className="resource-family-grid">
          {selectedAreaGroups.map((group) => {
            const active = group.id === selectedGroup?.id;
            return (
              <button
                key={group.id}
                type="button"
                className={active ? "resource-family-card active" : "resource-family-card"}
                onClick={() => onSelectGroup(group.id)}
              >
                <span>{group.area_name}</span>
                <strong>{shortResourceTitle(group.title)}</strong>
                <small>
                  知识点 {group.knowledge_point_count} · 实验 {group.experiment_count} · 题目 {group.question_count}
                </small>
              </button>
            );
          })}
        </div>
      ) : null}
    </Card>
  );
}

function ResourceChapterWorkbench({ group }: { group?: LearningResourceOverview["groups"][number] }) {
  if (!group) return null;
  const area = areaMeta(group.area_id);
  const isGeneralGroup = group.kind === "general" || group.area_id === "general";
  const publishedQuestions = countValue(group.question_status_counts, "published");
  const publishedVideo = Number(group.media_published_count || 0);
  const pendingVideo = Math.max(0, Number(group.media_count || 0) - publishedVideo);
  const questionTypes = questionTypeSummary(group.question_type_counts);

  return (
    <Card className="resource-workbench-card">
      <div className="resource-workbench-hero" style={{ "--area-color": area.color, "--area-ink": area.ink } as React.CSSProperties}>
        <div>
          <Space wrap className="resource-workbench-tags">
            <Tag color={area.ink}>{area.label}</Tag>
            {group.kind === "general" ? <Tag color="blue">通识</Tag> : <Tag>章节</Tag>}
          </Space>
          <Title level={3}>{group.title}</Title>
        </div>
        <div className="resource-workbench-metrics">
          <Statistic title="知识单元" value={group.knowledge_unit_count} />
          <Statistic title="知识点" value={group.knowledge_point_count} />
          <Statistic title="实验" value={group.experiment_count} />
          <Statistic title="视频" value={group.media_count} />
          <Statistic title="题目" value={group.question_count} />
        </div>
      </div>

      <div className="resource-workbench-grid">
        <section className="resource-workbench-panel resource-knowledge-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">知识框架</Text>
              <h3>知识单元与知识点</h3>
            </div>
          </Flex>
          <div className="resource-knowledge-status">
            <div>
              <span>知识单元</span>
              <strong>{group.knowledge_unit_count}</strong>
            </div>
            <div>
              <span>知识点</span>
              <strong>{group.knowledge_point_count}</strong>
            </div>
          </div>
          <div className="resource-unit-stack">
            {group.units.length ? (
              group.units.map((unit) => (
                <div key={unit.unit_id} className="resource-unit-card">
                  <Text strong>{unit.unit_title}</Text>
                  <div className="resource-kp-list">
                    {unit.knowledge_points.slice(0, 4).map((point) => (
                      <Tooltip key={point.knowledge_point_id} title={point.content} placement="right" overlayClassName="resource-kp-tooltip">
                        <div className="resource-kp-node">
                          <span>{point.content}</span>
                        </div>
                      </Tooltip>
                    ))}
                    {unit.knowledge_points.length > 4 ? (
                      <Text type="secondary" className="resource-more-text">
                        另有 {unit.knowledge_points.length - 4} 个知识点
                      </Text>
                    ) : null}
                  </div>
                </div>
              ))
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无知识单元" />
            )}
          </div>
        </section>

        <section className="resource-workbench-panel resource-experiment-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">{isGeneralGroup ? "通识定位" : "实验与视频"}</Text>
              <h3>{isGeneralGroup ? "通识资源说明" : "正式实验资源"}</h3>
            </div>
          </Flex>
          {isGeneralGroup ? (
            <div className="resource-general-context-card">
              <strong>通识资源不绑定正式实验</strong>
              <span>这里用于承载跨章节基础知识、模型方法和通用概念，作为理论教材的背景支撑，不要求引用实验视频。</span>
              <div className="resource-general-context-tags">
                <Tag color="green">跨章节</Tag>
              </div>
              <div className="resource-general-context-stats">
                <ResourceMiniStat label="知识单元" value={group.knowledge_unit_count} compact />
                <ResourceMiniStat label="知识点" value={group.knowledge_point_count} compact />
              </div>
            </div>
          ) : (
            <>
              <div className="resource-readiness-row">
                <div>
                  <span>已绑定视频</span>
                  <strong>{group.media_count}</strong>
                </div>
                <div>
                  <span>已发布视频</span>
                  <strong>{publishedVideo}</strong>
                </div>
                <div>
                  <span>待发布</span>
                  <strong>{pendingVideo}</strong>
                </div>
              </div>
              {!group.media_count ? <Alert type="warning" showIcon message="本章节实验还没有绑定视频资源" /> : null}
              <div className="resource-experiment-list">
                {group.experiments.length ? (
                  group.experiments.map((experiment) => (
                    <div key={experiment.id} className="resource-experiment-card">
                      <Flex justify="space-between" gap={12} align="flex-start">
                        <div>
                          <Text strong>
                            {experiment.code ? `${experiment.code} · ` : ""}
                            {experiment.title}
                          </Text>
                          <Space wrap className="resource-experiment-meta">
                            <Tag color={statusColor[experiment.status] || "default"}>{statusLabel[experiment.status] || experiment.status}</Tag>
                            <Tag color={experiment.media_count ? "blue" : "default"}>视频 {experiment.media_count}</Tag>
                            <Tag color={experiment.media_published_count ? "green" : "default"}>已发布视频 {experiment.media_published_count || 0}</Tag>
                            <Tag color={experiment.question_count ? "green" : "default"}>题目 {experiment.question_count}</Tag>
                          </Space>
                        </div>
                      </Flex>
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无绑定实验" />
                )}
              </div>
            </>
          )}
        </section>

        <section className="resource-workbench-panel resource-question-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">题库覆盖</Text>
              <h3>总数与题型</h3>
            </div>
          </Flex>
          <div className="resource-question-status">
            <div>
              <span>题目总数</span>
              <strong>{group.question_count}</strong>
            </div>
            <div>
              <span>已发布</span>
              <strong>{publishedQuestions}</strong>
            </div>
          </div>
          <div className="resource-question-type-list">
            {questionTypes.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <Progress percent={resourcePercent(item.value, group.question_count)} size="small" showInfo={false} />
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Card>
  );
}

type ExperimentFrameworkOverviewData = NonNullable<LearningResourceOverview["experiment_framework"]>;
type ExperimentFrameworkNodeData = ExperimentFrameworkOverviewData["nodes"][number];
type ExperimentFrameworkLinkData = ExperimentFrameworkOverviewData["formal_links"][number];

function experimentFrameworkNodeLabel(node?: ExperimentFrameworkNodeData | null) {
  if (!node) return "-";
  if (node.node_type === "book") return "教材";
  if (node.node_type === "chapter") return "章节";
  if (node.node_type === "protocol") return "实验条目";
  return "小节";
}

function collectExperimentFrameworkNodeIds(framework: ExperimentFrameworkOverviewData, rootId: string) {
  const children = new Map<string, string[]>();
  framework.nodes.forEach((node) => {
    if (!node.parent_id) return;
    const list = children.get(node.parent_id) || [];
    list.push(node.id);
    children.set(node.parent_id, list);
  });
  const ids = new Set<string>();
  const stack = [rootId];
  while (stack.length) {
    const nodeId = stack.pop();
    if (!nodeId || ids.has(nodeId)) continue;
    ids.add(nodeId);
    (children.get(nodeId) || []).forEach((childId) => stack.push(childId));
  }
  return ids;
}

function uniqueExperimentFrameworkLinks(links: ExperimentFrameworkLinkData[]) {
  const byExperiment = new Map<string, ExperimentFrameworkLinkData & { relation_count: number; has_canonical_evidence: boolean }>();
  links.forEach((link) => {
    const existing = byExperiment.get(link.experiment_id);
    if (!existing) {
      byExperiment.set(link.experiment_id, {
        ...link,
        relation_count: 1,
        has_canonical_evidence: link.relation_type === "canonical_evidence",
      });
      return;
    }
    existing.relation_count += 1;
    existing.has_canonical_evidence = existing.has_canonical_evidence || link.relation_type === "canonical_evidence";
  });
  return Array.from(byExperiment.values()).sort((a, b) => {
    const orderA = Number(a.sort_order || 0);
    const orderB = Number(b.sort_order || 0);
    if (orderA !== orderB) return orderA - orderB;
    return String(a.experiment_code || "").localeCompare(String(b.experiment_code || ""), "zh-Hans-CN");
  });
}

function preferredExperimentFrameworkRoot(roots: ExperimentFrameworkNodeData[]) {
  return [...roots].sort((a, b) => {
    const formalDelta = Number(b.formal_experiment_count || 0) - Number(a.formal_experiment_count || 0);
    if (formalDelta) return formalDelta;
    const evidenceDelta = Number(b.evidence_count || 0) - Number(a.evidence_count || 0);
    if (evidenceDelta) return evidenceDelta;
    return a.display_order - b.display_order;
  })[0];
}

function isStructuralExperimentFrameworkRoot(node: ExperimentFrameworkNodeData) {
  const compactTitle = node.title.replace(/\s+/g, "");
  return (
    /^第[一二三四五六七八九十]+部分/.test(compactTitle) &&
    Number(node.evidence_count || 0) <= 1 &&
    Number(node.child_count || 0) === 0 &&
    Number(node.formal_experiment_count || 0) === 0
  );
}

function experimentFrameworkDisplayRoots(roots: ExperimentFrameworkNodeData[]) {
  const visible = roots.filter((node) => !isStructuralExperimentFrameworkRoot(node));
  return visible.length ? visible : roots;
}

function experimentFrameworkSourceContext(roots: ExperimentFrameworkNodeData[]) {
  return roots.find((node) => isStructuralExperimentFrameworkRoot(node));
}

function experimentFrameworkRootActive(
  framework: ExperimentFrameworkOverviewData,
  root: ExperimentFrameworkNodeData,
  selectedNode?: ExperimentFrameworkNodeData,
) {
  if (!selectedNode) return false;
  if (root.id === selectedNode.id) return true;
  return collectExperimentFrameworkNodeIds(framework, root.id).has(selectedNode.id);
}

function ExperimentKnowledgeFrameworkPanel({ framework }: { framework?: LearningResourceOverview["experiment_framework"] | null }) {
  const rawRoots = framework?.roots || [];
  const roots = useMemo(() => experimentFrameworkDisplayRoots(rawRoots), [rawRoots]);
  const [selectedNodeId, setSelectedNodeId] = useState<string>();

  useEffect(() => {
    if (!framework?.available || !roots.length) return;
    if (!selectedNodeId || !framework.nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(preferredExperimentFrameworkRoot(roots).id);
    }
  }, [framework, roots, selectedNodeId]);

  if (!framework) return null;
  if (!framework.available) {
    return (
      <section className="experiment-framework-card">
        <Alert
          type="info"
          showIcon
          message="实验教材知识框架尚未导入"
          description="导入无机化学实验教材的标准分块后，这里会展示实验基本知识、基本操作、元素性质实验和通识内容。"
        />
      </section>
    );
  }

  const selectedNode = framework.nodes.find((node) => node.id === selectedNodeId) || preferredExperimentFrameworkRoot(roots);
  const selectedNodeIds = selectedNode ? collectExperimentFrameworkNodeIds(framework, selectedNode.id) : new Set<string>();
  const childNodes = framework.nodes
    .filter((node) => node.parent_id === selectedNode?.id)
    .sort((a, b) => a.display_order - b.display_order);
  const relatedLinks = uniqueExperimentFrameworkLinks(
    framework.formal_links.filter((link) => selectedNodeIds.has(link.node_id)),
  );
  const evidenceLinkCount = framework.formal_links.filter(
    (link) => selectedNodeIds.has(link.node_id) && link.relation_type === "canonical_evidence",
  ).length;
  const hasOperationalCoverage =
    Number(selectedNode?.formal_experiment_count || 0) > 0 ||
    Number(selectedNode?.video_count || 0) > 0 ||
    Number(selectedNode?.question_count || 0) > 0;

  return (
    <section className="experiment-framework-card">
      <div className="experiment-framework-layout">
        <section className="experiment-framework-tree">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">教材目录</Text>
              <h3>{framework.source.book_title || "无机化学实验（第四版）"}</h3>
            </div>
          </Flex>
          <div className="experiment-framework-root-list">
            {roots.map((node) => (
              <button
                key={node.id}
                type="button"
                className={experimentFrameworkRootActive(framework, node, selectedNode) ? "active" : ""}
                onClick={() => setSelectedNodeId(node.id)}
              >
                <span>{experimentFrameworkNodeLabel(node)}</span>
                <strong>{node.title}</strong>
                <small>
                  语料分块 {node.evidence_count}
                  {node.formal_experiment_count ? ` · 实验 ${node.formal_experiment_count}` : ""}
                  {node.question_count ? ` · 题目 ${node.question_count}` : ""}
                </small>
              </button>
            ))}
          </div>
        </section>

        <section className="experiment-framework-detail">
          <div className="experiment-framework-detail-hero">
            <div>
              <Space wrap>
                <Tag color="green">{experimentFrameworkNodeLabel(selectedNode)}</Tag>
                {selectedNode?.page_start ? <Tag>页码 {selectedNode.page_start}-{selectedNode.page_end || selectedNode.page_start}</Tag> : null}
              </Space>
              <Title level={4}>{selectedNode?.title}</Title>
              <Text type="secondary">{(selectedNode?.full_path || []).join(" / ")}</Text>
            </div>
            <div className={hasOperationalCoverage ? "experiment-framework-detail-stats" : "experiment-framework-support-summary"}>
              <Statistic title="语料分块" value={selectedNode?.evidence_count || 0} />
              <Statistic title="小节" value={childNodes.length} />
              {hasOperationalCoverage ? (
                <>
                  <Statistic title="正式实验" value={selectedNode?.formal_experiment_count || 0} />
                  <Statistic title="题目" value={selectedNode?.question_count || 0} />
                </>
              ) : null}
            </div>
          </div>

          <div className="experiment-framework-detail-grid">
            <div className="experiment-framework-child-panel">
              <Flex justify="space-between" align="center" gap={12}>
                <h3>小节</h3>
                <Tag>{childNodes.length} 个小节</Tag>
              </Flex>
              <div className="experiment-framework-child-list">
                {childNodes.length ? (
                  childNodes.map((node) => (
                    <div key={node.id} className="experiment-framework-child-card">
                      <span>{experimentFrameworkNodeLabel(node)}</span>
                      <strong>{node.title}</strong>
                      <small>
                        语料分块 {node.evidence_count}
                        {node.formal_experiment_count ? ` · 实验 ${node.formal_experiment_count}` : ""}
                        {node.question_count ? ` · 题目 ${node.question_count}` : ""}
                      </small>
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无小节" />
                )}
              </div>
            </div>

            <div className="experiment-framework-formal-panel">
              <Flex justify="space-between" align="center" gap={12}>
                <h3>关联正式实验</h3>
                <Tag color={evidenceLinkCount ? "green" : "default"}>语料映射 {evidenceLinkCount}</Tag>
              </Flex>
              <div className="experiment-framework-formal-list">
                {relatedLinks.length ? (
                  relatedLinks.map((link) => (
                    <div key={link.experiment_id} className="experiment-framework-formal-card">
                      <Text strong>
                        {link.experiment_code ? `${link.experiment_code} · ` : ""}
                        {link.experiment_title}
                      </Text>
                      <Space wrap>
                        <Tag color={statusColor[link.experiment_status] || "default"}>
                          {statusLabel[link.experiment_status] || link.experiment_status}
                        </Tag>
                        <Tag color={link.has_canonical_evidence ? "green" : "blue"}>
                          {link.has_canonical_evidence ? "教材语料" : "目录映射"}
                        </Tag>
                        {link.relation_count > 1 ? <Tag>关联 {link.relation_count}</Tag> : null}
                      </Space>
                    </div>
                  ))
                ) : (
                  <Alert
                    className="experiment-framework-support-alert"
                    type="info"
                    showIcon
                    message="本章暂无正式实验引用"
                    description="本章属于实验通识、基本操作无需关联实验。"
                  />
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}

type ResourceSourceKey = "theory" | "experiment";

function ResourceSourceWorkspace({
  overview,
  selectedGroup,
  onSelectGroup,
}: {
  overview?: LearningResourceOverview;
  selectedGroup?: LearningResourceOverview["groups"][number];
  onSelectGroup: (groupId: string) => void;
}) {
  const [activeSource, setActiveSource] = useState<ResourceSourceKey>("theory");
  const knowledgeDomain = overview?.domains?.knowledge;
  const experimentFramework = overview?.experiment_framework;

  return (
    <section className="resource-source-workspace">
      <div className="resource-source-workspace-header">
        <Segmented
          value={activeSource}
          onChange={(value) => setActiveSource(value as ResourceSourceKey)}
          options={[
            {
              value: "theory",
              label: (
                <span className="resource-source-switch-label">
                  <span>理论教材</span>
                  <b>{knowledgeDomain?.source_chunk_count || 0} 语料分块</b>
                </span>
              ),
            },
            {
              value: "experiment",
              label: (
                <span className="resource-source-switch-label">
                  <span>实验教材</span>
                  <b>{experimentFramework?.metrics.linked_chunk_count || 0} 语料分块</b>
                </span>
              ),
            },
          ]}
        />
      </div>

      {activeSource === "theory" ? (
        <div className="resource-source-panel resource-source-theory-panel">
          <ResourceOverviewNavigator overview={overview} selectedGroupId={selectedGroup?.id} onSelectGroup={onSelectGroup} />
          <ResourceChapterWorkbench group={selectedGroup} />
        </div>
      ) : (
        <div className="resource-source-panel resource-source-experiment-panel">
          <ExperimentKnowledgeFrameworkPanel framework={overview?.experiment_framework} />
        </div>
      )}
    </section>
  );
}

export function LearningResourcesPage() {
  const overview = useQuery({
    queryKey: ["admin-learning-resources-overview"],
    queryFn: () => api<LearningResourceOverview>("/api/admin/learning-resources/overview"),
  });
  const groups = overview.data?.groups || [];
  const [selectedGroupId, setSelectedGroupId] = useState<string>();

  useEffect(() => {
    if (!groups.length) return;
    if (!selectedGroupId || !groups.some((group) => group.id === selectedGroupId)) {
      setSelectedGroupId(groups[0].id);
    }
  }, [groups, selectedGroupId]);

  const selectedGroup = groups.find((group) => group.id === selectedGroupId) || groups[0];
  const domains = overview.data?.domains;
  const knowledge = domains?.knowledge;
  const experimentVideo = domains?.experiment_video;
  const questionBank = domains?.question_bank;
  const classesStudents = domains?.classes_students;
  const publishedQuestions = Number(questionBank?.published_question_count || 0);
  const totalQuestions = Number(questionBank?.question_count || 0);
  const publishedVideos = Number(experimentVideo?.published_video_count || 0);
  const totalVideoAssets = Number(experimentVideo?.video_asset_count || 0);
  const rosterCount = Number(classesStudents?.roster_count || 0);
  const activeStudents = Number(classesStudents?.active_student_count || 0);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="资源总览"
        description="统一查看知识框架、智能检索事实资源、实验视频、题库与班级学生的建设状态。"
      />

      <QueryState loading={overview.isLoading} error={overview.error} empty={!groups.length}>
        <div className="resource-dashboard-grid">
          <ResourceDomainCard
            title="知识框架 / 检索语料"
            eyebrow="教材事实资源"
            value={`${knowledge?.knowledge_unit_count || 0} / ${knowledge?.knowledge_point_count || 0}`}
            icon={<DatabaseOutlined />}
          >
            <div className="resource-domain-subgrid">
              <span>知识单元</span>
              <strong>{knowledge?.knowledge_unit_count || 0}</strong>
              <span>知识点</span>
              <strong>{knowledge?.knowledge_point_count || 0}</strong>
              <span>标准语料分块</span>
              <strong>{knowledge?.source_chunk_count || 0}</strong>
              <span>向量索引</span>
              <strong>{knowledge?.embedding_count || 0}</strong>
            </div>
          </ResourceDomainCard>

          <ResourceDomainCard
            title="实验与视频"
            eyebrow="实验管理概况"
            value={`${experimentVideo?.experiment_count || 0} 个实验`}
            icon={<ExperimentOutlined />}
            tone="blue"
          >
            <Progress percent={resourcePercent(publishedVideos, Math.max(totalVideoAssets, 1))} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>视频库</span>
              <strong>{totalVideoAssets}</strong>
              <span>已发布引用</span>
              <strong>{publishedVideos}</strong>
            </div>
            {!totalVideoAssets ? <Text type="secondary">视频库暂未上传资源</Text> : null}
          </ResourceDomainCard>

          <ResourceDomainCard
            title="题库"
            eyebrow="当前题目状态"
            value={`${totalQuestions} 道`}
            icon={<QuestionCircleOutlined />}
            tone="amber"
          >
            <Progress percent={resourcePercent(publishedQuestions, totalQuestions)} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>题目总数</span>
              <strong>{totalQuestions}</strong>
              <span>已发布</span>
              <strong>{publishedQuestions}</strong>
              <span>单选/判断/填空</span>
              <strong>
                {countValue(questionBank?.type_counts, "single_choice")} / {countValue(questionBank?.type_counts, "true_false")} / {countValue(questionBank?.type_counts, "fill_blank")}
              </strong>
            </div>
          </ResourceDomainCard>

          <ResourceDomainCard
            title="班级与学生"
            eyebrow="教学运营"
            value={`${classesStudents?.class_count || 0} 个班级`}
            icon={<TeamOutlined />}
            tone="purple"
          >
            <Progress percent={resourcePercent(activeStudents, rosterCount)} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>花名册学生</span>
              <strong>{rosterCount}</strong>
              <span>已激活账号</span>
              <strong>{activeStudents}</strong>
            </div>
            {!classesStudents?.class_count ? <Text type="secondary">尚未建立班级与花名册</Text> : null}
          </ResourceDomainCard>
        </div>

        <ResourceSourceWorkspace overview={overview.data} selectedGroup={selectedGroup} onSelectGroup={setSelectedGroupId} />
      </QueryState>
    </Space>
  );
}
