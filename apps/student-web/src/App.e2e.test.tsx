import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type {
  AuthUser,
  LoginResponse,
  PublicPosttestQuestion,
  PublicPretestQuestion,
  StudentAssistantGeneratedResponse,
  StudentAppConfigResponse,
  StudentExperimentDetailResponse,
  StudentLearningPageResponse,
  StudentPosttestReport,
  StudentPosttestResponse,
  StudentPretestResponse,
} from "./api";

const apiMocks = vi.hoisted(() => ({
  authToken: "",
  studentLogin: vi.fn(),
  changeStudentPassword: vi.fn(),
  loadCurrentUser: vi.fn(),
  logout: vi.fn(),
  startStudentPretest: vi.fn(),
  submitStudentPretest: vi.fn(),
  getStudentAppConfig: vi.fn(),
  getStudentLearningHome: vi.fn(),
  getStudentLearningPage: vi.fn(),
  getStudentExperimentGroup: vi.fn(),
  getStudentExperimentDetail: vi.fn(),
  startStudentPosttest: vi.fn(),
  submitStudentPosttest: vi.fn(),
  generatePosttestAiSummary: vi.fn(),
  explainPosttestMistakes: vi.fn(),
  streamStudentAssistantAsk: vi.fn(),
  submitStudentFeedback: vi.fn(),
}));

vi.mock("./api", () => ({
  getAuthToken: () => apiMocks.authToken,
  setAuthToken: (token: string) => {
    apiMocks.authToken = token;
  },
  studentLogin: apiMocks.studentLogin,
  changeStudentPassword: apiMocks.changeStudentPassword,
  loadCurrentUser: apiMocks.loadCurrentUser,
  logout: apiMocks.logout,
  startStudentPretest: apiMocks.startStudentPretest,
  submitStudentPretest: apiMocks.submitStudentPretest,
  getStudentAppConfig: apiMocks.getStudentAppConfig,
  getStudentLearningHome: apiMocks.getStudentLearningHome,
  getStudentLearningPage: apiMocks.getStudentLearningPage,
  getStudentExperimentGroup: apiMocks.getStudentExperimentGroup,
  getStudentExperimentDetail: apiMocks.getStudentExperimentDetail,
  startStudentPosttest: apiMocks.startStudentPosttest,
  submitStudentPosttest: apiMocks.submitStudentPosttest,
  generatePosttestAiSummary: apiMocks.generatePosttestAiSummary,
  explainPosttestMistakes: apiMocks.explainPosttestMistakes,
  streamStudentAssistantAsk: apiMocks.streamStudentAssistantAsk,
  submitStudentFeedback: apiMocks.submitStudentFeedback,
  studentMediaUrl: (path: string) => path,
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "请求失败，请稍后重试"),
}));

const user: AuthUser = {
  id: "student-user-e2e",
  username: "20249999",
  role: "student",
  display_name: "测试学生",
  status: "active",
  must_change_password: false,
  password_version: 1,
  student_id: "20249999",
  class_id: "class-e2e",
  class_name: "测试班",
};

const loginResponse: LoginResponse = {
  access_token: "student-token",
  token_type: "bearer",
  expires_at: "2099-01-01T00:00:00Z",
  user,
};

const pretestQuestion: PublicPretestQuestion = {
  id: "pre-q-1",
  question_type: "single_choice",
  stem: "摸底题：卤素实验中用于萃取溴单质的试剂是什么？",
  options: [
    { label: "A", text: "CCl4" },
    { label: "B", text: "NaOH" },
  ],
  area: "p区",
  related_chapter_ids: ["ch-19"],
  related_knowledge_point_ids: ["kp-halogen"],
};

const pretestResponse: StudentPretestResponse = {
  status: "in_progress",
  stage: 1,
  questions: [pretestQuestion],
};

const completedPretestResponse: StudentPretestResponse = {
  status: "completed",
  stage: null,
  questions: [],
};

const appConfig: StudentAppConfigResponse = {
  features: {
    ai_assistant_enabled: true,
    feedback_enabled: true,
    student_ai_assistant_enabled: true,
    rag_access_enabled: true,
  },
};

