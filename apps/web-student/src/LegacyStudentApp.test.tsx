import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LegacyStudentApp } from "./LegacyStudentApp";
import { ApiError, legacyStudentErrorMessage, setAuthToken } from "./api";

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
  "TKE",
  "TKT",
  "mastery_score",
  "mastery_prob",
  "检索增强",
  "知识检索",
];

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function createMemoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => values.delete(key),
    setItem: (key: string, value: string) => values.set(key, String(value)),
  };
}

function ensureBrowserStorage(): void {
  if (!window.localStorage) {
    Object.defineProperty(window, "localStorage", { configurable: true, value: createMemoryStorage() });
  }
  if (!window.sessionStorage) {
    Object.defineProperty(window, "sessionStorage", { configurable: true, value: createMemoryStorage() });
  }
}

function learningProfile(active = false) {
  const summary = {
    profile_id: "halogens-17",
    chapter_id: "chapter-halogen",
    title: "第13章 卤族元素",
    subtitle: "卤素性质实验",
    family_number: "17族",
    family_name: "卤素",
    element_symbols: ["F", "Cl", "Br", "I"],
  };
  if (!active) return summary;
  return {
    ...summary,
    hero: {
      eyebrow: "元素族",
      title: "卤素",
      summary: "观察卤素单质和卤离子的典型反应。",
    },
    default_element_symbol: "Cl",
    elements: [
      {
        symbol: "Cl",
        name: "氯",
        atomic_number: 17,
        group: "17",
        group_label: "17族",
        period: 3,
        block: "p",
        common_valence: "-1",
        card_focus: "氧化性与置换反应",
      },
      {
        symbol: "Br",
        name: "溴",
        atomic_number: 35,
        group: "17",
        group_label: "17族",
        period: 4,
        block: "p",
      },
      {
        symbol: "He",
        name: "氦",
        atomic_number: 2,
        group: "18",
        group_label: "18族",
        period: 1,
        block: "s",
      },
    ],
    property_cards: [
      {
        key: "oxidation",
        label: "氧化性",
        value: "Cl2 > Br2 > I2",
        description: "通过置换反应比较氧化性强弱。",
      },
    ],
  };
}

function alkaliProfile() {
  return {
    profile_id: "alkali-1",
    chapter_id: "chapter-alkali",
    title: "第12章 碱金属",
    subtitle: "钠钾性质实验",
    family_number: "1族",
    family_name: "碱金属",
    element_symbols: ["Li", "Na", "K"],
  };
}

