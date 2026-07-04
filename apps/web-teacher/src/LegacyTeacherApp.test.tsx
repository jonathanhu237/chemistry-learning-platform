import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LegacyTeacherApp } from "./LegacyTeacherApp";
import { setAuthToken } from "./api";

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function requestUrl(input: RequestInfo | URL): URL {
  const raw = typeof Request !== "undefined" && input instanceof Request ? input.url : String(input);
  return new URL(raw, "http://teacher-old.test");
}

function requestPaths(fetchMock: ReturnType<typeof installTeacherFetchMock>): string[] {
  return fetchMock.mock.calls.map((call) => {
    const url = requestUrl(call[0]);
    return `${url.pathname}${url.search}`;
  });
}

function cloneJson<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function expectNoForbiddenGenerationFlows(fetchMock: ReturnType<typeof installTeacherFetchMock>) {
  const urls = fetchMock.mock.calls.map((call) => requestUrl(call[0]));

  expect(urls.some((url) => url.pathname === "/api/teacher/question-banks/generate")).toBe(false);
  expect(urls.some((url) => `${url.pathname}${url.search}`.includes("workbench"))).toBe(false);
  expect(urls.some((url) => `${url.pathname}${url.search}`.includes("evidence-refresh"))).toBe(false);
}

const baseCounts = {
  question_count: 0,
  published_count: 0,
  draft_count: 0,
  disabled_count: 0,
  choice_count: 0,
  true_false_count: 0,
  fill_blank_count: 0,
  draft_candidate_count: 0,
  rejected_candidate_count: 0,
  published_candidate_count: 0,
  point_count: 0,
  directory_count: 0,
};

const catalogNodes = [
  {
    node_id: "dir-ch13-oxidation",
    parent_id: null,
    chapter_id: "CH13",
    node_kind: "directory",
    title: "氯的氧化性",
    summary: "氯水与还原性物质的反应。",
    status: "published",
    display_order: 1,
    content_status: null,
    media_count: 0,
    published_media_count: 0,
    breadcrumb_titles: ["CH13 卤族元素", "氯的氧化性"],
    root_node_id: "dir-ch13-oxidation",
    experiment_id: "exp-ch13",
    descendant_point_count: 2,
    counts: { ...baseCounts, question_count: 2, published_count: 1, draft_count: 1, point_count: 2, directory_count: 1 },
  },
  {
    node_id: "point-ch13-bleach",
    parent_id: "dir-ch13-oxidation",
    chapter_id: "CH13",
    node_kind: "point",
    title: "氯水漂白性实验",
    summary: "观察氯水使有色布条褪色。",
    status: "published",
    display_order: 2,
    canonical_point_id: "canon-bleach",
    canonical_point_title: "氯水漂白性实验",
    content_status: "published",
    principle_mode: "text",
    principle_text: "新制氯水中的 HClO 具有强氧化性。",
    phenomenon_explanation: "湿润有色布条逐渐褪色，干燥布条变化不明显。",
    safety_note: "氯水有刺激性气味，应在通风条件下少量取用。",
    media_count: 1,
    published_media_count: 1,
    breadcrumb_titles: ["CH13 卤族元素", "氯的氧化性", "氯水漂白性实验"],
    root_node_id: "dir-ch13-oxidation",
    experiment_id: "exp-ch13-bleach",
    descendant_point_count: 0,
    counts: { ...baseCounts, question_count: 1, published_count: 0, draft_count: 1, choice_count: 1, point_count: 1 },
  },
  {
    node_id: "dir-ch13-displacement",
    parent_id: null,
    chapter_id: "CH13",
    node_kind: "directory",
    title: "溴碘置换",
    summary: "比较氯、溴、碘单质的氧化性顺序。",
    status: "published",
    display_order: 3,
    content_status: null,
    media_count: 0,
    published_media_count: 0,
    breadcrumb_titles: ["CH13 卤族元素", "溴碘置换"],
    root_node_id: "dir-ch13-displacement",
    experiment_id: "exp-ch13",
    descendant_point_count: 2,
    counts: { ...baseCounts, question_count: 1, published_count: 1, point_count: 2, directory_count: 1 },
  },
  {
    node_id: "point-ch13-kbr",
    parent_id: "dir-ch13-displacement",
    chapter_id: "CH13",
    node_kind: "point",
    title: "氯水 + KBr + CCl4",
    summary: "观察溴被置换后在有机层中的颜色。",
    status: "published",
    display_order: 4,
    canonical_point_id: "canon-kbr",
    canonical_point_title: "氯水置换溴离子",
    content_status: "published",
    principle_mode: "text",
    principle_text: "Cl2 可氧化 Br- 生成 Br2。",
    phenomenon_explanation: "下层 CCl4 呈橙红色。",
    safety_note: "CCl4 避免吸入，废液集中回收。",
    media_count: 1,
    published_media_count: 1,
    breadcrumb_titles: ["CH13 卤族元素", "溴碘置换", "氯水 + KBr + CCl4"],
    root_node_id: "dir-ch13-displacement",
    experiment_id: "exp-ch13-kbr",
    descendant_point_count: 0,
    counts: { ...baseCounts, question_count: 1, published_count: 1, true_false_count: 1, point_count: 1 },
  },
  {
    node_id: "point-ch13-iodide",
    parent_id: "dir-ch13-displacement",
    chapter_id: "CH13",
    node_kind: "point",
    title: "碘离子检验",
    summary: "用淀粉观察碘单质生成。",
    status: "draft",
    display_order: 5,
    canonical_point_id: "canon-iodide",
    canonical_point_title: "碘离子检验",
    content_status: "draft",
    principle_mode: "text",
    principle_text: "I- 被氧化后与淀粉形成蓝色络合物。",
    phenomenon_explanation: "溶液遇淀粉后呈蓝色。",
    safety_note: "碘液避免接触皮肤。",
    media_count: 0,
    published_media_count: 0,
    breadcrumb_titles: ["CH13 卤族元素", "溴碘置换", "碘离子检验"],
    root_node_id: "dir-ch13-displacement",
    experiment_id: "exp-ch13-iodide",
    descendant_point_count: 0,
    counts: { ...baseCounts, point_count: 1 },
  },
] as const;

function catalogResponse() {
  return {
    items: catalogNodes,
    total: catalogNodes.length,
    chapters: [
      {
        chapter_id: "CH13",
        chapter_number: 13,
        chapter_title: "CH13 卤族元素",
        element_area: "非金属元素",
        point_count: 3,
      },
    ],
    chapter_id: "CH13",
    totals: {
      ...baseCounts,
      question_count: 3,
      published_count: 2,
      draft_count: 1,
      choice_count: 1,
      true_false_count: 1,
      fill_blank_count: 1,
      point_count: 3,
      directory_count: 2,
    },
  };
}

function catalogDetail(nodeId: string) {
  const node = catalogNodes.find((item) => item.node_id === nodeId) || catalogNodes[1];
  const isPoint = node.node_kind === "point";
  const mediaBindings =
    node.node_id === "point-ch13-bleach"
      ? [
          {
            binding_id: "binding-ch13-bleach",
            node_id: node.node_id,
            media_id: "media-ch13-bleach",
            title: "氯水漂白性实验视频",
            binding_status: "published",
            display_order: 1,
            published_at: "2026-07-02T10:00:00Z",
            metadata: {},
            original_file_name: "bleach-demo.mp4",
            mime_type: "video/mp4",
            playback_mime_type: "video/mp4",
            source_file_size_bytes: 2_048_000,
            playback_file_size_bytes: 1_024_000,
            playback_duration_seconds: 96,
            upload_status: "ready",
            processing_phase: "completed",
            processing_progress: 100,
            error_reason: null,
            has_thumbnail: true,
            created_at: "2026-07-02T09:50:00Z",
            updated_at: "2026-07-02T10:00:00Z",
          },
        ]
      : [];

  return {
    node: {
      ...node,
      teacher_note: isPoint ? "课堂讨论时强调现象与氧化性之间的证据链。" : "CH13 目录备注",
      validation: { ok: true, errors: [], warnings: [] },
    },
    breadcrumbs: node.breadcrumb_titles.map((title, index) => ({
      node_id: index === node.breadcrumb_titles.length - 1 ? node.node_id : `breadcrumb-${index}`,
      title,
      node_kind: index === node.breadcrumb_titles.length - 1 ? node.node_kind : "directory",
      chapter_id: node.chapter_id,
    })),
    children: catalogNodes.filter((item) => item.parent_id === node.node_id),
    point_content: isPoint
      ? {
          node_id: node.node_id,
          canonical_point_id: node.canonical_point_id,
          point_title: node.title,
          teacher_note: "课堂讨论时强调现象与氧化性之间的证据链。",
          principle_mode: node.principle_mode,
          principle_text: node.principle_text,
          phenomenon_explanation: node.phenomenon_explanation,
          safety_note: node.safety_note,
          content_status: node.content_status,
      }
      : null,
    media_bindings: mediaBindings,
    validation: { ok: true, errors: [], warnings: [] },
  };
}

