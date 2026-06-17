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
  StudentExperimentDetailResponse,
  StudentExperimentGroupResponse,
  StudentLearningHomeResponse,
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
  getStudentLearningHome: vi.fn(),
  getStudentExperimentGroup: vi.fn(),
  getStudentExperimentDetail: vi.fn(),
  startStudentPosttest: vi.fn(),
  submitStudentPosttest: vi.fn(),
  generatePosttestAiSummary: vi.fn(),
  explainPosttestMistakes: vi.fn(),
  streamStudentAssistantAsk: vi.fn(),
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
  getStudentLearningHome: apiMocks.getStudentLearningHome,
  getStudentExperimentGroup: apiMocks.getStudentExperimentGroup,
  getStudentExperimentDetail: apiMocks.getStudentExperimentDetail,
  startStudentPosttest: apiMocks.startStudentPosttest,
  submitStudentPosttest: apiMocks.submitStudentPosttest,
  generatePosttestAiSummary: apiMocks.generatePosttestAiSummary,
  explainPosttestMistakes: apiMocks.explainPosttestMistakes,
  streamStudentAssistantAsk: apiMocks.streamStudentAssistantAsk,
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

const learningHome: StudentLearningHomeResponse = {
  recommended_area_id: "p",
  recommended_parent_code: "19-1",
  areas: [
    { area_id: "s", area_name: "s区", enabled: true, parent_codes: ["18-1"], experiment_count: 1, published_video_count: 0, question_count: 10 },
    { area_id: "p", area_name: "p区", enabled: true, parent_codes: ["19-1"], experiment_count: 1, published_video_count: 0, question_count: 10 },
    { area_id: "d", area_name: "d区", enabled: true, parent_codes: ["20-2"], experiment_count: 1, published_video_count: 0, question_count: 10 },
    { area_id: "ds", area_name: "ds区", enabled: true, parent_codes: ["20-1"], experiment_count: 1, published_video_count: 0, question_count: 10 },
    { area_id: "f", area_name: "f区", enabled: true, parent_codes: ["21-1"], experiment_count: 1, published_video_count: 0, question_count: 10 },
  ],
  groups: [
    {
      parent_code: "18-1",
      parent_title: "实验 18-1 碱金属",
      area_id: "s",
      area_name: "s区",
      chapter_ids: ["ch-18"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 10,
      recommended: false,
    },
    {
      parent_code: "19-1",
      parent_title: "实验 19-1 卤素",
      area_id: "p",
      area_name: "p区",
      chapter_ids: ["ch-19"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 10,
      recommended: true,
    },
  ],
};

const experimentGroup: StudentExperimentGroupResponse = {
  parent_code: "19-1",
  parent_title: "实验 19-1 卤素",
  area_id: "p",
  area_name: "p区",
  experiments: [
    {
      id: "EXP_19_1_01",
      code: "19-1-01",
      title: "氯、溴、碘的置换次序",
      summary: "比较卤素单质氧化性强弱。",
      parent_code: "19-1",
      parent_title: "实验 19-1 卤素",
      module_title: "氯水 + KBr 溶液 + CCl4",
      chapter_ids: ["ch-19"],
      video_candidate_count: 1,
      published_video_count: 0,
      question_count: 10,
    },
  ],
};

const experimentDetail: StudentExperimentDetailResponse = {
  ...experimentGroup.experiments[0],
  video_candidates: ["氯水 + KBr 溶液 + CCl4"],
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
    apiMocks.studentLogin.mockResolvedValue(loginResponse);
    apiMocks.loadCurrentUser.mockResolvedValue(user);
    apiMocks.logout.mockResolvedValue(undefined);
    apiMocks.startStudentPretest.mockResolvedValue(pretestResponse);
    apiMocks.submitStudentPretest.mockResolvedValue(completedPretestResponse);
    apiMocks.getStudentLearningHome.mockResolvedValue(learningHome);
    apiMocks.getStudentExperimentGroup.mockResolvedValue(experimentGroup);
    apiMocks.getStudentExperimentDetail.mockResolvedValue(experimentDetail);
    apiMocks.startStudentPosttest.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentPosttest.mockResolvedValue({ status: "completed", report });
    apiMocks.generatePosttestAiSummary.mockResolvedValue(aiSummary);
    apiMocks.explainPosttestMistakes.mockResolvedValue(aiMistakeExplanation);
  });

  afterEach(() => cleanup());

  it("keeps pretest, periodic table, report, and AI Markdown rendering usable", async () => {
    render(<App />);

    fireEvent.change(await screen.findByPlaceholderText("请输入学号"), { target: { value: "20249999" } });
    fireEvent.change(screen.getByPlaceholderText("请输入密码"), { target: { value: "Codex2026!" } });
    fireEvent.click(screen.getByRole("button", { name: "登录" }));

    expect(await screen.findByRole("heading", { name: "请完成以下题目" })).toBeInTheDocument();
    expect(screen.getByText("摸底题：卤素实验中用于萃取溴单质的试剂是什么？")).toBeInTheDocument();
    await submitVisibleAssessment();

    const periodic = await screen.findByRole("region", { name: "元素周期表选择区" });
    expect(within(periodic).getByRole("button", { name: "H 氢" })).toBeInTheDocument();
    expect(within(periodic).getByRole("heading", { name: "p区", level: 3 })).toBeInTheDocument();
    fireEvent.click(within(periodic).getByRole("button", { name: "选择s区" }));
    expect(within(periodic).getByRole("heading", { name: "s区", level: 3 })).toBeInTheDocument();
    fireEvent.click(within(periodic).getByRole("button", { name: "选择p区" }));
    expect(within(periodic).getByRole("heading", { name: "p区", level: 3 })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "进入实验" }));
    expect(await screen.findByRole("heading", { name: "氯、溴、碘的置换次序" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /19-1-01/ }));

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
  });
});
