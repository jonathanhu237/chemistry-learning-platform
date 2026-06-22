import { describe, expect, it } from "vitest";

import { catalogEditorTabKeysForNode } from "./CatalogTreeEditor";

describe("catalog editor tab filtering", () => {
  it("hides point-only panels for directories", () => {
    expect(catalogEditorTabKeysForNode("directory")).toEqual(["content"]);
  });

  it("keeps video and related panels for points", () => {
    expect(catalogEditorTabKeysForNode("point")).toEqual(["content", "video", "related"]);
  });
});