function installStudentFetchMock() {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/auth/me")) {
      return jsonResponse({
        id: "student-1",
        username: "2026001",
        display_name: "李同学",
        role: "student",
        status: "active",
        student_id: "2026001",
        class_name: "数智一班",
      });
    }
    if (url.includes("/api/student/assessment/status")) {
      return jsonResponse({
        has_completed_smart_baseline: true,
        has_answered_questions: true,
        needs_smart_baseline: false,
        has_open_assessment: false,
        open_session_id: null,
        open_assessment_mode: null,
        smart_baseline_prompt_dismissed: false,
      });
    }
    if (url.includes("/api/student/legacy/video-points")) {
      const parsed = new URL(url, "http://test.local");
      const query = parsed.searchParams.get("q") || "";
      const items = [
        {
          id: "point-no-video",
          node_id: "point-no-video",
          chapter_id: "chapter-alkali",
          title: "钠与水反应观察",
          summary: "观察钠在水中的运动、放热和溶液颜色变化。",
          snippet: "钠与水反应现象。",
          catalog_path: ["第12章 碱金属", "钠钾性质实验", "钠与水反应观察"],
          media_count: 0,
          published_media_count: 0,
          thumbnail_path: null,
          is_recommended: true,
          recommended_order: 0,
        },
        {
          id: "point-1",
          node_id: "point-1",
          chapter_id: "chapter-halogen",
          title: "氯水漂白性实验",
          summary: "观察氯水与指示剂变化。",
          snippet: "氯水相关实验。",
          catalog_path: ["第13章 卤族元素", "氯的氧化性", "氯水漂白性实验"],
          media_count: 1,
          published_media_count: 1,
          preview_stream_path: "/api/student/media/assets/media-1/stream",
          thumbnail_path: "/api/student/media/assets/media-1/thumbnail",
          is_recommended: false,
          recommended_order: null,
        },
      ];
      const filtered = query ? items.filter((item) => `${item.title} ${item.summary} ${item.snippet}`.includes("氯水")) : items;
      return jsonResponse({
        status: filtered.length ? "ok" : "empty",
        query,
        total: filtered.length,
        items: filtered,
      });
    }
    if (url.includes("/api/student/home-video-feed")) {
      return jsonResponse({
        status: "ok",
        topic: "all",
        next_cursor: null,
        has_more: false,
        repeat_mode: "none",
        items: [
          {
            id: "feed-1",
            instance_id: "feed-1-instance",
            node_id: "point-1",
            title: "氯水漂白性实验",
            summary: "观察氯水与指示剂变化。",
            snippet: "氯水相关实验。",
            catalog_path: ["第13章 卤族元素", "氯的氧化性"],
            badges: ["全部视频"],
            video: {
              media_id: "media-1",
              title: "氯水漂白性实验",
              stream_path: "/api/media/media-1/stream",
              thumbnail_path: "/api/student/media/assets/media-1/thumbnail",
            },
            target: {
              kind: "point_detail",
              route: "/point/point-1",
              node_id: "point-1",
            },
          },
        ],
      });
    }
    if (url.includes("/api/student/video-library/search")) {
      return jsonResponse({
        query: "氯水",
        status: "ok",
        backend: "local",
        message: "",
        total: 1,
        groups: [
          {
            key: "videos",
            title: "实验视频",
            summary: "",
            items: [
              {
                id: "search-1",
                type: "video_point",
                title: "氯水漂白性实验",
                subtitle: "第13章 卤族元素 / 氯的氧化性",
                snippet: "观察氯水漂白。",
                score: 1,
                badges: [],
                action_label: "打开",
                target: {
                  kind: "point_detail",
                  route: "/point/point-1",
                  node_id: "point-1",
                },
              },
            ],
          },
        ],
        browse: {
          recommended: [],
          recent: [],
          chips: [],
        },
      });
    }
    if (url.includes("/api/student/learning-page?profile_id=halogens-17")) {
      return jsonResponse({
        recommended_profile_id: "halogens-17",
        profiles: [learningProfile(false), alkaliProfile()],
        active_profile: learningProfile(true),
        recommended_points: [
          {
            node_id: "point-1",
            chapter_id: "chapter-halogen",
            title: "氯水漂白性实验",
            summary: "优先复盘氯水氧化性与漂白性。",
            catalog_path: ["第13章 卤族元素", "氯的氧化性", "氯水漂白性实验"],
            catalog_node_ids: ["dir-oxidation", "point-1"],
            reason: "薄弱点位",
            mastery_score: 42,
            has_video: true,
          },
        ],
      });
    }
    if (url.includes("/api/student/learning-page")) {
      return jsonResponse({
        recommended_profile_id: "halogens-17",
        profiles: [learningProfile(false), alkaliProfile()],
        active_profile: null,
        recommended_points: [
          {
            node_id: "point-1",
            chapter_id: "chapter-halogen",
            title: "氯水漂白性实验",
            summary: "优先复盘氯水氧化性与漂白性。",
            catalog_path: ["第13章 卤族元素", "氯的氧化性", "氯水漂白性实验"],
            catalog_node_ids: ["dir-oxidation", "point-1"],
            reason: "薄弱点位",
            mastery_score: 42,
            has_video: true,
          },
        ],
      });
    }
    if (url.includes("/api/student/chapters/chapter-halogen/catalog")) {
      return jsonResponse({
        chapter_id: "chapter-halogen",
        chapter_title: "第13章 卤族元素",
        nodes: [
          {
            node_id: "dir-oxidation",
            chapter_id: "chapter-halogen",
            node_kind: "directory",
            title: "氯的氧化性",
            summary: "进入置换反应实验。",
            status: "published",
            display_order: 1,
            has_children: true,
            has_point_content: false,
            media_count: 0,
            published_media_count: 0,
          },
        ],
      });
    }
    if (url.includes("/api/student/chapters/chapter-alkali/catalog")) {
      return jsonResponse({
        chapter_id: "chapter-alkali",
        chapter_title: "第12章 碱金属",
        nodes: [
          {
            node_id: "point-no-video",
            chapter_id: "chapter-alkali",
            node_kind: "point",
            title: "钠与水反应观察",
            summary: "观察钠在水中的运动、放热和溶液颜色变化。",
            status: "published",
            display_order: 1,
            has_children: false,
            has_point_content: true,
            media_count: 0,
            published_media_count: 0,
          },
        ],
      });
    }
    if (url.includes("/api/student/catalog/nodes/dir-oxidation")) {
      return jsonResponse({
        node: {
          node_id: "dir-oxidation",
          chapter_id: "chapter-halogen",
          node_kind: "directory",
          title: "氯的氧化性",
          summary: "进入置换反应实验。",
          status: "published",
          display_order: 1,
          has_children: true,
          has_point_content: false,
          media_count: 0,
          published_media_count: 0,
        },
        breadcrumbs: [
          {
            node_id: "dir-oxidation",
            title: "氯的氧化性",
            node_kind: "directory",
            chapter_id: "chapter-halogen",
          },
        ],
        children: [
          {
            node_id: "point-1",
            chapter_id: "chapter-halogen",
            node_kind: "point",
            title: "氯水漂白性实验",
            summary: "观察试纸褪色。",
            status: "published",
            display_order: 1,
            has_children: false,
            has_point_content: true,
            media_count: 1,
            published_media_count: 1,
          },
        ],
      });
    }
    if (url.includes("/api/student/catalog/points/point-1")) {
      return jsonResponse({
        node_id: "point-1",
        canonical_node_id: "point-1",
        placement_node_id: "point-1",
        canonical_point_id: "point-1",
        chapter_id: "chapter-halogen",
        title: "氯水漂白性实验",
        summary: "观察氯水漂白性。",
        breadcrumbs: [
          { node_id: "dir-oxidation", title: "氯的氧化性", node_kind: "directory", chapter_id: "chapter-halogen" },
          { node_id: "point-1", title: "氯水漂白性实验", node_kind: "point", chapter_id: "chapter-halogen" },
        ],
        principle_text: "Cl2 + 2I- -> 2Cl- + I2 // 优先氧化 I- // Cl2 + 2Br- -> 2Cl- + Br2 // I- 基本反应完后再氧化 Br- // I2 + 5Cl2 + 6H2O -> 2HIO3 + 10HCl // 氯水过量时 I2 进一步被氧化",
        phenomenon_explanation: "试纸颜色逐渐褪去。",
        safety_note: "注意通风。",
        videos: [
          {
            media_id: "media-1",
            title: "氯水漂白性实验",
            stream_path: "/api/media/media-1/stream",
            thumbnail_path: "/api/student/media/assets/media-1/thumbnail",
          },
        ],
        related_points: [
          {
            node_id: "point-related-1",
            title: "磷在氧气中的燃烧",
            relation_type: "generated_default",
            source_node_id: "point-1",
          },
          {
            node_id: "point-related-2",
            title: "铁丝在氧气中的燃烧",
            relation_type: "manual",
            source_node_id: "point-1",
          },
        ],
        assessment_context: {
          point_node_id: "point-1",
          placement_node_id: "point-1",
          canonical_point_id: "point-1",
          chapter_id: "chapter-halogen",
          catalog_path: [
            { node_id: "dir-oxidation", title: "氯的氧化性", node_kind: "directory", chapter_id: "chapter-halogen" },
            { node_id: "point-1", title: "氯水漂白性实验", node_kind: "point", chapter_id: "chapter-halogen" },
          ],
        },
      });
    }
    if (url.includes("/api/student/custom-assessment/options")) {
      return jsonResponse({
        settings: {
          enabled: true,
          question_count_options: [5, 10, 15, 20],
          default_question_count: 10,
          max_question_count: 20,
          max_questions_per_experiment: 3,
          questions_per_point_options: [1, 2, 3],
          default_questions_per_point: 1,
        },
        smart_question_count: 10,
        experiments: [
          {
            id: "exp-1",
            code: "CAT-CH13-e084fc21",
            title: "一、卤素单质在不同溶剂中的溶解性",
            parent_title: "第13章 卤族元素",
            question_count: 15,
          },
          {
            id: "exp-2",
            code: "CAT-CH14-853fc89e",
            title: "一、氧气的制备与性质",
            parent_title: "第14章 氧族元素",
            question_count: 20,
          },
          {
            id: "exp-empty",
            code: "CAT-EMPTY",
            title: "暂未开放题目的实验",
            parent_title: "待补题库",
            question_count: 0,
          },
        ],
        scope_tree: [
          {
            id: "chapter-halogen",
            title: "第13章 卤族元素",
            kind: "chapter",
            parent_id: null,
            question_count: 15,
            children: [
              {
                id: "dir-halogen-solubility",
                title: "卤素单质在不同溶剂中的溶解性",
                kind: "directory",
                parent_id: "chapter-halogen",
                question_count: 15,
                children: [
                  {
                    id: "point-halogen-solubility",
                    title: "四氯化碳萃取卤素单质",
                    kind: "point",
                    parent_id: "dir-halogen-solubility",
                    question_count: 15,
                    children: [],
                  },
                ],
              },
            ],
          },
          {
            id: "chapter-oxygen",
            title: "第14章 氧族元素",
            kind: "chapter",
            parent_id: null,
            question_count: 20,
            children: [
              {
                id: "dir-oxygen-prep",
                title: "氧气的制备与性质",
                kind: "directory",
                parent_id: "chapter-oxygen",
                question_count: 20,
                children: [
                  {
                    id: "point-oxygen-prep",
                    title: "过氧化氢制取氧气",
                    kind: "point",
                    parent_id: "dir-oxygen-prep",
                    question_count: 20,
                    children: [],
                  },
                ],
              },
            ],
          },
        ],
      });
    }
    if (url.includes("/api/student/point-assessment/start")) {
      return jsonResponse({
        status: "in_progress",
        session_id: "point-session-1",
        assessment_mode: "point",
        composition: {
          total_questions: 4,
          weak_tendency_percent: 50,
          untested_question_count: 1,
        },
        experiments: [
          {
            id: "exp-point-1",
            title: "氯水对溴离子的氧化顺序",
            mastery_score: 51.5,
            evidence_count: 1,
            question_count: 4,
          },
        ],
        questions: [
          {
            id: "point-q1",
            experiment_id: "exp-point-1",
            experiment_title: "氯水对溴离子的氧化顺序",
            question_type: "single_choice",
            stem: "氯水优先氧化哪一种离子？",
            options: [
              { label: "A", text: "I-" },
              { label: "B", text: "Cl-" },
            ],
          },
        ],
      });
    }
    if (url.includes("/api/student/smart-assessment/start")) {
      return jsonResponse({
        status: "in_progress",
        session_id: "session-1",
        assessment_mode: "smart",
        composition: {
          total_questions: 3,
          target_question_count: 5,
          requested_question_count: 5,
          weak_tendency_percent: 60,
          untested_question_count: 2,
          measured_question_count: 1,
          selected_point_count: 2,
          warnings: { underfilled: true },
        },
        experiments: [
          {
            id: "exp-1",
            title: "氯水漂白性实验",
            mastery_score: 42.5,
            evidence_count: 3,
            question_count: 2,
          },
        ],
        questions: [
          {
            id: "smart-q1",
            experiment_id: "exp-1",
            experiment_title: "氯水漂白性实验",
            question_type: "single_choice",
            stem: "氯水使试纸褪色的主要原因是什么？",
            options: [
              { label: "A", text: "生成次氯酸" },
              { label: "B", text: "生成氯化钠" },
            ],
          },
          {
            id: "smart-q2",
            experiment_id: "exp-1",
            experiment_title: "氯水漂白性实验",
            question_type: "true_false",
            stem: "新制氯水具有氧化性。",
            options: [],
          },
          {
            id: "smart-q3",
            experiment_id: "exp-1",
            experiment_title: "氯水漂白性实验",
            question_type: "fill_blank",
            stem: "氯水与____反应可生成____。",
            options: [],
          },
        ],
      });
    }
    if (url.includes("/api/student/custom-assessment/start")) {
      return jsonResponse({
        status: "in_progress",
        session_id: "custom-session-1",
        assessment_mode: "custom",
        composition: {
          total_questions: 2,
          target_question_count: 10,
          requested_question_count: 10,
          custom_question_count: 2,
          max_questions_per_experiment: 3,
          warnings: {},
        },
        experiments: [
          {
            id: "exp-1",
            title: "一、卤素单质在不同溶剂中的溶解性",
            source: "custom",
            question_count: 2,
            evidence_count: 0,
          },
        ],
        questions: [
          {
            id: "custom-q1",
            experiment_id: "exp-1",
            experiment_title: "一、卤素单质在不同溶剂中的溶解性",
            question_type: "single_choice",
            stem: "卤素单质在有机溶剂中的颜色变化可用于判断什么？",
            options: [
              { label: "A", text: "溶解性和氧化还原现象" },
              { label: "B", text: "气体密度" },
            ],
          },
          {
            id: "custom-q2",
            experiment_id: "exp-1",
            experiment_title: "一、卤素单质在不同溶剂中的溶解性",
            question_type: "fill_blank",
            stem: "CCl4 层常用于观察卤素单质的____。",
            options: [],
          },
        ],
      });
    }
    if (url.includes("/api/student/legacy/smart-assessment/submit")) {
      return jsonResponse({
        status: "completed",
        report: {
          session_id: "session-1",
          assessment_mode: "smart",
          correct_count: 2,
          total_count: 3,
          score: 66.7,
          correct_rate: 0.667,
          mastery_changes: [],
          wrong_answers: [
            {
              question_id: "smart-q2",
              experiment_id: "exp-1",
              experiment_title: "氯水漂白性实验",
              stem: "新制氯水具有氧化性。",
            },
          ],
          next_recommendation: "建议复盘氯水漂白性实验。",
        },
        assessment_report: {
          id: "assessment-report-1",
          title: "智能测评报告",
          report_type: "smart",
          source_session_id: "session-1",
          score: 66.7,
          correct_count: 2,
          total_count: 3,
          correct_rate: 0.667,
          wrong_count: 1,
          completed_at: "2026-06-26T10:30:00Z",
        },
      });
    }
    if (url.includes("/api/student/legacy/reports/assessment-report-1") || url.includes("/api/student/legacy/reports/report-1")) {
      return jsonResponse({
        id: url.includes("assessment-report-1") ? "assessment-report-1" : "report-1",
        title: "卤族元素测评",
        report_type: "smart",
        source_session_id: "session-1",
        score: 82,
        correct_count: 8,
        total_count: 10,
        correct_rate: 0.8,
        wrong_count: 1,
        completed_at: "2026-06-26T10:00:00Z",
        ai_summary: {
          text: "本次报告显示你对卤素氧化性判断已经有基础，但需要继续复盘氯水漂白性实验。",
          source: "fallback",
          mode: "legacy_local_summary",
          generated_at: "2026-06-26T10:00:01Z",
        },
        mistake_explanation: {
          text: "AI 已根据本次错题生成解析：新制氯水含有氯气和次氯酸，判断氧化性时要把实验现象与有效成分对应起来。",
          source: "ai",
          mode: "ai_generated",
          generated_at: "2026-06-26T10:00:02Z",
        },
        next_steps: "先复盘错题解析，再回到相关实验视频巩固现象和原理。",
        covered_experiments: ["氯水漂白性实验"],
        wrong_questions: [
          {
            question_id: "q1",
            stem: "新制氯水具有氧化性。",
            experiment_title: "氯水漂白性实验",
            question_type: "true_false",
            submitted_answer: "错误",
            correct_answer: "正确",
            explanation: "新制氯水中含有氯气和次氯酸，能体现氧化性。",
            explanation_source: "stored",
            options: [],
          },
        ],
      });
    }
    if (url.includes("/api/student/legacy/reports/report-perfect")) {
      return jsonResponse({
        id: "report-perfect",
        title: "全部正确测评",
        report_type: "custom",
        source_session_id: "session-perfect",
        score: 100,
        correct_count: 5,
        total_count: 5,
        correct_rate: 1,
        wrong_count: 0,
        completed_at: "2026-06-26T11:00:00Z",
        ai_summary: {
          text: "本次测评全部答对，可以继续保持当前学习节奏。",
          source: "fallback",
          mode: "legacy_local_summary",
          generated_at: "2026-06-26T11:00:01Z",
        },
        next_steps: "",
        covered_experiments: [],
        wrong_questions: [],
      });
    }
    if (url.includes("/api/student/legacy/reports")) {
      return jsonResponse({
        reports: [
          {
            id: "report-1",
            title: "卤族元素测评",
            report_type: "smart",
            source_session_id: "session-1",
            score: 82,
            correct_count: 8,
            total_count: 10,
            correct_rate: 0.8,
            wrong_count: 1,
            completed_at: "2026-06-26T10:00:00Z",
          },
          {
            id: "report-perfect",
            title: "全部正确测评",
            report_type: "custom",
            source_session_id: "session-perfect",
            score: 100,
            correct_count: 5,
            total_count: 5,
            correct_rate: 1,
            wrong_count: 0,
            completed_at: "2026-06-26T11:00:00Z",
          },
        ],
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

describe("LegacyStudentApp", () => {
  beforeEach(() => {
    ensureBrowserStorage();
    window.history.pushState({}, "", "/");
    window.localStorage.clear();
    setAuthToken("student-token");
    vi.stubGlobal("fetch", installStudentFetchMock());
  });

  afterEach(() => {
    setAuthToken("");
    cleanup();
    vi.unstubAllGlobals();
  });

  it("opens a four-module old student shell with a finite all-point home library", async () => {
    const { container } = render(<LegacyStudentApp />);

    expect(await screen.findByRole("heading", { name: "实验视频库" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "主页" }).className).toContain("active");
    expect(screen.getByRole("button", { name: "学习" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "评测" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "报告" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "我的" })).toBeNull();
    expect(container.querySelectorAll(".legacy-tabbar-icon svg")).toHaveLength(4);
    expect(await screen.findByText("氯水漂白性实验")).toBeTruthy();
    expect(await screen.findByText("钠与水反应观察")).toBeTruthy();
    expect(container.querySelector(".legacy-video-card h2")?.textContent).toBe("氯水漂白性实验");
    expect((container.querySelector(".legacy-video-preview") as HTMLVideoElement | null)?.src).toContain("/api/student/media/assets/media-1/stream");
    expect(screen.getByText("推荐学习")).toBeTruthy();
    expect(screen.getByText("没有更多视频了")).toBeTruthy();
    expect(screen.getByText(/默认显示全部视频点位，不管当前是否已绑定视频。搜索后显示搜索结果内容。/)).toBeTruthy();

    const fetchMock = vi.mocked(fetch);
    const homeCalls = fetchMock.mock.calls.map((call) => String(call[0])).filter((url) => url.includes("/api/student/home-video-feed"));
    expect(homeCalls).toHaveLength(0);
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/api/student/legacy/video-points"))).toBe(true);
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/api/student/video-library/search"))).toBe(false);
    expect(screen.queryByText("推荐内容")).toBeNull();
    expect(screen.queryByText("视频库定位")).toBeNull();
    expect(container.querySelector(".legacy-video-body .legacy-meta-row")?.textContent).not.toContain("全部视频");
    assertNoForbiddenVisibleTerms(container);
  });

  it("requires initial password change before loading student content", async () => {
    const baseFetch = installStudentFetchMock();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/auth/me")) {
        return jsonResponse({
          id: "student-1",
          username: "26320501",
          display_name: "张三",
          role: "student",
          status: "active",
          must_change_password: true,
          password_version: 1,
          student_id: "26320501",
          class_id: "seed-class-6",
          class_name: "26 级本科 6 班",
        });
      }
      if (url.includes("/api/auth/student/password")) {
        const payload = JSON.parse(String(init?.body || "{}")) as { new_password?: string };
        expect(payload.new_password).toBe("newpass123");
        return jsonResponse({
          access_token: "new-student-token",
          token_type: "bearer",
          user: {
            id: "student-1",
            username: "26320501",
            display_name: "张三",
            role: "student",
            status: "active",
            must_change_password: false,
            password_version: 2,
            student_id: "26320501",
            class_id: "seed-class-6",
            class_name: "26 级本科 6 班",
          },
        });
      }
      return baseFetch(input);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<LegacyStudentApp />);

    expect(await screen.findByRole("heading", { name: "修改初始密码" })).toBeTruthy();
    expect(screen.getByText(/当前账号正在使用初始密码/)).toBeTruthy();
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/api/student/assessment/status"))).toBe(false);
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/api/student/legacy/video-points"))).toBe(false);

    fireEvent.change(screen.getByLabelText("新密码"), { target: { value: "newpass123" } });
    fireEvent.change(screen.getByLabelText("确认新密码"), { target: { value: "newpass123" } });
    fireEvent.click(screen.getByRole("button", { name: "保存并进入学习" }));

    expect(await screen.findByRole("heading", { name: "实验视频库" })).toBeTruthy();
    expect(fetchMock.mock.calls.some((call) => String(call[0]).includes("/api/auth/student/password"))).toBe(true);
  });

  it("shows a clear message when the student ID is not on the roster", async () => {
    setAuthToken("");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/auth/student/login")) {
          return jsonResponse({ detail: "Student not found" }, 401);
        }
        return jsonResponse({}, 404);
      }),
    );

    render(<LegacyStudentApp />);

    fireEvent.change(screen.getByLabelText("学号"), { target: { value: "99999999" } });
    fireEvent.change(screen.getByLabelText("密码"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "进入学习" }));

    expect(await screen.findByText("学生不存在，请联系管理员添加。")).toBeTruthy();
  });

  it("auto-starts the first smart baseline assessment for a student with no answers", async () => {
    const baseFetch = installStudentFetchMock();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/student/assessment/status")) {
          return jsonResponse({
            has_completed_smart_baseline: false,
            has_answered_questions: false,
            needs_smart_baseline: true,
            has_open_assessment: false,
            open_session_id: null,
            open_assessment_mode: null,
            smart_baseline_prompt_dismissed: false,
          });
        }
        return baseFetch(input);
      }),
    );

    render(<LegacyStudentApp />);

    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/session-1"));
    expect(window.location.search).toBe("?from=baseline");
    expect(await screen.findByRole("heading", { name: "首次摸底测评" })).toBeTruthy();
    expect(screen.getByText("共 3 题")).toBeTruthy();
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/smart-assessment/start"))).toBe(true);
  });

  it("returns from a home-opened point to the home video library", async () => {
    render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "打开 氯水漂白性实验" }));
    await screen.findByRole("heading", { name: "氯水漂白性实验" });

    fireEvent.click(screen.getByRole("button", { name: "返回首页" }));

    await waitFor(() => expect(window.location.pathname).toBe("/"));
    expect(await screen.findByRole("heading", { name: "实验视频库" })).toBeTruthy();
  });

  it("keeps search owned by the old home video library", async () => {
    const { container } = render(<LegacyStudentApp />);

    const input = await screen.findByPlaceholderText("输入实验、试剂、现象或点位名称");
    fireEvent.change(input, { target: { value: "氯水" } });
    fireEvent.click(screen.getByRole("button", { name: "搜索" }));

    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/legacy/video-points") && String(call[0]).includes("q="))).toBe(true));
    expect(await screen.findByText("当前共 1 个搜索结果")).toBeTruthy();
    expect(screen.getByRole("button", { name: "返回全部视频库" })).toBeTruthy();
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/video-library/search"))).toBe(false);
    expect(screen.queryByText("推荐内容")).toBeNull();
    expect(screen.queryByText("推荐搜索")).toBeNull();
    expect(screen.queryByText("分类浏览")).toBeNull();
    expect(container.querySelector(".legacy-video-body .legacy-meta-row")?.textContent).not.toContain("搜索结果");
    assertNoForbiddenVisibleTerms(container);
  });

  it("drills from periodic table to catalog directory and native point video", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "学习" }));
    expect(await screen.findByRole("heading", { name: "元素周期表" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "先从周期表的这一层进入" })).toBeNull();
    expect(screen.getAllByText("p区元素").length).toBeGreaterThan(0);
    expect(container.querySelector(".legacy-area-legend button.recommended")?.textContent).toContain("p区元素");
    expect(container.querySelector(".legacy-profile-grid button.recommended")?.textContent).toContain("卤素");

    fireEvent.click(screen.getByRole("button", { name: "Cl 氯" }));
    expect(await screen.findByText("当前章节：卤素")).toBeTruthy();
    await waitFor(() => expect(container.querySelector(".legacy-catalog-row.recommended")).toBeTruthy());
    expect(screen.queryByRole("heading", { name: "先看这些目录内容" })).toBeNull();
    expect(screen.getByText("薄弱点位")).toBeTruthy();
    expect(screen.getByRole("button", { name: "元素周期表" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "返回上一级目录" })).toBeTruthy();
    expect(await screen.findByText("当前元素")).toBeTruthy();
    expect(await screen.findByText("Cl 氯")).toBeTruthy();
    expect(await screen.findByText("氧化性与置换反应")).toBeTruthy();
    expect(await screen.findByText("原子序数 17")).toBeTruthy();
    expect(screen.queryByText("17族")).toBeNull();
    expect(screen.queryByText("元素族学习章节")).toBeNull();
    expect(screen.queryByRole("heading", { name: "17族（卤素）" })).toBeNull();
    expect(container.querySelector(".legacy-property-grid")).toBeNull();
    expect(container.querySelectorAll(".legacy-catalog-row")).toHaveLength(1);
    expect(screen.getByText("He").closest("button")?.style.background).toBe("rgb(238, 243, 255)");

    fireEvent.click((await screen.findAllByText("氯的氧化性"))[0].closest("button")!);
    await waitFor(() => expect(container.querySelector(".legacy-catalog-row.kind-point.recommended")).toBeTruthy());
    expect(screen.queryByRole("heading", { name: "先看这些目录内容" })).toBeNull();
    expect((await screen.findAllByText("氯水漂白性实验")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("heading", { name: "氯的氧化性" })).toBeNull();

    fireEvent.click((await screen.findAllByText("氯水漂白性实验"))[0].closest("button")!);
    await screen.findByRole("heading", { name: "氯水漂白性实验" });
    expect(screen.getByRole("button", { name: "返回学习目录" })).toBeTruthy();
    expect(screen.getByText("Cl2 + 2I- → 2Cl- + I2")).toBeTruthy();
    expect(screen.getByText("优先氧化 I-")).toBeTruthy();
    expect(screen.getByText("I2 + 5Cl2 + 6H2O → 2HIO3 + 10HCl")).toBeTruthy();
    expect(container.querySelectorAll(".legacy-principle-line").length).toBeGreaterThanOrEqual(3);
    const video = container.querySelector("video.native-video");
    expect(video).toBeTruthy();
    expect(video?.hasAttribute("controls")).toBe(true);
    expect(container.querySelector(".artplayer")).toBeNull();
    expect(screen.getByRole("heading", { name: "相关实验链接" })).toBeTruthy();
    expect(screen.getByText("磷在氧气中的燃烧")).toBeTruthy();
    expect(screen.getByText("铁丝在氧气中的燃烧")).toBeTruthy();
    expect(screen.getByText("推荐实验")).toBeTruthy();
    expect(screen.getByText("相关实验")).toBeTruthy();
    expect(screen.queryByText("BKT 后续建议")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /进行学后测评/ }));
    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/point-assessment/start"))).toBe(true));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/point-session-1"));
    expect(await screen.findByText("学后点位测评")).toBeTruthy();
    expect(await screen.findByText("氯水优先氧化哪一种离子？")).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("filters learnable chapters by selected periodic area and shows short chapter names", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "学习" }));
    await screen.findByRole("heading", { name: "元素周期表" });

    expect(screen.getByRole("button", { name: "卤素" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "碱金属" })).toBeTruthy();
    expect(screen.queryByText("17族（卤素）")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "s区元素" }));
    expect(screen.getByRole("button", { name: "碱金属" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "卤素" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "p区元素" }));
    expect(screen.getByRole("button", { name: "卤素" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "碱金属" })).toBeNull();
    assertNoForbiddenVisibleTerms(container);
  });

  it("returns from the old chapter breadcrumb to the periodic table", async () => {
    render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "学习" }));
    fireEvent.click(await screen.findByRole("button", { name: "Cl 氯" }));
    expect(await screen.findByText("当前章节：卤素")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "元素周期表" }));

    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(await screen.findByRole("heading", { name: "元素周期表" })).toBeTruthy();
  });

  it("shows a controlled unavailable state when an element has no profile", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "学习" }));
    await screen.findByRole("heading", { name: "元素周期表" });
    fireEvent.click(screen.getByRole("button", { name: "H 氢" }));

    expect(await screen.findByText("H 氢 暂无已发布学习章节。")).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("renders unified old assessment setup without the experiment range list", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "评测" }));
    expect(await screen.findByRole("heading", { name: "按掌握度与范围出题" })).toBeTruthy();
    expect(screen.queryByText("目标题数")).toBeNull();
    expect(screen.getByRole("button", { name: /智能组卷/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /自主选择测试范围/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /随机练习/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /全部范围/ })).toBeNull();
    expect(screen.queryByText("一、卤素单质在不同溶剂中的溶解性")).toBeNull();
    expect(screen.queryByPlaceholderText("搜索章节、目录或点位")).toBeNull();
    expect(screen.queryByText("生成智能测评")).toBeNull();
    assertNoForbiddenVisibleTerms(container);
  });

  it("filters and validates selected-range assessment before starting", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "评测" }));
    fireEvent.click(screen.getByRole("button", { name: /自主选择测试范围/ }));
    expect(screen.queryByText("卤素单质在不同溶剂中的溶解性")).toBeNull();
    expect(screen.getByRole("button", { name: "进入选择测试范围" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "进入选择测试范围" }));
    expect(screen.getByText("自主选择测试范围")).toBeTruthy();
    expect(screen.getByRole("button", { name: "返回测评方式" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "仅显示有题实验" })).toBeNull();
    expect(screen.getByText("每个点位抽题数")).toBeTruthy();
    expect(await screen.findByText("卤素单质在不同溶剂中的溶解性")).toBeTruthy();
    expect(screen.getAllByText("15 题").length).toBeGreaterThan(0);
    expect((screen.getByRole("button", { name: "开始测评" }) as HTMLButtonElement).disabled).toBe(true);

    fireEvent.change(screen.getByPlaceholderText("搜索章节、目录或点位"), { target: { value: "氧气" } });
    expect(await screen.findByText("氧气的制备与性质")).toBeTruthy();
    expect(screen.queryByText("卤素单质在不同溶剂中的溶解性")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /过氧化氢制取氧气/ }));
    fireEvent.click(screen.getByRole("button", { name: "2" }));
    fireEvent.click(screen.getByRole("button", { name: "开始测评" }));

    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/custom-session-1"));
    const customStartCall = vi.mocked(fetch).mock.calls.find((call) => String(call[0]).includes("/api/student/custom-assessment/start"));
    expect(JSON.parse(String(customStartCall?.[1]?.body))).toMatchObject({ scope_node_ids: ["point-oxygen-prep"], questions_per_point: 2 });
    expect(await screen.findByText("自选范围测评")).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("starts smart weak-point testing and renders old exam questions", async () => {
    const baseFetch = installStudentFetchMock();
    let resolveSubmit: (() => void) | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/student/legacy/smart-assessment/submit")) {
          return new Promise<Response>((resolve) => {
            resolveSubmit = () => {
              void baseFetch(input).then(resolve);
            };
          });
        }
        return baseFetch(input);
      }),
    );
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "评测" }));
    fireEvent.click(screen.getByRole("button", { name: "开始测评" }));

    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/session-1"));
    expect(await screen.findByText("智能组卷测评")).toBeTruthy();
    expect(screen.getByRole("button", { name: "返回评测" })).toBeTruthy();
    expect(screen.getByText("共 3 题")).toBeTruthy();
    expect(screen.getByText("已完成 0 题")).toBeTruthy();
    expect(screen.queryByText("薄弱倾向 60%")).toBeNull();
    expect(screen.queryByText("目标 5 题")).toBeNull();
    expect(screen.queryByText("实际 3 题")).toBeNull();
    expect(screen.getByText("题库可用题量不足，系统已按当前题库生成 3 题。")).toBeTruthy();
    expect(screen.getByText("氯水使试纸褪色的主要原因是什么？")).toBeTruthy();
    expect(screen.getByText("新制氯水具有氧化性。")).toBeTruthy();
    expect(screen.getByText("氯水与____反应可生成____。")).toBeTruthy();
    expect((screen.getByRole("button", { name: /请完成全部题目/ }) as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: /生成次氯酸/ }));
    fireEvent.click(screen.getByRole("button", { name: /正确/ }));
    fireEvent.change(screen.getByPlaceholderText("第 1 空答案"), { target: { value: "水" } });
    fireEvent.change(screen.getByPlaceholderText("第 2 空答案"), { target: { value: "HClO" } });
    expect(screen.getByText("已完成 3 题")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "提交答案" }));

    expect((await screen.findByRole("status")).textContent).toContain("正在批改答案并生成报告");
    expect(screen.getByText(/正在判分、更新各部分掌握度，并生成学习总结和错题讲解/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "正在批改并生成报告..." })).toBeTruthy();
    resolveSubmit?.();

    await waitFor(() => expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/legacy/smart-assessment/submit"))).toBe(true));
    const submitCall = vi.mocked(fetch).mock.calls.find((call) => String(call[0]).includes("/api/student/legacy/smart-assessment/submit"));
    expect(JSON.parse(String(submitCall?.[1]?.body)).answers).toContainEqual({ question_id: "smart-q3", answer: ["水", "HClO"] });
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/smart-assessment/submit"))).toBe(false);
    expect(await screen.findByRole("heading", { name: "智能组卷测评完成" })).toBeTruthy();
    expect(screen.getByText("66.7")).toBeTruthy();
    expect(screen.getByRole("button", { name: "返回测评" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "查看报告" })).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("explains stale legacy assessment submit sessions", () => {
    expect(legacyStudentErrorMessage(new ApiError(409, "No active assessment session"))).toBe(
      "本轮测评已经提交或已失效，请返回评测重新开始。",
    );
    expect(legacyStudentErrorMessage(new ApiError(401, "Student not found"))).toBe("学生不存在，请联系管理员添加。");
  });

  it("starts custom range assessment with a selected directory scope", async () => {
    render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "评测" }));
    fireEvent.click(screen.getByRole("button", { name: /自主选择测试范围/ }));
    fireEvent.click(screen.getByRole("button", { name: "进入选择测试范围" }));
    fireEvent.click(await screen.findByRole("button", { name: /卤素单质在不同溶剂中的溶解性/ }));
    fireEvent.click(screen.getByRole("button", { name: "3" }));
    fireEvent.click(screen.getByRole("button", { name: "开始测评" }));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/custom-session-1"));
    const calls = vi.mocked(fetch).mock.calls.filter((call) => String(call[0]).includes("/api/student/custom-assessment/start"));
    expect(JSON.parse(String(calls.at(-1)?.[1]?.body))).toMatchObject({
      scope_node_ids: ["dir-halogen-solubility"],
      questions_per_point: 3,
    });
  });

  it("renders report list and legacy AI wrong-question detail", async () => {
    const { container } = render(<LegacyStudentApp />);

    fireEvent.click(await screen.findByRole("button", { name: "报告" }));
    expect(screen.getByRole("button", { name: "退出登录" })).toBeTruthy();
    expect(await screen.findByText("学号")).toBeTruthy();
    expect(screen.getByText("2026001")).toBeTruthy();
    expect(screen.getByText("李同学")).toBeTruthy();
    expect(screen.getByText("数智一班")).toBeTruthy();
    expect(await screen.findByRole("heading", { name: "报告" })).toBeTruthy();
    expect(screen.getByText("待复盘错题")).toBeTruthy();
    expect(screen.getByText("卤族元素测评")).toBeTruthy();
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/legacy/reports"))).toBe(true);
    expect(vi.mocked(fetch).mock.calls.some((call) => String(call[0]).includes("/api/student/assessment-reports"))).toBe(false);

    fireEvent.click(screen.getAllByText("查看报告")[0]);
    await waitFor(() => expect(window.location.pathname).toBe("/reports/report-1"));
    expect(await screen.findByRole("heading", { name: "卤族元素测评" })).toBeTruthy();
    expect(screen.getByText("AI 学情总结")).toBeTruthy();
    expect(screen.getByText("错题解析")).toBeTruthy();
    expect(screen.getByText(/AI 已根据本次错题生成解析/)).toBeTruthy();
    expect(screen.getByText("新制氯水具有氧化性。")).toBeTruthy();
    expect(screen.queryByText("你的答案")).toBeNull();
    expect(screen.queryByText("参考答案")).toBeNull();
    expect(screen.getByRole("button", { name: "返回报告" })).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("shows a clear state when a legacy report has no wrong questions", async () => {
    window.history.pushState({}, "", "/reports/report-perfect");
    const { container } = render(<LegacyStudentApp />);

    expect(await screen.findByRole("heading", { name: "全部正确测评" })).toBeTruthy();
    expect(screen.getByText("本次没有错题。")).toBeTruthy();
    expect(screen.getByText("AI 学情总结")).toBeTruthy();
    assertNoForbiddenVisibleTerms(container);
  });

  it("redirects stale assistant routes to the safe home route", async () => {
    window.history.pushState({}, "", "/ai/chat");
    const { container } = render(<LegacyStudentApp />);

    await screen.findByRole("heading", { name: "实验视频库" });
    await waitFor(() => expect(window.location.pathname).toBe("/"));
    assertNoForbiddenVisibleTerms(container);
  });
});
