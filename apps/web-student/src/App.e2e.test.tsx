import "@testing-library/jest-dom/vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type {
  AuthUser,
  PublicPosttestQuestion,
  PublicPretestQuestion,
  CatalogPreviewNodeResponse,
  StudentAssessmentReport,
  StudentAppConfigResponse,
  StudentCatalogChapterResponse,
  StudentCatalogNodeResponse,
  StudentHomeVideoFeedResponse,
  StudentLearningHomeResponse,
  StudentLearningPageResponse,
  StudentPointDetailResponse,
  StudentPretestResponse,
  StudentSmartAssessmentReport,
  StudentSmartAssessmentResponse,
  StudentVideoLibrarySearchResponse,
} from "./api";

type ArtplayerTestLayer = {
  html?: unknown;
  click?: (component: unknown, event: Event) => void;
};

type ArtplayerTestControl = {
  html?: unknown;
  name?: string;
  position?: string;
  mounted?: (this: ArtplayerTestInstance, element: HTMLElement) => void;
  beforeUnmount?: (this: ArtplayerTestInstance, element: HTMLElement) => void;
};

type ArtplayerTestOption = {
  container?: HTMLElement;
  url?: string;
  poster?: string | null;
  playsInline?: boolean;
  autoplay?: boolean;
  muted?: boolean;
  miniProgressBar?: boolean;
  setting?: boolean;
  fullscreen?: boolean;
  fullscreenWeb?: boolean;
  lock?: boolean;
  playbackRate?: boolean;
  layers?: ArtplayerTestLayer[];
  controls?: ArtplayerTestControl[];
  moreVideoAttr?: Partial<HTMLVideoElement>;
};

type ArtplayerTestInstance = {
  option: ArtplayerTestOption;
  destroy: ReturnType<typeof vi.fn>;
  on: ReturnType<typeof vi.fn>;
  off: ReturnType<typeof vi.fn>;
  play: () => Promise<void>;
  pause: () => void;
  toggle: () => void;
  video: HTMLVideoElement;
  isReady: boolean;
  playing: boolean;
  duration: number;
  fullscreenWeb: boolean;
  seek: number;
  emit: (name: string, ...args: unknown[]) => void;
};

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
  getStudentHomeVideoFeed: vi.fn(),
  getStudentLearningHome: vi.fn(),
  getStudentLearningPage: vi.fn(),
  getStudentChapterCatalog: vi.fn(),
  getStudentCatalogNode: vi.fn(),
  getStudentCatalogPointDetail: vi.fn(),
  getPreviewCatalogNode: vi.fn(),
  getPreviewCatalogPointDetail: vi.fn(),
  searchStudentVideoLibrary: vi.fn(),
  startStudentPosttest: vi.fn(),
  submitStudentPosttest: vi.fn(),
  getStudentAssessmentStatus: vi.fn(),
  getStudentAssessmentReports: vi.fn(),
  getStudentAssessmentReport: vi.fn(),
  dismissStudentSmartBaselinePrompt: vi.fn(),
  startStudentSmartAssessment: vi.fn(),
  startStudentPointAssessment: vi.fn(),
  submitStudentSmartAssessment: vi.fn(),
  getStudentCustomAssessmentOptions: vi.fn(),
  startStudentCustomAssessment: vi.fn(),
  generatePosttestAiSummary: vi.fn(),
  explainPosttestMistakes: vi.fn(),
  streamStudentAssistantAsk: vi.fn(),
  submitStudentFeedback: vi.fn(),
}));

const artplayerInstances = vi.hoisted(() => [] as ArtplayerTestInstance[]);

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
  getStudentHomeVideoFeed: apiMocks.getStudentHomeVideoFeed,
  getStudentLearningHome: apiMocks.getStudentLearningHome,
  getStudentLearningPage: apiMocks.getStudentLearningPage,
  getStudentChapterCatalog: apiMocks.getStudentChapterCatalog,
  getStudentCatalogNode: apiMocks.getStudentCatalogNode,
  getStudentCatalogPointDetail: apiMocks.getStudentCatalogPointDetail,
  getPreviewCatalogNode: apiMocks.getPreviewCatalogNode,
  getPreviewCatalogPointDetail: apiMocks.getPreviewCatalogPointDetail,
  searchStudentVideoLibrary: apiMocks.searchStudentVideoLibrary,
  startStudentPosttest: apiMocks.startStudentPosttest,
  submitStudentPosttest: apiMocks.submitStudentPosttest,
  getStudentAssessmentStatus: apiMocks.getStudentAssessmentStatus,
  getStudentAssessmentReports: apiMocks.getStudentAssessmentReports,
  getStudentAssessmentReport: apiMocks.getStudentAssessmentReport,
  dismissStudentSmartBaselinePrompt: apiMocks.dismissStudentSmartBaselinePrompt,
  startStudentSmartAssessment: apiMocks.startStudentSmartAssessment,
  startStudentPointAssessment: apiMocks.startStudentPointAssessment,
  submitStudentSmartAssessment: apiMocks.submitStudentSmartAssessment,
  getStudentCustomAssessmentOptions: apiMocks.getStudentCustomAssessmentOptions,
  startStudentCustomAssessment: apiMocks.startStudentCustomAssessment,
  generatePosttestAiSummary: apiMocks.generatePosttestAiSummary,
  explainPosttestMistakes: apiMocks.explainPosttestMistakes,
  streamStudentAssistantAsk: apiMocks.streamStudentAssistantAsk,
  submitStudentFeedback: apiMocks.submitStudentFeedback,
  studentMediaUrl: (path: string) => path,
  previewMediaUrl: (path: string) => path,
  errorMessage: (error: unknown) => (error instanceof Error ? error.message : "request failed"),
}));

vi.mock("lottie-react", () => ({
  default: ({ className }: { className?: string }) => <div className={className} data-testid="atom-thinking-lottie" />,
}));

vi.mock("artplayer", () => {
  const Artplayer = vi.fn().mockImplementation(function ArtplayerMock(option: ArtplayerTestOption) {
    const root = document.createElement("div");
    root.className = "art-video-player";

    const video = document.createElement("video");
    Object.defineProperty(video, "paused", { configurable: true, value: true });
    Object.defineProperty(video, "ended", { configurable: true, value: false });
    Object.defineProperty(video, "readyState", { configurable: true, value: 1 });
    if (option.moreVideoAttr?.controls === false) {
      video.controls = false;
      video.removeAttribute("controls");
    }
    if (option.moreVideoAttr?.playsInline || option.playsInline) {
      video.setAttribute("playsinline", "");
    }
    root.appendChild(video);

    const bottom = document.createElement("div");
    bottom.className = "art-bottom";

    const indicator = document.createElement("div");
    indicator.className = "art-progress-indicator";
    bottom.appendChild(indicator);

    if (option.miniProgressBar) {
      root.classList.add("art-mini-progress-bar");
    }

    const controlsLeft = document.createElement("div");
    controlsLeft.className = "art-controls-left";
    bottom.appendChild(controlsLeft);
    root.appendChild(bottom);

    const listeners: Record<string, Array<(...args: unknown[]) => unknown>> = {};
    const mountedControls: Array<{ control: ArtplayerTestControl; element: HTMLElement }> = [];
    let isReady = false;
    let seekValue = 0;
    let fullscreenWebValue = false;
    const setPaused = (paused: boolean) => {
      Object.defineProperty(video, "paused", { configurable: true, value: paused });
    };
    const setReady = () => {
      isReady = true;
      Object.defineProperty(video, "readyState", { configurable: true, value: 4 });
    };
    let instance!: ArtplayerTestInstance;
    instance = {
      option,
      destroy: vi.fn(() => {
        mountedControls.forEach(({ control, element }) => control.beforeUnmount?.call(instance, element));
        root.remove();
      }),
      on: vi.fn((name: string, fn: (...args: unknown[]) => unknown) => {
        listeners[name] = [...(listeners[name] || []), fn];
        return instance;
      }),
      off: vi.fn((name: string, fn?: (...args: unknown[]) => unknown) => {
        if (!listeners[name]) return instance;
        listeners[name] = fn ? listeners[name].filter((listener) => listener !== fn) : [];
        return instance;
      }),
      play: vi.fn(() => {
        setReady();
        setPaused(false);
        instance.emit("video:play", new Event("play"));
        instance.emit("video:playing", new Event("playing"));
        return Promise.resolve();
      }),
      pause: vi.fn(() => {
        setPaused(true);
        instance.emit("video:pause", new Event("pause"));
      }),
      toggle: vi.fn(() => {
        if (instance.playing) {
          instance.pause();
        } else {
          void instance.play();
        }
      }),
      video,
      isReady: false,
      playing: false,
      duration: 0,
      fullscreenWeb: false,
      seek: 0,
      emit: (name: string, ...args: unknown[]) => {
        if (name === "ready") {
          setReady();
        }
        listeners[name]?.forEach((fn) => fn(...args));
      },
    };
    Object.defineProperties(instance, {
      isReady: {
        get: () => isReady,
      },
      playing: {
        get: () => !video.paused && !video.ended,
      },
      duration: {
        get: () => (Number.isFinite(video.duration) ? video.duration : 0),
      },
      fullscreenWeb: {
        get: () => fullscreenWebValue,
        set: (value: boolean) => {
          fullscreenWebValue = value;
          instance.emit("fullscreenWeb", value);
        },
      },
      seek: {
        get: () => seekValue,
        set: (value: number) => {
          seekValue = value;
          video.currentTime = value;
          instance.emit("seek", value, value);
          instance.emit("video:timeupdate", new Event("timeupdate"));
        },
      },
    });

    option.controls?.forEach((control) => {
      const controlElement = document.createElement("div");
      controlElement.className = `art-control art-control-${control.name || "custom"}`;
      if (control.html instanceof HTMLElement) {
        controlElement.appendChild(control.html);
      } else if (typeof control.html === "string") {
        controlElement.innerHTML = control.html;
      }
      controlsLeft.appendChild(controlElement);
      mountedControls.push({ control, element: controlElement });
      control.mounted?.call(instance, controlElement);
    });

    option.layers?.forEach((layer) => {
      if (!(layer.html instanceof HTMLElement)) return;
      if (typeof layer.click === "function") {
        layer.html.addEventListener("click", (event) => layer.click?.({}, event));
      }
      root.appendChild(layer.html);
    });

    option.container?.appendChild(root);
    artplayerInstances.push(instance);
    return instance;
  });
  return { default: Artplayer };
});

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
  media_count: 1,
  published_media_count: 1,
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
      annotation_text: "I- forms H2S during organic layer observation",
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

const catalogPointDetailWithVideo: StudentPointDetailResponse = {
  ...catalogPointDetail,
  title: "Separation of a mixed Cr3, Al3, and Mn2 solution with a deliberately long point video title",
  videos: [
    {
      media_id: "media-halogen",
      title: "Halogen displacement video",
      mime_type: "video/mp4",
      stream_path: "/media/halogen.mp4",
      thumbnail_path: "/media/halogen.jpg",
    },
  ],
  has_video: true,
  no_video_reason: null,
};