const draftQuestion = {
  id: "draft-ch13-1",
  generation_id: "gen-ch13-1",
  experiment_id: "exp-ch13-bleach",
  status: "draft",
  prompt: "围绕氯水漂白性实验生成课堂测评题。",
  mode: "legacy_point",
  validation_errors: [],
  payload: {
    id: "draft-payload-1",
    experiment_id: "exp-ch13-bleach",
    question_type: "single_choice",
    stem: "氯水使湿润有色布条褪色，最关键的微粒是什么？",
    options: [
      { label: "A", text: "HClO" },
      { label: "B", text: "Cl-" },
      { label: "C", text: "K+" },
      { label: "D", text: "CCl4" },
    ],
    answer: { value: "A" },
    explanation: "新制氯水中的 HClO 具有强氧化性，能使有色物质褪色。",
    difficulty: "basic",
    status: "draft",
  },
};

const publishedQuestion = {
  id: "question-ch13-1",
  experiment_id: "exp-ch13-bleach",
  question_type: "single_choice",
  stem: "为什么干燥有色布条放入氯气中不明显褪色？",
  options: [
    { label: "A", text: "缺少水生成 HClO" },
    { label: "B", text: "氯气不能溶于水" },
  ],
  answer: { value: "A" },
  explanation: "氯气需要与水反应生成 HClO 后才表现出明显漂白性。",
  difficulty: "basic",
  status: "published",
};

function extraPublishedQuestion(index: number) {
  return {
    ...cloneJson(publishedQuestion),
    id: `question-ch13-extra-${index}`,
    stem: `正式题库完整展示题 ${index}`,
    options: [
      { label: "A", text: `完整展示选项 ${index}` },
      { label: "B", text: "干扰项" },
    ],
    answer: { value: "A" },
    explanation: `正式题库解析 ${index}`,
  };
}

const classes = [
  {
    id: "class-1",
    class_name: "无机化学一班",
    description: "2026 春季 CH13 教学班",
    status: "active",
    student_count: 2,
    active_students: 2,
    completion_rate: 75,
    average_score: 82,
    missing_students: 0,
  },
];

const students = [
  {
    id: "class-student-1",
    class_id: "class-1",
    student_id: "2026001",
    student_name: "张三",
    username: "2026001",
    display_name: "张三",
    status: "active",
    activation_mode: "default_password",
    activated: true,
    class_name: "无机化学一班",
  },
  {
    id: "class-student-2",
    class_id: "class-1",
    student_id: "2026002",
    student_name: "李四",
    username: "2026002",
    display_name: "李四",
    status: "active",
    activation_mode: "default_password",
    activated: true,
    class_name: "无机化学一班",
  },
];

const smartAssessmentStrategy = {
  enabled: true,
  question_count: 10,
  untested_ratio_percent: 20,
  weak_tendency_percent: 70,
  max_questions_per_experiment: 2,
  weak_curve: 2,
  weak_max_bonus: 9,
};

function analyticsDashboard() {
  return {
    class_id: "class-1",
    metrics: {
      class_size: 2,
      active_students: 2,
      published_experiments: 2,
      published_experiment_groups: 1,
      completion_rate: 75,
      average_score: 82,
      missing_students: 0,
    },
    experiments: [],
    experiment_groups: [
      { id: "CAT-CH13-f99cb352", code: "CAT-CH13-f99cb352", title: "CAT-CH13-f99cb352", experiment_count: 2 },
      { id: "CAT-CH14-b62492d6", code: "CAT-CH14-b62492d6", title: "CAT-CH14-b62492d6", experiment_count: 1 },
    ],
    matrix: [
      {
        student_id: "2026001",
        student_name: "张三",
        status: "active",
        average_score: 88,
        experiments: {},
        experiment_groups: {
          "CAT-CH13-f99cb352": {
            status: "completed",
            mastery_score: 88,
            score: 88,
            evidence_count: 4,
            attempt_count: 2,
            points: [
              { point_node_id: "point-ch13-bleach", point_title: "氯水漂白性实验", experiment_id: "exp-ch13-bleach", experiment_title: "氯水氧化性", mastery_score: 92, score: 92, evidence_count: 2 },
              { point_node_id: "point-ch13-kbr", point_title: "氯水 + KBr + CCl4", experiment_id: "exp-ch13-kbr", experiment_title: "溴碘置换", mastery_score: 84, score: 84, evidence_count: 2 },
            ],
          },
          "CAT-CH14-b62492d6": {
            status: "completed",
            mastery_score: 82,
            score: 82,
            evidence_count: 2,
            attempt_count: 1,
            points: [
              { point_node_id: "point-ch14-h2o2", point_title: "过氧化氢分解", experiment_id: "exp-ch14-h2o2", experiment_title: "氧族元素", mastery_score: 82, score: 82, evidence_count: 2 },
            ],
          },
        },
      },
      {
        student_id: "2026002",
        student_name: "李四",
        status: "active",
        average_score: 76,
        experiments: {},
        experiment_groups: {
          "CAT-CH13-f99cb352": {
            status: "learning",
            mastery_score: 70,
            score: 70,
            evidence_count: 3,
            attempt_count: 2,
            points: [
              { point_node_id: "point-ch13-bleach", point_title: "氯水漂白性实验", experiment_id: "exp-ch13-bleach", experiment_title: "氯水氧化性", mastery_score: 78, score: 78, evidence_count: 2 },
              { point_node_id: "point-ch13-iodide", point_title: "碘离子检验", experiment_id: "exp-ch13-iodide", experiment_title: "溴碘置换", mastery_score: 62, score: 62, evidence_count: 1 },
            ],
          },
          "CAT-CH14-b62492d6": {
            status: "needs_attention",
            mastery_score: 58,
            score: 58,
            evidence_count: 1,
            attempt_count: 1,
            points: [
              { point_node_id: "point-ch14-h2o2", point_title: "过氧化氢分解", experiment_id: "exp-ch14-h2o2", experiment_title: "氧族元素", mastery_score: 58, score: 58, evidence_count: 1 },
            ],
          },
        },
      },
    ],
    recent_activity: [],
    missing_students: [],
  };
}

function studentLearningReport(studentId: string) {
  const studentName = studentId === "2026002" ? "李四" : "张三";

  return {
    student: { student_id: studentId, student_name: studentName },
    progress: [],
    latest_posttest_report: {
      session_id: `session-${studentId}`,
      score: studentId === "2026002" ? 76 : 88,
      correct_count: studentId === "2026002" ? 3 : 4,
      total_count: 5,
      ai_summary: {
        text: `${studentName}已经掌握 CH13 氯水漂白的核心证据。`,
        source: "assessment_report",
        mode: "prompt",
      },
      ai_mistake_explanation: {
        text: `${studentName}需要继续区分卤素单质和卤离子。`,
        source: "assessment_report",
        mode: "prompt",
      },
    },
    weak_video_points: [{ point_title: "碘离子检验", incorrect_rate: 40, attempt_count: 2 }],
  };
}

const assessmentReportSummary = {
  id: "report-ch13-1",
  student_id: "2026001",
  class_id: "class-1",
  report_type: "posttest",
  source_session_id: "session-2026001",
  title: "CH13 后测评价报告",
  score: 88,
  correct_count: 4,
  total_count: 5,
  correct_rate: 0.8,
  wrong_count: 1,
  completed_at: "2026-07-02T10:00:00Z",
};

const assessmentReportDetail = {
  ...assessmentReportSummary,
  summary: {
    text: "张三已经能解释氯水漂白现象，并能把 HClO 与氧化性联系起来。",
    source: "assessment_report_prompts",
    mode: "teacher_prompt",
  },
  mistake_explanation: {
    text: "错题集中在溴碘置换顺序，需要回看 KBr 与 CCl4 的分层颜色。",
    source: "assessment_report_prompts",
    mode: "teacher_prompt",
  },
  prompt_snapshot: { summary_prompt: "请总结 {{student_name}} 的 CH13 学习表现。" },
  payload: { chapter_id: "CH13" },
};

