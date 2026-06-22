import { describe, expect, it } from "vitest";

import type { CatalogNodeDetail } from "../../api/catalogTree";
import {
  buildCatalogNodeCreatePayload,
  buildCatalogPointContentPayload,
  buildCatalogRelatedLinksPayload,
  catalogHeaderPrimaryAction,
  catalogNodeActionCount,
  catalogNodeDirectoryPendingClass,
  catalogNodeDirectoryPendingCount,
  catalogNodeDirectoryPendingLabel,
  catalogNodeDirectoryPendingParts,
  catalogStatusColor,
  catalogStatusDotClass,
  catalogStatusFilterCount,
  catalogStatusFilterOptions,
  catalogNodePrimaryStateClass,
  catalogNodeStatusTooltip,
  catalogStatusLabel,
  displayCatalogPointTitle,
  hasDivergentPointTitle,
  hydrateCatalogNodeForm,
  hydrateCatalogPointContentForm,
  hydrateCatalogRelatedLinksForm,
  matchesCatalogNodeStatusFilter,
  resolveCatalogNodeStatus,
  siblingReorderItems,
} from "./catalogTreeMappers";

describe("catalog tree mappers", () => {
  it("builds directory create payloads without manual student-card fields", () => {
    const payload = buildCatalogNodeCreatePayload(
      {
        title: "  Observation branch  ",
        summary: "  nested  ",
        node_kind: "directory",
        teacher_note: " private ",
      },
      "CH1",
      "cat-parent",
    );

    expect(payload).toEqual({
      chapter_id: "CH1",
      parent_id: "cat-parent",
      node_kind: "directory",
      title: "Observation branch",
      summary: "nested",
      teacher_note: "private",
      canonical_point_id: null,
    });
    expect(payload).not.toHaveProperty("student_description");
    expect(payload).not.toHaveProperty("card_presentation");
  });

  it("keeps teacher notes out of derived student-facing card data", () => {
    const payload = buildCatalogNodeCreatePayload(
      {
        title: "Teacher notes only",
        summary: "legacy summary",
        node_kind: "point",
        teacher_note: "teacher-only note",
      },
      "CH1",
    );

    expect(payload).toMatchObject({
      summary: "legacy summary",
      teacher_note: "teacher-only note",
    });
    expect(payload).not.toHaveProperty("student_description");
    expect(payload).not.toHaveProperty("point_card_presentation");
  });

  it("hydrates node forms without stale manual student-card values", () => {
    const detail = {
      node: {
        title: "Video point",
        summary: "summary",
        node_kind: "point",
        teacher_note: "teacher note",
      },
    } as unknown as CatalogNodeDetail;

    const form = hydrateCatalogNodeForm(detail);

    expect(form).toMatchObject({ title: "Video point", summary: "summary", teacher_note: "teacher note" });
    expect(form).not.toHaveProperty("student_description");
    expect(form).not.toHaveProperty("point_card_short_description");
  });

  it("keeps teacher note in authoring payload while separating principle modes", () => {
    expect(
      buildCatalogPointContentPayload({
        point_title: "Sodium thiosulfate and acid",
        teacher_note: "teacher-only note",
        principle_mode: "equation",
        reaction_equations_text: " Na2S2O3 + 2HCl = 2NaCl + S + SO2 + H2O \n\n SO2 + I2 + 2H2O = H2SO4 + 2HI ",
        reaction_equations: [{ raw_text: "stale preview row should not win" }],
        principle_text: "hidden by mode",
        phenomenon_explanation: "Sulfur precipitate appears.",
        safety_note: "Use ventilation.",
      }),
    ).toEqual({
      point_title: "Sodium thiosulfate and acid",
      teacher_note: "teacher-only note",
      principle_mode: "equation",
      principle_equation: "Na2S2O3 + 2HCl = 2NaCl + S + SO2 + H2O\nSO2 + I2 + 2H2O = H2SO4 + 2HI",
      reaction_equations: [
        {
          raw_text: "Na2S2O3 + 2HCl = 2NaCl + S + SO2 + H2O",
          row_order: 1,
          metadata: {},
        },
        {
          raw_text: "SO2 + I2 + 2H2O = H2SO4 + 2HI",
          row_order: 2,
          metadata: {},
        },
      ],
      principle_text: "",
      phenomenon_explanation: "Sulfur precipitate appears.",
      safety_note: "Use ventilation.",
    });
  });

  it("hydrates point content from node title when content is missing", () => {
    const detail = {
      node: { title: "Fallback title", node_kind: "point" },
      point_content: null,
    } as unknown as CatalogNodeDetail;

    expect(hydrateCatalogPointContentForm(detail)).toMatchObject({
      point_title: "Fallback title",
      teacher_note: "",
      principle_mode: "text",
    });
  });

  it("hydrates migrated single equations into editable rows", () => {
    const detail = {
      node: { title: "Legacy equation point", node_kind: "point" },
      point_content: {
        point_title: "Legacy equation point",
        principle_mode: "equation",
        principle_equation: "Cl2 + 2 KBr = 2 KCl + Br2",
        reaction_equations: [],
      },
    } as unknown as CatalogNodeDetail;

    const values = hydrateCatalogPointContentForm(detail);

    expect(values.reaction_equations_text).toBe("Cl2 + 2 KBr = 2 KCl + Br2");
    expect(values.reaction_equations).toEqual([
      { raw_text: "Cl2 + 2 KBr = 2 KCl + Br2", row_order: 1 },
    ]);
  });

  it("hydrates stored equation rows into multiline text in display order", () => {
    const detail = {
      node: { title: "Multi equation point", node_kind: "point" },
      point_content: {
        point_title: "Multi equation point",
        principle_mode: "equation",
        principle_equation: "",
        reaction_equations: [
          { raw_text: "Cl2 + H2 = HCl", row_order: 1 },
          { raw_text: "Cl2 + 2KBr = 2KCl + Br2", row_order: 2 },
        ],
      },
    } as unknown as CatalogNodeDetail;

    expect(hydrateCatalogPointContentForm(detail).reaction_equations_text).toBe("Cl2 + H2 = HCl\nCl2 + 2KBr = 2KCl + Br2");
  });

  it("hydrates equation rows with normalized inline supplemental text", () => {
    const detail = {
      node: { title: "Annotated equation point", node_kind: "point" },
      point_content: {
        point_title: "Annotated equation point",
        principle_mode: "equation",
        principle_equation: "",
        reaction_equations: [
          {
            raw_text: "H2 + O2 = H2O // note: heat gently",
            equation_core: "H2 + O2 = H2O",
            annotation_text: "需微热",
            canonical_display: "H2 + O2 → H2O",
            row_order: 1,
          },
        ],
      },
    } as unknown as CatalogNodeDetail;

    expect(hydrateCatalogPointContentForm(detail).reaction_equations_text).toBe("H2 + O2 = H2O // 需微热");
  });

  it("uses one visible point title and detects divergent stored titles", () => {
    const aligned = {
      node: { title: "氯水 + KBr", node_kind: "point" },
      point_content: { point_title: "氯水 + KBr" },
    } as unknown as CatalogNodeDetail;
    const divergent = {
      node: { title: "Tree title", node_kind: "point" },
      point_content: { point_title: "Point title" },
    } as CatalogNodeDetail;

    expect(displayCatalogPointTitle(aligned)).toBe("氯水 + KBr");
    expect(displayCatalogPointTitle(divergent)).toBe("Point title");
    expect(hasDivergentPointTitle(aligned)).toBe(false);
    expect(hasDivergentPointTitle(divergent)).toBe(true);
  });

  it("keeps generated related experiments readable and saves retained defaults as overrides", () => {
    const detail = {
      related_links: [
        {
          source_node_id: "cat-source",
          target_node_id: "cat-target-a",
          target_title: "Generated neighbor",
          relation_type: "generated_default",
          hidden: false,
          sort_order: 3,
          source: "generated_default",
          metadata: { default_scope_label: "同目录默认" },
        },
      ],
    } as unknown as CatalogNodeDetail;

    const form = hydrateCatalogRelatedLinksForm(detail);
    expect(form.links?.[0]).toMatchObject({
      target_node_id: "cat-target-a",
      target_title: "Generated neighbor",
      relation_type: "generated_default",
      source: "generated_default",
      metadata: { default_scope_label: "同目录默认" },
    });
    expect(
      buildCatalogRelatedLinksPayload({
        links: [
          { target_node_id: "cat-target-a", relation_type: "generated_default", sort_order: 2 },
          { target_node_id: "cat-target-a", relation_type: "manual", sort_order: 3 },
          { target_node_id: "" },
        ],
      }),
    ).toEqual({
      links: [
        {
          target_node_id: "cat-target-a",
          relation_type: "default_override",
          hidden: false,
          sort_order: 1,
          metadata: {},
        },
      ],
    });
  });

  it("creates sibling reorder payloads by node id", () => {
    expect(
      siblingReorderItems(
        [
          { node_id: "cat-a", title: "A", display_order: 1 } as never,
          { node_id: "cat-b", title: "B", display_order: 2 } as never,
          { node_id: "cat-c", title: "C", display_order: 3 } as never,
        ],
        "cat-c",
        "up",
      ),
    ).toEqual([
      { node_id: "cat-a", display_order: 1 },
      { node_id: "cat-c", display_order: 2 },
      { node_id: "cat-b", display_order: 3 },
    ]);
  });

  it("maps catalog status to Chinese labels and sidebar dot classes", () => {
    expect(catalogStatusLabel("published")).toBe("已发布");
    expect(catalogStatusLabel("draft")).toBe("草稿");
    expect(catalogStatusLabel("archived")).toBe("已归档");
    expect(catalogStatusDotClass("published")).toBe("is-published");
    expect(catalogStatusDotClass("draft")).toBe("is-ready");
    expect(catalogStatusDotClass("archived")).toBe("is-archived");
    expect(catalogStatusColor("draft")).toBe("default");
  });

  it("keeps published and unpublished filters paired in the sidebar", () => {
    expect(catalogStatusFilterOptions.map((option) => option.label)).toEqual([
      "全部",
      "待处理",
      "异常",
      "缺内容",
      "缺视频",
      "待发布",
      "已发布",
      "同步异常",
      "缺实验原理",
      "缺现象解释",
      "缺安全提示",
    ]);
  });

  it("uses backend node status as the authoritative tree status", () => {
    const detail = {
      node: {
        node_id: "cat-point-1",
        title: "氯水 + KBr",
        node_kind: "point",
        status: "published",
        has_point_content: true,
        media_count: 1,
        node_status: {
          primary_state: "sync_attention",
          primary_label: "同步异常",
          primary_reason: "搜索或 AI 同步异常",
          core_readiness: { content_fields: "complete", video: "present", missing_fields: [] },
          visibility: { placement: "published", shared_content: "published", student_available: true },
          async_consumption: { search_index: "failed", ai_evidence: "available" },
          conditions: [],
        },
      },
    } as unknown as CatalogNodeDetail;

    expect(resolveCatalogNodeStatus(detail).primary_state).toBe("sync_attention");
    expect(catalogNodePrimaryStateClass("ready")).toBe("is-ready");
    expect(catalogNodePrimaryStateClass("sync_attention")).toBe("is-sync");
    expect(catalogNodePrimaryStateClass("blocked")).toBe("is-error");
    expect(catalogNodeStatusTooltip(detail)).toBe("同步异常：搜索或 AI 同步异常");
  });

  it("derives the selected point header primary action from readiness state", () => {
    const baseDetail = {
      node: {
        node_id: "cat-point-1",
        title: "氯水 + KBr",
        node_kind: "point",
        status: "published",
        has_point_content: true,
        media_count: 1,
        node_status: {
          primary_state: "published",
          primary_label: "已发布",
          primary_reason: "学生可见",
          core_readiness: { content_fields: "complete", video: "present", missing_fields: [] },
          visibility: { placement: "published", shared_content: "published", student_available: true },
          async_consumption: { search_index: "synced", ai_evidence: "available" },
          conditions: [],
        },
      },
    } as unknown as CatalogNodeDetail;

    expect(catalogHeaderPrimaryAction(baseDetail)).toMatchObject({ key: "preview-student", label: "预览学生端" });
    expect(
      catalogHeaderPrimaryAction({
        ...baseDetail,
        node: {
          ...baseDetail.node,
          node_status: {
            ...baseDetail.node.node_status!,
            primary_state: "needs_content",
            core_readiness: { content_fields: "missing", video: "absent", missing_fields: ["原理"] },
            visibility: { placement: "published", shared_content: "draft", student_available: false },
          },
        },
      }),
    ).toMatchObject({ key: "edit-content", label: "编辑内容" });
    expect(
      catalogHeaderPrimaryAction({
        ...baseDetail,
        node: {
          ...baseDetail.node,
          node_status: {
            ...baseDetail.node.node_status!,
            primary_state: "ready",
            visibility: { placement: "published", shared_content: "draft", student_available: false },
          },
        },
      }),
    ).toMatchObject({ key: "publish-content", label: "发布学习内容" });
    expect(
      catalogHeaderPrimaryAction({
        ...baseDetail,
        node: {
          ...baseDetail.node,
          node_status: {
            ...baseDetail.node.node_status!,
            primary_state: "needs_video",
            core_readiness: { content_fields: "complete", video: "absent", missing_fields: [] },
          },
        },
      }),
    ).toMatchObject({ key: "bind-video", label: "绑定视频" });
    expect(
      catalogHeaderPrimaryAction({
        ...baseDetail,
        node: {
          ...baseDetail.node,
          node_status: {
            ...baseDetail.node.node_status!,
            primary_state: "needs_video",
            core_readiness: { content_fields: "complete", video: "absent", missing_fields: [] },
            visibility: { placement: "published", shared_content: "draft", student_available: false },
          },
        },
      }),
    ).toMatchObject({ key: "bind-video", label: "绑定视频" });
  });

  it("uses student preview as the selected directory fallback primary action", () => {
    const detail = {
      node: {
        node_id: "cat-dir-1",
        title: "四、氯的歧化反应",
        node_kind: "directory",
        status: "published",
        node_status: {
          primary_state: "published",
          primary_label: "已发布",
          primary_reason: "目录已发布",
          core_readiness: { content_fields: "not_applicable", video: "not_applicable", missing_fields: [] },
          visibility: { placement: "published", shared_content: "not_applicable", student_available: true },
          async_consumption: { search_index: "idle", ai_evidence: "idle" },
          conditions: [],
        },
      },
    } as unknown as CatalogNodeDetail;

    expect(catalogHeaderPrimaryAction(detail)).toMatchObject({ key: "preview-student", label: "预览学生端" });
  });

  it("falls back to binary video readiness when node_status is absent", () => {
    const point = {
      node_id: "cat-point-no-video",
      title: "Missing video",
      node_kind: "point",
      status: "published",
      has_point_content: true,
      media_count: 0,
      validation: { ok: true, errors: [], warnings: [] },
    } as never;

    const status = resolveCatalogNodeStatus(point);

    expect(status.primary_state).toBe("needs_video");
    expect(status.core_readiness.video_label).toBe("无视频");
    expect(status.visibility.student_available).toBe(true);
  });

  it("falls back to missing content before missing video", () => {
    const point = {
      node_id: "cat-point-no-content",
      title: "Missing content",
      node_kind: "point",
      status: "published",
      has_point_content: false,
      media_count: 0,
      validation: { ok: true, errors: [], warnings: [] },
    } as never;

    const status = resolveCatalogNodeStatus(point);

    expect(status.primary_state).toBe("needs_content");
    expect(status.primary_reason).toBe("三要素尚未填写");
    expect(status.visibility.student_available).toBe(true);
  });

  it("matches focused status filters from primary and aggregate state", () => {
    const directory = {
      node_id: "cat-dir",
      title: "Directory",
      node_kind: "directory",
      status: "published",
      descendant_point_count: 6,
      node_status: {
        primary_state: "needs_content",
        primary_label: "缺内容",
        primary_reason: "2 个后代点位缺内容",
        core_readiness: {
          content_fields: "not_applicable",
          video: "not_applicable",
          missing_fields: [],
          descendant_action_count: 2,
          descendant_status_counts: { needs_content: 2, needs_video: 0, ready: 1, published: 3, sync_attention: 1 },
          descendant_missing_field_counts: { principle: 1, phenomenon: 0, safety: 2 },
        },
        visibility: { placement: "published", shared_content: "not_applicable", student_available: true },
        async_consumption: { search_index: "not_applicable", ai_evidence: "not_applicable" },
        conditions: [],
      },
    } as never;

    expect(matchesCatalogNodeStatusFilter(directory, "needs_content")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(directory, "blocked")).toBe(false);
    expect(matchesCatalogNodeStatusFilter(directory, "needs_video")).toBe(false);
    expect(matchesCatalogNodeStatusFilter(directory, "sync_attention")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(directory, "unpublished")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(directory, "published")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(directory, "missing_principle")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(directory, "missing_phenomenon")).toBe(false);
    expect(matchesCatalogNodeStatusFilter(directory, "missing_safety")).toBe(true);
    expect(catalogNodeActionCount(directory)).toBe(4);
  });

  it("builds directory row pending badges from actionable states without ready counts", () => {
    const directory = {
      node_id: "cat-dir-pending",
      title: "Directory",
      node_kind: "directory",
      status: "published",
      descendant_point_count: 12,
      node_status: {
        primary_state: "needs_content",
        primary_label: "缺内容",
        primary_reason: "7 个后代点位缺内容",
        core_readiness: {
          content_fields: "not_applicable",
          video: "not_applicable",
          missing_fields: [],
          descendant_action_count: 14,
          descendant_status_counts: {
            blocked: 1,
            needs_content: 7,
            needs_video: 2,
            draft: 3,
            ready: 4,
            published: 5,
            sync_attention: 1,
          },
          descendant_missing_field_counts: {},
        },
        visibility: { placement: "published", shared_content: "not_applicable", student_available: true },
        async_consumption: { search_index: "not_applicable", ai_evidence: "not_applicable" },
        conditions: [],
      },
    } as never;

    expect(catalogNodeDirectoryPendingParts(directory).map((item) => [item.key, item.count])).toEqual([
      ["blocked", 1],
      ["needs_content", 7],
      ["needs_video", 2],
      ["draft", 3],
      ["sync_attention", 1],
    ]);
    expect(catalogNodeDirectoryPendingCount(directory)).toBe(14);
    expect(catalogNodeDirectoryPendingLabel(directory)).toBe("待处理：14 个点位（1 个阻断，7 个缺内容，2 个缺视频，3 个草稿，1 个同步异常）");
    expect(catalogNodeDirectoryPendingClass(directory)).toBe("is-error");
  });

  it("matches focused missing-field filters for direct points using structured keys", () => {
    const point = {
      node_id: "cat-point",
      title: "Missing safety",
      node_kind: "point",
      status: "published",
      node_status: {
        primary_state: "needs_content",
        primary_label: "缺内容",
        primary_reason: "缺少安全提示",
        core_readiness: {
          content_fields: "missing",
          video: "present",
          missing_field_keys: ["safety"],
          missing_field_labels: ["安全提示"],
          missing_fields: ["安全提示"],
        },
        visibility: { placement: "published", shared_content: "draft", student_available: false },
        async_consumption: { search_index: "idle", ai_evidence: "idle" },
        conditions: [],
      },
    } as never;

    expect(matchesCatalogNodeStatusFilter(point, "needs_content")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(point, "missing_safety")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(point, "missing_principle")).toBe(false);
  });

  it("matches unpublished filter for draft, ready, and aggregate unpublished states", () => {
    const draftNode = {
      node_id: "cat-draft",
      title: "Draft directory",
      node_kind: "directory",
      status: "draft",
      validation: { ok: true, errors: [], warnings: [] },
    } as never;
    const readyNode = {
      node_id: "cat-ready",
      title: "Ready point",
      node_kind: "point",
      status: "draft",
      has_point_content: true,
      media_count: 1,
      validation: { ok: true, errors: [], warnings: [] },
    } as never;
    const aggregateNode = {
      node_id: "cat-aggregate",
      title: "Published directory with draft descendants",
      node_kind: "directory",
      status: "published",
      node_status: {
        primary_state: "published",
        primary_label: "已发布",
        primary_reason: "目录已发布",
        core_readiness: {
          content_fields: "not_applicable",
          video: "not_applicable",
          missing_fields: [],
          descendant_status_counts: { draft: 1, published: 0 },
        },
        visibility: { placement: "published", shared_content: "not_applicable", student_available: true },
        async_consumption: { search_index: "not_applicable", ai_evidence: "not_applicable" },
        conditions: [],
      },
    } as never;

    expect(matchesCatalogNodeStatusFilter(draftNode, "unpublished")).toBe(false);
    expect(matchesCatalogNodeStatusFilter(readyNode, "unpublished")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(aggregateNode, "unpublished")).toBe(true);
    expect(matchesCatalogNodeStatusFilter(aggregateNode, "published")).toBe(false);
    const aggregatePublishedNode = {
      node_id: "cat-aggregate-published",
      title: "Published directory with published descendants",
      node_kind: "directory",
      status: "published",
      node_status: {
        primary_state: "published",
        primary_label: "已发布",
        primary_reason: "目录已发布",
        core_readiness: {
          content_fields: "not_applicable",
          video: "not_applicable",
          missing_fields: [],
          descendant_status_counts: { draft: 0, ready: 0, published: 2 },
        },
        visibility: { placement: "published", shared_content: "not_applicable", student_available: true },
        async_consumption: { search_index: "not_applicable", ai_evidence: "not_applicable" },
        conditions: [],
      },
    } as never;

    expect(matchesCatalogNodeStatusFilter(aggregatePublishedNode, "published")).toBe(true);
  });

  it("maps chapter summary counts to status filter chips", () => {
    const summary = {
      point_count: 12,
      actionable_point_count: 7,
      point_status_counts: {
        blocked: 1,
        needs_content: 2,
        needs_video: 3,
        ready: 4,
        draft: 1,
        published: 5,
        sync_attention: 1,
      },
      point_missing_field_counts: {
        principle: 4,
        phenomenon: 2,
        safety: 1,
      },
    } as never;

    expect(catalogStatusFilterCount(summary, "all")).toBe(12);
    expect(catalogStatusFilterCount(summary, "actionable")).toBe(7);
    expect(catalogStatusFilterCount(summary, "blocked")).toBe(1);
    expect(catalogStatusFilterCount(summary, "unpublished")).toBe(5);
    expect(catalogStatusFilterCount(summary, "published")).toBe(5);
    expect(catalogStatusFilterCount(summary, "missing_principle")).toBe(4);
    expect(catalogStatusFilterCount(summary, "missing_phenomenon")).toBe(2);
    expect(catalogStatusFilterCount(summary, "missing_safety")).toBe(1);
    expect(catalogStatusFilterCount(undefined, "all")).toBeNull();
  });
});
