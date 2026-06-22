import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type {
  AuthUser,
  PublicPosttestQuestion,
  PublicPretestQuestion,
  StudentAppConfigResponse,
  StudentCatalogChapterResponse,
  StudentCatalogNodeResponse,
  StudentLearningHomeResponse,
  StudentLearningPageResponse,
  StudentPointDetailResponse,
  StudentPosttestReport,
  StudentPosttestResponse,
  StudentPretestResponse,
  StudentVideoLibrarySearchResponse,
} from "./api";

const apiMocks = vi.hoisted(() => ({
  authToken: "student-token",
  studentLogin: vi.fn(),
  exchangeStudentPreviewTicket: vi.fn(),
  changeStudentPassword: vi.fn(),
  loadCurrentUser: vi.fn(),
  logout: vi.fn(),
  startStudentPretest: vi.fn(),
  submitStudentPretest: vi.fn(),
  getStudentAppConfig: vi.fn(),
  getStudentLearningHome: vi.fn(),
  getStudentLearningPage: vi.fn(),
  getStudentChapterCatalog: vi.fn(),
  getStudentCatalogNode: vi.fn(),
  getStudentCatalogPointDetail: vi.fn(),
  getPreviewCatalogPointDetail: vi.fn(),
  searchStudentVideoLibrary: vi.fn(),
  startStudentPosttest: vi.fn(),
  submitStudentPosttest: vi.fn(),
  generatePosttestAiSummary: vi.fn(),
  explainPosttestMistakes: vi.fn(),
  streamStudentAssistantAsk: vi.fn(),
  submitStudentFeedback: vi.fn(),
}));