function installTeacherFetchMock() {
  let questionDrafts = [cloneJson(draftQuestion)];
  let questionBankQuestions = [cloneJson(publishedQuestion), ...Array.from({ length: 11 }, (_, index) => extraPublishedQuestion(index + 1))];
  let teacherAccounts = [
    {
      id: "teacher-1",
      username: "teacher",
      display_name: "王老师",
      role: "teacher",
      status: "active",
      must_change_password: false,
    },
    {
      id: "teacher-2",
      username: "teacher2",
      display_name: "李老师",
      role: "teacher",
      status: "disabled",
      must_change_password: true,
    },
  ];
  let aiConfiguration = {
    provider: "openai",
    base_url: "https://api.deepseek.com",
    model: "deepseek-v4-flash",
    connection_check_interval_minutes: 30,
    api_key_configured: false,
    api_key_fingerprint: null as string | null,
    can_edit: true,
    enabled_features: {
      rag_access_enabled: true,
      student_ai_assistant: true,
      student_learning_analytics: true,
      question_bank_assistant: true,
      teacher_learning_analytics: true,
    },
    status: {
      ready: false,
      message: "请先保存模型名称和 API Key。",
      effective_mode: "fallback",
      connectivity_status: "not_configured",
      recent_request_count: 0,
      recent_error_count: 0,
      last_checked_at: null as string | null,
    },
    chat_provider: {
      role: "chat_completion",
      provider: "openai",
      base_url: "https://api.deepseek.com",
      model: "deepseek-v4-flash",
      api_key_configured: false,
      api_key_fingerprint: null as string | null,
    },
  };

  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = requestUrl(input);
    const path = url.pathname;
    const method = String(init?.method || "GET").toUpperCase();

    if (path === "/api/auth/me") {
      return jsonResponse({
        id: "teacher-1",
        username: "teacher",
        display_name: "王老师",
        role: "teacher",
        status: "active",
      });
    }

    if (path === "/api/auth/password" && method === "POST") {
      return jsonResponse({ ok: true });
    }

    if (path === "/api/teacher/accounts/teachers" && method === "GET") {
      return jsonResponse(teacherAccounts);
    }

    if (path === "/api/teacher/accounts/teachers" && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      const account = {
        id: `teacher-${teacherAccounts.length + 1}`,
        username: body.username,
        display_name: body.display_name,
        role: "teacher",
        status: "active",
        must_change_password: Boolean(body.must_change_password),
      };
      teacherAccounts = [...teacherAccounts, account];
      return jsonResponse(account, 201);
    }

    if (path.startsWith("/api/teacher/accounts/teachers/") && method === "PATCH") {
      const accountId = decodeURIComponent(path.split("/").at(-1) || "");
      const body = JSON.parse(String(init?.body || "{}"));
      const existing = teacherAccounts.find((account) => account.id === accountId);
      if (!existing) return jsonResponse({ detail: "Teacher account not found" }, 404);
      const updated = { ...existing, ...body };
      teacherAccounts = teacherAccounts.map((account) => (account.id === accountId ? updated : account));
      return jsonResponse(updated);
    }

    if (path === "/api/teacher/ai-configuration") {
      if (method === "PUT") {
        const body = JSON.parse(String(init?.body || "{}"));
        const nextBaseUrl = body.base_url || body.chat_provider?.base_url || aiConfiguration.base_url;
        const nextModel = body.model || body.chat_provider?.model || aiConfiguration.model;
        const nextApiKeyConfigured = Boolean(body.api_key) || aiConfiguration.api_key_configured;
        aiConfiguration = {
          ...aiConfiguration,
          provider: "openai",
          base_url: nextBaseUrl,
          model: nextModel,
          api_key_configured: nextApiKeyConfigured,
          api_key_fingerprint: nextApiKeyConfigured ? (body.api_key ? "sk-...test" : aiConfiguration.api_key_fingerprint || "sk-...saved") : null,
          can_edit: true,
          status: {
            ready: Boolean(nextModel && nextApiKeyConfigured),
            message: nextApiKeyConfigured ? `模型 ${nextModel} 可访问。` : "请先保存模型名称和 API Key。",
            effective_mode: nextApiKeyConfigured ? "ai" : "fallback",
            connectivity_status: nextApiKeyConfigured ? "connected" : "not_configured",
            recent_request_count: 0,
            recent_error_count: 0,
            last_checked_at: "2026-07-03T08:00:00Z",
          },
          chat_provider: {
            role: "chat_completion",
            provider: "openai",
            base_url: nextBaseUrl,
            model: nextModel,
            api_key_configured: nextApiKeyConfigured,
            api_key_fingerprint: nextApiKeyConfigured ? (body.api_key ? "sk-...test" : aiConfiguration.api_key_fingerprint || "sk-...saved") : null,
          },
        };
        return jsonResponse(aiConfiguration);
      }

      return jsonResponse(aiConfiguration);
    }

    if (path === "/api/teacher/question-banks/catalog") {
      return jsonResponse(catalogResponse());
    }

    if (path === "/api/teacher/media/upload-policy") {
      return jsonResponse({
        max_media_upload_mb: 200,
        max_media_upload_bytes: 209_715_200,
        allowed_extensions: [".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"],
      });
    }

    if (path === "/api/teacher/media/assets" && method === "POST") {
      return jsonResponse({
        id: "media-uploaded-iodide",
        title: "碘离子检验演示",
        original_file_name: "iodide-demo.mp4",
        mime_type: "video/mp4",
        file_size_bytes: 12,
        upload_status: "processing",
        processing_phase: "queued",
        processing_progress: 0,
        error_reason: null,
        created_at: "2026-07-02T11:00:00Z",
        updated_at: "2026-07-02T11:00:00Z",
      });
    }

    if (path === "/api/teacher/catalog/nodes" && method === "POST") {
      return jsonResponse(catalogDetail("point-ch13-iodide"));
    }

    const catalogMediaBindingMatch = path.match(/^\/api\/teacher\/catalog\/nodes\/([^/]+)\/media-bindings$/);
    if (catalogMediaBindingMatch && method === "POST") {
      return jsonResponse({
        binding_id: "binding-uploaded-iodide",
        detail: catalogDetail(decodeURIComponent(catalogMediaBindingMatch[1])),
      });
    }

    const catalogMediaBindingActionMatch = path.match(/^\/api\/teacher\/catalog\/media-bindings\/([^/]+)\/([^/]+)$/);
    if (catalogMediaBindingActionMatch && method === "POST") {
      return jsonResponse(catalogDetail("point-ch13-bleach"));
    }

    const catalogNodeStatusMatch = path.match(/^\/api\/teacher\/catalog\/nodes\/([^/]+)\/status$/);
    if (catalogNodeStatusMatch && method === "POST") {
      return jsonResponse(catalogDetail(decodeURIComponent(catalogNodeStatusMatch[1])));
    }

    const catalogPointContentMatch = path.match(/^\/api\/teacher\/catalog\/nodes\/([^/]+)\/point-content$/);
    if (catalogPointContentMatch && method === "PUT") {
      return jsonResponse(catalogDetail(decodeURIComponent(catalogPointContentMatch[1])));
    }

    const catalogNodeMatch = path.match(/^\/api\/teacher\/catalog\/nodes\/([^/]+)$/);
    if (catalogNodeMatch) {
      return jsonResponse(catalogDetail(decodeURIComponent(catalogNodeMatch[1])));
    }

    if (path === "/api/teacher/question-banks/drafts") {
      const visibleDrafts = questionDrafts.filter((draft) => draft.status === "draft");
      return jsonResponse({ items: visibleDrafts, total: visibleDrafts.length });
    }

    if (path === "/api/teacher/question-banks/questions") {
      const visibleQuestions = questionBankQuestions.filter((question) => question.status === "published");
      return jsonResponse({ items: visibleQuestions, total: visibleQuestions.length });
    }

    const revokeQuestionMatch = path.match(/^\/api\/teacher\/question-banks\/questions\/([^/]+)\/revoke-to-draft$/);
    if (revokeQuestionMatch && method === "POST") {
      const questionId = decodeURIComponent(revokeQuestionMatch[1]);
      const question = questionBankQuestions.find((item) => item.id === questionId);
      if (!question || question.status !== "published") return jsonResponse({ detail: "Only published questions can be revoked to draft" }, 400);
      questionBankQuestions = questionBankQuestions.map((item) => (item.id === questionId ? { ...item, status: "draft" } : item));
      const questionMetadata =
        "metadata" in question && question.metadata && typeof question.metadata === "object" ? (question.metadata as Record<string, unknown>) : {};
      const draft = {
        ...cloneJson(draftQuestion),
        id: `draft-from-${questionId}`,
        status: "draft",
        payload: {
          ...cloneJson(question),
          metadata: { ...questionMetadata, revoked_from_question_id: questionId },
          status: "draft",
        },
      };
      questionDrafts = [draft, ...questionDrafts];
      return jsonResponse(draft);
    }

    if (path === "/api/teacher/question-banks/legacy-point-generate" && method === "POST") {
      return jsonResponse({
        generation_id: "gen-ch13-2",
        mode: "legacy_point",
        warning: null,
        source_refs: [{ point_node_id: "point-ch13-bleach", chapter_id: "CH13" }],
        evidence_package: { source: "catalog_point_content" },
        drafts: [draftQuestion],
      });
    }

    const publishDraftMatch = path.match(/^\/api\/teacher\/question-banks\/drafts\/([^/]+)\/publish$/);
    if (publishDraftMatch && method === "POST") {
      const draftId = decodeURIComponent(publishDraftMatch[1]);
      const draft = questionDrafts.find((item) => item.id === draftId);
      if (!draft || draft.status !== "draft") return jsonResponse({ detail: "Only draft questions can be published" }, 400);
      const payload = (draft.payload || {}) as Record<string, unknown> & { metadata?: { revoked_from_question_id?: unknown } };
      const revokedFromQuestionId = String(payload.metadata?.revoked_from_question_id || "");
      const question = {
        ...cloneJson(publishedQuestion),
        ...payload,
        id: revokedFromQuestionId || `question-from-${draftId}`,
        status: "published",
      };
      questionBankQuestions = revokedFromQuestionId
        ? questionBankQuestions.map((item) => (item.id === revokedFromQuestionId ? question : item))
        : [question, ...questionBankQuestions];
      const publishedDraftPayload = { ...cloneJson(draftQuestion.payload), ...payload, status: "published" };
      questionDrafts = questionDrafts.map((item) => (item.id === draftId ? { ...item, status: "published", payload: publishedDraftPayload } : item));
      return jsonResponse(question);
    }

    const draftUpdateMatch = path.match(/^\/api\/teacher\/question-banks\/drafts\/([^/]+)$/);
    if (draftUpdateMatch && method === "PATCH") {
      const draftId = decodeURIComponent(draftUpdateMatch[1]);
      const body = JSON.parse(String(init?.body || "{}"));
      const existing = questionDrafts.find((draft) => draft.id === draftId);
      if (!existing) return jsonResponse({ detail: "Draft not found" }, 404);
      const updated = { ...existing, payload: body.payload, status: body.status || "draft" };
      questionDrafts = questionDrafts.map((draft) => (draft.id === draftId ? updated : draft));
      return jsonResponse(updated);
    }

    const draftRejectMatch = path.match(/^\/api\/teacher\/question-banks\/drafts\/([^/]+)\/reject$/);
    if (draftRejectMatch && method === "POST") {
      const draftId = decodeURIComponent(draftRejectMatch[1]);
      const existing = questionDrafts.find((draft) => draft.id === draftId);
      if (!existing) return jsonResponse({ detail: "Draft not found" }, 404);
      const updated = { ...existing, status: "rejected" };
      questionDrafts = questionDrafts.map((draft) => (draft.id === draftId ? updated : draft));
      return jsonResponse(updated);
    }

    if (path === "/api/teacher/classes" && method === "POST") {
      return jsonResponse({
        id: "class-new",
        class_name: "无机化学二班",
        description: "新增测试班级",
        status: "active",
        student_count: 0,
      });
    }

    const classMatch = path.match(/^\/api\/teacher\/classes\/([^/]+)$/);
    if (classMatch && method === "DELETE") {
      const classId = decodeURIComponent(classMatch[1]);
      const existing = classes.find((item) => item.id === classId) || classes[0];
      return jsonResponse({
        ...existing,
        status: "archived",
      });
    }

    if (path === "/api/teacher/classes") {
      return jsonResponse(classes);
    }

    if (path === "/api/teacher/classes/class-1/smart-assessment-strategy") {
      if (method === "PUT") {
        const body = JSON.parse(String(init?.body || "{}"));
        return jsonResponse({
          strategy: body,
          inherited_strategy: smartAssessmentStrategy,
          source: "class",
          has_override: true,
          can_edit: true,
        });
      }
      if (method === "DELETE") {
        return jsonResponse({
          strategy: smartAssessmentStrategy,
          inherited_strategy: smartAssessmentStrategy,
          source: "system_default",
          has_override: false,
          can_edit: true,
        });
      }
      return jsonResponse({
        strategy: smartAssessmentStrategy,
        inherited_strategy: smartAssessmentStrategy,
        source: "system_default",
        has_override: false,
        can_edit: true,
      });
    }

    if (/^\/api\/teacher\/classes\/[^/]+\/registration-settings$/.test(path)) {
      if (method === "PUT") {
        const body = JSON.parse(String(init?.body || "{}"));
        return jsonResponse({
          mode: body.mode || "roster_only",
          default_password_policy: body.default_password_policy || "student_id_name_activation",
          default_password_mode: body.default_password_mode || "student_id",
          has_default_password: Boolean(body.default_password),
          source: "class",
        });
      }
      return jsonResponse({
        mode: "roster_only",
        default_password_policy: "student_id_name_activation",
        default_password_mode: "student_id",
        has_default_password: false,
        source: "system_default",
      });
    }

    if (path === "/api/teacher/classes/class-1/roster/import" && method === "POST") {
      return jsonResponse({
        import_id: "import-1",
        mode: "upsert",
        total_rows: 2,
        valid_rows: 2,
        invalid_rows: 0,
        disabled_missing: 0,
      });
    }

    if (path === "/api/teacher/classes/class-1/students" && method === "POST") {
      return jsonResponse({
        id: "class-student-new",
        class_id: "class-1",
        student_id: "2026003",
        student_name: "王五",
        status: "pending",
        activation_mode: "default_password",
        activated: false,
      });
    }

    const rosterStudentMatch = path.match(/^\/api\/teacher\/classes\/class-1\/students\/([^/]+)$/);
    if (rosterStudentMatch && method === "PATCH") {
      const student = students.find((item) => item.student_id === decodeURIComponent(rosterStudentMatch[1])) || students[0];
      return jsonResponse({
        ...student,
        ...JSON.parse(String(init?.body || "{}")),
      });
    }

    if (rosterStudentMatch && method === "DELETE") {
      const student = students.find((item) => item.student_id === decodeURIComponent(rosterStudentMatch[1])) || students[0];
      return jsonResponse(student);
    }

    const resetStudentPasswordMatch = path.match(/^\/api\/teacher\/classes\/class-1\/students\/([^/]+)\/reset-password$/);
    if (resetStudentPasswordMatch && method === "POST") {
      return jsonResponse({ ok: true });
    }

    if (path === "/api/teacher/classes/class-1/students") {
      return jsonResponse(students);
    }

    if (path === "/api/teacher/analytics/classes/class-1/dashboard") {
      return jsonResponse(analyticsDashboard());
    }

    const studentReportMatch = path.match(/^\/api\/teacher\/analytics\/classes\/class-1\/students\/([^/]+)$/);
    if (studentReportMatch) {
      return jsonResponse(studentLearningReport(decodeURIComponent(studentReportMatch[1])));
    }

    if (path === "/api/teacher/assessment-report-prompts") {
      if (method === "PUT") {
        return jsonResponse({
          settings: JSON.parse(String(init?.body || "{}")),
          inherited_settings: null,
          source: "global",
          has_override: true,
          supported_variables: ["student_name", "score", "wrong_questions", "chapter_title"],
          can_edit: true,
        });
      }

      if (method === "DELETE") {
        return jsonResponse({
          settings: {
            summary_prompt: "默认总结 {{student_name}} 的学习表现。",
            mistake_prompt: "默认讲解 {{wrong_questions}}。",
          },
          inherited_settings: null,
          source: "global",
          has_override: false,
          supported_variables: ["student_name", "score", "wrong_questions", "chapter_title"],
          can_edit: true,
        });
      }

      return jsonResponse({
        settings: {
          summary_prompt: "请面向教师总结 {{student_name}} 在 {{chapter_title}} 的学习表现。",
          mistake_prompt: "请解释 {{student_name}} 的错题原因：{{wrong_questions}}。",
        },
        inherited_settings: null,
        source: "global",
        has_override: false,
        supported_variables: ["student_name", "score", "wrong_questions", "chapter_title"],
        can_edit: true,
      });
    }

    if (path === "/api/teacher/classes/class-1/students/2026001/assessment-reports") {
      return jsonResponse({ reports: [assessmentReportSummary] });
    }

    if (path === "/api/teacher/classes/class-1/students/2026001/assessment-reports/report-ch13-1") {
      return jsonResponse(assessmentReportDetail);
    }

    if (path === "/api/teacher/classes/class-1/students/2026002/assessment-reports") {
      return jsonResponse({ reports: [] });
    }

    return jsonResponse({ detail: `Unhandled test request: ${method} ${path}` }, 404);
  });
}

