import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type {
  AuthUser,
  PublicPretestQuestion,
  PublicSmartAssessmentQuestion,
  StudentAppConfigResponse,
  StudentExperimentDetailResponse,
  StudentLearningHomeResponse,
  StudentLearningPageResponse,
  StudentPretestResponse,
  StudentSmartAssessmentReport,
  StudentSmartAssessmentResponse,
  StudentVideoLibrarySearchResponse,
} from "./api";

const apiMocks = vi.hoisted(() => ({
  authToken: "student-token",
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
  searchStudentVideoLibrary: vi.fn(),
  startStudentPosttest: vi.fn(),
  submitStudentPosttest: vi.fn(),
  startStudentSmartAssessment: vi.fn(),
  submitStudentSmartAssessment: vi.fn(),
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
  searchStudentVideoLibrary: apiMocks.searchStudentVideoLibrary,
  startStudentPosttest: apiMocks.startStudentPosttest,
  submitStudentPosttest: apiMocks.submitStudentPosttest,
  startStudentSmartAssessment: apiMocks.startStudentSmartAssessment,
  submitStudentSmartAssessment: apiMocks.submitStudentSmartAssessment,
  generatePosttestAiSummary: apiMocks.generatePosttestAiSummary,
  explainPosttestMistakes: apiMocks.explainPosttestMistakes,
  streamStudentAssistantAsk: apiMocks.streamStudentAssistantAsk,
  submitStudentFeedback: apiMocks.submitStudentFeedback,
  studentMediaUrl: (path: string) => path,
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "request failed"),
}));

vi.mock("./features/atom-viewer/AtomViewerZdog", () => ({
  AtomViewerZdog: ({ element, mode }: { element: { name: string }; mode: "bohr" | "orbital" }) => (
    <figure className="atom-viewer">
      <canvas className="atom-canvas" aria-label={`${element.name} ${mode}`} />
      <figcaption className="atom-hint">atom model</figcaption>
    </figure>
  ),
}));

const user: AuthUser = {
  id: "student-user-e2e",
  username: "20249999",
  role: "student",
  display_name: "Route Stack Student",
  status: "active",
  must_change_password: false,
  password_version: 1,
  student_id: "20249999",
  class_id: "class-e2e",
  class_name: "Class E2E",
};

const completedPretestResponse: StudentPretestResponse = {
  status: "completed",
  stage: null,
  questions: [],
};

const pretestQuestion: PublicPretestQuestion = {
  id: "pre-q-1",
  question_type: "single_choice",
  stem: "Pretest question",
  options: [{ label: "A", text: "A" }],
  area: "p",
  related_chapter_ids: ["CH17"],
  related_knowledge_point_ids: ["kp-halogen"],
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
  title: "Halogen displacement",
  summary: "Chlorine displaces bromide.",
  parent_code: "19-1",
  parent_title: "Experiment 19-1 Halogens",
  module_title: "Chlorine water + KBr + CCl4",
  chapter_ids: ["CH17"],
  video_candidate_count: 1,
  published_video_count: 0,
  question_count: 2,
  property_key: "oxidation",
  property_title: "Oxidation",
  point_key: "halogen-displacement",
  point_title: "Halogen displacement observation",
  formula: "Cl2 + 2Br- -> 2Cl- + Br2",
  videos: [],
  video_candidates: ["Chlorine water + KBr + CCl4"],
};