const learningPoint = {
  id: "EXP_19_1_01",
  code: "19-1-01",
  title: "氯、溴、碘的置换次序",
  summary: "比较卤素单质氧化性强弱。",
  parent_code: "19-1",
  parent_title: "实验 19-1 卤素",
  module_title: "氯水 + KBr 溶液 + CCl4",
  chapter_ids: ["CH17"],
  video_candidate_count: 1,
  published_video_count: 0,
  question_count: 10,
  property_key: "oxidation",
  property_title: "氧化性",
  point_key: "halogen-displacement",
  point_title: "卤素置换观察",
  formula: "Cl2 + 2Br- -> 2Cl- + Br2",
  videos: [],
  video_candidates: ["氯水 + KBr 溶液 + CCl4"],
};

const learningPage: StudentLearningPageResponse = {
  recommended_profile_id: "halogens-17",
  profiles: [
    {
      profile_id: "halogens-17",
      chapter_id: "CH17",
      title: "第 17 族 卤族元素",
      subtitle: "p区元素性质与实验",
      family_number: "17",
      family_name: "卤族元素",
      element_symbols: ["F", "Cl", "Br", "I"],
    },
  ],
  active_profile: {
    profile_id: "halogens-17",
    chapter_id: "CH17",
    title: "第 17 族 卤族元素",
    subtitle: "p区元素性质与实验",
    family_number: "17",
    family_name: "卤族元素",
    hero: {
      eyebrow: "p区",
      title: "卤素单质氧化性与置换反应",
      summary: "从族元素性质进入实验点位学习。",
    },
    default_element_symbol: "Cl",
    element_symbols: ["F", "Cl", "Br", "I"],
    elements: [
      {
        symbol: "Cl",
        name: "氯",
        atomic_number: 17,
        state: "气体",
        group_label: "第 17 族",
        electron_configuration: "[Ne]3s2 3p5",
        common_valence: "-1, +1, +5, +7",
        redox_tendency: "氧化性较强",
      },
      {
        symbol: "Br",
        name: "溴",
        atomic_number: 35,
        state: "液体",
        group_label: "第 17 族",
        electron_configuration: "[Ar]3d10 4s2 4p5",
        common_valence: "-1, +1, +5",
        redox_tendency: "可被氯置换",
      },
    ],
    property_cards: [
      { key: "oxidation", label: "氧化性", value: "F2 > Cl2 > Br2 > I2", description: "卤素单质氧化性沿族递减。" },
    ],
    family_common_properties: [
      { key: "oxidation", label: "氧化性", value: "由强到弱", description: "置换反应可用于比较。" },
    ],
    property_sections: [
      {
        key: "oxidation",
        title: "氧化性",
        subtitle: "置换反应",
        summary: "氯能把溴离子氧化为溴单质。",
        formula: "Cl2 + 2Br- -> 2Cl- + Br2",
        tone: "green",
      },
    ],
    reference_media: [],
    related_groups: [
      {
        property_key: "oxidation",
        property_title: "氧化性",
        parent_code: "19-1",
        parent_title: "实验 19-1 卤素",
        points: [learningPoint],
      },
    ],
    chapter_experiment_groups: [
      {
        parent_code: "19-1",
        parent_title: "实验 19-1 卤素",
        points: [learningPoint],
      },
    ],
  },
};

const experimentDetail: StudentExperimentDetailResponse = {
  id: learningPoint.id,
  code: learningPoint.code,
  title: learningPoint.title,
  summary: learningPoint.summary,
  parent_code: learningPoint.parent_code,
  parent_title: learningPoint.parent_title,
  module_title: learningPoint.module_title,
  chapter_ids: learningPoint.chapter_ids,
  video_candidate_count: learningPoint.video_candidate_count,
  published_video_count: learningPoint.published_video_count,
  question_count: learningPoint.question_count,
  video_candidates: learningPoint.video_candidates,
  videos: [],
};