vi.mock("./api", () => ({
  getAuthToken: () => apiMocks.authToken,
  isPreviewAuthSession: () => false,
  setAuthToken: (token: string) => {
    apiMocks.authToken = token;
  },
  setPreviewAuthToken: (token: string) => {
    apiMocks.authToken = token;
  },
  clearPreviewAuthToken: () => {
    apiMocks.authToken = "";
  },
  studentLogin: apiMocks.studentLogin,
  exchangeStudentPreviewTicket: apiMocks.exchangeStudentPreviewTicket,
  changeStudentPassword: apiMocks.changeStudentPassword,
  loadCurrentUser: apiMocks.loadCurrentUser,
  logout: apiMocks.logout,
  startStudentPretest: apiMocks.startStudentPretest,
  submitStudentPretest: apiMocks.submitStudentPretest,
  getStudentAppConfig: apiMocks.getStudentAppConfig,
  getStudentLearningHome: apiMocks.getStudentLearningHome,
  getStudentLearningPage: apiMocks.getStudentLearningPage,
  getStudentChapterCatalog: apiMocks.getStudentChapterCatalog,
  getStudentCatalogNode: apiMocks.getStudentCatalogNode,
  getStudentCatalogPointDetail: apiMocks.getStudentCatalogPointDetail,
  getPreviewCatalogPointDetail: apiMocks.getPreviewCatalogPointDetail,
  searchStudentVideoLibrary: apiMocks.searchStudentVideoLibrary,
  startStudentPosttest: apiMocks.startStudentPosttest,
  submitStudentPosttest: apiMocks.submitStudentPosttest,
  generatePosttestAiSummary: apiMocks.generatePosttestAiSummary,
  explainPosttestMistakes: apiMocks.explainPosttestMistakes,
  streamStudentAssistantAsk: apiMocks.streamStudentAssistantAsk,
  submitStudentFeedback: apiMocks.submitStudentFeedback,
  studentMediaUrl: (path: string) => path,
  previewMediaUrl: (path: string) => path,
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

const catalogChapter: StudentCatalogChapterResponse = {
  chapter_id: "CH17",
  chapter_title: "Halogen chapter",
  nodes: [
    {
      node_id: "cat-dir-halogen",
      chapter_id: "CH17",
      parent_id: null,
      node_kind: "directory",
      title: "Halogen displacement catalog",
      summary: "Open catalog entries for halogen experiments.",
      status: "published",
      display_order: 1,
      actions: ["open_directory"],
      has_children: true,
      has_point_content: false,
      media_count: 0,
      published_media_count: 0,
    },
  ],
};

const catalogNestedDirectoryNode: StudentCatalogNodeResponse["children"][number] = {
  node_id: "cat-dir-oxidation",
  chapter_id: "CH17",
  parent_id: "cat-dir-halogen",
  node_kind: "directory",
  title: "Oxidation experiments",
  summary: "Choose a concrete displacement point.",
  status: "published",
  display_order: 1,
  actions: ["open_directory"],
  has_children: true,
  has_point_content: false,
  media_count: 0,
  published_media_count: 0,
};

const catalogPointNode: StudentCatalogNodeResponse["children"][number] = {
  node_id: "cat-point-halogen",
  chapter_id: "CH17",
  parent_id: "cat-dir-oxidation",
  node_kind: "point",
  title: "Orange layer observation",
  summary: "Chlorine water displaces bromide and produces bromine in CCl4.",
  status: "published",
  display_order: 1,
  actions: ["open_point"],
  has_children: false,
  has_point_content: true,
  media_count: 0,
  published_media_count: 0,
};

const catalogDirectory: StudentCatalogNodeResponse = {
  node: catalogChapter.nodes[0],
  breadcrumbs: [
    {
      node_id: "cat-dir-halogen",
      title: "Halogen displacement catalog",
      node_kind: "directory",
      chapter_id: "CH17",
    },
  ],
  children: [catalogNestedDirectoryNode],
};

const catalogNestedDirectory: StudentCatalogNodeResponse = {
  node: catalogNestedDirectoryNode,
  breadcrumbs: [
    {
      node_id: "cat-dir-halogen",
      title: "Halogen displacement catalog",
      node_kind: "directory",
      chapter_id: "CH17",
    },
    {
      node_id: "cat-dir-oxidation",
      chapter_id: "CH17",
      title: "Oxidation experiments",
      node_kind: "directory",
    },
  ],
  children: [catalogPointNode],
};

const catalogPointDetail: StudentPointDetailResponse = {
  node_id: "cat-point-halogen",
  canonical_node_id: "cat-point-halogen",
  source_node_id: null,
  placement_node_id: "cat-point-halogen",
  canonical_point_id: "cat-canon-halogen",
  chapter_id: "CH17",
  title: "Orange layer observation",
  summary: "Chlorine displaces bromide in the organic layer.",
  breadcrumbs: [
    {
      node_id: "cat-dir-halogen",
      title: "Halogen displacement catalog",
      node_kind: "directory",
      chapter_id: "CH17",
    },
    {
      node_id: "cat-point-halogen",
      title: "Orange layer observation",
      node_kind: "point",
      chapter_id: "CH17",
    },
  ],
  principle_mode: "equation",
  principle_equation: "Cl2 + 2 KBr = 2 KCl + Br2",
  principle_text: null,
  reaction_equations: [
    {
      row_order: 1,
      raw_text: "Cl2 + 2 KBr = 2 KCl + Br2",
      canonical_display: "Cl2 + 2 KBr = 2 KCl + Br2",
      canonical_mhchem: "\\ce{Cl2 + 2 KBr -> 2 KCl + Br2}",
      annotation_text: "condition: organic layer observation",
      validation_status: "valid",
    },
  ],
  phenomenon_explanation: "Chlorine displaces bromine ions, and bromine dissolves into the organic layer.",
  safety_note: "Handle chlorine water in a ventilated space and avoid direct inhalation.",
  videos: [],
  has_video: false,
  no_video_reason: "Video is not bound yet.",
  related_points: [
    {
      node_id: "cat-point-iodine",
      title: "Iodine comparison",
      relation_type: "manual",
      source_node_id: "cat-point-halogen",
    },
  ],
  assessment_context: {
    point_node_id: "cat-point-halogen",
    placement_node_id: "cat-point-halogen",
    canonical_point_id: "cat-canon-halogen",
    chapter_id: "CH17",
    source_node_id: null,
    catalog_path: [
      {
        node_id: "cat-dir-halogen",
        title: "Halogen displacement catalog",
        node_kind: "directory",
        chapter_id: "CH17",
      },
      {
        node_id: "cat-point-halogen",
        title: "Orange layer observation",
        node_kind: "point",
        chapter_id: "CH17",
      },
    ],
  },
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
        id: "video_point:cat-point-halogen",
        type: "video_point",
        title: "Orange layer observation",
        subtitle: "Halogen displacement",
        snippet: "Chlorine water + KBr + CCl4",
        score: 8,
        badges: ["Halogens", "Video point"],
        action_label: "View point",
        target: {
          kind: "point_detail",
          route: "/point/cat-point-halogen",
          node_id: "cat-point-halogen",
          profile_id: "halogens-17",
          chapter_id: "CH17",
          catalog_path: ["Halogen displacement catalog", "Orange layer observation"],
          property_key: "oxidation",
          property_title: "Oxidation",
          element_symbol: "Cl",
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
          id: "video_point:cat-point-halogen",
          type: "video_point",
          title: "Orange layer observation",
          subtitle: "Halogen displacement",
          snippet: "Chlorine water + KBr + CCl4",
          score: 8,
          badges: ["Halogens", "Video point"],
          action_label: "View point",
        target: {
            kind: "point_detail",
            route: "/point/cat-point-halogen",
            node_id: "cat-point-halogen",
            profile_id: "halogens-17",
            chapter_id: "CH17",
            catalog_path: ["Halogen displacement catalog", "Orange layer observation"],
            property_key: "oxidation",
            property_title: "Oxidation",
            element_symbol: "Cl",
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
            node_id: "cat-point-halogen",
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

const posttestQuestions: PublicPosttestQuestion[] = [
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

const posttestResponse: StudentPosttestResponse = {
  status: "in_progress",
  session_id: "posttest-session-e2e",
  experiments: [{ id: "EXP_19_1_01", code: "19-1-01", title: "Halogen displacement", parent_code: "19-1", parent_title: "Experiment 19-1 Halogens" }],
  questions: posttestQuestions,
};

const report: StudentPosttestReport = {
  session_id: "posttest-session-e2e",
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
  next_recommendation: "Review halogen displacement.",
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
    apiMocks.exchangeStudentPreviewTicket.mockResolvedValue({
      access_token: "preview-student-token",
      token_type: "bearer",
      expires_at: "2030-01-01T00:00:00Z",
      user: { ...user, preview_mode: true, preview_purpose: "teacher_student_device_preview" },
      preview_policy: {
        feedback_enabled: true,
        account_mutation_enabled: false,
        assessment_enabled: true,
        assistant_enabled: true,
        analytics_side_effects_enabled: false,
        blocked_routes: [],
        message: "预览模式可以体验学生端流程，但不会提交真实反馈或账号变更。",
      },
    });
    apiMocks.loadCurrentUser.mockResolvedValue(user);
    apiMocks.logout.mockResolvedValue(undefined);
    apiMocks.startStudentPretest.mockResolvedValue(completedPretestResponse);
    apiMocks.submitStudentPretest.mockResolvedValue({ status: "completed", stage: null, questions: [] } satisfies StudentPretestResponse);
    apiMocks.getStudentAppConfig.mockResolvedValue(appConfig);
    apiMocks.getStudentLearningHome.mockResolvedValue(learningHome);
    apiMocks.getStudentLearningPage.mockResolvedValue(learningPage);
    apiMocks.getStudentChapterCatalog.mockResolvedValue(catalogChapter);
    apiMocks.getStudentCatalogNode.mockImplementation((nodeId: string) =>
      Promise.resolve(nodeId === "cat-dir-oxidation" ? catalogNestedDirectory : catalogDirectory),
    );
    apiMocks.getStudentCatalogPointDetail.mockResolvedValue(catalogPointDetail);
    apiMocks.getPreviewCatalogPointDetail.mockResolvedValue(catalogPointDetail);
    apiMocks.searchStudentVideoLibrary.mockResolvedValue(videoLibraryResponse);
    apiMocks.startStudentPosttest.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentPosttest.mockResolvedValue({ status: "completed", report });
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
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");

    await clickRoot("learn");
    expect(document.querySelector(".periodic-grid")).not.toBeNull();
    expect(screen.getByText("元素周期表")).toBeInTheDocument();
    expect(screen.getByText("选择元素分区")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "搜索元素" })).toBeInTheDocument();
    expect(document.querySelector(".learning-recommendation-card")).not.toBeNull();
    expect(document.querySelector(".chapter-entry-card")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "p区元素" }));
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");
    const areaPopover = await screen.findByRole("dialog", { name: "p区元素" });
    expect(areaPopover).toHaveClass("learning-area-popover");
    await waitFor(() => expect(areaPopover.querySelector(".chapter-entry-card")).not.toBeNull());
    fireEvent.pointerDown(document.querySelector<HTMLElement>(".learning-area-popover-backdrop")!);
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "p区元素" })).not.toBeInTheDocument());
    expect(window.location.pathname).toBe("/learn");
    fireEvent.click(screen.getByRole("button", { name: "p区元素" }));
    const reopenedAreaPopover = await screen.findByRole("dialog", { name: "p区元素" });
    fireEvent.click(reopenedAreaPopover.querySelector<HTMLButtonElement>(".chapter-entry-card")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".family-catalog-shell")).not.toBeNull());
    expect(document.querySelector(".family-detail-frame")).not.toBeNull();
    expect(document.querySelector(".family-catalog-context")).not.toBeNull();
    expect(document.querySelector(".family-element-rail")).not.toBeNull();
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
    await waitFor(() => expect(document.querySelector(".catalog-node-card")).not.toBeNull());

    fireEvent.click(document.querySelector<HTMLButtonElement>(".chapter-element-detail-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17/element/Cl"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".atom-model-card")).not.toBeNull());
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();
    expect(screen.queryByRole("button", { name: "问 AI" })).not.toBeInTheDocument();

    await waitFor(() => expect(document.querySelector(".catalog-node-card-main")).not.toBeNull());
    const familyCatalogPath = window.location.pathname;
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-halogen"));
    expect(window.location.pathname).toBe(familyCatalogPath);
    await waitFor(() => expect(document.querySelector(".family-catalog-shell")).not.toBeNull());
    expect(document.querySelector(".family-detail-frame")).not.toBeNull();
    expect(document.querySelector<HTMLButtonElement>(".family-catalog-up-action")).not.toBeDisabled();
    fireEvent.click(document.querySelector<HTMLButtonElement>(".family-catalog-more-action")!);
    await waitFor(() => expect(document.querySelector(".family-catalog-more-sheet")).not.toBeNull());
    fireEvent.pointerDown(document.querySelector<HTMLElement>(".family-catalog-more-backdrop")!);
    await waitFor(() => expect(document.querySelector(".family-catalog-more-sheet")).toBeNull());
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-directory")).not.toBeNull());
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-oxidation"));
    expect(window.location.pathname).toBe(familyCatalogPath);
    await waitFor(() => expect(document.querySelector(".family-catalog-shell")).not.toBeNull());
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-point")).not.toBeNull());
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("Cl");
    expectBottomNavHidden();

    fireEvent.click(document.querySelector<HTMLButtonElement>(".context-assistant-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));

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

  it("renders structured point detail content, related links, and the fixed test handoff", async () => {
    await renderAuthenticatedApp("/point/cat-point-halogen?from=chapter&chapterId=CH17&pointTitle=Orange%20layer%20observation");

    await waitFor(() => expect(apiMocks.getStudentCatalogPointDetail).toHaveBeenCalledWith("cat-point-halogen"));
    expect(screen.getByText("暂无可播放视频")).toBeInTheDocument();
    expect(screen.getByText("实验原理")).toBeInTheDocument();
    expect(screen.getByText("暂无可播放视频")).toBeInTheDocument();
    expect(screen.getByText("实验原理")).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("Cl2 + 2 KBr = 2 KCl + Br2"))).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("说明：condition: organic layer observation"))).toBeInTheDocument();
    expect(screen.getByText("现象解释")).toBeInTheDocument();
    expect(screen.getByText("安全提示")).toBeInTheDocument();
    expect(screen.getByText("现象解释")).toBeInTheDocument();
    expect(screen.getByText("安全提示")).toBeInTheDocument();
    expect(screen.queryByText("Halogen evidence")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Iodine comparison").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-iodine"));

    fireEvent.click(screen.getByRole("button", { name: "开始练习" }));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expectBottomNavHidden();
  });

  it("renders teacher preview point details without creating a student session or mutation actions", async () => {
    window.history.replaceState({}, "", "/preview/catalog/points/cat-point-halogen?preview_token=teacher-preview-token");
    render(<App />);

    await waitFor(() => expect(apiMocks.getPreviewCatalogPointDetail).toHaveBeenCalledWith("cat-point-halogen", "teacher-preview-token"));
    expect(apiMocks.loadCurrentUser).not.toHaveBeenCalled();
    expect(document.querySelector(".student-app-shell")).toBeNull();
    expect(screen.getAllByText("Orange layer observation").length).toBeGreaterThan(0);
    expect(screen.queryByText("开始练习")).not.toBeInTheDocument();
    expect(screen.queryByText("带着这个点位问 AI")).not.toBeInTheDocument();
    expect(document.querySelector(".finish-action")).toBeNull();
    expect(apiMocks.submitStudentPosttest).not.toHaveBeenCalled();
    expect(apiMocks.submitStudentFeedback).not.toHaveBeenCalled();
  });

  it("bootstraps a full teacher preview session without overwriting normal login flow", async () => {
    window.history.replaceState({}, "", "/preview/session?ticket=teacher-ticket");
    render(<App />);

    await waitFor(() => expect(apiMocks.exchangeStudentPreviewTicket).toHaveBeenCalledWith("teacher-ticket"));
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    await waitFor(() => expect(document.querySelector(".student-app-shell")).not.toBeNull());
    expect(apiMocks.authToken).toBe("preview-student-token");
    expect(apiMocks.loadCurrentUser).not.toHaveBeenCalled();
    expect(apiMocks.startStudentPretest).not.toHaveBeenCalled();
  });

  it("keeps preview profile friendly and intercepts feedback submit without hiding the form", async () => {
    apiMocks.loadCurrentUser.mockResolvedValue({
      ...user,
      username: "preview_student_teacher",
      display_name: "Preview Student - Teacher",
      student_id: "TPV_STUDENT_46DB7A5A3B0B4B02A9EF788DB1A237",
      class_name: "Preview Class - Teacher",
      preview_mode: true,
      preview_purpose: "teacher_student_device_preview",
    });
    apiMocks.getStudentAppConfig.mockResolvedValue({
      features: {
        ai_assistant_enabled: true,
        feedback_enabled: false,
        student_ai_assistant_enabled: true,
        rag_access_enabled: true,
      },
      preview_mode: true,
      preview_policy: {
        feedback_enabled: true,
        account_mutation_enabled: false,
        assessment_enabled: true,
        assistant_enabled: true,
        analytics_side_effects_enabled: false,
        blocked_routes: [],
        message: "预览模式可以体验学生端流程，但不会提交真实反馈或账号变更。",
      },
    } satisfies StudentAppConfigResponse);

    await renderAuthenticatedApp("/profile");

    expect(screen.getByText("00000000")).toBeInTheDocument();
    expect(screen.getByText("施测平")).toBeInTheDocument();
    expect(screen.getByText("数智一班")).toBeInTheDocument();
    expect(screen.queryByText("反馈入口已关闭")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("提交反馈").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/feedback/new"));
    expect(await screen.findByRole("form", { name: "学生端反馈" })).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("描述你遇到的问题或建议，可以配一张截图"), {
      target: { value: "预览里填写一条反馈" },
    });
    const submitButton = screen.getByRole("button", { name: "提交反馈" });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    expect(apiMocks.submitStudentFeedback).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByRole("dialog", { name: "预览模式提示" })).toHaveTextContent("预览模式不能提交反馈"),
    );
  });

  it("keeps normal student profile and feedback submit on the real student path", async () => {
    await renderAuthenticatedApp("/profile");

    expect(screen.getByText("20249999")).toBeInTheDocument();
    expect(screen.getByText("Route Stack Student")).toBeInTheDocument();
    expect(screen.getByText("Class E2E")).toBeInTheDocument();
    expect(screen.queryByText("00000000")).not.toBeInTheDocument();
    expect(screen.queryByText("施测平")).not.toBeInTheDocument();
    expect(screen.queryByText("数智一班")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("提交反馈").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/feedback/new"));
    fireEvent.change(screen.getByPlaceholderText("描述你遇到的问题或建议，可以配一张截图"), {
      target: { value: "正常学生反馈提交" },
    });
    const submitButton = screen.getByRole("button", { name: "提交反馈" });
    await waitFor(() => expect(submitButton).toBeEnabled());
    fireEvent.click(submitButton);

    await waitFor(() => expect(apiMocks.submitStudentFeedback).toHaveBeenCalledTimes(1));
    expect(apiMocks.submitStudentFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        content: "正常学生反馈提交",
        page_path: "/feedback/new",
      }),
    );
    expect(screen.queryByRole("dialog", { name: "预览模式提示" })).not.toBeInTheDocument();
  });

  it("serves direct root and detail client routes with route-level navigation visibility", async () => {
    await renderAuthenticatedApp("/learn");
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");
    expect(document.querySelector(".periodic-grid")).not.toBeNull();
    expect(document.querySelector(".chapter-entry-card")).toBeNull();
    cleanup();

    await renderAuthenticatedApp("/learn/area/p");
    await waitFor(() => expect(window.location.pathname).toBe("/learn/area/p"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".chapter-card-panel")).not.toBeNull());
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

    await renderAuthenticatedApp("/catalog/cat-dir-halogen");
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-halogen"));
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-directory")).not.toBeNull());
    expect(document.querySelector(".family-catalog-shell")).toBeNull();
    expectBottomNavHidden();
    cleanup();

    await renderAuthenticatedApp("/point/cat-point-halogen");
    await waitFor(() => expect(apiMocks.getStudentCatalogPointDetail).toHaveBeenLastCalledWith("cat-point-halogen"));
    await waitFor(() => expect(document.querySelector(".catalog-point-detail")).not.toBeNull());
    expectBottomNavHidden();
    cleanup();

    await renderAuthenticatedApp("/feedback/new");
    await waitFor(() => expect(window.location.pathname).toBe("/feedback/new"));
    expectBottomNavHidden();
    expect(screen.getByRole("form", { name: "学生端反馈" })).toBeInTheDocument();
  });

  it("surfaces wrong durable route type failures from directory and point APIs", async () => {
    apiMocks.getStudentCatalogNode.mockRejectedValueOnce(new Error("Catalog node is not a directory"));
    await renderAuthenticatedApp("/catalog/cat-point-halogen");
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenCalledWith("cat-point-halogen"));
    expect(await screen.findByText("Catalog node is not a directory")).toBeInTheDocument();
    cleanup();

    apiMocks.getStudentCatalogPointDetail.mockRejectedValueOnce(new Error("Catalog node is not a point"));
    await renderAuthenticatedApp("/point/cat-dir-halogen");
    await waitFor(() => expect(apiMocks.getStudentCatalogPointDetail).toHaveBeenCalledWith("cat-dir-halogen"));
    expect(await screen.findByText("Catalog node is not a point")).toBeInTheDocument();
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