const learningPage: StudentLearningPageResponse = {
  recommended_profile_id: "halogens-17",
  profiles: [
    {
      profile_id: "halogens-17",
      chapter_id: "CH17",
      title: "Group 17 Halogens",
      subtitle: "p-block family properties and experiments",
      family_number: "17",
      family_name: "Halogens",
      element_symbols: ["F", "Cl", "Br", "I"],
    },
    {
      profile_id: "alkali-alkaline-earth",
      chapter_id: "CH18",
      title: "s-block metals",
      subtitle: "s-block family properties and experiments",
      family_number: "1/2",
      family_name: "Alkali and alkaline earth metals",
      element_symbols: ["Li", "Na", "K", "Mg", "Ca"],
    },
  ],
  active_profile: {
    profile_id: "halogens-17",
    chapter_id: "CH17",
    title: "Group 17 Halogens",
    subtitle: "p-block family properties and experiments",
    family_number: "17",
    family_name: "Halogens",
    hero: {
      eyebrow: "p-block",
      title: "Halogen oxidation and displacement",
      summary: "Learn the trend through facts and experiment videos.",
    },
    default_element_symbol: "Cl",
    element_symbols: ["F", "Cl", "Br", "I"],
    elements: [
      {
        symbol: "Cl",
        name: "Chlorine",
        atomic_number: 17,
        card_focus: "Experiment focus: oxidizes bromide",
        card_relevance: "Links directly to the halogen displacement video.",
        card_tags: ["Group 17", "Gas", "Common -1"],
        relative_atomic_mass: "35.45",
        group: "17",
        period: 3,
        block: "p",
        state_at_20c: "Gas",
        density: "0.002898 g/cm3",
        rsc_url: "https://periodic-table.rsc.org/element/17/chlorine",
        fact_source: "RSC",
        state: "gas",
        group_label: "Group 17",
        electron_configuration: "[Ne]3s2 3p5",
        common_valence: "-1, +1, +5, +7",
        redox_tendency: "Strong oxidizer",
      },
      {
        symbol: "Br",
        name: "Bromine",
        atomic_number: 35,
        card_focus: "Experiment focus: displaced by chlorine",
        card_relevance: "The organic-layer color change helps confirm bromine formation.",
        card_tags: ["Group 17", "Liquid", "Common -1"],
        relative_atomic_mass: "79.904",
        group: "17",
        period: 4,
        block: "p",
        state_at_20c: "Liquid",
        density: "3.11 g/cm3",
        rsc_url: "https://periodic-table.rsc.org/element/35/bromine",
        fact_source: "RSC",
        state: "liquid",
        group_label: "Group 17",
        electron_configuration: "[Ar]3d10 4s2 4p5",
        common_valence: "-1, +1, +5",
        redox_tendency: "Can be displaced by chlorine",
      },
    ],
    property_cards: [{ key: "oxidation", label: "Oxidation", value: "F2 > Cl2 > Br2 > I2", description: "Oxidizing ability decreases down the group." }],
    family_common_properties: [{ key: "oxidation", label: "Oxidation", value: "Decreasing", description: "Displacement reactions show the trend." }],
    property_sections: [
      {
        key: "oxidation",
        title: "Oxidation",
        subtitle: "Displacement",
        summary: "Chlorine oxidizes bromide to bromine.",
        formula: "Cl2 + 2Br- -> 2Cl- + Br2",
        tone: "green",
      },
    ],
    reference_media: [],
    related_groups: [
      {
        property_key: "oxidation",
        property_title: "Oxidation",
        parent_code: "19-1",
        parent_title: "Experiment 19-1 Halogens",
        points: [learningPoint],
      },
    ],
    chapter_experiment_groups: [
      {
        parent_code: "19-1",
        parent_title: "Experiment 19-1 Halogens",
        points: [learningPoint],
      },
    ],
  },
};