const posttestQuestions: PublicPosttestQuestion[] = [
  {
    id: "post-q-1",
    experiment_id: "EXP_19_1_01",
    experiment_title: "氯、溴、碘的置换次序",
    question_type: "single_choice",
    stem: "氯水加入 KBr 后，CCl4 层呈什么颜色？",
    options: [
      { label: "A", text: "无色" },
      { label: "B", text: "橙红色" },
    ],
    related_chapter_ids: ["ch-19"],
    related_knowledge_point_ids: ["kp-halogen"],
  },
  {
    id: "post-q-2",
    experiment_id: "EXP_19_1_01",
    experiment_title: "氯、溴、碘的置换次序",
    question_type: "fill_blank",
    stem: "该置换反应证明氯单质的____性更强。",
    options: [],
    related_chapter_ids: ["ch-19"],
    related_knowledge_point_ids: ["kp-halogen"],
  },
];

const posttestResponse: StudentPosttestResponse = {
  status: "in_progress",
  session_id: "posttest-session-e2e",
  experiments: [{ id: "EXP_19_1_01", code: "19-1-01", title: "氯、溴、碘的置换次序", parent_code: "19-1", parent_title: "实验 19-1 卤素" }],
  questions: posttestQuestions,
};

const report: StudentPosttestReport = {
  session_id: "posttest-session-e2e",
  experiments: posttestResponse.experiments,
  correct_count: 1,
  total_count: 2,
  score: 50,
  correct_rate: 0.5,
  mastery_before_average: 50,
  mastery_after_average: 45,
  mastery_delta: -5,
  mastery_changes: [
    {
      knowledge_point_id: "EXP_19_1_01",
      experiment_id: "EXP_19_1_01",
      experiment_title: "氯、溴、碘的置换次序",
      content: "氯、溴、碘的置换次序",
      before_score: 50,
      after_score: 45,
      delta: -5,
    },
  ],
  wrong_answers: [
    {
      question_id: "post-q-1",
      experiment_id: "EXP_19_1_01",
      experiment_title: "氯、溴、碘的置换次序",
      question_type: "single_choice",
      stem: "氯水加入 KBr 后，CCl4 层呈什么颜色？",
      options: posttestQuestions[0].options,
      submitted_answer: "A",
      correct_answer: "B",
      explanation: "Br2 被 CCl4 萃取后呈橙红色。",
    },
  ],
  next_recommendation: "建议复习卤素单质氧化性强弱顺序。",
};

const aiSummary: StudentAssistantGeneratedResponse = {
  text: "### 学习总结\n\n- 本轮重点是 **卤素置换**。",
  source: "ai",
  mode: "test",
  cached: true,
};

const aiMistakeExplanation: StudentAssistantGeneratedResponse = {
  text: String.raw`### 共同错因

- **核心观察**：CCl4 层变橙红色说明生成 $\ce{Br2}$。

---

### 复习抓手

1. 记住 $\ce{Cl2 + 2Br- -> 2Cl- + Br2}$。
2. 观察有机层颜色，而不是水层。`,
  source: "ai",
  mode: "test",
  cached: true,
};

function answerVisibleAssessment() {
  const questionCards = document.querySelectorAll("article.question-card");
  questionCards.forEach((card) => {
    const option = card.querySelector<HTMLButtonElement>("button.option");
    if (option) {
      fireEvent.click(option);
      return;
    }
    const input = card.querySelector<HTMLInputElement>("input.fill-answer");
    if (input) {
      fireEvent.change(input, { target: { value: "氧化" } });
    }
  });
}

async function submitVisibleAssessment() {
  answerVisibleAssessment();
  const submitButton = screen.getByRole("button", { name: "提交答案" });
  await waitFor(() => expect(submitButton).toBeEnabled());
  fireEvent.click(submitButton);
}

