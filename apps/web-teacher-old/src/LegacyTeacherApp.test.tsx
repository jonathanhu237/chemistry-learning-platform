import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LegacyTeacherApp } from "./LegacyTeacherApp";
import { setAuthToken } from "./api";

const forbiddenVisibleTerms = [
  "Atom",
  "RAG",
  "Agent",
  "chunk",
  "embedding",
  "rerank",
  "Qwen",
  "BGE",
  "OpenAI",
  "学习助手",
  "智能监控",
  "AI出题",
  "导入名单",
  "重置账号",
];

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function installTeacherFetchMock() {
  return vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = new URL(String(input), "http://teacher-old.test");
    const path = url.pathname;

    if (path === "/api/auth/me") {
      return jsonResponse({
        id: "teacher-1",
        username: "teacher",
        display_name: "王老师",
        role: "teacher",
        status: "active",
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/overview") {
      return jsonResponse({
        metrics: [
          { key: "video_points", label: "实验视频点位", value: 51, unit: "个", description: "按实验知识单元汇总的学习视频入口" },
          { key: "questions", label: "题库题目", value: 1965, unit: "题", description: "覆盖实验点位的测评题目" },
          { key: "classes", label: "教学班级", value: 2, unit: "个", description: "纳入展示的教学班级" },
          { key: "students", label: "学生人数", value: 78, unit: "人", description: "已导入或已注册的学生" },
        ],
        loop: [
          { title: "实验视频学习", description: "学生先围绕实验点位观看现象、原理和安全提示。" },
          { title: "测评作答", description: "系统从题库中按掌握度或自选范围抽题。" },
          { title: "掌握度更新", description: "答题结果写入知识追踪模型，形成点位掌握度。" },
          { title: "复习与组卷", description: "薄弱点位用于下一轮视频推荐和组卷权重调整。" },
        ],
        resource_summary: {
          question_total: 1965,
          video_point_total: 51,
          class_total: 2,
        },
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/video-resources") {
      return jsonResponse({
        total: 2,
        items: [
          {
            node_id: "point-1",
            chapter_id: "chapter-halogen",
            title: "氯水漂白性实验",
            summary: "观察氯水漂白现象。",
            catalog_path: ["第13章 卤族元素", "氯的氧化性", "氯水漂白性实验"],
            media_count: 1,
            published_media_count: 1,
            question_count: 5,
            published_question_count: 4,
            has_video: true,
            is_recommended: true,
            resource_status: "已绑定视频",
          },
          {
            node_id: "point-2",
            chapter_id: "chapter-halogen",
            title: "KI水溶液中碘离子检验",
            summary: "观察碘离子被氧化后的颜色变化。",
            catalog_path: ["第13章 卤族元素", "卤素离子的还原性"],
            media_count: 0,
            published_media_count: 0,
            question_count: 3,
            published_question_count: 3,
            has_video: false,
            is_recommended: false,
            resource_status: "待补充视频",
          },
        ],
      });
    }
    if (path === "/api/admin/legacy/video-points/point-1/recommendation") {
      return jsonResponse({
        status: "ok",
        query: "",
        total: 1,
        items: [],
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/question-resources") {
      return jsonResponse({
        total: 3,
        totals: {
          question_count: 11,
          published_count: 10,
          draft_count: 1,
          choice_count: 6,
          true_false_count: 3,
          fill_blank_count: 2,
          point_count: 2,
        },
        items: [
          {
            node_id: "point-1",
            chapter_id: "chapter-halogen",
            node_kind: "point",
            title: "氯水漂白性实验",
            status: "published",
            breadcrumb_titles: ["第13章 卤族元素", "氯的氧化性"],
            experiment_id: "exp-1",
            question_count: 5,
            published_count: 4,
            draft_count: 1,
            choice_count: 2,
            true_false_count: 1,
            fill_blank_count: 2,
            media_count: 1,
            published_media_count: 1,
            point_count: 1,
          },
          {
            node_id: "cat-md-ch13-9c350312b24b56946e",
            chapter_id: "chapter-halogen",
            node_kind: "point",
            title: "氯水 + KBr + CCl₄",
            status: "published",
            breadcrumb_titles: ["第13章 卤族元素", "氯、溴、碘的置换次序", "氯水 + KBr + CCl₄"],
            experiment_id: "exp-2",
            question_count: 6,
            published_count: 6,
            draft_count: 0,
            choice_count: 4,
            true_false_count: 2,
            fill_blank_count: 0,
            media_count: 1,
            published_media_count: 1,
            point_count: 1,
          },
          {
            node_id: "dir-1",
            chapter_id: "chapter-halogen",
            node_kind: "directory",
            title: "氯的氧化性",
            status: "published",
            breadcrumb_titles: ["第13章 卤族元素"],
            experiment_id: "exp-dir",
            question_count: 5,
            published_count: 4,
            draft_count: 1,
            choice_count: 2,
            true_false_count: 1,
            fill_blank_count: 2,
            media_count: 1,
            published_media_count: 1,
            point_count: 1,
          },
        ],
      });
    }
    if (path === "/api/admin/classes") {
      if (_init?.method === "POST") {
        return jsonResponse({
          id: "class-2",
          class_name: "无机化学二班",
          description: "新增演示班",
          status: "active",
          student_count: 0,
        });
      }
      return jsonResponse([
        {
          id: "class-1",
          class_name: "无机化学一班",
          description: "2026 春季演示班",
          status: "active",
          student_count: 2,
        },
      ]);
    }
    if (path === "/api/admin/classes/class-1/students") {
      if (_init?.method === "POST") {
        return jsonResponse({
          id: "student-3",
          class_id: "class-1",
          student_id: "2026003",
          student_name: "王五",
          status: "pending",
          activation_mode: "default_password",
          activated: false,
        });
      }
      return jsonResponse([
        {
          id: "student-1",
          class_id: "class-1",
          student_id: "2026001",
          student_name: "张三",
          status: "active",
          activation_mode: "default_password",
          activated: true,
        },
        {
          id: "student-2",
          class_id: "class-1",
          student_id: "2026002",
          student_name: "李四",
          status: "pending",
          activation_mode: "default_password",
          activated: false,
        },
      ]);
    }
    if (path === "/api/admin/legacy/teacher-demo/classes") {
      return jsonResponse({
        classes: [
          {
            id: "class-1",
            class_name: "无机化学一班",
            description: "2026 春季演示班",
            status: "active",
            student_count: 38,
            active_students: 30,
            completion_rate: 78.5,
            average_score: 83.2,
            missing_students: 8,
          },
        ],
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/classes/class-1/analytics") {
      return jsonResponse({
        class_id: "class-1",
        metrics: {
          class_size: 38,
          active_students: 30,
          completion_rate: 78.5,
          average_score: 83.2,
          missing_students: 8,
        },
        experiment_groups: [{ id: "group-1", title: "卤素实验", experiment_count: 9 }],
        students: [
          {
            student_id: "2026001",
            student_name: "李同学",
            average_score: 82,
            evidence_count: 3,
            attempt_count: 2,
            status: "已有记录",
          },
        ],
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/classes/class-1/weak-points") {
      return jsonResponse({
        total: 1,
        point_total: 1,
        items: [],
        point_items: [
          {
            point_node_id: "point-1",
            point_key: "point-1",
            point_title: "氯水漂白性实验",
            experiment_id: "exp-1",
            experiment_title: "氯水漂白性实验",
            attempt_count: 10,
            incorrect_count: 6,
            incorrect_rate: 60,
            representative_questions: [{ question_id: "q1", stem: "如何判断氯水具有氧化性？" }],
          },
        ],
      });
    }
    if (path === "/api/admin/legacy/teacher-demo/evaluation-system") {
      return jsonResponse({
        evaluated_objects: ["实验点位掌握度", "章节实验覆盖"],
        evidence_sources: ["实验视频学习记录", "智能测评作答结果"],
        update_mechanism: "以实验点位为最小知识单元，学生每次测评都会更新对应点位的掌握度。",
        score_bands: [
          { label: "优秀", min_score: 85, max_score: 100, description: "能够稳定解释实验现象。" },
          { label: "需巩固", min_score: 0, max_score: 69.99, description: "建议优先复习错题对应的实验点位。" },
        ],
        outputs: ["学生学习报告", "班级学情概览", "薄弱点位排行"],
      });
    }
    return jsonResponse({}, 404);
  });
}

function assertNoForbiddenVisibleTerms(container: HTMLElement) {
  const text = container.textContent || "";
  for (const term of forbiddenVisibleTerms) {
    expect(text).not.toContain(term);
  }
}

function assertNoUnexpectedBusinessMutations(fetchMock: ReturnType<typeof installTeacherFetchMock>, options: { allowClassManagement?: boolean } = {}) {
  const mutationCalls = fetchMock.mock.calls.filter((call) => {
    const path = new URL(String(call[0]), "http://teacher-old.test").pathname;
    const method = String(call[1]?.method || "GET").toUpperCase();
    const isAllowedLegacyRecommendationWrite =
      method === "PUT" && path.startsWith("/api/admin/legacy/video-points/") && path.endsWith("/recommendation");
    const isAllowedClassManagement =
      options.allowClassManagement &&
      method === "POST" &&
      (path === "/api/admin/classes" || /^\/api\/admin\/classes\/[^/]+\/students$/.test(path));
    return (
      path.startsWith("/api/admin/") &&
      ["POST", "PUT", "PATCH", "DELETE"].includes(method) &&
      !isAllowedLegacyRecommendationWrite &&
      !isAllowedClassManagement
    );
  });
  expect(mutationCalls).toEqual([]);
}

describe("LegacyTeacherApp", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    window.localStorage.clear();
    setAuthToken("teacher-token");
  });

  afterEach(() => {
    setAuthToken("");
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders only read-only demo navigation and BKT overview", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<LegacyTeacherApp />);

    expect(await screen.findByRole("heading", { name: "教学工作台" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "视频资源" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "题库资源" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "班级" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "学情分析" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "评价体系" })).toBeTruthy();
    expect(await screen.findByText("BKT 教学反馈闭环")).toBeTruthy();
    expect(screen.getByText("实验视频学习")).toBeTruthy();
    assertNoUnexpectedBusinessMutations(fetchMock);
    assertNoForbiddenVisibleTerms(container);
  });

  it("shows video resources and lets teachers maintain legacy recommendation labels", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<LegacyTeacherApp />);

    fireEvent.click(await screen.findByRole("button", { name: "视频资源" }));
    expect(await screen.findByRole("heading", { name: "视频资源" })).toBeTruthy();
    expect(await screen.findByText("氯水漂白性实验")).toBeTruthy();
    expect(screen.getAllByText("已绑定视频").length).toBeGreaterThan(0);
    expect(screen.getAllByText("推荐学习").length).toBeGreaterThan(0);
    expect(screen.getByText("题目 4")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "取消推荐" }));
    expect(await screen.findByText("已取消推荐学习：氯水漂白性实验")).toBeTruthy();
    expect(
      fetchMock.mock.calls.some((call) => {
        const path = new URL(String(call[0]), "http://teacher-old.test").pathname;
        return path === "/api/admin/legacy/video-points/point-1/recommendation" && call[1]?.method === "PUT";
      }),
    ).toBe(true);
    fireEvent.change(screen.getByPlaceholderText("输入实验、试剂、现象或点位名称"), { target: { value: "氯水" } });
    fireEvent.click(screen.getByRole("button", { name: "搜索" }));
    await waitFor(() => expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("q=%E6%B0%AF%E6%B0%B4"))).toBe(true));
    assertNoUnexpectedBusinessMutations(fetchMock);
    assertNoForbiddenVisibleTerms(container);
  });

  it("shows question resources and generates review drafts through the old teacher workbench", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<LegacyTeacherApp />);

    fireEvent.click(await screen.findByRole("button", { name: "题库资源" }));
    expect(await screen.findByRole("heading", { name: "题库资源" })).toBeTruthy();
    expect(await screen.findByText("题库建设流程")).toBeTruthy();
    expect(await screen.findByText("演示数据已载入")).toBeTruthy();
    expect(await screen.findByText("教材依据就绪 · 题目 5")).toBeTruthy();
    expect(screen.getAllByText("氯水漂白性实验").length).toBeGreaterThan(0);
    expect((await screen.findAllByText("待审题目")).length).toBeGreaterThan(0);
    expect(await screen.findByText("暂无待审题目。输入提示词后会在这里显示教师审核卡片。")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "生成待审题" }));
    expect(await screen.findByText("已生成 1 条待审题目，请教师复核后入库。")).toBeTruthy();
    expect(await screen.findByText("围绕“氯水漂白性实验”进行实验现象观察时，下列哪项最适合作为课堂测评的判断依据？")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "通过入库" }));
    expect(await screen.findByText("教师审核通过，题目已入库。")).toBeTruthy();
    expect(
      fetchMock.mock.calls.every((call) => {
        const url = new URL(String(call[0]), "http://teacher-old.test");
        return !url.pathname.startsWith("/api/admin/question-banks/");
      }),
    ).toBe(true);
    expect(await screen.findByText("点位题库覆盖")).toBeTruthy();
    expect(screen.getByText("选择 2")).toBeTruthy();
    assertNoUnexpectedBusinessMutations(fetchMock);
    assertNoForbiddenVisibleTerms(container);
  });

  it("shows class list and analytics weak point ranking", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    const { container } = render(<LegacyTeacherApp />);

    fireEvent.click(await screen.findByRole("button", { name: "班级" }));
    expect(await screen.findByRole("heading", { name: "班级" })).toBeTruthy();
    expect(await screen.findByText("无机化学一班")).toBeTruthy();
    expect(await screen.findByText("张三")).toBeTruthy();
    expect(screen.getByText("李四")).toBeTruthy();
    expect(screen.getAllByText("待首次登录").length).toBeGreaterThan(0);
    fireEvent.change(screen.getByPlaceholderText("例如：2026001"), { target: { value: "2026003" } });
    fireEvent.change(screen.getByPlaceholderText("学生姓名"), { target: { value: "王五" } });
    fireEvent.click(screen.getByRole("button", { name: "创建学生" }));
    expect(await screen.findByText("已创建学生：王五（2026003），初始密码以当前班级设置为准。")).toBeTruthy();
    expect(
      fetchMock.mock.calls.some((call) => {
        const url = new URL(String(call[0]), "http://teacher-old.test");
        return url.pathname === "/api/admin/classes/class-1/students" && call[1]?.method === "POST" && String(call[1]?.body || "").includes("\"student_name\":\"王五\"");
      }),
    ).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "学情分析" }));
    expect(await screen.findByRole("heading", { name: "学情分析" })).toBeTruthy();
    expect(await screen.findByText("李同学")).toBeTruthy();
    expect((await screen.findAllByText("氯水漂白性实验")).length).toBeGreaterThan(0);
    expect(screen.getByText("薄弱点位排行")).toBeTruthy();
    assertNoUnexpectedBusinessMutations(fetchMock, { allowClassManagement: true });
    assertNoForbiddenVisibleTerms(container);
  });

  it("shows evaluation system score bands and redirects stale mutation routes", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/question-bank/workbench");
    const { container } = render(<LegacyTeacherApp />);

    expect(await screen.findByRole("heading", { name: "教学工作台" })).toBeTruthy();
    await waitFor(() => expect(window.location.pathname).toBe("/"));

    fireEvent.click(screen.getByRole("button", { name: "评价体系" }));
    expect(await screen.findByRole("heading", { name: "评价体系" })).toBeTruthy();
    expect(await screen.findByText("评价对象")).toBeTruthy();
    expect(screen.getByText("优秀")).toBeTruthy();
    expect(screen.getByText("教学输出")).toBeTruthy();
    expect(screen.getByText("测评报告 Prompt")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "保存报告 Prompt" }));
    expect(await screen.findByText("报告 Prompt 已保存，本次演示将按新的总结和错题讲解口径生成报告。")).toBeTruthy();
    assertNoUnexpectedBusinessMutations(fetchMock);
    assertNoForbiddenVisibleTerms(container);
  });
});
