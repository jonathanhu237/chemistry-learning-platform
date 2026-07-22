import { describe, expect, it } from "vitest";

import type { CatalogNodeCard } from "../../api/catalogTree";
import { catalogArchiveMutationVariables } from "./catalogArchiveConfirmation";

function pointNode(overrides: Partial<CatalogNodeCard> = {}): CatalogNodeCard {
  return {
    node_id: "point-1",
    chapter_id: "CH13",
    node_kind: "point",
    title: "氯气漂白",
    summary: "",
    status: "published",
    display_order: 1,
    actions: [],
    has_children: false,
    descendant_point_count: 0,
    has_point_content: true,
    media_count: 1,
    published_media_count: 1,
    validation: { ok: true, errors: [], warnings: [] },
    ...overrides,
  };
}

describe("catalog teacher workflow", () => {
  it("archives a confirmed node with explicit final-placement permission", () => {
    expect(catalogArchiveMutationVariables(pointNode({ active_placement_count: 1 }))).toEqual({
      nodeId: "point-1",
      action: "archive",
      includeSubtree: true,
      archiveFinalPlacement: true,
    });
  });
});
