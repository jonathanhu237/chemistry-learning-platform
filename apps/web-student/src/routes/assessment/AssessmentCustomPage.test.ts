import { describe, expect, it } from "vitest";
import type { CustomAssessmentScopeNode } from "../../api";
import { filterAssessmentScopeTree, selectedAssessmentPointIds, toggleAssessmentScopeSelection } from "./AssessmentCustomPage";

const tree: CustomAssessmentScopeNode[] = [
  {
    id: "chapter-halogen",
    title: "卤族元素",
    kind: "chapter",
    parent_id: null,
    question_count: 5,
    children: [
      {
        id: "directory-chlorine",
        title: "氯气的制备与性质",
        kind: "directory",
        parent_id: "chapter-halogen",
        question_count: 5,
        children: [
          {
            id: "point-chlorine-prep",
            title: "实验室制取氯气",
            kind: "point",
            parent_id: "directory-chlorine",
            question_count: 3,
            children: [],
          },
          {
            id: "point-chlorine-empty",
            title: "氯气收集",
            kind: "point",
            parent_id: "directory-chlorine",
            question_count: 0,
            children: [],
          },
        ],
      },
    ],
  },
  {
    id: "chapter-oxygen",
    title: "氧族元素",
    kind: "chapter",
    parent_id: null,
    question_count: 2,
    children: [
      {
        id: "point-oxygen-prep",
        title: "过氧化氢制取氧气",
        kind: "point",
        parent_id: "chapter-oxygen",
        question_count: 2,
        children: [],
      },
    ],
  },
];

describe("custom assessment scope tree", () => {
  it("keeps the full matching ancestry while filtering by point title", () => {
    const filtered = filterAssessmentScopeTree(tree, "过氧化氢");

    expect(filtered).toHaveLength(1);
    expect(filtered[0].id).toBe("chapter-oxygen");
    expect(filtered[0].children.map((node) => node.id)).toEqual(["point-oxygen-prep"]);
  });

  it("expands selected chapters and directories to unique usable leaf points", () => {
    expect(selectedAssessmentPointIds(tree, new Set(["chapter-halogen"]))).toEqual(["point-chlorine-prep"]);
    expect(selectedAssessmentPointIds(tree, new Set(["directory-chlorine", "point-chlorine-prep"]))).toEqual([
      "point-chlorine-prep",
    ]);
    expect(selectedAssessmentPointIds(tree, new Set(["point-chlorine-empty"]))).toEqual([]);
  });

  it("clears hidden descendants from the full tree when a filtered parent is selected", () => {
    const filteredParent = filterAssessmentScopeTree(tree, "实验室制取氯气")[0];
    expect(filteredParent.children[0].children.map((node) => node.id)).toEqual(["point-chlorine-prep"]);

    const selected = toggleAssessmentScopeSelection(
      tree,
      new Set(["point-chlorine-prep", "point-chlorine-empty"]),
      filteredParent.id,
    );

    expect(Array.from(selected)).toEqual(["chapter-halogen"]);
  });
});