const homeVideoFeedResponse: StudentHomeVideoFeedResponse = {
  status: "ok",
  message: "",
  items: [
    {
      id: "feed:cat-point-halogen",
      node_id: "cat-point-halogen",
      placement_node_id: "cat-point-halogen",
      canonical_point_id: "cat-canon-halogen",
      chapter_id: "CH17",
      title: "Orange layer observation",
      summary: "Chlorine water oxidizes bromide and produces an orange organic layer.",
      snippet: "Chlorine water + KBr + CCl4",
      catalog_path: ["Halogen displacement catalog", "Orange layer observation"],
      badges: ["Textbook chapter 13", "Experiment video"],
      reason: "catalog",
      video: {
        media_id: "media-halogen",
        title: "Halogen displacement video",
        mime_type: "video/mp4",
        stream_path: "/api/student/media/assets/media-halogen/stream",
        thumbnail_path: "/api/student/media/assets/media-halogen/thumbnail",
        duration_seconds: 35,
      },
      target: {
        kind: "point_detail",
        route: "/point/cat-point-halogen",
        node_id: "cat-point-halogen",
        placement_node_id: "cat-point-halogen",
        canonical_point_id: "cat-canon-halogen",
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
      title: "Atom explanation",
      summary: "Ask with context.",
      items: [
        {
          id: "ai_prompt:orange",
          type: "ai_prompt",
          title: "Explain orange layer",
          subtitle: "Atom 学习助手",
          snippet: "Explain the observed orange CCl4 layer.",
          score: 1,
          badges: ["Atom"],
          action_label: "Ask Atom",
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

const emptyVideoLibraryResponse: StudentVideoLibrarySearchResponse = {
  ...videoLibraryResponse,
  query: "zzz",
  status: "empty",
  message: "没有找到匹配的实验视频结果。",
  total: 0,
  browse: {
    recommended: [],
    recent: [],
    chips: [],
  },
  groups: [],
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

const posttestResponse: StudentSmartAssessmentResponse = {
  status: "in_progress",
  session_id: "posttest-session-e2e",
  assessment_mode: "smart",
  strategy: {
    enabled: true,
    question_count: 1,
    untested_ratio_percent: 20,
    weak_tendency_percent: 70,
    max_questions_per_experiment: 2,
    weak_curve: 2,
    weak_max_bonus: 9,
  },
  composition: {
    total_questions: 1,
    target_question_count: 1,
    untested_question_count: 1,
    measured_question_count: 0,
    untested_ratio_percent: 20,
    weak_tendency_percent: 70,
    max_questions_per_experiment: 2,
    warnings: {},
  },
  experiments: [
    {
      id: "EXP_19_1_01",
      code: "19-1-01",
      title: "Halogen displacement",
      parent_code: "19-1",
      parent_title: "Experiment 19-1 Halogens",
      mastery_score: null,
      evidence_count: 1,
      source: "untested",
      question_count: 1,
    },
  ],
  questions: posttestQuestions,
};

const report: StudentSmartAssessmentReport = {
  session_id: "posttest-session-e2e",
  assessment_mode: "smart",
  strategy: posttestResponse.strategy,
  composition: posttestResponse.composition,
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

const assessmentReport: StudentAssessmentReport = {
  id: "assessment-report-e2e",
  student_id: "20249999",
  class_id: "class-1",
  report_type: "smart",
  source_session_id: report.session_id,
  title: "智能测评报告",
  score: report.score,
  correct_count: report.correct_count,
  total_count: report.total_count,
  correct_rate: report.correct_rate,
  wrong_count: report.wrong_answers.length,
  completed_at: "2026-06-25T10:00:00Z",
  summary: {
    text: "### Study summary\n\n- Review **halogens**.",
    source: "ai",
    mode: "test",
    generated_at: "2026-06-25T10:00:01Z",
  },
  mistake_explanation: {
    text: "### Mistake explanation\n\n- Bromine in CCl4 is orange.",
    source: "ai",
    mode: "test",
    generated_at: "2026-06-25T10:00:02Z",
  },
  prompt_snapshot: {},
  payload: report,
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

function installVisualViewport(height: number, layoutHeight = height) {
  const listeners: Record<string, Array<(event: Event) => void>> = {};
  Object.defineProperty(window, "innerHeight", { configurable: true, value: layoutHeight });
  const viewport = {
    height,
    width: 390,
    offsetTop: 0,
    offsetLeft: 0,
    pageTop: 0,
    pageLeft: 0,
    scale: 1,
    addEventListener: vi.fn((type: string, listener: EventListenerOrEventListenerObject | null) => {
      if (typeof listener !== "function") return;
      listeners[type] = [...(listeners[type] || []), listener];
    }),
    removeEventListener: vi.fn((type: string, listener: EventListenerOrEventListenerObject | null) => {
      if (typeof listener !== "function") return;
      listeners[type] = (listeners[type] || []).filter((item) => item !== listener);
    }),
  } as unknown as VisualViewport & { height: number };

  Object.defineProperty(window, "visualViewport", { configurable: true, value: viewport });
  return {
    setHeight(nextHeight: number) {
      viewport.height = nextHeight;
      (listeners.resize || []).forEach((listener) => listener(new Event("resize")));
    },
  };
}

function answerVisibleAssessment() {
  document.querySelectorAll("article.question-card").forEach((card) => {
    const option = card.querySelector<HTMLButtonElement>("button.option");
    if (option) fireEvent.click(option);
  });
}

function installStorageStub(name: "localStorage" | "sessionStorage") {
  if (window[name]) return;
  const store = new Map<string, string>();
  Object.defineProperty(window, name, {
    configurable: true,
    value: {
      get length() {
        return store.size;
      },
      clear: () => store.clear(),
      getItem: (key: string) => store.get(key) ?? null,
      key: (index: number) => Array.from(store.keys())[index] ?? null,
      removeItem: (key: string) => store.delete(key),
      setItem: (key: string, value: string) => store.set(key, String(value)),
    },
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
    artplayerInstances.length = 0;
    installStorageStub("sessionStorage");
    installStorageStub("localStorage");
    window.sessionStorage.clear();
    window.localStorage.clear();
    window.history.replaceState({}, "", "/");
    Object.defineProperty(window, "visualViewport", { configurable: true, value: undefined });
    Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });
    Object.defineProperty(window.HTMLMediaElement.prototype, "play", { value: vi.fn().mockResolvedValue(undefined), writable: true });
    Object.defineProperty(window.HTMLMediaElement.prototype, "pause", { value: vi.fn(), writable: true });
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
    apiMocks.getStudentAssessmentStatus.mockResolvedValue({
      has_completed_smart_baseline: true,
      has_open_assessment: false,
      open_session_id: null,
      open_assessment_mode: null,
      smart_baseline_prompt_dismissed: false,
    });
    apiMocks.dismissStudentSmartBaselinePrompt.mockResolvedValue({
      has_completed_smart_baseline: false,
      has_open_assessment: false,
      open_session_id: null,
      open_assessment_mode: null,
      smart_baseline_prompt_dismissed: true,
    });
    apiMocks.getStudentHomeVideoFeed.mockResolvedValue(homeVideoFeedResponse);
    apiMocks.getStudentLearningHome.mockResolvedValue(learningHome);
    apiMocks.getStudentLearningPage.mockResolvedValue(learningPage);
    apiMocks.getStudentChapterCatalog.mockResolvedValue(catalogChapter);
    apiMocks.getStudentCatalogNode.mockImplementation((nodeId: string) =>
      Promise.resolve(nodeId === "cat-dir-oxidation" ? catalogNestedDirectory : catalogDirectory),
    );
    apiMocks.getStudentCatalogPointDetail.mockResolvedValue(catalogPointDetail);
    apiMocks.getPreviewCatalogNode.mockImplementation((nodeId: string): Promise<CatalogPreviewNodeResponse> => {
      if (nodeId === "cat-point-halogen") {
        return Promise.resolve({ node_kind: "point", directory: null, point: catalogPointDetail, learning_page: null });
      }
      return Promise.resolve({
        node_kind: "directory",
        directory: nodeId === "cat-dir-oxidation" ? catalogNestedDirectory : catalogDirectory,
        point: null,
        learning_page: learningPage,
      });
    });
    apiMocks.getPreviewCatalogPointDetail.mockResolvedValue(catalogPointDetail);
    apiMocks.searchStudentVideoLibrary.mockResolvedValue(videoLibraryResponse);
    apiMocks.startStudentPosttest.mockResolvedValue(posttestResponse);
    apiMocks.submitStudentPosttest.mockResolvedValue({ status: "completed", report });
    apiMocks.startStudentSmartAssessment.mockResolvedValue(posttestResponse);
    apiMocks.startStudentPointAssessment.mockResolvedValue({ ...posttestResponse, assessment_mode: "point" });
    apiMocks.submitStudentSmartAssessment.mockResolvedValue({ status: "completed", report, assessment_report: assessmentReport });
    apiMocks.getStudentAssessmentReports.mockResolvedValue({ reports: [assessmentReport] });
    apiMocks.getStudentAssessmentReport.mockResolvedValue(assessmentReport);
    apiMocks.getStudentCustomAssessmentOptions.mockResolvedValue({
      settings: {
        enabled: true,
        question_count_options: [5, 10, 15, 20],
        default_question_count: 10,
        max_question_count: 20,
        max_questions_per_experiment: 3,
      },
      experiments: [
        {
          id: "EXP_19_1_01",
          code: "19-1-01",
          title: "Halogen displacement",
          parent_code: "19-1",
          parent_title: "Experiment 19-1 Halogens",
          question_count: 1,
        },
      ],
    });
    apiMocks.startStudentCustomAssessment.mockResolvedValue({ ...posttestResponse, assessment_mode: "custom" });
    apiMocks.generatePosttestAiSummary.mockResolvedValue({ text: "### Study summary\n\n- Review **halogens**.", source: "ai", mode: "test", cached: true });
    apiMocks.explainPosttestMistakes.mockResolvedValue({ text: "### Mistake explanation\n\n- $\\ce{Br2}$ is orange.", source: "ai", mode: "test", cached: true });
    apiMocks.streamStudentAssistantAsk.mockImplementation(async (_payload, onEvent) => {
      onEvent({ event: "delta", delta: "### Route answer\n\n- $\\ce{Cl2}$ oxidizes bromide." });
      onEvent({ event: "final", response: { source_count: 1, sources: [{ title: "Halogen evidence", chunk_id: "halogen" }] } });
    });
    apiMocks.submitStudentFeedback.mockResolvedValue({ id: "feedback-e2e", status: "open", attachment_count: 0 });
  });

  afterEach(() => cleanup());

  it("prompts first-time students to start a smart baseline assessment", async () => {
    apiMocks.getStudentAssessmentStatus
      .mockResolvedValueOnce({
        has_completed_smart_baseline: false,
        has_open_assessment: false,
        open_session_id: null,
        open_assessment_mode: null,
        smart_baseline_prompt_dismissed: false,
      })
      .mockResolvedValue({
        has_completed_smart_baseline: true,
        has_open_assessment: false,
        open_session_id: null,
        open_assessment_mode: null,
        smart_baseline_prompt_dismissed: false,
      });

    await renderAuthenticatedApp("/");

    expect(await screen.findByRole("dialog", { name: "先做一次智能测评" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "去测评" }));

    await waitFor(() => expect(apiMocks.startStudentSmartAssessment).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
  });

  it("lets students permanently dismiss the smart baseline prompt", async () => {
    apiMocks.getStudentAssessmentStatus.mockResolvedValue({
      has_completed_smart_baseline: false,
      has_open_assessment: false,
      open_session_id: null,
      open_assessment_mode: null,
      smart_baseline_prompt_dismissed: false,
    });

    await renderAuthenticatedApp("/");

    expect(await screen.findByRole("dialog", { name: "先做一次智能测评" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "不再提醒" }));

    await waitFor(() => expect(apiMocks.dismissStudentSmartBaselinePrompt).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "先做一次智能测评" })).not.toBeInTheDocument());
  });

  it("starts point-scoped assessment from a completed learning point", async () => {
    await renderAuthenticatedApp("/point/cat-point-halogen?from=chapter&chapterId=CH17");

    await waitFor(() => expect(apiMocks.getStudentCatalogPointDetail).toHaveBeenCalledWith("cat-point-halogen"));
    fireEvent.click(screen.getByRole("button", { name: "测一测" }));

    await waitFor(() => expect(apiMocks.startStudentPointAssessment).toHaveBeenCalledWith("cat-point-halogen"));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expect((await screen.findAllByRole("region", { name: "点位测评" })).length).toBeGreaterThan(0);
  });

  it("tells students when a point assessment entry continues an unfinished assessment", async () => {
    apiMocks.startStudentPointAssessment.mockResolvedValueOnce({ ...posttestResponse, assessment_mode: "smart" });

    await renderAuthenticatedApp("/point/cat-point-halogen?from=chapter&chapterId=CH17");

    fireEvent.click(screen.getByRole("button", { name: "测一测" }));

    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expect(await screen.findByText("你还有一轮未完成测评，已为你继续打开原测评。完成后再回到本点位测一测。")).toBeInTheDocument();
  });

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
    const ordinaryNavButtons = Array.from(nav.querySelectorAll('button:not([data-root="ai"])'));
    expect(ordinaryNavButtons.every((button) => button.classList.contains("student-bottom-nav-standard"))).toBe(true);
    const atomNavButton = nav.querySelector<HTMLButtonElement>('button[data-root="ai"]');
    expect(atomNavButton).toHaveClass("student-bottom-nav-primary");
    expect(atomNavButton).toHaveAttribute("aria-label", "Atom");
    expect(atomNavButton?.querySelector(".student-bottom-nav-icon svg")?.getAttribute("class")).toContain("lucide-atom");
    expect(atomNavButton?.querySelector(".student-bottom-nav-label")).toHaveTextContent("Atom");
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");

    await waitFor(() => expect(apiMocks.getStudentHomeVideoFeed).toHaveBeenCalledWith(16));
    expect(screen.getByRole("img", { name: "中山大学" })).toBeInTheDocument();
    expect(screen.queryByText("今天先看一个现象")).not.toBeInTheDocument();
    const homeTopicRail = screen.getByLabelText("实验视频推荐标签");
    expect(homeTopicRail).toHaveClass("home-video-topic-rail");
    expect(within(homeTopicRail).getByRole("button", { name: "推荐" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(within(homeTopicRail).getByRole("button", { name: "最新" }));
    expect(within(homeTopicRail).getByRole("button", { name: "推荐" })).toHaveAttribute("aria-pressed", "false");
    expect(within(homeTopicRail).getByRole("button", { name: "最新" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Orange layer observation")).toBeInTheDocument();
    const homeVideoActions = screen.getByLabelText("视频操作：Orange layer observation");
    expect(within(homeVideoActions).getByRole("button", { name: "查看实验：Orange layer observation" })).toHaveClass("home-video-open-action");
    expect(within(homeVideoActions).getByRole("button", { name: "点赞：Orange layer observation" })).toHaveAttribute("aria-pressed", "false");
    expect(within(homeVideoActions).getByRole("button", { name: "收藏：Orange layer observation" })).toHaveAttribute("aria-pressed", "false");
    expect(within(homeVideoActions).getByRole("button", { name: "转发实验视频：Orange layer observation" })).toBeInTheDocument();
    expect(within(homeVideoActions).getByRole("button", { name: "更多操作：Orange layer observation" })).toBeInTheDocument();
    expect(within(homeVideoActions).queryByRole("button", { name: "搜索相关" })).not.toBeInTheDocument();
    const homeAtomAction = within(homeVideoActions).getByRole("button", { name: "问问Atom：Orange layer observation" });
    expect(homeAtomAction).toHaveClass("atom");
    expect(homeAtomAction.querySelector("svg")?.getAttribute("class")).toContain("lucide-atom");
    fireEvent.click(homeAtomAction);
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");
    fireEvent.click(screen.getByRole("button", { name: "搜索实验视频" }));
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenCalledWith(""));
    expect(screen.getByRole("search")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("推荐视频")).toBeInTheDocument());
    const videoLibraryRecommendations = screen.getByLabelText("推荐视频");
    expect(within(videoLibraryRecommendations).getByText("Orange layer observation")).toBeInTheDocument();
    expect(within(videoLibraryRecommendations).getByText("Halogen displacement catalog / Orange layer observation")).toBeInTheDocument();
    const recommendedChapterTag = videoLibraryRecommendations.querySelector(".video-library-row-chapter-tag");
    expect(recommendedChapterTag).toHaveTextContent("Group 17 Halogens");
    expect(within(videoLibraryRecommendations).queryByText("Textbook chapter 13")).not.toBeInTheDocument();
    expect(within(videoLibraryRecommendations).queryByText("Chlorine water + KBr + CCl4")).not.toBeInTheDocument();
    expect(videoLibraryRecommendations.querySelector(".video-library-row-badges")).toBeNull();
    expect(videoLibraryRecommendations.querySelector(".video-library-row-cover img")?.getAttribute("src")).toContain(
      "/api/student/media/assets/media-halogen/thumbnail",
    );
    expect(screen.getByLabelText("推荐搜索")).toBeInTheDocument();
    expect(screen.queryByText("常见实验线索")).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("搜索实验视频库"), { target: { value: "orange" } });
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenLastCalledWith("orange"));
    await waitFor(() => expect(screen.getByText("关于“orange”的实验视频")).toBeInTheDocument());
    await waitFor(() =>
      expect(document.querySelector(".video-library-results .video-library-search-video-row .video-library-row-chapter-tag")).toHaveTextContent(
        "Group 17 Halogens",
      ),
    );
    expect(document.querySelector(".video-library-results .video-library-search-video-row.has-cover .video-library-row-cover img")).not.toBeNull();
    expect(window.localStorage.getItem("student.videoLibrarySearch.history.v1")).toBeNull();
    fireEvent.click(document.querySelector<HTMLButtonElement>(".video-library-results .video-library-search-video-row")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expect(JSON.parse(window.localStorage.getItem("student.videoLibrarySearch.history.v1") || "[]")).toEqual(["orange"]);
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/home"));
    expect(activeRoot()).toBe("home");
    fireEvent.click(screen.getByRole("button", { name: "查看实验视频：Orange layer observation" }));
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/home"));

    await clickRoot("learn");
    expect(document.querySelector(".periodic-grid")).not.toBeNull();
    expect(screen.getByText("元素周期表")).toBeInTheDocument();
    expect(screen.getByText("选择元素分区")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "搜索元素" })).toBeInTheDocument();
    expect(document.querySelector(".periodic-search svg")?.getAttribute("class")).toContain("lucide-search");
    expect(document.querySelector(".periodic-search svg")?.getAttribute("class")).not.toContain("lucide-atom");
    expect(document.querySelector(".learning-recommendation-card")).toBeNull();
    expect(document.querySelector(".chapter-entry-card")).toBeNull();
    fireEvent.click(document.querySelector<HTMLButtonElement>(".element-cell[title^='Cl ']")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("Cl");
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");
    const elementSearch = await screen.findByRole("textbox", { name: "搜索元素" });
    fireEvent.change(elementSearch, { target: { value: "钾" } });
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/alkali-alkaline-earth"));
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("K");
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    fireEvent.change(await screen.findByRole("textbox", { name: "搜索元素" }), { target: { value: "不存在元素" } });
    expect(await screen.findByText("不存在该元素")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/learn");
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
    expect(screen.queryByRole("searchbox", { name: "查找本章目录内容" })).not.toBeInTheDocument();
    expect(screen.getByText("Experiment focus: oxidizes bromide")).toBeInTheDocument();
    expect(screen.getByText("Links directly to the halogen displacement video.")).toBeInTheDocument();
    expect(screen.queryByText("Chlorine在Halogens中的位置")).not.toBeInTheDocument();
    expect(document.querySelector(".atom-model-card")).toBeNull();
    expect(document.querySelector(".chapter-view-switcher")).toBeNull();
    expect(document.querySelector(".family-common-panel")).toBeNull();
    expect(document.querySelector(".property-section-panel")).toBeNull();
    expect(document.querySelector(".finish-action")).toBeNull();
    expect(screen.queryByRole("button", { name: "选章节" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "问问Atom" })).not.toBeInTheDocument();
    await waitFor(() => expect(document.querySelector(".catalog-node-card")).not.toBeNull());
    const catalogHeader = document.querySelector(".family-catalog-browser-head");
    expect(catalogHeader).not.toBeNull();
    expect(catalogHeader).not.toHaveTextContent("章节学习目录");
    expect(catalogHeader).not.toHaveTextContent("章节学习目录下");
    expect(document.querySelector(".family-catalog-up-action")).toBeNull();
    expect(document.querySelector(".family-catalog-root-path")).toHaveTextContent("17族（Group 17 Halogens）");
    expect(document.querySelector(".family-catalog-breadcrumbs")).toBeNull();
    expect(document.querySelector(".catalog-end-marker")).toHaveTextContent("当前共1目录");
    expect(document.querySelector(".family-catalog-crumb.is-active")).toHaveTextContent("17族（Group 17 Halogens）");

    fireEvent.click(screen.getByRole("button", { name: "搜索" }));
    await waitFor(() => expect(window.location.pathname).toBe("/search"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    expect(new URLSearchParams(window.location.search).get("chapterId")).toBe("CH17");
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("Cl");
    expect(screen.getByRole("searchbox")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("推荐内容")).toBeInTheDocument());
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "Orange" } });
    await waitFor(() => expect(screen.getByText("关于“Orange”的知识点位")).toBeInTheDocument());
    expect(screen.queryByText("实验视频")).not.toBeInTheDocument();
    expect(screen.queryByText("目录结果")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Orange layer observation")).toBeInTheDocument());
    expect(screen.getByText("Oxidation experiments")).toBeInTheDocument();
    const searchResultSections = Array.from(document.querySelectorAll<HTMLElement>(".video-library-results .video-library-result-section"));
    expect(searchResultSections).toHaveLength(1);
    expect(searchResultSections[0]).toHaveAttribute("aria-label", "知识点位结果");
    expect(searchResultSections[0].querySelector(".video-library-directory-row")).not.toBeNull();
    expect(searchResultSections[0].querySelector(".video-library-search-video-row")).not.toBeNull();
    fireEvent.click(screen.getByText("Oxidation experiments").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/catalog/cat-dir-oxidation"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/search"));
    fireEvent.click(screen.getByText("Orange layer observation").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("Cl");
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/search"));
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();

    fireEvent.click(document.querySelector<HTMLButtonElement>(".chapter-element-detail-action")!);
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17/element/Cl"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".atom-model-card")).not.toBeNull());
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/chapter/halogens-17"));
    expectBottomNavHidden();
    expect(screen.queryByRole("button", { name: "问问Atom" })).not.toBeInTheDocument();

    await waitFor(() => expect(document.querySelector(".catalog-node-card-main")).not.toBeNull());
    const familyCatalogPath = window.location.pathname;
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-halogen"));
    expect(window.location.pathname).toBe(familyCatalogPath);
    await waitFor(() => expect(document.querySelector(".family-catalog-shell")).not.toBeNull());
    expect(document.querySelector(".family-detail-frame")).not.toBeNull();
    expect(document.querySelector(".family-catalog-up-action")).toBeNull();
    expect(document.querySelector(".family-catalog-root-path")).toHaveTextContent("17族（Group 17 Halogens）");
    expect(document.querySelector(".family-catalog-breadcrumbs")).toHaveTextContent("Halogen displacement catalog");
    expect(document.querySelector(".family-catalog-crumb.is-active")).toHaveTextContent("Halogen displacement catalog");
    fireEvent.click(document.querySelector<HTMLButtonElement>(".family-catalog-more-action")!);
    await waitFor(() => expect(document.querySelector(".family-catalog-more-sheet")).not.toBeNull());
    expect(document.querySelector(".family-catalog-more-head button")).toBeNull();
    fireEvent.pointerDown(document.querySelector<HTMLElement>(".family-catalog-more-backdrop")!);
    await waitFor(() => expect(document.querySelector(".family-catalog-more-sheet")).toBeNull());
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-directory")).not.toBeNull());
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-oxidation"));
    expect(window.location.pathname).toBe(familyCatalogPath);
    await waitFor(() => expect(document.querySelector(".family-catalog-shell")).not.toBeNull());
    expect(document.querySelector(".family-catalog-root-path")).toHaveTextContent("17族（Group 17 Halogens）");
    expect(document.querySelector(".family-catalog-breadcrumbs")).toHaveTextContent("Halogen displacement catalog");
    expect(document.querySelector(".family-catalog-crumb.is-active")).toHaveTextContent("Oxidation experiments");
    const halogenCrumb = Array.from(document.querySelectorAll<HTMLButtonElement>(".family-catalog-crumb")).find(
      (button) => button.textContent === "Halogen displacement catalog",
    );
    expect(halogenCrumb).toBeTruthy();
    fireEvent.click(halogenCrumb!);
    await waitFor(() => expect(document.querySelector(".family-catalog-crumb.is-active")).toHaveTextContent("Halogen displacement catalog"));
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-directory")).not.toBeNull());
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(document.querySelector(".family-catalog-crumb.is-active")).toHaveTextContent("Oxidation experiments"));
    await waitFor(() => expect(document.querySelector(".catalog-node-card.kind-point")).not.toBeNull());
    expect(document.querySelector(".catalog-end-marker")).toHaveTextContent("当前共1实验");
    fireEvent.click(document.querySelector<HTMLButtonElement>(".catalog-node-card-main")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));
    expect(new URLSearchParams(window.location.search).get("profileId")).toBe("halogens-17");
    expect(new URLSearchParams(window.location.search).get("elementSymbol")).toBe("Cl");
    expectBottomNavHidden();

    fireEvent.click(screen.getByRole("button", { name: "问问Atom" }));
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-halogen"));

    fireEvent.click(screen.getByRole("button", { name: "测一测" }));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/session/posttest-session-e2e"));
    expectBottomNavHidden();
    await submitVisibleAssessment();
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/reports/assessment-report-e2e"));
    expectBottomNavHidden();
    await waitFor(() => expect(apiMocks.getStudentAssessmentReport).toHaveBeenCalledWith("assessment-report-e2e"));
    await waitFor(() => expect(document.querySelector(".summary-ai-text ul.ai-md-list")).not.toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "问问Atom" }));
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/reports/assessment-report-e2e"));

    fireEvent.click(screen.getByRole("button", { name: "继续学习" }));
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");

    await clickRoot("profile");
    fireEvent.click(screen.getByRole("button", { name: /测评报告/ }));
    await waitFor(() => expect(window.location.pathname).toBe("/profile/reports"));
    await waitFor(() => expect(apiMocks.getStudentAssessmentReports).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: /智能测评报告/ }));
    await waitFor(() => expect(window.location.pathname).toBe("/assessment/reports/assessment-report-e2e"));
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/profile/reports"));
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/profile"));
    expect(screen.queryByRole("form", { name: "学生端反馈" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /提交反馈/ }));
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

  it("renders playable point videos with custom mobile shell, title below, and active in-player back", async () => {
    apiMocks.getStudentCatalogPointDetail.mockResolvedValueOnce(catalogPointDetailWithVideo);

    await renderAuthenticatedApp("/point/cat-point-halogen?from=learn&pointTitle=Long%20fallback");

    await waitFor(() => expect(artplayerInstances).toHaveLength(1));
    expect(document.querySelector(".catalog-point-detail > .pagebar")).toBeNull();
    expect(document.querySelector(".video-stage")).toBeNull();

    const player = document.querySelector(".point-art-player");
    const summary = document.querySelector(".catalog-point-summary");
    expect(player).not.toBeNull();
    expect(summary).not.toBeNull();
    expect(document.querySelector(".catalog-point-detail > :first-child")).toBe(player);
    expect(document.querySelector(".catalog-point-detail > .point-art-player + .catalog-point-summary")).toBe(summary);
    expect(summary).not.toHaveClass("experiment-detail-card");
    expect(document.querySelector(".catalog-point-detail > .experiment-detail-card")).toBeNull();
    expect(player!.compareDocumentPosition(summary!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText(catalogPointDetailWithVideo.title)).toBeInTheDocument();
    expect(screen.getByText((content) => content.includes("Halogen displacement catalog"))).toBeInTheDocument();

    const instance = artplayerInstances[0];
    expect(instance.option.url).toBe("/media/halogen.mp4");
    expect(instance.option.poster).toBe("/media/halogen.jpg");
    expect(instance.option.playsInline).toBe(true);
    expect(instance.option.autoplay).toBe(true);
    expect(instance.option.muted).toBe(true);
    expect(instance.option.miniProgressBar).toBe(false);
    expect(instance.option.setting).toBe(false);
    expect(instance.option.fullscreen).toBe(false);
    expect(instance.option.fullscreenWeb).toBe(false);
    expect(instance.option.lock).toBe(false);
    expect(instance.option.playbackRate).toBe(false);
    expect(instance.option.controls).toBeUndefined();
    expect(instance.option.layers).toBeUndefined();
    expect(instance.option.moreVideoAttr?.controls).toBe(false);
    expect(instance.option.moreVideoAttr?.playsInline).toBe(true);
    expect(instance.video.controls).toBe(false);

    const shell = document.querySelector<HTMLDivElement>(".point-youtube-shell");
    expect(shell).not.toBeNull();
    expect(shell).not.toHaveClass("point-youtube-shell-active");
    expect(document.querySelector(".point-youtube-inactive-progress")).not.toBeNull();
    expect(document.querySelector(".point-youtube-progress-thumb")).not.toBeNull();
    expect(document.querySelector(".point-player-back-layer")).toBeNull();
    expect(document.querySelector(".point-player-time-capsule")).toBeNull();
    expect(document.querySelector(".point-art-player .art-video-player.art-mini-progress-bar")).toBeNull();

    Object.defineProperty(instance.video, "duration", { configurable: true, value: 713 });
    instance.video.currentTime = 34;
    act(() => instance.emit("video:durationchange", new Event("durationchange")));
    expect(document.querySelector(".point-youtube-time-capsule")).toHaveTextContent("0:34 / 11:53");

    act(() => instance.emit("ready"));
    await waitFor(() => expect(instance.play).toHaveBeenCalled());
    await waitFor(() => expect(document.querySelector(".point-youtube-play")).toHaveAttribute("aria-label", "暂停"));

    const toggleButton = document.querySelector<HTMLButtonElement>(".point-youtube-play");
    expect(toggleButton).not.toBeNull();
    vi.useFakeTimers();
    try {
      fireEvent.pointerDown(shell!);
      expect(shell).toHaveClass("point-youtube-shell-active");
      act(() => vi.advanceTimersByTime(2800));
      expect(shell).not.toHaveClass("point-youtube-shell-active");

      fireEvent.pointerDown(shell!);
      expect(shell).toHaveClass("point-youtube-shell-active");
      fireEvent.click(toggleButton!);
      expect(instance.pause).toHaveBeenCalled();
      expect(toggleButton).toHaveAttribute("aria-label", "播放");
      act(() => vi.advanceTimersByTime(4000));
      expect(shell).toHaveClass("point-youtube-shell-active");
    } finally {
      vi.useRealTimers();
    }

    const fullscreenButton = document.querySelector<HTMLButtonElement>(".point-youtube-fullscreen");
    expect(fullscreenButton).not.toBeNull();
    fireEvent.click(fullscreenButton!);
    expect(instance.fullscreenWeb).toBe(true);

    Object.defineProperty(instance.video, "duration", { configurable: true, value: 100 });
    act(() => instance.emit("video:durationchange", new Event("durationchange")));
    const progressHit = document.querySelector<HTMLDivElement>(".point-youtube-progress-hit");
    expect(progressHit).not.toBeNull();
    progressHit!.getBoundingClientRect = () =>
      ({ left: 0, width: 200, top: 0, right: 200, bottom: 30, height: 30, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect;
    fireEvent.pointerDown(progressHit!, { pointerId: 12, clientX: 100 });
    expect(instance.seek).toBe(50);

    const backLayer = document.querySelector<HTMLButtonElement>(".point-youtube-back");
    expect(backLayer).not.toBeNull();
    expect(backLayer!.querySelector(".point-player-back-icon")).not.toBeNull();
    expect(backLayer!.querySelector(".student-back-arrow-icon")).not.toBeNull();
    expect(backLayer!.querySelector(".point-player-back-glyph")).toBeNull();
    fireEvent.click(backLayer!);
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
  });

  it("renders structured point detail content, related links, and the fixed test handoff", async () => {
    await renderAuthenticatedApp("/point/cat-point-halogen?from=chapter&chapterId=CH17&pointTitle=Orange%20layer%20observation");

    await waitFor(() => expect(apiMocks.getStudentCatalogPointDetail).toHaveBeenCalledWith("cat-point-halogen"));
    expect(document.querySelector(".catalog-point-detail > .pagebar")).toBeNull();
    expect(document.querySelector(".point-art-player-empty")).not.toBeNull();
    expect(document.querySelector(".catalog-point-detail > :first-child")).toHaveClass("point-art-player-empty");
    expect(document.querySelector(".catalog-point-summary")).not.toHaveClass("experiment-detail-card");
    expect(screen.getByText("暂无可播放视频")).toBeInTheDocument();
    expect(screen.getByText("实验原理")).toBeInTheDocument();
    expect(screen.getByText("暂无可播放视频")).toBeInTheDocument();
    expect(screen.getByText("实验原理")).toBeInTheDocument();
    expect(document.querySelector(".point-equation-list .point-chem-equation .katex")).not.toBeNull();
    expect(document.querySelector(".point-equation-list .point-chem-equation .katex-display")).toBeNull();
    expect(document.querySelector(".point-equation-list .point-chem-equation")).toHaveClass("chem-equation-inline");
    expect(document.querySelector(".point-equation-list .chem-equation-fallback")).toBeNull();
    expect(document.querySelector(".point-equation-note")?.textContent).toContain("organic layer observation");
    expect(document.querySelector(".point-equation-note .chem-equation-inline .katex")).toBeNull();
    expect(screen.getByText("现象解释")).toBeInTheDocument();
    expect(screen.getByText("安全提示")).toBeInTheDocument();
    expect(screen.getByText("现象解释")).toBeInTheDocument();
    expect(screen.getByText("安全提示")).toBeInTheDocument();
    expect(screen.queryByText("Halogen evidence")).not.toBeInTheDocument();
    const summary = document.querySelector(".catalog-point-summary");
    const titleActions = document.querySelector(".point-title-actions");
    const phenomenon = document.querySelector(".phenomenon-section");
    const principle = document.querySelector(".principle-section");
    const safety = document.querySelector(".safety-section");
    const related = document.querySelector(".related-point-section");
    expect(summary).not.toBeNull();
    expect(titleActions).not.toBeNull();
    expect(phenomenon).not.toBeNull();
    expect(principle).not.toBeNull();
    expect(safety).not.toBeNull();
    expect(related).not.toBeNull();
    expect(document.querySelector(".point-detail-actions")).toBeNull();
    expect(summary!.compareDocumentPosition(titleActions!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(titleActions!.compareDocumentPosition(phenomenon!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(phenomenon!.compareDocumentPosition(principle!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(principle!.compareDocumentPosition(safety!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(safety!.compareDocumentPosition(related!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(document.querySelector(".related-point-thumb")).not.toBeNull();
    expect(document.querySelector(".related-point-copy")).not.toBeNull();
    expect(document.querySelector(".point-equation-index")).not.toBeNull();
    expect(screen.queryByText((content) => content.includes("补充说明："))).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Iodine comparison").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/point/cat-point-iodine"));

    fireEvent.click(screen.getByRole("button", { name: "测一测" }));
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
    expect(screen.queryByText("带着这个点位问问Atom")).not.toBeInTheDocument();
    expect(document.querySelector(".finish-action")).toBeNull();
    expect(apiMocks.submitStudentPosttest).not.toHaveBeenCalled();
    expect(apiMocks.submitStudentSmartAssessment).not.toHaveBeenCalled();
    expect(apiMocks.submitStudentFeedback).not.toHaveBeenCalled();
  });

  it("renders teacher preview directory nodes and navigates within the preview token scope", async () => {
    window.history.replaceState({}, "", "/preview/catalog/nodes/cat-dir-halogen?preview_token=teacher-preview-token");
    render(<App />);

    await waitFor(() => expect(apiMocks.getPreviewCatalogNode).toHaveBeenCalledWith("cat-dir-halogen", "teacher-preview-token"));
    expect(apiMocks.loadCurrentUser).not.toHaveBeenCalled();
    expect(apiMocks.getStudentLearningPage).not.toHaveBeenCalled();
    expect(apiMocks.getStudentChapterCatalog).not.toHaveBeenCalled();
    expect(apiMocks.getStudentCatalogNode).not.toHaveBeenCalled();
    expect(document.querySelector(".student-app-shell")).toBeNull();
    expect(document.querySelector(".family-catalog-shell")).not.toBeNull();
    expect(document.querySelector(".preview-catalog-directory")).toBeNull();
    expect(document.querySelector(".catalog-directory-panel")).toBeNull();
    expect(await screen.findByText("Oxidation experiments")).toBeInTheDocument();
    expect(screen.getAllByText("Halogen displacement catalog").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByText("Oxidation experiments").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/preview/catalog/nodes/cat-dir-oxidation"));
    await waitFor(() => expect(apiMocks.getPreviewCatalogNode).toHaveBeenCalledWith("cat-dir-oxidation", "teacher-preview-token"));
    expect(screen.getByText("Orange layer observation")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Orange layer observation").closest("button")!);
    await waitFor(() => expect(window.location.pathname).toBe("/preview/catalog/nodes/cat-point-halogen"));
    await waitFor(() => expect(apiMocks.getPreviewCatalogNode).toHaveBeenCalledWith("cat-point-halogen", "teacher-preview-token"));
    expect(document.querySelector(".catalog-point-detail")).not.toBeNull();
    expect(screen.queryByText("蠑蟋狗ｻ・ｹ")).not.toBeInTheDocument();

    fireEvent.click(document.querySelector(".point-player-empty-back") as HTMLButtonElement);
    await waitFor(() => expect(window.location.pathname).toBe("/preview/catalog/nodes/cat-dir-oxidation"));
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

  it("renders video-library search history as committed rows without category cards", async () => {
    window.localStorage.setItem("student.videoLibrarySearch.history.v1", JSON.stringify(["CCl4"]));

    await renderAuthenticatedApp("/video-library");

    await waitFor(() => expect(window.location.pathname).toBe("/video-library"));
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenCalledWith(""));
    await waitFor(() => expect(apiMocks.getStudentHomeVideoFeed).toHaveBeenCalledWith(6));

    const historySection = screen.getByLabelText("搜索历史");
    expect(within(historySection).getByRole("button", { name: /CCl4/ })).toBeInTheDocument();
    expect(screen.getByLabelText("推荐视频")).toBeInTheDocument();
    expect(screen.queryByText("常见实验线索")).not.toBeInTheDocument();

    fireEvent.click(within(historySection).getByRole("button", { name: /CCl4/ }));

    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenLastCalledWith("CCl4"));
    expect(JSON.parse(window.localStorage.getItem("student.videoLibrarySearch.history.v1") || "[]")).toEqual(["CCl4"]);
  });

  it("renders a plain empty message for empty video search results", async () => {
    apiMocks.searchStudentVideoLibrary.mockImplementation((query = "") =>
      Promise.resolve(query ? { ...emptyVideoLibraryResponse, query } : videoLibraryResponse),
    );

    await renderAuthenticatedApp("/video-library?q=zzz");

    await waitFor(() => expect(screen.getByText("关于“zzz”的实验视频")).toBeInTheDocument());
    expect(screen.getByText("这里什么都没有哦👀")).toBeInTheDocument();
    expect(document.querySelector(".video-library-banner")).toBeNull();
    expect(document.querySelector(".video-library-results .empty-learning-card")).toBeNull();
  });

  it("renders root Atom running turns as a flat thinking line with phase transitions", async () => {
    let emitStreamEvent: ((event: { event: string; message?: string; delta?: string; response?: unknown }) => void) | undefined;
    let finishResponse: (() => void) | undefined;
    apiMocks.streamStudentAssistantAsk.mockReset();
    apiMocks.streamStudentAssistantAsk.mockImplementationOnce(async (_payload, onEvent) => {
      emitStreamEvent = onEvent;
      onEvent({ event: "status", message: "正在判断问题类型与安全策略" });
      await new Promise<void>((resolve) => {
        finishResponse = resolve;
      });
      onEvent({
        event: "final",
        response: {
          source_count: 1,
          suggested_prompts: ["继续观察什么现象？"],
        },
      });
    });

    await renderAuthenticatedApp("/ai");

    fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
      target: { value: "为什么出现橙色有机层？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发送问题" }));
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("status", { name: "正在判断问题范围" })).toBeInTheDocument());

    const runningMessage = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-message.assistant.running");
    expect(runningMessage).not.toBeNull();
    expect(runningMessage?.querySelector(".ai-thinking-line")).not.toBeNull();
    const atomMark = runningMessage?.querySelector(".ai-thinking-atom-mark");
    expect(atomMark?.getAttribute("aria-hidden")).toBe("true");
    expect(atomMark?.getAttribute("data-motion")).toBe("looping");
    expect(atomMark?.querySelector(".ai-thinking-lottie")).not.toBeNull();
    expect(runningMessage?.querySelector(".ai-message-meta")).toBeNull();
    expect(runningMessage?.querySelector(".ai-message-actions")).toBeNull();
    expect(runningMessage?.querySelector(".ai-source-summary")).toBeNull();
    expect(runningMessage?.querySelector(".ai-message-skeleton")).toBeNull();
    expect(screen.queryByRole("button", { name: "继续观察什么现象？" })).not.toBeInTheDocument();
    expect(screen.queryByText("正在判断问题类型与安全策略")).not.toBeInTheDocument();

    act(() => {
      emitStreamEvent?.({ event: "status", message: "正在检索课程证据" });
    });
    await waitFor(() => expect(screen.getByRole("status", { name: "正在检索课程资料" })).toBeInTheDocument(), { timeout: 2000 });
    await waitFor(() => {
      expect(runningMessage?.querySelector(".ai-thinking-text.outgoing")).toHaveTextContent("正在判断问题范围");
      expect(runningMessage?.querySelector(".ai-thinking-text.current.incoming")).toHaveTextContent("正在检索课程资料");
    });
    expect(document.querySelectorAll(".ai-chat-panel.root .ai-thinking-line[role='status']")).toHaveLength(1);

    act(() => {
      emitStreamEvent?.({ event: "delta", delta: "### Streaming answer\n\n- The organic layer contains bromine." });
    });
    await waitFor(() => expect(screen.getByRole("status", { name: "正在输出回答" })).toBeInTheDocument(), { timeout: 2000 });
    await waitFor(() => {
      expect(runningMessage?.querySelector(".ai-thinking-text.outgoing")).toHaveTextContent("正在检索课程资料");
      expect(runningMessage?.querySelector(".ai-thinking-text.current.incoming")).toHaveTextContent("正在输出回答");
    });
    await waitFor(() => expect(screen.getByText("Streaming answer")).toBeInTheDocument());

    await act(async () => {
      finishResponse?.();
    });
    await waitFor(() => expect(screen.getByText("Streaming answer")).toBeInTheDocument());
    const completedMessage = Array.from(document.querySelectorAll<HTMLElement>(".ai-chat-panel.root .ai-message.assistant.done")).find((node) =>
      node.textContent?.includes("Streaming answer"),
    );
    expect(completedMessage).not.toBeNull();
    expect(completedMessage?.querySelector(".ai-thinking-line")).toBeNull();
    expect(completedMessage?.querySelector(".ai-message-actions")).not.toBeNull();
    expect(completedMessage?.querySelector(".ai-message-citation")).toHaveTextContent("1");
    expect(screen.getByRole("button", { name: "继续观察什么现象？" })).toBeInTheDocument();
  });

  it("prioritizes visible thinking stream events without copying them into the answer", async () => {
    let emitStreamEvent:
      | ((event: { event: string; message?: string; source?: "reasoning_summary" | "agent_trace"; phase?: string; sequence?: number; delta?: string; response?: unknown }) => void)
      | undefined;
    let finishResponse: (() => void) | undefined;
    apiMocks.streamStudentAssistantAsk.mockReset();
    apiMocks.streamStudentAssistantAsk.mockImplementationOnce(async (_payload, onEvent) => {
      emitStreamEvent = onEvent;
      onEvent({ event: "status", message: "正在判断问题类型与安全策略" });
      onEvent({ event: "thinking", source: "reasoning_summary", phase: "reasoning", sequence: 7, message: "正在分析实验现象" });
      await new Promise<void>((resolve) => {
        finishResponse = resolve;
      });
      onEvent({
        event: "final",
        response: {
          source_count: 0,
          suggested_prompts: [],
        },
      });
    });

    await renderAuthenticatedApp("/ai");

    fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
      target: { value: "请解释氧化还原实验现象" },
    });
    fireEvent.click(document.querySelector<HTMLButtonElement>(".ai-chat-panel.root .ai-send-action")!);
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("status", { name: "正在分析实验现象" })).toBeInTheDocument());
    expect(screen.queryByRole("status", { name: "正在判断问题范围" })).not.toBeInTheDocument();

    act(() => {
      emitStreamEvent?.({ event: "delta", delta: "### Visible answer\n\n- Bromine makes the organic layer orange." });
    });
    await waitFor(() => expect(screen.getByText("Visible answer")).toBeInTheDocument());
    expect(screen.getByRole("status", { name: "正在分析实验现象" })).toBeInTheDocument();

    await act(async () => {
      finishResponse?.();
    });
    await waitFor(() => expect(screen.getByText("Visible answer")).toBeInTheDocument());
    const completedMessage = Array.from(document.querySelectorAll<HTMLElement>(".ai-chat-panel.root .ai-message.assistant.done")).find((node) =>
      node.textContent?.includes("Visible answer"),
    );
    expect(completedMessage).not.toBeNull();
    expect(completedMessage?.querySelector(".ai-thinking-line")).toBeNull();
    expect(completedMessage?.textContent).not.toContain("正在分析实验现象");

    const copyButton = completedMessage?.querySelector<HTMLButtonElement>('button[aria-label="Copy Atom answer"]');
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    fireEvent.click(copyButton!);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("### Visible answer\n\n- Bromine makes the organic layer orange."));
  });

  it("keeps root Atom thinking status meaningful with reduced motion", async () => {
    const originalMatchMedia = window.matchMedia;
    const reducedMotionMedia = {
      matches: true,
      media: "(prefers-reduced-motion: reduce)",
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
    Object.defineProperty(window, "matchMedia", { configurable: true, value: vi.fn().mockReturnValue(reducedMotionMedia) });

    let finishResponse: (() => void) | undefined;
    apiMocks.streamStudentAssistantAsk.mockReset();
    apiMocks.streamStudentAssistantAsk.mockImplementationOnce(async (_payload, onEvent) => {
      onEvent({ event: "status", message: "正在判断问题类型与安全策略" });
      await new Promise<void>((resolve) => {
        finishResponse = resolve;
      });
      onEvent({ event: "final", response: { source_count: 0, suggested_prompts: [] } });
    });

    try {
      await renderAuthenticatedApp("/ai");

      fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
        target: { value: "先判断我的问题范围" },
      });
      fireEvent.click(screen.getByRole("button", { name: "发送问题" }));

      await waitFor(() => expect(screen.getByRole("status", { name: "正在判断问题范围" })).toBeInTheDocument());
      const atomMark = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-thinking-atom-mark");
      expect(atomMark).not.toBeNull();
      expect(atomMark?.getAttribute("aria-hidden")).toBe("true");
      expect(atomMark?.getAttribute("data-motion")).toBe("reduced");
      expect(atomMark?.querySelector(".ai-thinking-atom-static")).not.toBeNull();
      expect(atomMark?.querySelector(".ai-thinking-lottie")).toBeNull();

      await act(async () => {
        finishResponse?.();
      });
    } finally {
      cleanup();
      Object.defineProperty(window, "matchMedia", { configurable: true, value: originalMatchMedia });
    }
  });

  it("keeps the Atom thinking mark stable across common phone widths", async () => {
    const viewports = [
      { width: 360, height: 780 },
      { width: 390, height: 844 },
      { width: 430, height: 932 },
    ];

    for (const viewport of viewports) {
      cleanup();
      Object.defineProperty(window, "innerWidth", { configurable: true, value: viewport.width });
      Object.defineProperty(window, "innerHeight", { configurable: true, value: viewport.height });
      window.dispatchEvent(new Event("resize"));
      window.localStorage.clear();
      window.sessionStorage.clear();
      window.history.replaceState({}, "", "/");

      let finishResponse: (() => void) | undefined;
      apiMocks.streamStudentAssistantAsk.mockReset();
      apiMocks.streamStudentAssistantAsk.mockImplementationOnce(async (_payload, onEvent) => {
        onEvent({ event: "status", message: "正在检索课程证据" });
        await new Promise<void>((resolve) => {
          finishResponse = resolve;
        });
        onEvent({ event: "final", response: { source_count: 0, suggested_prompts: [] } });
      });

      await renderAuthenticatedApp("/ai");
      fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
        target: { value: `检查 ${viewport.width}px 下的思考状态` },
      });
      fireEvent.click(screen.getByRole("button", { name: "发送问题" }));

      await waitFor(() => expect(screen.getByRole("status", { name: "正在检索课程资料" })).toBeInTheDocument());
      const thinkingLine = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-thinking-line");
      const atomMark = thinkingLine?.querySelector<HTMLElement>(".ai-thinking-atom-mark");
      expect(thinkingLine).not.toBeNull();
      expect(atomMark).not.toBeNull();
      expect(atomMark?.getAttribute("aria-hidden")).toBe("true");
      expect(thinkingLine?.querySelector(".ai-thinking-text.current")).toHaveTextContent("正在检索课程资料");

      await act(async () => {
        finishResponse?.();
      });
    }
  });

  it("renders the AI root as direct chat and restores local history for follow-up turns", async () => {
    let finishSecondResponse: (() => void) | undefined;
    apiMocks.streamStudentAssistantAsk.mockReset();
    apiMocks.streamStudentAssistantAsk
      .mockImplementationOnce(async (_payload, onEvent) => {
        onEvent({ event: "delta", delta: "### Route answer\n\n- $\\ce{Cl2}$ oxidizes bromide." });
        onEvent({
          event: "final",
          response: {
            source_count: 1,
            sources: [{ title: "Halogen evidence", chunk_id: "halogen" }],
            suggested_prompts: ["继续观察什么现象？", "相关反应式是什么？"],
          },
        });
      })
      .mockImplementationOnce(async (_payload, onEvent) => {
        onEvent({ event: "delta", delta: "### Follow-up answer\n\n- Oxidation relates to electron loss." });
        await new Promise<void>((resolve) => {
          finishSecondResponse = resolve;
        });
        onEvent({
          event: "final",
          response: {
            source_count: 1,
            sources: [{ title: "Oxidation evidence", chunk_id: "oxidation" }],
            suggested_prompts: ["怎样判断氧化剂？"],
          },
        });
      })
      .mockImplementationOnce(async (_payload, onEvent) => {
        onEvent({ event: "error", message: "Cannot read properties of undefined (reading 'length')" });
      });

    await renderAuthenticatedApp("/ai");

    await waitFor(() => expect(window.location.pathname).toBe("/ai"));
    expect(activeRoot()).toBe("ai");
    expect(document.querySelector(".student-app-shell.root-route.root-ai")).not.toBeNull();
    expect(document.querySelector(".student-app-shell.root-ai > .student-app-header")).toBeNull();
    expect(document.querySelector(".student-app-shell.root-ai .student-route-content > .ai-root-page")).not.toBeNull();
    const rootPanel = document.querySelector<HTMLElement>(".ai-chat-panel.root");
    expect(rootPanel).not.toBeNull();
    expect(rootPanel).toHaveClass("is-empty");
    expect(rootPanel).toHaveClass("root-state-empty");
    expect(rootPanel).toHaveAttribute("data-root-layout", "empty");
    expect(rootPanel).toHaveAttribute("data-root-state", "empty");
    expect(document.querySelector(".ai-chat-panel.root .ai-root-star-shell")).toBeNull();
    const rootHeader = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-chat-head.root");
    expect(rootHeader).not.toBeNull();
    expect(rootHeader?.querySelector("h2")).toHaveTextContent("Atom");
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-empty.root")).toBeNull();
    expect(rootPanel).toHaveClass("is-empty");
    expect(rootPanel).toHaveClass("root-state-empty");
    expect(rootPanel).toHaveAttribute("data-root-layout", "empty");
    expect(rootPanel).toHaveAttribute("data-root-state", "empty");
    expect(screen.getByText("从一个实验开始吧！")).toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel.root .ai-root-welcome svg")?.getAttribute("class")).toContain("lucide-atom");
    const rootComposer = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-chat-compose.root");
    expect(rootComposer).not.toBeNull();
    expect(rootComposer).toHaveClass("is-compact");
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-compose-input textarea")).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-workbench")).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-context-action")).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-send-action")).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "向 Atom 提问" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("问实验现象、步骤或原理")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看 Atom 历史记录" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新建 Atom 对话" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "选择学习背景" })).toHaveAttribute("aria-pressed", "false");
    const rootActions = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-chat-head.root .ai-root-actions");
    expect(rootActions).not.toBeNull();
    expect(rootActions?.querySelectorAll(".ai-root-icon-action")).toHaveLength(2);
    expect(rootActions?.querySelector(".ai-history-action")).not.toBeNull();
    expect(rootActions?.querySelector(".ai-new-chat-action")).not.toBeNull();
    expect(document.querySelector(".ai-starter-surface")).toBeNull();
    expect(document.querySelector(".ai-starter-card")).toBeNull();
    expect(document.querySelector('.ai-chat-panel.root input[type="file"]')).toBeNull();
    expect(
      Array.from(document.querySelectorAll<HTMLButtonElement>(".ai-chat-panel.root button"))
        .map((button) => button.textContent || "")
        .join(" "),
    ).not.toMatch(/上传|附件|模型|语音|图片/);

    fireEvent.click(screen.getByRole("button", { name: "选择学习背景" }));
    expect(await screen.findByRole("dialog", { name: "选择学习背景" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "选择学习背景" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(document.querySelector<HTMLButtonElement>(".atom-context-picker-close")!);
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "选择学习背景" })).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "查看 Atom 历史记录" }));
    expect(await screen.findByRole("dialog", { name: "Atom 历史记录" })).toHaveTextContent("还没有历史记录");
    fireEvent.click(screen.getByRole("button", { name: "关闭 Atom 历史记录" }));

    fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
      target: { value: "为什么 CCl4 层会变橙色？" },
    });
    expect(screen.queryByText("从一个实验开始吧！")).not.toBeInTheDocument();
    expect(rootPanel).toHaveClass("has-draft");
    expect(rootPanel).toHaveClass("root-state-draft");
    expect(rootPanel).toHaveAttribute("data-root-layout", "draft");
    expect(rootPanel).toHaveAttribute("data-root-state", "draft");
    expect(document.querySelector(".ai-chat-stream.root-empty")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-stream.root-draft")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "发送问题" }));
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(1));
    expect(apiMocks.streamStudentAssistantAsk).toHaveBeenLastCalledWith(
      expect.objectContaining({
        question: "为什么 CCl4 层会变橙色？",
        context_type: "learning_home",
        conversation_history: [],
      }),
      expect.any(Function),
    );
    await waitFor(() => expect(screen.getByText("Route answer")).toBeInTheDocument());
    expect(rootPanel).toHaveClass("has-messages");
    expect(rootPanel).toHaveClass("root-state-conversation");
    expect(rootPanel).toHaveAttribute("data-root-layout", "conversation");
    expect(rootPanel).toHaveAttribute("data-root-state", "conversation");
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-stream.root-conversation")).not.toBeNull();
    const rootUserMessage = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-message.user");
    const routeAnswerMessage = Array.from(document.querySelectorAll<HTMLElement>(".ai-chat-panel.root .ai-message.assistant.done")).find((node) =>
      node.textContent?.includes("Route answer"),
    );
    expect(rootUserMessage).not.toBeNull();
    expect(rootUserMessage).toHaveClass("user");
    expect(routeAnswerMessage).not.toBeNull();
    expect(routeAnswerMessage).toHaveClass("assistant", "done");
    expect(routeAnswerMessage?.querySelector(".ai-message-meta")).toBeNull();
    expect(routeAnswerMessage?.querySelector(".ai-source-summary")).toBeNull();
    expect(routeAnswerMessage?.querySelector(".ai-message-actions")).not.toBeNull();
    expect(routeAnswerMessage?.querySelector(".ai-message-citation")).toHaveTextContent("1");
    expect(routeAnswerMessage?.textContent).not.toContain("Halogen evidence");
    expect(routeAnswerMessage?.textContent).not.toContain("halogen");
    const helpfulButton = routeAnswerMessage?.querySelector<HTMLButtonElement>('button[aria-label="Mark Atom answer helpful"]');
    const unhelpfulButton = routeAnswerMessage?.querySelector<HTMLButtonElement>('button[aria-label="Mark Atom answer unhelpful"]');
    const copyButton = routeAnswerMessage?.querySelector<HTMLButtonElement>('button[aria-label="Copy Atom answer"]');
    expect(helpfulButton).not.toBeNull();
    expect(unhelpfulButton).not.toBeNull();
    expect(copyButton).not.toBeNull();
    fireEvent.click(helpfulButton!);
    expect(helpfulButton).toHaveAttribute("aria-pressed", "true");
    expect(unhelpfulButton).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(unhelpfulButton!);
    expect(helpfulButton).toHaveAttribute("aria-pressed", "false");
    expect(unhelpfulButton).toHaveAttribute("aria-pressed", "true");
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    fireEvent.click(copyButton!);
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("### Route answer\n\n- $\\ce{Cl2}$ oxidizes bromide."));
    await waitFor(() => expect(routeAnswerMessage?.querySelector('button[aria-label="Atom answer copied"]')).not.toBeNull());
    expect(screen.getByRole("button", { name: "继续观察什么现象？" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "相关反应式是什么？" })).toBeInTheDocument();
    expect(screen.queryByText("我应该先复习哪一块？")).not.toBeInTheDocument();
    expect(screen.queryByText("从一个实验开始吧！")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "新建 Atom 对话" }));
    await waitFor(() => expect(screen.queryByText("Route answer")).not.toBeInTheDocument());
    expect(rootPanel).toHaveClass("is-empty");
    expect(rootPanel).toHaveClass("root-state-empty");
    expect(rootPanel).toHaveAttribute("data-root-layout", "empty");
    expect(rootPanel).toHaveAttribute("data-root-state", "empty");
    expect(screen.queryByRole("button", { name: "继续观察什么现象？" })).not.toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-empty.root")).toBeNull();
    expect(screen.getByText("从一个实验开始吧！")).toBeInTheDocument();

    cleanup();
    await renderAuthenticatedApp("/ai");
    fireEvent.click(screen.getByRole("button", { name: "查看 Atom 历史记录" }));
    await screen.findByRole("dialog", { name: "Atom 历史记录" });
    fireEvent.click(screen.getByText("为什么 CCl4 层会变橙色？").closest("button")!);
    await waitFor(() => expect(screen.getByText("Route answer")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "继续观察什么现象？" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "继续观察什么现象？" }));
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(2));
    expect(apiMocks.streamStudentAssistantAsk).toHaveBeenLastCalledWith(
      expect.objectContaining({
        question: "继续观察什么现象？",
        conversation_history: [
          { role: "user", content: "为什么 CCl4 层会变橙色？" },
          { role: "assistant", content: "### Route answer\n\n- $\\ce{Cl2}$ oxidizes bromide." },
        ],
      }),
      expect.any(Function),
    );
    expect(screen.queryByRole("button", { name: "继续观察什么现象？" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "相关反应式是什么？" })).not.toBeInTheDocument();
    await act(async () => {
      finishSecondResponse?.();
    });
    await waitFor(() => expect(screen.getByText("Follow-up answer")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "继续观察什么现象？" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "怎样判断氧化剂？" })).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
      target: { value: "触发失败" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发送问题" }));
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(3));
    await waitFor(() => expect(screen.getByText("Cannot read properties of undefined (reading 'length')")).toBeInTheDocument());
    const errorMessage = screen.getByText("Cannot read properties of undefined (reading 'length')").closest(".ai-message");
    expect(errorMessage).toHaveClass("assistant", "error");
    expect(errorMessage?.querySelector(".ai-message-actions")).toBeNull();
    expect(screen.queryByRole("button", { name: "怎样判断氧化剂？" })).not.toBeInTheDocument();
  });

  it("binds one Atom root chat to a selected learning point from catalog or search", async () => {
    apiMocks.streamStudentAssistantAsk.mockReset();
    apiMocks.streamStudentAssistantAsk.mockImplementation(async (_payload, onEvent) => {
      onEvent({ event: "delta", delta: "Point bound answer" });
      onEvent({ event: "final", response: { source_count: 1 } });
    });

    await renderAuthenticatedApp("/ai");

    fireEvent.click(screen.getByRole("button", { name: "选择学习背景" }));
    expect(await screen.findByRole("dialog", { name: "选择学习背景" })).toBeInTheDocument();
    const shell = document.querySelector<HTMLElement>(".student-app-shell.root-route.root-ai");
    await waitFor(() => expect(shell).toHaveClass("context-picker-active"));
    await waitFor(() => expect(apiMocks.getStudentLearningPage).toHaveBeenCalled());

    fireEvent.click(await screen.findByRole("button", { name: /Group 17 Halogens/ }));
    await waitFor(() => expect(apiMocks.getStudentChapterCatalog).toHaveBeenCalledWith("CH17"));
    fireEvent.click(await screen.findByRole("button", { name: /Halogen displacement catalog/ }));
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-halogen"));
    fireEvent.click(await screen.findByRole("button", { name: /Oxidation experiments/ }));
    await waitFor(() => expect(apiMocks.getStudentCatalogNode).toHaveBeenLastCalledWith("cat-dir-oxidation"));
    fireEvent.click(await screen.findByRole("button", { name: /Orange layer observation/ }));
    await waitFor(() => expect(shell).not.toHaveClass("context-picker-active"));

    await waitFor(() => expect(screen.queryByRole("dialog", { name: "选择学习背景" })).not.toBeInTheDocument());
    expect(screen.getByRole("region", { name: "已绑定学习背景" })).toHaveTextContent("Orange layer observation");
    expect(screen.getByRole("button", { name: "更换学习背景" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "移除学习背景" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "选择学习背景" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "更换学习背景" }));
    fireEvent.change(await screen.findByRole("searchbox", { name: "搜索可绑定点位" }), { target: { value: "CCl4" } });
    await waitFor(() => expect(apiMocks.searchStudentVideoLibrary).toHaveBeenLastCalledWith("CCl4", 12));
    fireEvent.click(await screen.findByRole("button", { name: /Orange layer observation/ }));

    fireEvent.change(screen.getByRole("textbox", { name: "向 Atom 提问" }), {
      target: { value: "这个点位为什么会出现橙色层？" },
    });
    fireEvent.click(screen.getByRole("button", { name: "发送问题" }));
    await waitFor(() => expect(apiMocks.streamStudentAssistantAsk).toHaveBeenCalledTimes(1));
    expect(apiMocks.streamStudentAssistantAsk).toHaveBeenLastCalledWith(
      expect.objectContaining({
        question: "这个点位为什么会出现橙色层？",
        context_type: "learning_point",
        context_title: "Orange layer observation",
        chapter_id: "CH17",
        point_node_id: "cat-point-halogen",
        catalog_path: ["Halogen displacement catalog", "Orange layer observation"],
        conversation_history: [],
      }),
      expect.any(Function),
    );
    expect(screen.getByRole("region", { name: "已绑定学习背景" })).toHaveTextContent("已绑定此点位");
    expect(screen.queryByRole("button", { name: "移除学习背景" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "已绑定学习背景，新建 Atom 对话后可更换" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "查看 Atom 历史记录" }));
    const historyDialog = await screen.findByRole("dialog", { name: "Atom 历史记录" });
    fireEvent.click(within(historyDialog).getByText("这个点位为什么会出现橙色层？").closest("button")!);
    await waitFor(() => expect(screen.getByRole("region", { name: "已绑定学习背景" })).toHaveTextContent("Orange layer observation"));

    fireEvent.click(screen.getByRole("button", { name: "新建 Atom 对话" }));
    await waitFor(() => expect(screen.queryByRole("region", { name: "已绑定学习背景" })).not.toBeInTheDocument());
    expect(screen.getByRole("button", { name: "选择学习背景" })).toHaveAttribute("aria-pressed", "false");
  });

  it("uses a visible-viewport keyboard layout only for the root Atom composer", async () => {
    const viewport = installVisualViewport(760);
    await renderAuthenticatedApp("/ai");

    const shell = document.querySelector<HTMLElement>(".student-app-shell.root-route.root-ai");
    const composer = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-chat-compose.root");
    const textarea = document.querySelector<HTMLTextAreaElement>(".ai-chat-panel.root .ai-chat-compose textarea");
    const bottomNav = document.querySelector<HTMLElement>(".student-bottom-nav");
    expect(shell).not.toBeNull();
    expect(composer).not.toBeNull();
    expect(textarea).not.toBeNull();
    expect(bottomNav).not.toBeNull();
    expect(composer).toHaveClass("is-compact");
    expect(shell).not.toHaveClass("keyboard-active");
    expect(shell?.style.getPropertyValue("--student-visual-viewport-height")).toBe("760px");
    expect(shell?.style.getPropertyValue("--student-keyboard-bottom-inset")).toBe("0px");

    Object.defineProperty(textarea!, "scrollHeight", { configurable: true, value: 48 });
    fireEvent.change(textarea!, { target: { value: "Cl2 and KBr observation" } });
    expect(document.querySelector(".ai-chat-panel.root")).toHaveClass("has-draft");
    expect(document.querySelector(".ai-chat-panel.root")).toHaveClass("root-state-draft");
    expect(document.querySelector(".ai-chat-panel.root")).toHaveAttribute("data-root-state", "draft");
    fireEvent.focusIn(textarea!);
    viewport.setHeight(520);
    await waitFor(() => expect(shell).toHaveClass("keyboard-active"));
    await waitFor(() => expect(shell?.style.getPropertyValue("--student-visual-viewport-height")).toBe("520px"));
    expect(shell?.style.getPropertyValue("--student-keyboard-bottom-inset")).toBe("240px");
    expect(document.querySelector(".ai-chat-stream.root-empty .ai-root-welcome")).toBeNull();
    expect(textarea).toHaveValue("Cl2 and KBr observation");
    await waitFor(() => expect(composer).toHaveClass("is-compact"));
    expect(textarea!.style.maxHeight).toBe("36px");
    expect(textarea!.style.height).toBe("36px");
    expect(textarea!.style.overflowY).toBe("hidden");

    Object.defineProperty(textarea!, "scrollHeight", { configurable: true, value: 140 });
    fireEvent.change(textarea!, { target: { value: "Cl2 and KBr observation\nWhy does the organic layer change?" } });
    await waitFor(() => expect(composer).toHaveClass("is-expanded"));
    const expectedComposerMaxHeight = Math.floor(520 * 0.618);
    const expectedComposerMaxInputHeight = expectedComposerMaxHeight - 13 - 56 - 10;
    expect(textarea!.style.maxHeight).toBe(`${expectedComposerMaxInputHeight}px`);
    expect(textarea!.style.height).toBe("140px");
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-workbench .ai-context-action")).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-workbench .ai-send-action")).not.toBeNull();

    const longQuestion = "Cl2 and KBr observation ".repeat(32);
    Object.defineProperty(textarea!, "scrollHeight", { configurable: true, value: 520 });
    fireEvent.change(textarea!, { target: { value: longQuestion } });
    await waitFor(() => expect(textarea!.style.height).toBe(`${expectedComposerMaxInputHeight}px`));
    expect(Number.parseInt(textarea!.style.height, 10) + 13 + 56 + 10).toBe(expectedComposerMaxHeight);
    expect(textarea).toHaveClass("is-scrollable");
    expect(textarea!.style.overflowY).toBe("auto");
    expect(composer).toHaveClass("is-expanded");

    textarea!.blur();
    fireEvent.focusOut(textarea!);
    await waitFor(() => expect(shell).not.toHaveClass("keyboard-active"));
    expect(textarea).toHaveValue(longQuestion);

    fireEvent.focusIn(textarea!);
    await waitFor(() => expect(shell).toHaveClass("keyboard-active"));
    viewport.setHeight(500);
    await waitFor(() => expect(shell?.style.getPropertyValue("--student-visual-viewport-height")).toBe("500px"));
    viewport.setHeight(760);
    await waitFor(() => expect(shell).not.toHaveClass("keyboard-active"));

    fireEvent.focusIn(textarea!);
    await waitFor(() => expect(shell).toHaveClass("keyboard-active"));
    fireEvent.click(rootButton("learn"));
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(document.querySelector(".student-app-shell")).not.toHaveClass("keyboard-active");

    cleanup();
    await renderAuthenticatedApp("/ai/chat");
    const detailShell = document.querySelector<HTMLElement>(".student-app-shell.detail-route");
    const detailTextarea = document.querySelector<HTMLTextAreaElement>(".ai-chat-panel.detail .ai-chat-compose textarea");
    expect(detailShell).not.toBeNull();
    expect(detailTextarea).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-context-action")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-chat-workbench")).toBeNull();
    fireEvent.focusIn(detailTextarea!);
    expect(detailShell).not.toHaveClass("keyboard-active");
    expect(document.querySelector(".student-bottom-nav")).toBeNull();
  });

  it("uses compact lane width to stabilize root composer boundary text", async () => {
    const viewport = installVisualViewport(760);
    await renderAuthenticatedApp("/ai");

    const composer = document.querySelector<HTMLElement>(".ai-chat-panel.root .ai-chat-compose.root");
    const textarea = document.querySelector<HTMLTextAreaElement>(".ai-chat-panel.root .ai-chat-compose-input textarea");
    const compactMeasure = document.querySelector<HTMLTextAreaElement>(".ai-chat-panel.root .ai-chat-compact-measure");

    expect(composer).not.toBeNull();
    expect(textarea).not.toBeNull();
    expect(compactMeasure).not.toBeNull();
    expect(composer).toHaveClass("is-compact");
    expect(compactMeasure!.rows).toBe(1);

    Object.defineProperty(textarea!, "scrollHeight", { configurable: true, value: 36 });
    Object.defineProperty(compactMeasure!, "scrollHeight", { configurable: true, value: 36 });
    fireEvent.change(textarea!, { target: { value: "1" } });

    await waitFor(() => expect(composer).toHaveClass("is-compact"));
    expect(textarea!.style.height).toBe("36px");

    Object.defineProperty(textarea!, "scrollHeight", { configurable: true, value: 36 });
    Object.defineProperty(compactMeasure!, "scrollHeight", { configurable: true, value: 70 });
    fireEvent.change(textarea!, { target: { value: "222222222223333333333333333333" } });

    await waitFor(() => expect(composer).toHaveClass("is-expanded"));
    expect(textarea!.style.height).toBe("68px");
    expect(compactMeasure!.style.width).not.toBe("");

    viewport.setHeight(520);
    await waitFor(() => expect(composer).toHaveClass("is-expanded"));
    expect(textarea!.style.height).toBe("68px");

    Object.defineProperty(compactMeasure!, "scrollHeight", { configurable: true, value: 36 });
    fireEvent.change(textarea!, { target: { value: "short question" } });
    await waitFor(() => expect(composer).toHaveClass("is-compact"));
    expect(textarea!.style.height).toBe("36px");
  });

  it("serves direct root and detail client routes with route-level navigation visibility", async () => {
    await renderAuthenticatedApp("/learn");
    await waitFor(() => expect(window.location.pathname).toBe("/learn"));
    expect(activeRoot()).toBe("learn");
    expect(document.querySelector(".periodic-grid")).not.toBeNull();
    expect(document.querySelector(".learning-recommendation-card")).toBeNull();
    expect(document.querySelector(".chapter-entry-card")).toBeNull();
    cleanup();

    await renderAuthenticatedApp("/learn/area/p");
    await waitFor(() => expect(window.location.pathname).toBe("/learn/area/p"));
    expectBottomNavHidden();
    await waitFor(() => expect(document.querySelector(".chapter-card-panel")).not.toBeNull());
    cleanup();

    await renderAuthenticatedApp("/ai");
    await waitFor(() => expect(window.location.pathname).toBe("/ai"));
    expect(activeRoot()).toBe("ai");
    expect(document.querySelector(".student-app-shell.root-route.root-ai")).not.toBeNull();
    expect(document.querySelector(".student-app-shell.root-ai > .student-app-header")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.root")).not.toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-root-star-shell")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.root .ai-chat-empty.root")).toBeNull();
    expect(screen.getByText("从一个实验开始吧！")).toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel.root .ai-root-welcome svg")?.getAttribute("class")).toContain("lucide-atom");
    expect(screen.getByRole("textbox", { name: "向 Atom 提问" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("问实验现象、步骤或原理")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "查看 Atom 历史记录" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "新建 Atom 对话" })).toBeInTheDocument();
    cleanup();

    await renderAuthenticatedApp("/ai/chat");
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    expect(document.querySelector(".student-app-shell.detail-route")).not.toBeNull();
    expect(document.querySelector(".ai-root-page")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.root")).toBeNull();
    expect(document.querySelector(".ai-root-star-shell")).toBeNull();
    expect(screen.queryByText("从一个实验开始吧！")).not.toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel.detail")).not.toBeNull();
    expect(screen.getByPlaceholderText("围绕当前内容提问")).toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel.detail .ai-root-actions")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-history-action")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-new-chat-action")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-context-action")).toBeNull();
    expect(document.querySelector(".ai-chat-panel.detail .ai-chat-workbench")).toBeNull();
    expect(screen.getByRole("textbox", { name: "向 Atom 提问" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "查看 Atom 历史记录" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "新建 Atom 对话" })).not.toBeInTheDocument();
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
  }, 15_000);

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
    expect(screen.getByText("Atom 学习助手暂未开放")).toBeInTheDocument();
    expect(document.querySelector(".ai-chat-panel")).toBeNull();
    cleanup();

    await renderAuthenticatedApp("/ai/chat");
    await waitFor(() => expect(window.location.pathname).toBe("/ai/chat"));
    expectBottomNavHidden();
    expect(document.querySelector(".ai-chat-panel")).toBeNull();
    expect(document.querySelector(".empty-learning-card")).not.toBeNull();
    cleanup();

    await renderAuthenticatedApp("/profile");
    await clickRoot("profile");
    expect(screen.getByText("反馈入口已关闭")).toBeInTheDocument();
  });
});