describe("student app e2e flow", () => {
  beforeEach(() => {
    apiMocks.authToken = "";
    vi.clearAllMocks();
    Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });
    apiMocks.studentLogin.mockResolvedValue(loginResponse);
    apiMocks.loadCurrentUser.mockResolvedValue(user);
    apiMocks.logout.mockResolvedValue(undefined);
    apiMocks.startStudentPretest.mockResolvedValue(pretestResponse);
    apiMocks.submitStudentPretest.mockResolvedValue(completedPretestResponse);
    apiMocks.getStudentAppConfig.mockResolvedValue(appConfig);
    apiMocks.getStudentLearningPage.mockResolvedValue(learningPage);
    apiMocks.getStudentExperimentDetail.mockResolvedValue(experimentDetail);
    apiMocks.startStudentPosttest.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentPosttest.mockResolvedValue({ status: "completed", report });
    apiMocks.generatePosttestAiSummary.mockResolvedValue(aiSummary);
    apiMocks.explainPosttestMistakes.mockResolvedValue(aiMistakeExplanation);
    apiMocks.submitStudentFeedback.mockResolvedValue({ id: "feedback-e2e", status: "open", attachment_count: 0 });
  });

  afterEach(() => cleanup());

  it("keeps pretest fallback, periodic table, report, and AI Markdown rendering usable", async () => {
    render(<App />);

    fireEvent.change(await screen.findByPlaceholderText("请输入学号"), { target: { value: "20249999" } });
    fireEvent.change(screen.getByPlaceholderText("请输入密码"), { target: { value: "Codex2026!" } });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(await screen.findByRole("heading", { name: "课前摸底暂未接入" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "跳过课前摸底" }));

    const periodic = await screen.findByRole("region", { name: "元素周期表选择区" });
    expect(within(periodic).getByRole("button", { name: "H 氢，选择s区" })).toBeInTheDocument();
    fireEvent.click(within(periodic).getByRole("button", { name: "H 氢，选择s区" }));
    expect(screen.getByRole("heading", { name: "s区", level: 2 })).toBeInTheDocument();
    fireEvent.click(within(periodic).getByRole("button", { name: "Cl 氯，选择p区" }));
    expect(screen.getByRole("heading", { name: "p区", level: 2 })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /第 17 族 卤族元素/ }));
    expect(await screen.findByRole("heading", { name: "第 17 族 卤族元素" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /看实验视频/ }));
    expect(await screen.findByRole("heading", { name: "实验-点位视频" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /卤素置换观察/ }));

    expect((await screen.findAllByText("氯水 + KBr 溶液 + CCl4")).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "完成学习" }));

    expect(await screen.findByRole("heading", { name: "请完成学习后测" })).toBeInTheDocument();
    await submitVisibleAssessment();

    expect(await screen.findByRole("heading", { name: "本轮实验报告" })).toBeInTheDocument();
    await waitFor(() => expect(document.querySelector(".summary-ai-text ul.ai-md-list")).not.toBeNull());
    expect(screen.getByText("卤素置换")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "AI 讲解错题" }));

    await waitFor(() => expect(document.querySelector(".mistake-ai-answer hr.ai-md-divider")).not.toBeNull());
    expect(document.querySelector(".mistake-ai-answer strong.ai-md-strong")).not.toBeNull();
    expect(document.querySelector(".mistake-ai-answer ol.ai-md-list")).not.toBeNull();
    expect(document.querySelector(".mistake-ai-answer .katex")).not.toBeNull();
    expect(screen.queryByText("---")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "反馈" }));
    expect(screen.getByRole("dialog", { name: "页面反馈" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "内容问题" }));
    fireEvent.change(screen.getByPlaceholderText("描述你在当前页面遇到的问题或建议"), {
      target: { value: "报告里的错题讲解建议再清楚一点" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交反馈" }));

    await waitFor(() => expect(apiMocks.submitStudentFeedback).toHaveBeenCalledTimes(1));
    expect(apiMocks.submitStudentFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        feedback_type: "content",
        content: "报告里的错题讲解建议再清楚一点",
        metadata: expect.objectContaining({
          screen: "posttest_report",
          session_id: "posttest-session-e2e",
        }),
      }),
    );
    expect(await screen.findByText("已收到反馈，老师后台可以看到。")).toBeInTheDocument();
  });
});