const learningHome: StudentLearningHomeResponse = {
  recommended_area_id: "p",
  recommended_parent_code: "19-1",
  areas: [
    {
      area_id: "p",
      area_name: "p-block",
      enabled: true,
      parent_codes: ["19-1"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 2,
    },
  ],
  groups: [
    {
      parent_code: "19-1",
      parent_title: "Experiment 19-1 Halogens",
      area_id: "p",
      area_name: "p-block",
      chapter_ids: ["CH17"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 2,
      recommended: true,
    },
  ],
};

const experimentGroup = {
  parent_code: "19-1",
  parent_title: "Experiment 19-1 Halogens",
  area_id: "p",
  area_name: "p-block",
  experiments: [learningPoint],
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
  selected_point_key: "halogen-displacement",
  selected_point_title: "Orange layer observation",
  point_content_status: "published",
  principle_mode: "equation",
  principle_equation: "Cl2 + 2 KBr = 2 KCl + Br2",
  principle_text: null,
  phenomenon_explanation: "Chlorine displaces bromine ions, and bromine dissolves into the organic layer.",
  safety_note: "Handle chlorine water in a ventilated space and avoid direct inhalation.",
  related_points: [
    {
      experiment_id: learningPoint.id,
      point_key: "iodine-displacement",
      point_title: "Iodine comparison",
      experiment_title: learningPoint.title,
      relation_type: "default",
    },
  ],
  assessment_context: {
    experiment_id: learningPoint.id,
    chapter_ids: learningPoint.chapter_ids,
    parent_code: learningPoint.parent_code,
    parent_title: learningPoint.parent_title,
  },
  video_candidates: learningPoint.video_candidates,
  videos: [],
};

const videoLibraryResponse: StudentVideoLibrarySearchResponse = {
  query: "",
  status: "ok",
  backend: "local",
  message: "",
  total: 2,
  browse: {
    recommended: [
      {
        id: "video_point:EXP_19_1_01:candidate:0",
        type: "video_point",
        title: "Orange layer observation",
        subtitle: "Halogen displacement",
        snippet: "Chlorine water + KBr + CCl4",
        score: 8,
        badges: ["Halogens", "Video point"],
        action_label: "View point",
        target: {
          kind: "point_detail",
          route: "/point/EXP_19_1_01",
          experiment_id: "EXP_19_1_01",
          profile_id: "halogens-17",
          chapter_id: "CH17",
          property_key: "oxidation",
          property_title: "Oxidation",
          element_symbol: "Cl",
          point_key: "halogen-displacement",
          point_title: "Orange layer observation",
        },
      },
    ],
    recent: [],
    chips: [
      { kind: "phenomenon", label: "orange layer", query: "orange" },
      { kind: "reagent", label: "CCl4", query: "CCl4" },
    ],
  },
  groups: [
    {
      key: "video_points",
      title: "Video points",
      summary: "Open experiment observation points.",
      items: [
        {
          id: "video_point:EXP_19_1_01:candidate:0",
          type: "video_point",
          title: "Orange layer observation",
          subtitle: "Halogen displacement",
          snippet: "Chlorine water + KBr + CCl4",
          score: 8,
          badges: ["Halogens", "Video point"],
          action_label: "View point",
          target: {
            kind: "point_detail",
            route: "/point/EXP_19_1_01",
            experiment_id: "EXP_19_1_01",
            profile_id: "halogens-17",
            chapter_id: "CH17",
            property_key: "oxidation",
            property_title: "Oxidation",
            element_symbol: "Cl",
            point_key: "halogen-displacement",
            point_title: "Orange layer observation",
          },
        },
      ],
    },
    {
      key: "ai",
      title: "AI explanation",
      summary: "Ask with context.",
      items: [
        {
          id: "ai_prompt:orange",
          type: "ai_prompt",
          title: "Explain orange layer",
          subtitle: "AI learning assistant",
          snippet: "Explain the observed orange CCl4 layer.",
          score: 1,
          badges: ["AI"],
          action_label: "Ask AI",
          target: {
            kind: "ai_chat",
            route: "/ai/chat",
            experiment_id: "EXP_19_1_01",
            chapter_id: "CH17",
            context_title: "Explain orange layer",
            context_summary: "Explain the observed orange CCl4 layer.",
            prompt: "Why does CCl4 become orange?",
          },
        },
      ],
    },
  ],
};

const posttestQuestions: PublicSmartAssessmentQuestion[] = [
  {
    id: "post-q-1",
    experiment_id: "EXP_19_1_01",
    experiment_title: "Halogen displacement",
    question_type: "single_choice",
    stem: "What color appears in CCl4?",
    options: [
      { label: "A", text: "colorless" },
      { label: "B", text: "orange" },
    ],
    related_chapter_ids: ["CH17"],
    related_knowledge_point_ids: ["kp-halogen"],
  },
];

const smartAssessmentStrategy = {
  enabled: true,
  question_count: 1,
  untested_ratio_percent: 50,
  weak_tendency_percent: 80,
  max_questions_per_experiment: 2,
  weak_curve: 2,
  weak_max_bonus: 9,
};

const smartAssessmentComposition = {
  total_questions: 1,
  target_question_count: 1,
  untested_question_count: 1,
  measured_question_count: 0,
  untested_ratio_percent: 50,
  weak_tendency_percent: 80,
  max_questions_per_experiment: 2,
  warnings: {},
};

const posttestResponse: StudentSmartAssessmentResponse = {
  status: "in_progress",
  session_id: "posttest-session-e2e",
  strategy: smartAssessmentStrategy,
  composition: smartAssessmentComposition,
  experiments: [
    {
      id: "EXP_19_1_01",
      code: "19-1-01",
      title: "Halogen displacement",
      parent_code: "19-1",
      parent_title: "Experiment 19-1 Halogens",
      mastery_score: 42,
      evidence_count: 0,
      source: "untested",
      draw_tickets: null,
      question_count: 1,
      reason: "未测实验按老师设置的比例纳入",
    },
  ],
  questions: posttestQuestions,
};

const report: StudentSmartAssessmentReport = {
  session_id: "posttest-session-e2e",
  strategy: smartAssessmentStrategy,
  composition: smartAssessmentComposition,
  experiments: posttestResponse.experiments,
  correct_count: 1,
  total_count: 1,
  score: 100,
  correct_rate: 1,
  mastery_before_average: 50,
  mastery_after_average: 60,
  mastery_delta: 10,
  mastery_changes: [],
  wrong_answers: [
    {
      question_id: "post-q-1",
      experiment_id: "EXP_19_1_01",
      experiment_title: "Halogen displacement",
      question_type: "single_choice",
      stem: "What color appears in CCl4?",
      options: posttestQuestions[0].options,
      submitted_answer: "A",
      correct_answer: "B",
      explanation: "Bromine dissolves in CCl4 and appears orange.",
    },
  ],
  next_recommendation: "### Study summary\n\n- Review halogen displacement.",
};

function rootButton(root: string): HTMLButtonElement {
  const button = document.querySelector<HTMLButtonElement>(`.student-bottom-nav button[data-root="${root}"]`);
  if (!button) throw new Error(`Missing root nav button: ${root}`);
  return button;
}

function activeRoot(): string | null {
  return document.querySelector(".student-bottom-nav button.active")?.getAttribute("data-root") || null;
}

async function clickRoot(root: string) {
  fireEvent.click(rootButton(root));
  await waitFor(() => expect(window.location.pathname).toBe(`/${root}`));
  await waitFor(() => expect(activeRoot()).toBe(root));
}

function expectBottomNavHidden() {
  expect(document.querySelector(".student-bottom-nav")).toBeNull();
}

function answerVisibleAssessment() {
  document.querySelectorAll("article.question-card").forEach((card) => {
    const option = card.querySelector<HTMLButtonElement>("button.option");
    if (option) fireEvent.click(option);
  });
}

async function submitVisibleAssessment() {
  answerVisibleAssessment();
  const submitButton = screen.getByRole("button", { name: "提交答案" });
  await waitFor(() => expect(submitButton).toBeEnabled());
  fireEvent.click(submitButton);
}

async function renderAuthenticatedApp(pathname = "/") {
  window.history.replaceState({}, "", pathname);
  render(<App />);
  const skipPretest = await screen.findByRole("button", { name: "跳过课前摸底" }).catch(() => null);
  if (skipPretest) fireEvent.click(skipPretest);
  await waitFor(() => expect(document.querySelector(".student-app-shell")).not.toBeNull());
  await waitFor(() => expect(apiMocks.loadCurrentUser).toHaveBeenCalled());
}

describe("student app route stack", () => {
  beforeEach(() => {
    apiMocks.authToken = "student-token";
    vi.clearAllMocks();
    window.sessionStorage.clear();
    window.history.replaceState({}, "", "/");
    Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });
    apiMocks.loadCurrentUser.mockResolvedValue(user);
    apiMocks.logout.mockResolvedValue(undefined);
    apiMocks.startStudentPretest.mockResolvedValue(completedPretestResponse);
    apiMocks.submitStudentPretest.mockResolvedValue({ status: "completed", stage: null, questions: [] } satisfies StudentPretestResponse);
    apiMocks.getStudentAppConfig.mockResolvedValue(appConfig);
    apiMocks.getStudentLearningHome.mockResolvedValue(learningHome);
    apiMocks.getStudentLearningPage.mockResolvedValue(learningPage);
    apiMocks.getStudentExperimentGroup.mockResolvedValue(experimentGroup);
    apiMocks.getStudentExperimentDetail.mockResolvedValue(experimentDetail);
    apiMocks.searchStudentVideoLibrary.mockResolvedValue(videoLibraryResponse);
    apiMocks.startStudentPosttest.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentPosttest.mockResolvedValue({ status: "completed", report });
    apiMocks.startStudentSmartAssessment.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentSmartAssessment.mockResolvedValue({ status: "completed", report });
    apiMocks.generatePosttestAiSummary.mockResolvedValue({ text: "### Study summary\n\n- Review **halogens**.", source: "ai", mode: "test", cached: true });
    apiMocks.explainPosttestMistakes.mockResolvedValue({ text: "### Mistake explanation\n\n- $\\ce{Br2}$ is orange.", source: "ai", mode: "test", cached: true });
    apiMocks.streamStudentAssistantAsk.mockImplementation(async (_payload, onEvent) => {
      onEvent({ event: "delta", delta: "### Route answer\n\n- $\\ce{Cl2}$ oxidizes bromide." });
      onEvent({ event: "final", response: { source_count: 1, sources: [{ title: "Halogen evidence", chunk_id: "halogen" }] } });
    });
    apiMocks.submitStudentFeedback.mockResolvedValue({ id: "feedback-e2e", status: "open", attachment_count: 0 });
  });

  afterEach(() => cleanup());

  it("drives roots, details, contextual AI, assessment, and feedback through URLs instead of tab state", async () => {
    await renderAuthenticatedApp("/");

    const nav = await screen.findByRole("navigation", { name: "学生端主导航" });
    expect(Array.from(nav.querySelectorAll("button")).map((button) => button.getAttribute("data-root"))).toEqual([
      "home",
      "learn",
      "ai",
      "assessment",
      "profile",
    ]);
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");

    fireEvent.click(screen.getByText("实验视频库").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenCalledWith(""));
    expect(screen.getByRole("search")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("搜索实验视频库"), { target: { value: "orange" } });
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenLastCalledWith("orange"));
    fireEvent.click(document.querySelector<HTMLButtonElement>(".video-library-results .video-result-card")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/EXP_19_1_01"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");

    await clickRoot("learn");
    expect(document.querySelector(".periodic-grid")).not.toBeNull();
    fireEvent.click(document.querySelector<HTMLButtonElement>(".chapter-entry-card.recommended")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".chapter-element-summary")).not.toBeNull());
    expect(screen.getByText("Experiment focus: oxidizes bromide")).toBeInTheDocument();
    expect(screen.getByText("Links directly to the halogen displacement video.")).toBeInTheDocument();
    expect(screen.queryByText("Chlorine在Halogens中的位置")).not.toBeInTheDocument();
    expect(document.querySelector(".atom-model-card")).toBeNull();
    expect(document.querySelector(".chapter-view-switcher")).toBeNull();
    expect(document.querySelector(".family-common-panel")).toBeNull();
    expect(document.querySelector(".property-section-panel")).toBeNull();
    expect(document.querySelector(".finish-action")).toBeNull();
    expect(screen.queryByRole("button", { name: "选章节" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "问 AI" })).not.toBeInTheDocument();
    await waitFor(() => expect(document.querySelector(".learning-point-card")).not.toBeNull());

    fireEvent.click(document.querySelector<HTMLButtonElement>(".chapter-element-detail-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17/element/Cl"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".atom-model-card")).not.toBeNull());
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();
    expect(screen.queryByRole("button", { name: "问 AI" })).not.toBeInTheDocument();

    fireEvent.click(document.querySelector<HTMLButtonElement>(".learning-point-card")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/EXP_19_1_01"));
    expectBottomNavHidden();

    fireEvent.click(document.querySelector<HTMLButtonElement>(".context-assistant-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/point/EXP_19_1_01"));

    fireEvent.click(document.querySelector<HTMLButtonElement>(".finish-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expectBottomNavHidden();
    await submitVisibleAssessment();
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/report/posttest-session-e2e"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".summary-ai-text ul.ai-md-list")).not.toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "问 AI" }));
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/report/posttest-session-e2e"));

    fireEvent.click(screen.getByRole("button", { name: "继续学习" }));
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");

    await clickRoot("profile");
    expect(screen.queryByRole("form", { name: "学生端反馈" })).not.toBeInTheDocument();
    fireEvent.click(document.querySelector<HTMLButtonElement>(".profile-entry-card")!);
    await waitFor(() => expect(window.location.pathname).toBe("/feedback/new"));
    expectBottomNavHidden();
    fireEvent.click(screen.getByRole("button", { name: "内容问题" }));
    fireEvent.change(screen.getByPlaceholderText("描述你遇到的问题或建议，可以配一张截图"), {
      target: { value: "Route stack feedback" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交反馈" }));
    await waitFor(() => expect(apiMocks.submitStudentFeedback).toHaveBeenCalledTimes(1));
    expect(apiMocks.submitStudentFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        content: "Route stack feedback",
        page_path: "/feedback/new",
        metadata: expect.objectContaining({ route: "feedback_new", from: "profile" }),
      }),
    );
  });

  it("starts a smart assessment directly from the assessment center and reports composition", async () => {
    await renderAuthenticatedApp("/assessment");

    await waitFor(() => expect(window.location.pathname).toBe("/assessment"));
    expect(screen.getByText("随时开始智能测评")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "开始智能测评" }));
    await waitFor(() => expect(apiMocks.startStudentSmartAssessment).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expectBottomNavHidden();
    expect(screen.getByText("智能组卷")).toBeInTheDocument();
    expect(screen.getByText("1 题未测实验")).toBeInTheDocument();
    expect(screen.getByText("薄弱倾向 80%")).toBeInTheDocument();
    expect(screen.getAllByText("Halogen displacement").length).toBeGreaterThan(0);

    await submitVisibleAssessment();
    await waitFor(() =>
      expect(apiMocks.submitStudentSmartAssessment).toHaveBeenCalledWith("posttest-session-e2e", [
        { question_id: "post-q-1", answer: "A" },
      ]),
    );
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/report/posttest-session-e2e"));
    expect(screen.getByText("智能测评报告")).toBeInTheDocument();
    expect(screen.getByText("目标占比 50%")).toBeInTheDocument();
    expect(screen.getByText("薄弱倾向 80%")).toBeInTheDocument();
  });

  it("renders structured point detail content, related links, and the fixed test handoff", async () => {
    await renderAuthenticatedApp("/point/EXP_19_1_01?from=chapter&pointKey=halogen-displacement&pointTitle=Orange%20layer%20observation");

    await waitFor(() => expect(apiMocks.getStudentExperimentDetail).toHaveBeenCalledWith("EXP_19_1_01", "halogen-displacement"));
    expect(screen.getByText("暂无可播放视频")).toBeInTheDocument();
    expect(screen.getByText("实验原理")).toBeInTheDocument();
    expect(screen.getByText("Cl2 + 2 KBr = 2 KCl + Br2")).toBeInTheDocument();
    expect(screen.getByText("现象解释")).toBeInTheDocument();
    expect(screen.getByText("安全提示")).toBeInTheDocument();
    expect(screen.queryByText("Halogen evidence")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Iodine comparison").closest("button")!);
    await waitFor(() => expect(window.location.search).toContain("iodine-displacement"));
    expect(apiMocks.getStudentExperimentDetail).toHaveBeenLastCalledWith("EXP_19_1_01", "iodine-displacement");

    fireEvent.click(screen.getByRole("button", { name: "开始测试" }));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expectBottomNavHidden();
  });

  it("serves direct root and detail client routes with route-level navigation visibility", async () => {
    await renderAuthenticatedApp("/learn");
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");
    cleanup();

    await renderAuthenticatedApp("/ai/chat");
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    expect(document.querySelector(".ai-chat-panel")).not.toBeNull();
    cleanup();

    await renderAuthenticatedApp("/video-library");
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".video-library-page")).not.toBeNull());
    cleanup();

    await renderAuthenticatedApp("/chapter/halogens-17/element/Cl");
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17/element/Cl"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".atom-model-card")).not.toBeNull());
    cleanup();

    await renderAuthenticatedApp("/feedback/new");
    await waitFor(() => expect(window.location.pathname).toBe("/feedback/new"));
    expectBottomNavHidden();
    expect(screen.getByRole("form", { name: "学生端反馈" })).toBeInTheDocument();
  });

  it("keeps five root routes while feature-disabled pages render disabled centers", async () => {
    apiMocks.getStudentAppConfig.mockResolvedValue({
      features: {
        ai_assistant_enabled: false,
        feedback_enabled: false,
        student_ai_assistant_enabled: false,
        rag_access_enabled: true,
      },
    });

    await renderAuthenticatedApp("/");
    const nav = await screen.findByRole("navigation", { name: "学生端主导航" });
    expect(Array.from(nav.querySelectorAll("button")).map((button) => button.getAttribute("data-root"))).toEqual([
      "home",
      "learn",
      "ai",
      "assessment",
      "profile",
    ]);

    await clickRoot("ai");
    expect(screen.getByText("AI 学习助手暂未开放")).toBeInTheDocument();
    await clickRoot("profile");
    expect(screen.getByText("反馈入口已关闭")).toBeInTheDocument();
  });
});
