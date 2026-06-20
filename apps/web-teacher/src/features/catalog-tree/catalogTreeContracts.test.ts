import { describe, expect, it } from "vitest";

import catalogTreeApiSource from "../../api/catalogTree.ts?raw";
import advancedPanelSource from "./CatalogAdvancedPanel.tsx?raw";
import aiContextPanelSource from "./CatalogAiContextPanel.tsx?raw";
import editorHeaderSource from "./CatalogEditorHeader.tsx?raw";
import contentPanelSource from "./CatalogNodeContentPanel.tsx?raw";
import editorSource from "./CatalogTreeEditor.tsx?raw";
import rowSource from "./CatalogTreeRow.tsx?raw";
import treeDataSource from "./catalogTreeData.ts?raw";
import treeSource from "./CatalogTreeNodeList.tsx?raw";
import workspaceSource from "./CatalogTreeWorkspacePage.tsx?raw";
import videoPanelSource from "./CatalogVideoPanel.tsx?raw";
import relatedPanelSource from "./CatalogRelatedLinksPanel.tsx?raw";
import studentCardPanelSource from "./CatalogStudentCardPanel.tsx?raw";

describe("catalog tree UI contracts", () => {
  it("keeps directory and point editor panels separate", () => {
    expect(editorSource).toContain("directoryCatalogEditorTabKeys");
    expect(editorSource).toContain("pointCatalogEditorTabKeys");
    expect(editorSource).toContain('key: "content"');
    expect(editorSource).toContain('key: "video"');
    expect(editorSource).toContain('key: "related"');
    expect(editorSource).toContain('key: "student-card"');
    expect(editorSource).toContain('key: "ai-context"');
    expect(editorSource).toContain('key: "publish"');
    expect(editorSource).toContain('key: "advanced"');
    expect(aiContextPanelSource).toContain("Static fallback evidence");
    expect(aiContextPanelSource).toContain("Dynamic RAG probe");
    expect(aiContextPanelSource).toContain("Teacher-only teaching notes");
    expect(catalogTreeApiSource).toContain("getCatalogPointAiContext");
    expect(catalogTreeApiSource).toContain("runCatalogPointRagProbe");
    expect(contentPanelSource).toContain('name="point_title"');
    expect(contentPanelSource).toContain('name="teacher_note"');
    expect(contentPanelSource).toContain('label="教学备注"');
    expect(contentPanelSource).not.toContain("管理摘要");
    expect(workspaceSource).not.toContain('label="摘要"');
    expect(studentCardPanelSource).toContain('name="student_description"');
    expect(studentCardPanelSource).toContain('name="card_image_asset_id"');
    expect(studentCardPanelSource).toContain('name="point_card_short_description"');
    expect(videoPanelSource).toContain("isPointCapable");
    expect([editorSource, contentPanelSource, studentCardPanelSource, videoPanelSource, relatedPanelSource, advancedPanelSource].join("\n")).not.toContain(
      "shortcut_target_node_id",
    );
    expect([editorSource, contentPanelSource, studentCardPanelSource, videoPanelSource, relatedPanelSource, advancedPanelSource].join("\n")).not.toContain(
      "uploadCatalogPointMedia",
    );
    expect([editorSource, contentPanelSource, studentCardPanelSource, videoPanelSource, relatedPanelSource, advancedPanelSource].join("\n")).not.toContain(
      'type="file"',
    );
  });

  it("keeps chapter switching in the heading and resets stale node detail on chapter change", () => {
    expect(workspaceSource).toContain('className="catalog-chapter-switcher"');
    expect(workspaceSource).toContain("setSelectedNodeId(null);");
    expect(workspaceSource).toContain("}, [chapterId]);");
    expect(workspaceSource).not.toContain("chapter-select");
    expect(workspaceSource).not.toMatch(/import\s*\{[^}]*\bSelect\b[^}]*\}\s*from\s*"antd"/);
    expect(editorSource).toContain("catalog-editor-empty-state");
    expect(editorSource).toContain("<CatalogEditorHeader");
    expect(editorSource).toContain('className="catalog-editor-tabs"');
  });

  it("keeps operational/debug fields out of default content panels", () => {
    expect(contentPanelSource).not.toContain("Node ID");
    expect(contentPanelSource).not.toContain("search_preview");
    expect(contentPanelSource).not.toContain("display_order");
    expect(advancedPanelSource).toContain("Node ID");
    expect(advancedPanelSource).toContain("display_order");
    expect(advancedPanelSource).toContain("search_preview");
  });

  it("keeps the video panel as existing-media binding only", () => {
    expect(videoPanelSource).toContain("mutations.bindMedia.mutate");
    expect(videoPanelSource).toContain("getMediaAssetFileUrl");
    expect(videoPanelSource).toContain("getMediaAssetThumbnailUrl");
    expect(editorSource).not.toContain("shortcut_target_node_id");
    expect(catalogTreeApiSource).not.toContain("media/upload");
    expect(catalogTreeApiSource).not.toContain("uploadCatalogPointMedia");
  });

  it("uses Arborist movement with invalid point-drop feedback instead of Ant Design Tree behavior", () => {
    expect(treeSource).toContain('from "react-arborist"');
    expect(treeSource).toContain("onMove={handleMove}");
    expect(treeSource).toContain("disableDrop=");
    expect(treeSource).toContain("resolveCatalogArboristMove");
    expect(treeSource).toContain("resolveCatalogDropDisabled");
    expect(treeSource).toContain("applyCatalogTreeMoveOptimistically");
    expect(treeSource).toContain("renderDragPreview={DragPreviewRenderer}");
    expect(treeSource).toContain("onRefreshRoots");
    expect(workspaceSource).toContain("mutateAsync");
    expect(treeDataSource).toContain("targetParent?.kind === \"point\"");
    expect(treeDataSource).toContain("applyCatalogTreeMoveOptimistically");
    expect(treeSource).toContain("onReorder");
    expect(treeSource).toContain("onMove");
    expect(treeSource).not.toMatch(/import\s*\{[^}]*\bTree\b[^}]*\}\s*from\s*"antd"/);
    expect(treeSource).not.toContain("titleRender");
    expect(treeSource).not.toContain("onDrop");
    expect(treeSource).not.toContain("switcherIcon");
  });

  it("uses the sidebar tree skin with experiment-specific point icons", () => {
    expect(rowSource).toContain("ChevronRight");
    expect(rowSource).toContain("ChevronDown");
    expect(rowSource).toContain("FolderOpen");
    expect(rowSource).toContain("FlaskConical");
    expect(rowSource).toContain("catalog-sidebar-switcher-spacer");
    expect(rowSource).toContain("catalog-sidebar-trailing");
    expect(rowSource).toContain("catalog-sidebar-status-dot");
    expect(rowSource).toContain("catalog-sidebar-point-status");
    expect(rowSource).toContain("CatalogArboristModernDragPreview");
    expect(rowSource).toContain("offset || mouse");
    expect(rowSource).toContain("node.isDragging");
    expect(rowSource).toContain("setTimeout");
    expect(rowSource).toContain("500");
    expect(rowSource).toContain("descendant_point_count");
    expect(rowSource).not.toContain("{catalogNode.status}");
    expect(rowSource).not.toContain("catalog-tree-status-tag");
    expect(rowSource).not.toContain("视频 ${catalogNode.published_media_count}");
    expect(rowSource).not.toContain("FileTextOutlined");
    expect(rowSource).not.toContain("HolderOutlined");
    expect(rowSource).not.toContain("catalog-tree-drag-handle");
    expect([treeSource, rowSource].join("\n")).not.toContain("ArrowUpOutlined");
    expect([treeSource, rowSource].join("\n")).not.toContain("ArrowDownOutlined");
  });

  it("keeps add wording chapter-oriented instead of root-node oriented", () => {
    expect(workspaceSource).not.toContain("PlusOutlined");
    expect(workspaceSource).not.toContain("<Space.Compact>");
    expect(workspaceSource).toContain("catalog-tree-filterbar");
    expect(treeSource).toContain("添加到本章");
    expect(treeSource).toContain("新建目录");
    expect(treeSource).toContain("新建点位");
    expect(treeSource).not.toContain("新建根目录");
    expect(treeSource).not.toContain("新建根点位");
  });

  it("renders editor status labels in Chinese instead of backend enum text", () => {
    expect(editorHeaderSource).toContain("catalogStatusLabel(node.status)");
    expect(editorHeaderSource).not.toContain("{node.status}</Tag>");
  });

  it("gates directory-only editor queries and tabs", () => {
    expect(editorSource).toContain('["content", "student-card", "publish", "advanced"]');
    expect(editorSource).toContain('["content", "video", "related", "student-card", "ai-context", "publish", "advanced"]');
    expect(editorSource).toContain("useCatalogMediaAssets(pointCapable)");
    expect(editorSource).toContain("pointCapable && relatedQuery.trim().length >= 2");
  });
});