describe("LegacyTeacherApp", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    globalThis.localStorage?.clear();
    setAuthToken("teacher-token");
  });

  afterEach(() => {
    setAuthToken("");
    cleanup();
    vi.unstubAllGlobals();
  });

  const renderClassPage = async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/classes");
    render(<LegacyTeacherApp />);

    expect(await screen.findByTestId("teacher-page-classes")).toBeTruthy();
    expect(await screen.findByText("张三")).toBeTruthy();
    return fetchMock;
  };

  const clickFirstRosterAction = async (name: string) => {
    let actionButton: HTMLElement | null = null;
    await waitFor(() => {
      const rosterTable = screen.getByLabelText("学生名单");
      const buttons = within(rosterTable).getAllByRole("button", { name });
      expect(buttons.length).toBeGreaterThan(0);
      actionButton = buttons[0] as HTMLElement;
    });
    if (!actionButton) throw new Error(`Roster action not found: ${name}`);
    fireEvent.click(actionButton);
  };

  it("renders the focused teacher navigation and catalog-backed CH13 point editor", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<LegacyTeacherApp />);

    const breadcrumb = await screen.findByRole("navigation", { name: "当前位置" });
    expect(within(breadcrumb).getByText("后台工作台")).toBeTruthy();
    expect(within(breadcrumb).getByText("实验管理")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "实验管理" })).toBeNull();
    const userMenuButton = screen.getByRole("button", { name: /王老师/ });
    fireEvent.click(userMenuButton);
    const userMenu = await screen.findByRole("menu");
    expect(within(userMenu).getAllByRole("menuitem").map((item) => item.textContent?.trim())).toEqual(["登出"]);
    expect(screen.queryByRole("button", { name: "退出登录" })).toBeNull();

    const nav = screen.getByRole("navigation", { name: "后台导航" });
    const navLabels = within(nav)
      .getAllByRole("button")
      .map((button) => String(button.textContent).trim());
    expect(navLabels).toEqual(["实验管理", "班级管理", "AI 出题", "组卷管理", "学情分析", "AI 配置", "设置"]);
    expect(within(nav).queryByRole("button", { name: "视频资源" })).toBeNull();
    expect(within(nav).queryByRole("button", { name: "题库资源" })).toBeNull();
    expect(within(nav).getByRole("button", { name: "班级管理" })).toBeTruthy();
    expect(within(nav).queryByRole("button", { name: "评价体系" })).toBeNull();

    expect(await screen.findByRole("heading", { name: "章节目录与点位" })).toBeTruthy();
    const tree = await screen.findByRole("tree", { name: "章节目录与点位" });
    expect((await screen.findAllByRole("treeitem")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "新增点位" })).toBeNull();
    expect((await screen.findAllByText("CH13 卤族元素")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("氯的氧化性")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("溴碘置换")).length).toBeGreaterThan(0);
    expect((await screen.findAllByText("氯水漂白性实验")).length).toBeGreaterThan(0);
    expect(await screen.findByText("碘离子检验")).toBeTruthy();
    expect(within(tree).queryByText("3 点")).toBeNull();
    expect(within(tree).queryByText("5 题")).toBeNull();
    expect(await screen.findByDisplayValue("新制氯水中的 HClO 具有强氧化性。")).toBeTruthy();
    expect(screen.queryByLabelText("摘要")).toBeNull();
    expect(screen.queryByLabelText("教师备注")).toBeNull();
    expect(screen.queryByLabelText("点位标题")).toBeNull();
    expect(screen.queryByRole("button", { name: "发布" })).toBeNull();
    expect(screen.queryByRole("button", { name: "取消发布" })).toBeNull();
    expect(screen.queryByText("点位资料")).toBeNull();
    expect(screen.queryByText("目录信息")).toBeNull();
    const existingVideoRegion = await screen.findByRole("region", { name: "视频" });
    expect(within(existingVideoRegion).queryByText("氯水漂白性实验视频")).toBeNull();
    expect(within(existingVideoRegion).getByText("bleach-demo.mp4")).toBeTruthy();
    expect(within(existingVideoRegion).getByRole("button", { name: "移除" })).toBeTruthy();
    expect(within(existingVideoRegion).getByRole("button", { name: "上传" })).toBeTruthy();
    expect(screen.queryByText("1000 KB")).toBeNull();
    expect(screen.queryByText("1:36")).toBeNull();
    expect(screen.queryByLabelText("视频标题")).toBeNull();
    expect(screen.getByRole("button", { name: "学生端展示说明" })).toBeTruthy();
    expect(screen.getByText("关闭后，该节点及下级不会展示给学生。")).toBeTruthy();
    const visibilitySwitch = screen.getByRole("switch", { name: "学生端可见" });
    expect(visibilitySwitch.getAttribute("aria-checked")).toBe("true");
    fireEvent.click(visibilitySwitch);
    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/nodes/point-ch13-bleach/status"));
    const statusCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/catalog/nodes/point-ch13-bleach/status");
    expect(statusCall).toBeTruthy();
    expect(JSON.parse(String(statusCall?.[1]?.body))).toEqual({ action: "unpublish", include_subtree: true });

    const pointItem = within(tree)
      .getAllByRole("treeitem")
      .find((item) => item.getAttribute("aria-expanded") === null && item.textContent?.includes("碘离子检验"));
    expect(pointItem).toBeTruthy();
    fireEvent.contextMenu(pointItem!);
    const pointMenu = await screen.findByRole("menu");
    expect(within(pointMenu).getByRole("menuitem", { name: "删除点位" })).toBeTruthy();
    expect(within(pointMenu).queryByRole("menuitem", { name: "新增目录" })).toBeNull();
    expect(within(pointMenu).queryByText("碘离子检验")).toBeNull();
    fireEvent.click(within(pointMenu).getByRole("menuitem", { name: "删除点位" }));
    const pointDeleteDialog = await screen.findByRole("dialog", { name: "删除点位" });
    expect(within(pointDeleteDialog).getByText("碘离子检验")).toBeTruthy();
    fireEvent.click(within(pointDeleteDialog).getByRole("button", { name: "取消" }));

    const displacementItem = within(tree)
      .getAllByRole("treeitem")
      .find((item) => item.getAttribute("aria-expanded") === "true" && item.textContent?.includes("溴碘置换"));
    expect(displacementItem).toBeTruthy();
    fireEvent.contextMenu(displacementItem!);
    const directoryMenu = await screen.findByRole("menu");
    expect(within(directoryMenu).getByRole("menuitem", { name: "新增目录" })).toBeTruthy();
    expect(within(directoryMenu).getByRole("menuitem", { name: "新增点位" })).toBeTruthy();
    expect(within(directoryMenu).getByRole("menuitem", { name: "删除目录" })).toBeTruthy();
    expect(within(directoryMenu).queryByText("溴碘置换")).toBeNull();
    fireEvent.click(within(directoryMenu).getByRole("menuitem", { name: "新增点位" }));
    const dialog = await screen.findByRole("dialog", { name: "新增点位" });
    expect(within(dialog).getByText("位置：溴碘置换")).toBeTruthy();
    fireEvent.change(within(dialog).getByLabelText("名称"), { target: { value: "KI 淀粉验证" } });
    expect(within(dialog).queryByLabelText("摘要")).toBeNull();
    fireEvent.click(within(dialog).getByRole("button", { name: "创建点位" }));
    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/nodes"));
    const createCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/catalog/nodes");
    expect(createCall).toBeTruthy();
    expect(JSON.parse(String(createCall?.[1]?.body))).toMatchObject({
      chapter_id: "CH13",
      parent_id: "dir-ch13-displacement",
      node_kind: "point",
      title: "KI 淀粉验证",
    });
    expect(JSON.parse(String(createCall?.[1]?.body))).not.toHaveProperty("summary");

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/catalog?chapter_id=CH13"));
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("lets a teacher manage settings from the settings page", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<LegacyTeacherApp />);

    await screen.findByRole("navigation", { name: "当前位置" });
    fireEvent.click(screen.getByTestId("teacher-nav-settings"));

    const settingsPage = await screen.findByTestId("teacher-page-settings");
    const settings = await within(settingsPage).findByTestId("teacher-settings-page");
    expect(within(settings).queryByText("当前账号")).toBeNull();
    expect(within(settings).queryByText("账号类型")).toBeNull();
    expect(within(settings).getByText("修改密码")).toBeTruthy();
    const accountManagement = await within(settings).findByTestId("teacher-account-management");
    expect(within(accountManagement).getByText("账号管理")).toBeTruthy();
    expect(within(accountManagement).queryByText("添加教师账号")).toBeNull();
    expect(await within(accountManagement).findByText("王老师")).toBeTruthy();
    expect(within(accountManagement).getByText("teacher2")).toBeTruthy();
    expect(within(accountManagement).getByText("本人")).toBeTruthy();
    expect(within(accountManagement).getByText("已停用")).toBeTruthy();
    expect(screen.queryByRole("dialog", { name: "设置" })).toBeNull();

    fireEvent.change(within(settings).getByLabelText("当前密码"), { target: { value: "old-password" } });
    fireEvent.change(within(settings).getByLabelText("新密码"), { target: { value: "new-password-123" } });
    fireEvent.change(within(settings).getByLabelText("确认新密码"), { target: { value: "new-password-123" } });
    fireEvent.click(within(settings).getByRole("button", { name: "保存密码" }));

    await waitFor(() => expect(fetchMock.mock.calls.some((call) => requestUrl(call[0]).pathname === "/api/auth/password")).toBe(true));
    expect(within(settings).queryByText("个人密码已更新。")).toBeNull();
    const passwordRequest = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/auth/password");
    expect(passwordRequest).toBeTruthy();
    expect(passwordRequest?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(passwordRequest?.[1]?.body))).toEqual({
      current_password: "old-password",
      new_password: "new-password-123",
    });

    fireEvent.click(within(accountManagement).getByRole("button", { name: "启用" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/accounts/teachers/teacher-2" && String(call[1]?.method || "GET").toUpperCase() === "PATCH",
        ),
      ).toBe(true),
    );
    expect(within(accountManagement).queryByText("李老师已启用。")).toBeNull();
    const statusRequest = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/accounts/teachers/teacher-2" && String(call[1]?.method || "GET").toUpperCase() === "PATCH",
    );
    expect(statusRequest).toBeTruthy();
    expect(JSON.parse(String(statusRequest?.[1]?.body))).toEqual({ status: "active" });

    fireEvent.change(within(settings).getByLabelText("后台账号"), { target: { value: "teacher3" } });
    fireEvent.change(within(settings).getByLabelText("显示姓名"), { target: { value: "陈老师" } });
    fireEvent.change(within(settings).getByLabelText("初始密码"), { target: { value: "teacher-pass-123" } });
    fireEvent.click(within(settings).getByRole("button", { name: "新增账号" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/accounts/teachers" && String(call[1]?.method || "GET").toUpperCase() === "POST",
        ),
      ).toBe(true),
    );
    expect(within(settings).queryByText("已新增后台账号。")).toBeNull();
    const teacherRequest = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/accounts/teachers" && String(call[1]?.method || "GET").toUpperCase() === "POST",
    );
    expect(teacherRequest).toBeTruthy();
    expect(teacherRequest?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(teacherRequest?.[1]?.body))).toEqual({
      username: "teacher3",
      display_name: "陈老师",
      password: "teacher-pass-123",
      must_change_password: true,
    });
  });

  it("lets a teacher configure smart assessment paper assembly", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<LegacyTeacherApp />);

    await screen.findByRole("navigation", { name: "当前位置" });
    fireEvent.click(screen.getByTestId("teacher-nav-paper"));

    const page = await screen.findByTestId("teacher-page-paper");
    const workbench = await within(page).findByTestId("teacher-paper-management");
    expect(within(workbench).getByText("智能组卷策略")).toBeTruthy();
    expect(await within(workbench).findByText("当前班级继承默认策略")).toBeTruthy();
    expect(within(workbench).getByRole("img", { name: "抽题权重公式" })).toBeTruthy();
    expect(within(workbench).getByText("M=掌握度；T=薄弱倾向；B=加权上限；C=曲线。题量控制出题数；单实验最多题数避免试卷集中到同一实验。")).toBeTruthy();
    expect(within(workbench).getByText("薄弱权重曲线")).toBeTruthy();
    expect(within(workbench).getByText("7.3 票")).toBeTruthy();
    expect(within(workbench).queryByText("当前班级预估")).toBeNull();
    expect(within(workbench).queryByText("氯水漂白性实验")).toBeNull();
    expect(within(workbench).queryByText("未测目标 2 题")).toBeNull();
    expect(within(workbench).queryByText("启用")).toBeNull();
    expect(within(workbench).queryByText("未测点位比例")).toBeNull();

    fireEvent.click(within(within(workbench).getByLabelText("每次题量选项")).getByRole("button", { name: "15题" }));
    fireEvent.click(within(workbench).getByRole("button", { name: "保存策略" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/smart-assessment-strategy" &&
            String(call[1]?.method || "GET").toUpperCase() === "PUT",
        ),
      ).toBe(true),
    );
    expect(within(page).queryByText("智能组卷策略已保存。")).toBeNull();
    const saveRequest = fetchMock.mock.calls.find(
      (call) =>
        requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/smart-assessment-strategy" &&
        String(call[1]?.method || "GET").toUpperCase() === "PUT",
    );
    expect(saveRequest).toBeTruthy();
    expect(JSON.parse(String(saveRequest?.[1]?.body))).toMatchObject({
      enabled: true,
      question_count: 15,
      untested_ratio_percent: 20,
      max_questions_per_experiment: 2,
    });
    expect(requestPaths(fetchMock)).not.toContain("/api/teacher/classes/class-1/smart-assessment-preview");
  });

  it("configures the DeepSeek model used by AI generation features", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<LegacyTeacherApp />);

    await screen.findByRole("navigation", { name: "当前位置" });
    fireEvent.click(screen.getByTestId("teacher-nav-aiConfig"));

    const settingsPage = await screen.findByTestId("teacher-page-ai-config");
    fireEvent.click(within(settingsPage).getByRole("tab", { name: "大语言模型配置" }));
    const sidebar = await within(settingsPage).findByTestId("teacher-ai-config-model");
    expect(screen.queryByRole("dialog", { name: "设置" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "AI 模型配置" })).toBeNull();
    expect(await within(sidebar).findByDisplayValue("https://api.deepseek.com")).toBeTruthy();
    expect(within(sidebar).getByDisplayValue("deepseek-v4-flash")).toBeTruthy();
    expect(within(sidebar).getByLabelText("API 密钥").getAttribute("placeholder")).toBe("");
    expect(within(sidebar).queryByText("模型服务")).toBeNull();
    expect(within(sidebar).queryByText("连接检测间隔")).toBeNull();
    expect(within(sidebar).queryByText("启用范围")).toBeNull();
    expect(within(sidebar).queryByText("上次检测")).toBeNull();
    expect(within(sidebar).queryByText("近期调用")).toBeNull();
    expect(within(sidebar).queryByRole("button", { name: "使用默认值" })).toBeNull();

    fireEvent.change(within(sidebar).getByLabelText("API 密钥"), { target: { value: "sk-test-from-ui" } });
    fireEvent.click(within(sidebar).getByRole("button", { name: "保存配置" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/ai-configuration" && String(call[1]?.method || "GET").toUpperCase() === "PUT",
        ),
      ).toBe(true),
    );
    expect(within(sidebar).queryByText("AI 模型配置已保存。")).toBeNull();
    const updateCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/ai-configuration" && String(call[1]?.method || "GET").toUpperCase() === "PUT",
    );
    expect(updateCall).toBeTruthy();
    expect(JSON.parse(String(updateCall?.[1]?.body))).toMatchObject({
      provider: "openai",
      base_url: "https://api.deepseek.com",
      model: "deepseek-v4-flash",
      api_key: "sk-test-from-ui",
      chat_provider: {
        provider: "openai",
        base_url: "https://api.deepseek.com",
        model: "deepseek-v4-flash",
        api_key: "sk-test-from-ui",
      },
    });
    expect(JSON.parse(String(updateCall?.[1]?.body))).not.toHaveProperty("enabled_features");
    expect(JSON.parse(String(updateCall?.[1]?.body))).not.toHaveProperty("connection_check_interval_minutes");
    await waitFor(() => expect(within(sidebar).getByLabelText("API 密钥").getAttribute("placeholder")).toBe("****"));
  });

  it("uploads and binds a video from the catalog point editor", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/experiments");

    const { container } = render(<LegacyTeacherApp />);

    const tree = await screen.findByRole("tree", { name: "章节目录与点位" });
    const iodideItem = await within(tree).findByRole("treeitem", { name: "碘离子检验" });
    fireEvent.click(iodideItem);

    expect(await screen.findByDisplayValue("I- 被氧化后与淀粉形成蓝色络合物。")).toBeTruthy();
    const videoRegion = await screen.findByRole("region", { name: "视频" });
    expect(within(videoRegion).getByText("暂无视频")).toBeTruthy();
    expect(within(videoRegion).queryByLabelText("视频标题")).toBeNull();

    const fileInput = container.querySelector(".legacy-point-video-field input[type='file']") as HTMLInputElement | null;
    expect(fileInput).toBeTruthy();
    const file = new File(["demo-content"], "iodide-demo.mp4", { type: "video/mp4" });
    fireEvent.change(fileInput!, { target: { files: [file] } });

    expect(await within(videoRegion).findByText("iodide-demo.mp4")).toBeTruthy();
    expect(within(videoRegion).getByText("待保存")).toBeTruthy();
    expect(requestPaths(fetchMock)).not.toContain("/api/teacher/media/assets");
    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/media/assets"));
    const uploadCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/media/assets");
    expect(uploadCall).toBeTruthy();
    expect(uploadCall?.[1]?.method).toBe("POST");
    expect(uploadCall?.[1]?.body).toBeInstanceOf(FormData);
    const formData = uploadCall?.[1]?.body as FormData;
    expect(formData.get("title")).toBe("碘离子检验");
    expect((formData.get("file") as File).name).toBe("iodide-demo.mp4");

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/nodes/point-ch13-iodide/media-bindings"));
    const bindingCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/catalog/nodes/point-ch13-iodide/media-bindings");
    expect(bindingCall).toBeTruthy();
    expect(JSON.parse(String(bindingCall?.[1]?.body))).toEqual({
      media_asset_id: "media-uploaded-iodide",
      title: "碘离子检验",
      metadata: { source: "teacher_point_editor" },
    });
    expect(screen.queryByText("已保存节点资料。")).toBeNull();
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("stages removing a point video until the catalog editor is saved", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/experiments");

    render(<LegacyTeacherApp />);

    const videoRegion = await screen.findByRole("region", { name: "视频" });
    expect(within(videoRegion).getByText("bleach-demo.mp4")).toBeTruthy();
    fireEvent.click(within(videoRegion).getByRole("button", { name: "移除" }));

    expect(within(videoRegion).getByText("暂无视频")).toBeTruthy();
    expect(within(videoRegion).getByText("待保存")).toBeTruthy();
    expect(requestPaths(fetchMock)).not.toContain("/api/teacher/catalog/media-bindings/binding-ch13-bleach/delete");

    fireEvent.click(screen.getByRole("button", { name: "保存" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/media-bindings/binding-ch13-bleach/delete"));
    expect(screen.queryByText("已保存节点资料。")).toBeNull();
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("archives points and directories from the catalog tree context menu", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/experiments");

    render(<LegacyTeacherApp />);

    const tree = await screen.findByRole("tree", { name: "章节目录与点位" });
    const iodideItem = await within(tree).findByRole("treeitem", { name: "碘离子检验" });
    fireEvent.contextMenu(iodideItem);
    fireEvent.click(within(await screen.findByRole("menu")).getByRole("menuitem", { name: "删除点位" }));
    const pointDialog = await screen.findByRole("dialog", { name: "删除点位" });
    fireEvent.click(within(pointDialog).getByRole("button", { name: "确认删除" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/nodes/point-ch13-iodide/status"));
    const pointDeleteCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/catalog/nodes/point-ch13-iodide/status");
    expect(pointDeleteCall).toBeTruthy();
    expect(JSON.parse(String(pointDeleteCall?.[1]?.body))).toEqual({ action: "archive", include_subtree: true });
    expect(screen.queryByText("已删除点位。")).toBeNull();

    const refreshedTree = await screen.findByRole("tree", { name: "章节目录与点位" });
    const displacementItem = await within(refreshedTree).findByRole("treeitem", { name: "溴碘置换" });
    fireEvent.contextMenu(displacementItem);
    fireEvent.click(within(await screen.findByRole("menu")).getByRole("menuitem", { name: "删除目录" }));
    const directoryDialog = await screen.findByRole("dialog", { name: "删除目录" });
    expect(within(directoryDialog).getByText("删除目录会同时删除它下面的目录和点位。相关视频、题目和历史引用不会被物理清除。")).toBeTruthy();
    fireEvent.click(within(directoryDialog).getByRole("button", { name: "确认删除" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/catalog/nodes/dir-ch13-displacement/status"));
    const directoryDeleteCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/catalog/nodes/dir-ch13-displacement/status");
    expect(directoryDeleteCall).toBeTruthy();
    expect(JSON.parse(String(directoryDeleteCall?.[1]?.body))).toEqual({ action: "archive", include_subtree: true });
    expect(screen.queryByText("已删除目录及其下级内容。")).toBeNull();
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("generates and reviews point-sourced drafts through legacy-point-generate only", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/questions");

    render(<LegacyTeacherApp />);

    expect(await screen.findByRole("heading", { name: "命题工作区" })).toBeTruthy();
    expect(screen.queryByLabelText("AI 出题概览")).toBeNull();
    expect(await screen.findByText("新制氯水中的 HClO 具有强氧化性。")).toBeTruthy();
    expect(await screen.findByText("氯水使湿润有色布条褪色，最关键的微粒是什么？")).toBeTruthy();
    expect(screen.getByText("正式题库")).toBeTruthy();
    expect(await screen.findByText("为什么干燥有色布条放入氯气中不明显褪色？")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "退回修改" })).toBeNull();
    expect(screen.queryByRole("button", { name: "撤销选中正式题" })).toBeNull();
    expect(screen.queryByRole("button", { name: "入库选中待审题" })).toBeNull();
    const bankPanel = screen.getByRole("region", { name: "正式题库" });
    expect(within(bankPanel).getByText("缺少水生成 HClO")).toBeTruthy();
    expect(within(bankPanel).getByText("氯气需要与水反应生成 HClO 后才表现出明显漂白性。")).toBeTruthy();
    expect(within(bankPanel).getByText("正式题库完整展示题 11")).toBeTruthy();

    const reviewPanel = screen.getByRole("region", { name: "待审队列" });
    const initialDraftCard = within(reviewPanel).getByRole("button", { name: /氯水使湿润有色布条褪色/ });
    fireEvent.click(within(initialDraftCard).getByRole("button", { name: "删除" }));
    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/drafts/draft-ch13-1/reject"));
    await waitFor(() => expect(within(reviewPanel).queryByRole("button", { name: /氯水使湿润有色布条褪色/ })).toBeNull());

    const initialQuestionCard = within(bankPanel).getByRole("button", { name: /为什么干燥有色布条放入氯气中不明显褪色/ });
    fireEvent.click(within(initialQuestionCard).getByRole("button", { name: "撤销到待审" }));
    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/questions/question-ch13-1/revoke-to-draft"));

    const revokedDraftCard = await within(reviewPanel).findByRole("button", { name: /为什么干燥有色布条放入氯气中不明显褪色/ });
    fireEvent.click(within(revokedDraftCard).getByRole("button", { name: "修改" }));
    fireEvent.change(screen.getByLabelText("题干"), { target: { value: "修改后的氯水漂白性题干？" } });
    fireEvent.change(screen.getByLabelText("答案"), { target: { value: "B" } });
    fireEvent.click(screen.getByRole("button", { name: "保存修改" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/drafts/draft-from-question-ch13-1"));
    const updateDraftCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/question-banks/drafts/draft-from-question-ch13-1" && String(call[1]?.method || "GET").toUpperCase() === "PATCH",
    );
    expect(updateDraftCall).toBeTruthy();
    expect(JSON.parse(String(updateDraftCall?.[1]?.body))).toMatchObject({
      status: "draft",
      payload: {
        stem: "修改后的氯水漂白性题干？",
        answer: { value: "B" },
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "生成待审题" }));

    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/legacy-point-generate"));
    expect(screen.queryByText("已生成 1 条待审题，来源为点位三段式资料。")).toBeNull();

    const generationCall = fetchMock.mock.calls.find((call) => requestUrl(call[0]).pathname === "/api/teacher/question-banks/legacy-point-generate");
    expect(generationCall).toBeTruthy();
    expect(generationCall?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(generationCall?.[1]?.body))).toMatchObject({
      experiment_id: "exp-ch13-bleach",
      chapter_ids: ["CH13"],
      target_point_node_ids: ["point-ch13-bleach"],
      question_types: ["single_choice"],
      count: 1,
    });

    const updatedDraftCard = await within(reviewPanel).findByRole("button", { name: /修改后的氯水漂白性题干/ });
    fireEvent.click(within(updatedDraftCard).getByRole("button", { name: "入库" }));
    await waitFor(() => expect(requestPaths(fetchMock)).toContain("/api/teacher/question-banks/drafts/draft-from-question-ch13-1/publish"));
    expect(screen.queryByText("教师审核通过，题目已入库。")).toBeNull();
    expect(await screen.findByText("修改后的氯水漂白性题干？")).toBeTruthy();

    const paths = requestPaths(fetchMock);
    expect(paths).toContain("/api/teacher/question-banks/drafts?point_node_id=point-ch13-bleach&canonical_point_id=canon-bleach");
    expect(paths.some((path) => path.startsWith("/api/teacher/question-banks/questions?") && path.includes("status_filter=published"))).toBe(true);
    expect(paths).toContain("/api/teacher/question-banks/questions/question-ch13-1/revoke-to-draft");
    expect(paths).toContain("/api/teacher/question-banks/drafts/draft-ch13-1/reject");
    expect(paths).toContain("/api/teacher/question-banks/drafts/draft-from-question-ch13-1/publish");
    expect(paths).not.toContain("/api/teacher/question-banks/drafts/draft-ch13-1/publish");
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("manages classes and roster students from the restored class page", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/classes");

    render(<LegacyTeacherApp />);

    expect(await screen.findByTestId("teacher-page-classes")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "班级管理" })).toBeNull();
    expect(screen.queryByLabelText("班级概览")).toBeNull();
    expect((await screen.findAllByText("无机化学一班")).length).toBeGreaterThan(0);
    expect(await screen.findByText("张三")).toBeTruthy();
    expect(screen.getByText("李四")).toBeTruthy();
    expect((screen.getByLabelText("当前班级") as HTMLSelectElement).value).toBe("class-1");
    expect(screen.queryByRole("heading", { name: "班级" })).toBeNull();
    expect(screen.queryByLabelText("班级列表")).toBeNull();
    expect(screen.getByRole("button", { name: "删除班级" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "学生名单" })).toBeTruthy();
    expect(screen.getByText("无机化学一班 · 初始密码：使用学号")).toBeTruthy();
    expect(screen.queryByText("登录方式")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "导入名单" }));
    const importDialog = await screen.findByRole("dialog", { name: "导入学生名单" });
    const rosterFileInput = importDialog.querySelector('input[type="file"]');
    expect(rosterFileInput).toBeTruthy();
    fireEvent.change(rosterFileInput as HTMLInputElement, {
      target: { files: [new File(["student_id,student_name\n26320004,赵六"], "students.csv", { type: "text/csv" })] },
    });
    expect(within(importDialog).getByText("students.csv")).toBeTruthy();
    fireEvent.click(within(importDialog).getByRole("button", { name: "导入名单" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/roster/import" && String(call[1]?.method || "GET").toUpperCase() === "POST",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("导入完成：2 条有效。")).toBeNull();
    const settingsCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/registration-settings" && String(call[1]?.method || "GET").toUpperCase() === "PUT",
    );
    expect(settingsCall).toBeTruthy();
    expect(JSON.parse(String(settingsCall?.[1]?.body))).toMatchObject({
      mode: "roster_only",
      default_password_mode: "student_id",
      default_password_policy: "student_id_name_activation",
    });
    const importCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/roster/import" && String(call[1]?.method || "GET").toUpperCase() === "POST",
    );
    expect(importCall).toBeTruthy();
    const importBody = importCall?.[1]?.body as FormData;
    expect(importBody.get("mode")).toBe("upsert");
    expect((importBody.get("file") as File).name).toBe("students.csv");

    fireEvent.click(screen.getByRole("button", { name: "添加学生" }));
    fireEvent.change(await screen.findByLabelText("学号"), { target: { value: "2026003" } });
    fireEvent.change(screen.getByLabelText("姓名"), { target: { value: "王五" } });
    const studentSubmitButton = screen.getAllByRole("button", { name: "添加学生" }).at(-1);
    expect(studentSubmitButton).toBeTruthy();
    fireEvent.click(studentSubmitButton as HTMLElement);

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students" && String(call[1]?.method || "GET").toUpperCase() === "POST",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已添加学生。")).toBeNull();
    const createStudentCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students" && String(call[1]?.method || "GET").toUpperCase() === "POST",
    );
    expect(createStudentCall).toBeTruthy();
    expect(JSON.parse(String(createStudentCall?.[1]?.body))).toEqual({
      student_id: "2026003",
      student_name: "王五",
      status: "pending",
      activation_mode: "default_password",
    });

    fireEvent.click(screen.getByRole("button", { name: "新增班级" }));
    fireEvent.change(await screen.findByLabelText("班级名称"), { target: { value: "无机化学二班" } });
    expect(screen.queryByLabelText("备注")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "创建班级" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes" && String(call[1]?.method || "GET").toUpperCase() === "POST",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已创建班级。")).toBeNull();
    const createClassCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes" && String(call[1]?.method || "GET").toUpperCase() === "POST",
    );
    expect(createClassCall).toBeTruthy();
    expect(JSON.parse(String(createClassCall?.[1]?.body))).toEqual({
      class_name: "无机化学二班",
    });
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("deletes the selected class from the class page controls", async () => {
    const fetchMock = await renderClassPage();

    fireEvent.click(screen.getByRole("button", { name: "删除班级" }));
    const deleteDialog = await screen.findByRole("dialog", { name: "删除班级" });
    expect(within(deleteDialog).getByText("无机化学一班")).toBeTruthy();
    fireEvent.click(within(deleteDialog).getByRole("button", { name: "确认删除" }));

    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1" && String(call[1]?.method || "GET").toUpperCase() === "DELETE",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已删除班级。")).toBeNull();

    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("edits roster student names from the class page", async () => {
    const fetchMock = await renderClassPage();

    await clickFirstRosterAction("编辑");
    const editDialog = await screen.findByRole("dialog", { name: "编辑学生" });
    expect(within(editDialog).getByDisplayValue("2026001")).toBeTruthy();
    fireEvent.change(within(editDialog).getByLabelText("姓名"), { target: { value: "张三丰" } });
    fireEvent.click(within(editDialog).getByRole("button", { name: "保存" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" && String(call[1]?.method || "GET").toUpperCase() === "PATCH",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已更新学生姓名。")).toBeNull();
    const editStudentCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" && String(call[1]?.method || "GET").toUpperCase() === "PATCH",
    );
    expect(editStudentCall).toBeTruthy();
    expect(JSON.parse(String(editStudentCall?.[1]?.body))).toEqual({ student_name: "张三丰" });

    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("resets roster student passwords from the class page", async () => {
    const fetchMock = await renderClassPage();

    await clickFirstRosterAction("重置密码");
    const passwordDialog = await screen.findByRole("dialog", { name: "重置密码" });
    fireEvent.change(within(passwordDialog).getByLabelText("新密码"), { target: { value: "newpass123" } });
    fireEvent.click(within(passwordDialog).getByRole("button", { name: "重置密码" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001/reset-password" &&
            String(call[1]?.method || "GET").toUpperCase() === "POST",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已重置 张三 的密码。")).toBeNull();
    const resetPasswordCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001/reset-password" && String(call[1]?.method || "GET").toUpperCase() === "POST",
    );
    expect(resetPasswordCall).toBeTruthy();
    expect(JSON.parse(String(resetPasswordCall?.[1]?.body))).toEqual({
      initial_password: "newpass123",
      force_change: true,
    });

    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("toggles roster student status from the class page", async () => {
    const fetchMock = await renderClassPage();

    await clickFirstRosterAction("停用");
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) =>
            requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" &&
            String(call[1]?.method || "GET").toUpperCase() === "PATCH" &&
            String(call[1]?.body || "").includes("disabled"),
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已停用学生账号。")).toBeNull();
    const disableStudentCall = fetchMock.mock.calls.find(
      (call) =>
        requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" &&
        String(call[1]?.method || "GET").toUpperCase() === "PATCH" &&
        String(call[1]?.body || "").includes("disabled"),
    );
    expect(disableStudentCall).toBeTruthy();
    expect(JSON.parse(String(disableStudentCall?.[1]?.body))).toEqual({ status: "disabled" });

    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("deletes roster student accounts from the class page", async () => {
    const fetchMock = await renderClassPage();

    await clickFirstRosterAction("删除");
    const deleteDialog = await screen.findByRole("dialog", { name: "删除学生" });
    expect(within(deleteDialog).getByText("删除后该学生账号将无法登录，名单中也不再展示该学生。")).toBeTruthy();
    fireEvent.click(within(deleteDialog).getByRole("button", { name: "确认删除" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" && String(call[1]?.method || "GET").toUpperCase() === "DELETE",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("已删除学生账号。")).toBeNull();
    const deleteStudentCall = fetchMock.mock.calls.find(
      (call) => requestUrl(call[0]).pathname === "/api/teacher/classes/class-1/students/2026001" && String(call[1]?.method || "GET").toUpperCase() === "DELETE",
    );
    expect(deleteStudentCall).toBeTruthy();

    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("loads learning analytics from the dashboard endpoint", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/analytics");

    render(<LegacyTeacherApp />);

    expect(await screen.findByTestId("teacher-page-analytics")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "学情分析" })).toBeNull();
    expect(await screen.findByRole("heading", { name: "学生报告与各元素得分" })).toBeTruthy();
    expect(await screen.findByText("张三")).toBeTruthy();
    expect(screen.getByText("李四")).toBeTruthy();
    expect(screen.getByText("第 1 / 1 页 · 共 2 名学生")).toBeTruthy();
    expect(screen.getByText("卤族元素")).toBeTruthy();
    expect(screen.getByText("氧族元素")).toBeTruthy();
    const analyticsTable = screen.getByRole("table", { name: "学生报告与各元素得分" });
    expect(within(analyticsTable).queryByRole("columnheader", { name: "平均分" })).toBeNull();
    expect(screen.queryByText("CAT-CH13-f99cb352")).toBeNull();
    expect(screen.queryByRole("heading", { name: "点位得分明细" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "学生报告" })).toBeNull();
    expect(screen.getByRole("button", { name: "查看张三测试报告" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "查看李四测试报告" })).toBeTruthy();

    expect(screen.getByRole("button", { name: "查看张三卤族元素点位得分详情" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "查看李四卤族元素点位得分详情" })).toBeTruthy();
    expect(within(analyticsTable).queryByText(/证据/)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "查看张三卤族元素点位得分详情" }));
    const zhangDialog = await screen.findByRole("dialog", { name: "张三 · 卤族元素" });
    expect(within(zhangDialog).getByRole("table", { name: "点位得分明细" })).toBeTruthy();
    expect(within(zhangDialog).getByText("第 1 / 1 页 · 共 2 个点位")).toBeTruthy();
    expect(within(zhangDialog).getByText("氯水漂白性实验")).toBeTruthy();
    expect(within(zhangDialog).getByText("92 分")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "查看李四卤族元素点位得分详情" }));
    const liDialog = await screen.findByRole("dialog", { name: "李四 · 卤族元素" });
    expect(within(liDialog).getByText("62 分")).toBeTruthy();
    expect(within(liDialog).getByText("碘离子检验")).toBeTruthy();

    const paths = requestPaths(fetchMock);
    expect(paths).toContain("/api/teacher/classes");
    expect(paths).toContain("/api/teacher/analytics/classes/class-1/dashboard");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports/report-ch13-1");
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("opens student assessment reports from the analytics table", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/analytics");

    render(<LegacyTeacherApp />);

    expect(await screen.findByTestId("teacher-page-analytics")).toBeTruthy();
    expect(await screen.findByRole("heading", { name: "学生报告与各元素得分" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "查看张三测试报告" }));

    const reportDialog = await screen.findByRole("dialog", { name: "张三 · 测试报告" });
    expect(within(reportDialog).getByText("测试次数")).toBeTruthy();
    expect(within(reportDialog).getByText("1 次")).toBeTruthy();
    expect(await within(reportDialog).findByText("CH13 后测评价报告")).toBeTruthy();
    const reportButton = within(reportDialog).getByRole("button", { name: /CH13 后测评价报告/ });
    await waitFor(() => expect(reportButton.getAttribute("aria-pressed")).toBe("true"));
    expect(within(reportButton).getByText("88 分")).toBeTruthy();
    expect(within(reportButton).getByText(/4\/5 题 · 错题 1/)).toBeTruthy();
    expect(await within(reportDialog).findByText("张三已经能解释氯水漂白现象，并能把 HClO 与氧化性联系起来。")).toBeTruthy();
    expect(within(reportDialog).getByText("错题集中在溴碘置换顺序，需要回看 KBr 与 CCl4 的分层颜色。")).toBeTruthy();

    const paths = requestPaths(fetchMock);
    expect(paths).toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports");
    expect(paths).toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports/report-ch13-1");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students");
    expectNoForbiddenGenerationFlows(fetchMock);
  });

  it("loads report prompts from the AI configuration page", async () => {
    const fetchMock = installTeacherFetchMock();
    vi.stubGlobal("fetch", fetchMock);
    window.history.pushState({}, "", "/ai-config");

    render(<LegacyTeacherApp />);

    expect(await screen.findByTestId("teacher-page-ai-config")).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "评价报告" })).toBeNull();
    expect(await screen.findByRole("tab", { name: "报告生成 Prompt" })).toBeTruthy();
    expect(await screen.findByRole("heading", { name: "报告生成 Prompt" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "student_name" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "学生报告" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "保存 Prompt" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (call) => requestUrl(call[0]).pathname === "/api/teacher/assessment-report-prompts" && String(call[1]?.method || "GET").toUpperCase() === "PUT",
        ),
      ).toBe(true),
    );
    expect(screen.queryByText("报告生成 Prompt 已保存。")).toBeNull();

    const paths = requestPaths(fetchMock);
    expect(paths).toContain("/api/teacher/assessment-report-prompts");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports");
    expect(paths).not.toContain("/api/teacher/classes/class-1/students/2026001/assessment-reports/report-ch13-1");
    expect(
      fetchMock.mock.calls.some(
        (call) => requestUrl(call[0]).pathname === "/api/teacher/assessment-report-prompts" && String(call[1]?.method || "GET").toUpperCase() === "PUT",
      ),
    ).toBe(true);
    expectNoForbiddenGenerationFlows(fetchMock);
  });
});
