import { describe, expect, it } from "vitest";

import type { CatalogBreadcrumb } from "../../api/catalogTree";
import { catalogDirectoryPathLabel, catalogPathLabel } from "./catalogPath";

const samplePath: CatalogBreadcrumb[] = [
  { node_id: "dir-1", title: "一级目录", node_kind: "directory", chapter_id: "CH99" },
  { node_id: "dir-2", title: "二级目录", node_kind: "directory", chapter_id: "CH99" },
  { node_id: "point-1", title: "实验点位", node_kind: "point", chapter_id: "CH99" },
];

describe("catalog path labels", () => {
  it("uses the chapter as the path root for point locations", () => {
    expect(catalogPathLabel(samplePath, "CH99")).toBe("CH99 / 一级目录 / 二级目录 / 实验点位");
  });

  it("uses the chapter as the path root for shared placement directory locations", () => {
    expect(catalogDirectoryPathLabel(samplePath, "CH99")).toBe("CH99 / 一级目录 / 二级目录");
  });
});
