import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import katex from "katex";
import "katex/dist/katex.min.css";
import "../styles.css";
import { DECK_META as initialMeta, DECK_SLIDES as initialSlides } from "../slides.js";

function TeX({ expression, block = false }) {
  const html = katex.renderToString(expression, {
    displayMode: block,
    throwOnError: false,
    strict: "ignore"
  });
  return (
    <span
      className={`tex-render ${block ? "block" : "inline"}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

function App() {
  const searchParams = new URLSearchParams(window.location.search);
  const printMode = searchParams.get("print") === "1";
  const autoPrint = printMode && searchParams.get("auto") !== "0";
  const exportOnly = searchParams.get("export") === "1";
  const exportScale = exportOnly ? normalizedExportScale(searchParams.get("scale")) : 1;
  const [meta, setMeta] = useState(initialMeta);
  const [slides, setSlides] = useState(initialSlides);
  const [current, setCurrent] = useState(() => initialSlideIndex(initialSlides));
  const [overview, setOverview] = useState(false);
  const stageWrapRef = useRef(null);
  const stageShellRef = useRef(null);
  const stageRef = useRef(null);
  const slide = slides[current] || slides[0];

  useEffect(() => {
    const resize = () => scaleStage(stageWrapRef.current, stageShellRef.current, stageRef.current, overview);
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [current, overview, slides]);

  useEffect(() => {
    if (!import.meta.hot) return undefined;
    const dispose = import.meta.hot.accept("../slides.js", (module) => {
      setMeta(module.DECK_META);
      setSlides(module.DECK_SLIDES);
      setCurrent((value) => Math.min(value, module.DECK_SLIDES.length - 1));
    });
    return dispose;
  }, []);

  useEffect(() => {
    if (!autoPrint) return undefined;
    let cancelled = false;
    const printWhenReady = async () => {
      if (document.fonts?.ready) await document.fonts.ready;
      await Promise.all(Array.from(document.images).map((image) => {
        if (image.complete) return Promise.resolve();
        return new Promise((resolve) => {
          image.addEventListener("load", resolve, { once: true });
          image.addEventListener("error", resolve, { once: true });
        });
      }));
      if (cancelled) return;
      window.setTimeout(() => window.print(), 250);
    };
    printWhenReady();
    return () => {
      cancelled = true;
    };
  }, [autoPrint, slides]);

  function openPdfExport() {
    const url = new URL(window.location.href);
    url.searchParams.set("print", "1");
    url.searchParams.delete("auto");
    url.searchParams.delete("export");
    url.searchParams.delete("scale");
    url.searchParams.delete("n");
    const opened = window.open(url.toString(), "_blank");
    if (opened) {
      opened.opener = null;
      return;
    }
    window.location.href = url.toString();
  }

  if (printMode) {
    return (
      <main className="print-shell" aria-label="PDF 导出画布">
        {slides.map((item) => (
          <section className="print-page" key={item.no} aria-label={`第 ${item.no} 页`}>
            <SlideView slide={item} total={slides.length} />
          </section>
        ))}
      </main>
    );
  }

  if (exportOnly) {
    return (
      <main
        className="export-shell"
        aria-label="PDF 导出画布"
        style={{ width: 1280 * exportScale, height: 720 * exportScale }}
      >
        <div className="export-stage" style={{ transform: `scale(${exportScale})` }}>
          <SlideView slide={slide} total={slides.length} />
        </div>
      </main>
    );
  }

  return (
    <main className="review-shell">
      <aside className="rail" aria-label="页面导航">
        <div className="rail-head">
          <div>
            <p className="eyebrow">Provincial Review</p>
            <h1>{meta.project}</h1>
          </div>
          <button className="mode-toggle" type="button" onClick={() => setOverview((v) => !v)} title="切换总览" aria-pressed={overview}>
            {overview ? "单页" : "总览"}
          </button>
        </div>
        <div className="slide-list">
          {slides.map((item, index) => (
            <button
              className={`nav-item ${index === current ? "active" : ""}`}
              type="button"
              data-index={index}
              key={item.no}
              onClick={() => {
                setCurrent(index);
                setOverview(false);
              }}
            >
              <span className="nav-no">{pad(item.no)}</span>
              <span className="nav-copy">
                <span className="nav-section">{item.section}</span>
                <span className="nav-title">{item.title}</span>
              </span>
            </button>
          ))}
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-copy">
            <p className="eyebrow">{slide.section}</p>
            <h2>{slide.title}</h2>
          </div>
          <div className="topbar-tools">
            <button className="pdf-export-button" type="button" onClick={openPdfExport} title="导出 PDF">
              导出 PDF
            </button>
          </div>
        </header>

        <div className="stage-wrap" ref={stageWrapRef}>
          {!overview && (
            <div className="stage-shell" ref={stageShellRef}>
              <div className="stage" ref={stageRef}>
                <SlideView slide={slide} total={slides.length} />
              </div>
            </div>
          )}
          {overview && (
            <div className="overview-grid">
              {slides.map((item, index) => (
                <button
                  className="overview-card"
                  type="button"
                  key={item.no}
                  onClick={() => {
                    setCurrent(index);
                    setOverview(false);
                  }}
                >
                  <div className="overview-thumb"><SlideView slide={item} total={slides.length} /></div>
                  <div className="overview-meta"><strong>{pad(item.no)}</strong><span>{item.title}</span></div>
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

    </main>
  );
}

function SlideView({ slide, total }) {
  if (slide.layout === "cover") return <CoverSlide slide={slide} />;
  if (slide.layout === "chapter") return <ChapterSlide slide={slide} total={total} />;
  if (slide.layout === "backgroundValue") return <BackgroundValueSlide slide={slide} />;
  if (slide.layout === "supportGap") return <SupportGapSlide slide={slide} />;
  if (slide.layout === "policyDirection") return <PolicyDirectionSlide slide={slide} />;
  if (slide.layout === "platformPosition") return <PlatformPositionSlide slide={slide} />;
  if (slide.layout === "experimentNeed") return <ExperimentNeedSlide slide={slide} />;
  if (slide.layout === "resourceQuestion") return <ResourceQuestionSlide slide={slide} />;
  if (slide.layout === "systemBlueprint") return <SystemBlueprintSlide slide={slide} />;
  if (slide.layout === "questionLogic") return <QuestionLogicSlide slide={slide} />;
  if (slide.layout === "bktUpdate") return <BktUpdateSlide slide={slide} />;
  if (slide.layout === "recommendationStrategy") return <RecommendationStrategySlide slide={slide} />;
  if (slide.layout === "resourceShowcase") return <ResourceShowcaseSlide slide={slide} />;
  if (slide.layout === "questionShowcase") return <QuestionShowcaseSlide slide={slide} />;
  if (slide.layout === "studentLearningShowcase") return <StudentLearningShowcaseSlide slide={slide} />;
  if (slide.layout === "teacherAnalyticsShowcase") return <TeacherAnalyticsShowcaseSlide slide={slide} />;
  if (slide.layout === "referenceList") return <ReferenceListSlide slide={slide} />;
  return (
    <article className="slide">
      <SlideHeader slide={slide} />
      <div className="content">{renderBody(slide)}</div>
    </article>
  );
}

function SlideHeader({ slide }) {
  return (
    <header className="slide-header">
      <div className="slide-heading-copy">
        <div className="slide-kicker">项目答辩 · {slide.section}</div>
        <div className="slide-title">{slide.title}</div>
      </div>
    </header>
  );
}

function CoverSlide({ slide }) {
  return (
    <article className="slide cover-slide">
      <section className="cover-stack">
        <p className="cover-label">省赛答辩 · 化学实验创新设计竞赛</p>
        <h2>{slide.title.split("\n").map((line, index, lines) => (
          <React.Fragment key={`${line}-${index}`}>{line}{index < lines.length - 1 ? <br /> : null}</React.Fragment>
        ))}</h2>
        <p className="subtitle">{slide.subtitle}</p>
        {slide.chips?.length ? (
          <div className="chips">{slide.chips.map((chip) => <span className="chip" key={chip}>{chip}</span>)}</div>
        ) : null}
      </section>
      <div className="cover-diagram" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
    </article>
  );
}

function renderBody(slide) {
  if (slide.layout === "agenda") return <Agenda slide={slide} />;
  if (slide.layout === "statement") return <Statement slide={slide} />;
  if (slide.layout === "cards") return <Cards slide={slide} />;
  if (slide.layout === "flow") return <Flow slide={slide} />;
  if (slide.layout === "screenshot") return <Screenshot slide={slide} />;
  if (slide.layout === "metrics") return <Metrics slide={slide} />;
  if (slide.layout === "architecture") return <Architecture slide={slide} />;
  if (slide.layout === "closing") return <Closing slide={slide} />;
  return null;
}

function Agenda({ slide }) {
  return (
    <section className="agenda-layout">
      {slide.lead ? <p className="page-lead">{slide.lead}</p> : null}
      <div className="agenda-list">
        {(slide.items || []).map(([no, title]) => (
          <div className="agenda-item" key={`${no}-${title}`}>
            <strong>{no}</strong>
            <h3>{title}</h3>
          </div>
        ))}
      </div>
    </section>
  );
}

function ChapterSlide({ slide, total }) {
  const partNo = slide.section?.match(/\d+/)?.[0] || pad(slide.no);
  return (
    <article className="slide chapter-slide">
      <section className="chapter-copy">
        <p className="chapter-label">PART {partNo}</p>
        <h2>{slide.title}</h2>
      </section>
    </article>
  );
}

function Statement({ slide }) {
  return (
    <section className="statement-grid">
      <div>
        <div className="hero-word">{slide.hero}</div>
        <div className="lead-large">{slide.lead}</div>
        <div className="support">{slide.support}</div>
      </div>
      <div className="bullet-stack"><Bullets items={slide.bullets} /></div>
    </section>
  );
}

function BackgroundValueSlide({ slide }) {
  return (
    <article className="slide background-value-slide">
      <div className="background-kicker">01 选题背景</div>
      <section className="background-head">
        <h2>{slide.title}</h2>
        <p>{withCitations(slide.lead)}</p>
      </section>
      <section className="value-board">
        {(slide.pillars || []).map(([title, text], index) => (
          <section className="value-pillar" key={title}>
            <span>{pad(index + 1)}</span>
            <h3>{title}</h3>
            <p>{withCitations(text)}</p>
          </section>
        ))}
      </section>
      <section className="background-conclusion">
        <span>必要性</span>
        <p>{withCitations(slide.conclusion)}</p>
      </section>
    </article>
  );
}

function SupportGapSlide({ slide }) {
  return (
    <article className="slide support-gap-slide">
      <div className="background-kicker">01 选题背景</div>
      <section className="gap-head">
        <h2>{slide.title}</h2>
        <p>{withCitations(slide.lead)}</p>
      </section>
      <section className="gap-timeline">
        {(slide.stages || []).map(([phase, title, text], index) => (
          <section className="gap-stage" key={phase}>
            <div className="gap-phase">{phase}</div>
            <div className="gap-copy">
              <span>{pad(index + 1)}</span>
              <h3>{title}</h3>
              <p>{withCitations(text)}</p>
            </div>
          </section>
        ))}
      </section>
      <section className="gap-conclusion">
        <p>{withCitations(slide.conclusion)}</p>
      </section>
    </article>
  );
}

function PolicyDirectionSlide({ slide }) {
  return (
    <article className="slide policy-direction-slide">
      <div className="background-kicker">01 选题背景</div>
      <section className="policy-head">
        <h2>{slide.title}</h2>
        <p>{withCitations(slide.lead)}</p>
      </section>
      <section className="policy-grid">
        {(slide.policies || []).map(([title, text], index) => (
          <section className={`policy-card policy-card-${index + 1}`} key={title}>
            <span>{pad(index + 1)}</span>
            <h3>{title}</h3>
            <p>{withCitations(text)}</p>
          </section>
        ))}
      </section>
      <section className="policy-conclusion">
        <span>趋势判断</span>
        <p>{withCitations(slide.conclusion)}</p>
      </section>
    </article>
  );
}

function PlatformPositionSlide({ slide }) {
  return (
    <article className="slide platform-position-slide">
      <div className="background-kicker">01 选题背景</div>
      <section className="platform-head">
        <h2>{slide.title}</h2>
        <p>{withCitations(slide.lead)}</p>
      </section>
      <section className="platform-body">
        <section className="resource-base">
          <p>已有资源基础</p>
          <div className="resource-numbers">
            {(slide.stats || []).map(([value, label]) => (
              <div key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="support-system">
          {(slide.needs || []).map(([title, text]) => (
            <section className="support-item" key={title}>
              <h3>{title}</h3>
              <p>{withCitations(text)}</p>
            </section>
          ))}
        </section>
      </section>
      <section className="platform-conclusion">
        <span>平台定位</span>
        <p>{withCitations(slide.conclusion)}</p>
      </section>
    </article>
  );
}

function ExperimentNeedSlide({ slide }) {
  return (
    <article className="slide experiment-need-slide">
      <div className="experiment-kicker">01 选题背景</div>
      <section className="experiment-hero">
        <div>
          <h2>{slide.title}</h2>
          {slide.focus ? <p>{slide.focus}</p> : null}
          {slide.lead ? <small>{slide.lead}</small> : null}
        </div>
        <div className="tube-scene" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </section>
      <section className="experiment-barriers">
          {(slide.barriers || []).map(([title, text], index) => (
            <section className="barrier-tile" key={title}>
              <span className="barrier-index">{pad(index + 1)}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </section>
          ))}
      </section>
      {slide.solution ? (
        <section className="experiment-solution">
          <span>解决思路</span>
          <p>{slide.solution}</p>
        </section>
      ) : null}
    </article>
  );
}

function ResourceQuestionSlide({ slide }) {
  return (
    <article className="slide resource-question-slide">
      <div className="resource-kicker">01 选题背景</div>
      <section className="resource-head">
        <h2>{slide.title}</h2>
        {slide.lead ? <p>{slide.lead}</p> : null}
      </section>
      <section className="resource-stats">
        {(slide.stats || []).map(([value, label, text]) => (
          <section className={`resource-stat ${text ? "" : "no-caption"}`} key={`${value}-${label}`}>
            <div className="resource-stat-main">
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
            {text ? <p>{text}</p> : null}
          </section>
        ))}
      </section>
      {slide.question ? (
        <section className="resource-question">
          <span>提出问题</span>
          <p>{slide.question}</p>
        </section>
      ) : null}
    </article>
  );
}

function SystemBlueprintSlide({ slide }) {
  return (
    <article className="slide system-blueprint-slide">
      <div className="blueprint-kicker">02 总体方案</div>
      <section className="blueprint-head">
        <h2>{slide.title}</h2>
        {slide.lead ? <p>{slide.lead}</p> : null}
      </section>

      <section className="blueprint-board">
        <section className="blueprint-lane teacher-lane">
          <div className="lane-label">教师端</div>
          {(slide.teacher || []).map(([title, text], index) => (
            <div className="blueprint-step" key={title}>
              <span>{pad(index + 1)}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </section>

        <section className="mastery-engine">
          <div className="engine-ring" aria-hidden="true" />
          <div className="engine-copy">
            <span>系统判断</span>
            <h3>{slide.engine?.title}</h3>
            <p>{slide.engine?.caption}</p>
          </div>
          <div className="mastery-bars">
            {(slide.engine?.samples || []).map(([label, value]) => (
              <div className="mastery-row" key={label} style={{ "--value": value }}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="blueprint-lane student-lane">
          <div className="lane-label">学生端</div>
          {(slide.student || []).map(([title, text], index) => (
            <div className="blueprint-step" key={title}>
              <span>{pad(index + 3)}</span>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
          <svg className="student-test-flow" viewBox="0 0 460 258" aria-hidden="true" focusable="false">
            <defs>
              <marker id="studentTestArrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse">
                <path d="M 0 0 L 10 5 L 0 10 Z" />
              </marker>
            </defs>
            <path className="student-test-flow-path" d="M 420 66 C 448 112 448 170 420 218" />
          </svg>
        </section>

        <div className="flow-line teacher-to-engine" aria-hidden="true" />
        <div className="flow-line engine-to-student" aria-hidden="true" />
        <div className="flow-line student-to-engine" aria-hidden="true" />
        <svg className="question-to-test-flow" viewBox="0 0 1128 390" aria-hidden="true" focusable="false">
          <defs>
            <marker id="questionToTestArrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="userSpaceOnUse">
              <path d="M 0 0 L 12 6 L 0 12 Z" />
            </marker>
          </defs>
          <path className="question-to-test-flow-path" d="M 318 220 C 304 338 384 360 510 360 C 614 360 654 338 670 314" />
        </svg>
      </section>

    </article>
  );
}

function QuestionLogicSlide({ slide }) {
  return (
    <article className="slide question-logic-slide">
      <div className="logic-kicker">02 总体方案</div>
      <section className="logic-head">
        <h2>{slide.title}</h2>
        {slide.lead ? <p>{slide.lead}</p> : null}
      </section>

      <section className="logic-inputs" aria-label="出题输入条件">
        {(slide.inputs || []).map(([title, text], index) => (
          <section className="logic-input" key={title}>
            <span>{pad(index + 1)}</span>
            <h3>{title}</h3>
            <p>{text}</p>
          </section>
        ))}
      </section>

      <section className="logic-pipeline" aria-label="出题生成链路">
        {(slide.pipeline || []).map(([no, title, text], index) => (
          <section className={`logic-step ${index === 1 ? "logic-step-ai" : ""}`} key={title}>
            <span>{no}</span>
            <h3>{title}</h3>
            <p>{text}</p>
          </section>
        ))}
      </section>

      <section className="logic-safeguards" aria-label="出题控制点">
        {(slide.safeguards || []).map(([title, text]) => (
          <section className="logic-safeguard" key={title}>
            <h3>{title}</h3>
            <p>{text}</p>
          </section>
        ))}
      </section>
    </article>
  );
}

function BktUpdateSlide({ slide }) {
  return (
    <article className="slide bkt-update-slide">
      <div className="bkt-kicker">02 总体方案</div>
      <section className="bkt-head">
        <h2>{slide.title}</h2>
        <p>{withInlineMath(slide.lead)}</p>
      </section>

      <section className="bkt-params" aria-label="BKT 参数">
        {(slide.params || []).map(([label, value, text]) => (
          <section className="bkt-param" key={label}>
            <span>{label}</span>
            <strong><TeX expression={value} /></strong>
            <p>{text}</p>
          </section>
        ))}
      </section>

      <section className="bkt-body">
        <section className="bkt-formulas" aria-label="BKT 更新公式">
          {(slide.formulas || []).map(([title, formula]) => (
            <section className="bkt-formula" key={title}>
              <h3>{title}</h3>
              <TeX expression={formula} block />
            </section>
          ))}
        </section>

        <section className="bkt-examples" aria-label="BKT 更新样例">
          {(slide.examples || []).map(([title, value, text]) => (
            <section className={`bkt-example ${title === "答错" ? "wrong" : "correct"}`} key={title}>
              <span>{title}</span>
              <strong>{value}</strong>
              <p>{text}</p>
            </section>
          ))}
        </section>
      </section>
    </article>
  );
}

const PERIODIC_DECO_CELLS = [
  ["H", 1, 1], ["He", 18, 1],
  ["Li", 1, 2], ["Be", 2, 2], ["B", 13, 2], ["C", 14, 2], ["N", 15, 2], ["O", 16, 2], ["F", 17, 2], ["Ne", 18, 2],
  ["Na", 1, 3], ["Mg", 2, 3], ["Al", 13, 3], ["Si", 14, 3], ["P", 15, 3], ["S", 16, 3], ["Cl", 17, 3], ["Ar", 18, 3],
  ["K", 1, 4], ["Ca", 2, 4], ["Sc", 3, 4], ["Ti", 4, 4], ["V", 5, 4], ["Cr", 6, 4], ["Mn", 7, 4], ["Fe", 8, 4], ["Co", 9, 4], ["Ni", 10, 4], ["Cu", 11, 4], ["Zn", 12, 4], ["Ga", 13, 4], ["Ge", 14, 4], ["As", 15, 4], ["Se", 16, 4], ["Br", 17, 4], ["Kr", 18, 4],
  ["Rb", 1, 5], ["Sr", 2, 5], ["Y", 3, 5], ["Zr", 4, 5], ["Nb", 5, 5], ["Mo", 6, 5], ["Tc", 7, 5], ["Ru", 8, 5], ["Rh", 9, 5], ["Pd", 10, 5], ["Ag", 11, 5], ["Cd", 12, 5], ["In", 13, 5], ["Sn", 14, 5], ["Sb", 15, 5], ["Te", 16, 5], ["I", 17, 5], ["Xe", 18, 5],
  ["Cs", 1, 6], ["Ba", 2, 6], ["La", 3, 6], ["Hf", 4, 6], ["Ta", 5, 6], ["W", 6, 6], ["Re", 7, 6], ["Os", 8, 6], ["Ir", 9, 6], ["Pt", 10, 6], ["Au", 11, 6], ["Hg", 12, 6], ["Tl", 13, 6], ["Pb", 14, 6], ["Bi", 15, 6], ["Po", 16, 6], ["At", 17, 6], ["Rn", 18, 6],
  ["Fr", 1, 7], ["Ra", 2, 7], ["Ac", 3, 7], ["Rf", 4, 7], ["Db", 5, 7], ["Sg", 6, 7], ["Bh", 7, 7], ["Hs", 8, 7], ["Mt", 9, 7], ["Ds", 10, 7], ["Rg", 11, 7], ["Cn", 12, 7], ["Nh", 13, 7], ["Fl", 14, 7], ["Mc", 15, 7], ["Lv", 16, 7], ["Ts", 17, 7], ["Og", 18, 7],
  ["Ce", 4, 8], ["Pr", 5, 8], ["Nd", 6, 8], ["Pm", 7, 8], ["Sm", 8, 8], ["Eu", 9, 8], ["Gd", 10, 8], ["Tb", 11, 8], ["Dy", 12, 8], ["Ho", 13, 8], ["Er", 14, 8], ["Tm", 15, 8], ["Yb", 16, 8], ["Lu", 17, 8],
  ["Th", 4, 9], ["Pa", 5, 9], ["U", 6, 9], ["Np", 7, 9], ["Pu", 8, 9], ["Am", 9, 9], ["Cm", 10, 9], ["Bk", 11, 9], ["Cf", 12, 9], ["Es", 13, 9], ["Fm", 14, 9], ["Md", 15, 9], ["No", 16, 9], ["Lr", 17, 9]
];

function RecommendationStrategySlide({ slide }) {
  return (
    <article className="slide recommendation-strategy-slide">
      <div className="recommend-kicker">02 总体方案</div>
      <section className="recommend-head">
        <h2>{slide.title}</h2>
        <p>{slide.lead}</p>
      </section>

      <section className="recommend-body">
        <section className="recommend-hierarchy" aria-label="推荐数据层级">
          {(slide.hierarchy || []).map(([level, value, text]) => (
            <section className="recommend-node" key={level}>
              <span>{level}</span>
              <h3>{withInlineMath(value)}</h3>
              <p>{text}</p>
            </section>
          ))}
        </section>

        <section className="recommend-periodic" aria-label="元素周期表装饰">
          <div className="periodic-caption">
            <span>按族定位薄弱区域</span>
            <strong>卤族元素</strong>
          </div>
          <div className="periodic-grid" aria-hidden="true">
            {PERIODIC_DECO_CELLS.map(([symbol, col, row]) => (
              <span
                className={`periodic-cell ${row >= 8 ? "f-block" : ""} ${row < 8 && col >= 13 ? "p-block" : ""} ${row < 8 && col === 17 ? "target-family" : ""}`}
                style={{ gridColumn: col, gridRow: row }}
                key={`${symbol}-${row}-${col}`}
              >
                {symbol}
              </span>
            ))}
          </div>
        </section>
      </section>

    </article>
  );
}

function ResourceShowcaseSlide({ slide }) {
  return (
    <article className="slide resource-showcase-slide">
      <div className="showcase-kicker">03 应用展示</div>
      <section className="showcase-head">
        <h2>{slide.title}</h2>
        <p>{slide.lead}</p>
      </section>

      <section className="showcase-screens" aria-label="教师端与学生端资源展示">
        <figure className="showcase-shot teacher-shot">
          <div className="showcase-window-bar">
            <span />
          </div>
          <img src={slide.teacherImage} alt={slide.teacherCaption} />
          <figcaption>{slide.teacherCaption}</figcaption>
        </figure>

        <figure className="showcase-shot student-shot">
          <div className="showcase-phone-top" aria-hidden="true" />
          <img src={slide.studentImage} alt={slide.studentCaption} />
          <figcaption>{slide.studentCaption}</figcaption>
        </figure>
      </section>

      <section className="showcase-notes">
        {(slide.notes || []).map(([label, text]) => (
          <div className="showcase-note" key={label}>
            <span>{label}</span>
            <p>{text}</p>
          </div>
        ))}
      </section>
    </article>
  );
}

function QuestionShowcaseSlide({ slide }) {
  return (
    <article className="slide question-showcase-slide">
      <div className="question-showcase-kicker">03 应用展示</div>
      <section className="question-showcase-head">
        <h2>{slide.title}</h2>
        <p>{slide.lead}</p>
      </section>

      <section className="question-screenshot-body" aria-label="教师端出题真实截图">
        <figure className="question-real-shot">
          <div className="question-shot-bar">
            <span />
          </div>
          <img src={slide.image} alt="教师端智能命题截图" />
        </figure>

        <aside className="question-real-notes" aria-label="截图说明">
          {(slide.notes || []).map(([title, text], index) => (
            <section className="question-real-note" key={title}>
              <span>{pad(index + 1)}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </section>
          ))}
        </aside>
      </section>

      <section className="question-shot-summary">
        <span>功能定位</span>
        <p>出题不直接发布，而是先形成待审题目，由教师把关后进入正式题库。</p>
      </section>
    </article>
  );
}

function StudentLearningShowcaseSlide({ slide }) {
  return (
    <article className="slide student-learning-showcase-slide">
      <div className="student-learning-kicker">03 应用展示</div>
      <section className="student-learning-head">
        <h2>{slide.title}</h2>
        <p>{slide.lead}</p>
      </section>

      <section className="student-learning-body" aria-label="学生端学习链路真实截图">
        <div className="student-learning-phones">
          {(slide.images || []).map(([label, src, caption], index) => (
            <figure className="student-phone-shot" key={label}>
              <div className="student-phone-label">
                <span>{pad(index + 1)}</span>
                <strong>{label}</strong>
              </div>
              <div className="student-phone-frame">
                <img src={src} alt={caption} />
              </div>
              <figcaption>{caption}</figcaption>
            </figure>
          ))}
        </div>

        <aside className="student-learning-steps" aria-label="学生学习步骤说明">
          {(slide.steps || []).map(([no, title, text]) => (
            <section className="student-learning-step" key={no}>
              <span>{no}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </section>
          ))}
        </aside>
      </section>

      <section className="student-learning-summary">
        <span>学习闭环</span>
        <p>{slide.summary}</p>
      </section>
    </article>
  );
}

function TeacherAnalyticsShowcaseSlide({ slide }) {
  return (
    <article className="slide teacher-analytics-showcase-slide">
      <div className="teacher-analytics-kicker">03 应用展示</div>
      <section className="teacher-analytics-head">
        <h2>{slide.title}</h2>
        <p>{slide.lead}</p>
      </section>

      <section className="teacher-analytics-body" aria-label="教师端学情分析真实截图">
        <figure className="teacher-analytics-shot">
          <img src={slide.image} alt="教师端学情分析后台截图" />
        </figure>

        <aside className="teacher-analytics-notes" aria-label="学情分析说明">
          {(slide.notes || []).map(([title, text], index) => (
            <section className="teacher-analytics-note" key={title}>
              <span>{pad(index + 1)}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </section>
          ))}
        </aside>
      </section>

      <section className="teacher-analytics-summary">
        <span>教学反馈</span>
        <p>{slide.summary}</p>
      </section>
    </article>
  );
}

function ReferenceListSlide({ slide }) {
  return (
    <article className="slide references-slide">
      <div className="reference-kicker">资料来源</div>
      <section className="reference-head">
        <h2>{slide.title}</h2>
        <p>用于支撑“选题背景”和平台建设必要性的政策、教学研究与项目内部资料。</p>
      </section>
      <section className="reference-grid">
        {(slide.references || []).map(([no, text]) => (
          <div className="reference-item" key={no}>
            <strong>{no}</strong>
            <p>{text}</p>
          </div>
        ))}
      </section>
    </article>
  );
}

function withCitations(text = "") {
  return text.split(/(\[\d+\])/g).filter(Boolean).map((part, index) => (
    /^\[\d+\]$/.test(part)
      ? <span className="inline-cite" key={`${part}-${index}`}>{part}</span>
      : <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>
  ));
}

function withInlineMath(text = "") {
  return text.split(/(\$[^$]+\$)/g).filter(Boolean).map((part, index) => (
    /^\$[^$]+\$$/.test(part)
      ? <TeX expression={part.slice(1, -1)} key={`${part}-${index}`} />
      : <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>
  ));
}

function Cards({ slide }) {
  return (
    <>
      <p className="page-lead">{slide.lead}</p>
      <div className="card-grid">
        {(slide.cards || []).map(([title, text]) => (
          <section className="info-card" key={title}><h3>{title}</h3><p>{text}</p></section>
        ))}
      </div>
    </>
  );
}

function Flow({ slide }) {
  const positions = [[60, 214], [304, 74], [686, 74], [928, 214], [686, 368], [304, 368]];
  return (
    <div className="flow-board">
      <div className="flow-center"><div><strong>{slide.center}</strong><span>{slide.lead}</span></div></div>
      {(slide.nodes || []).map(([title, text], index) => (
        <div className="flow-node" style={{ left: positions[index]?.[0] || 0, top: positions[index]?.[1] || 0 }} key={`${title}-${index}`}>
          <div><strong>{title}</strong><span>{text}</span></div>
        </div>
      ))}
    </div>
  );
}

function Screenshot({ slide }) {
  const shot = <figure className="shot-frame"><img src={slide.image} alt="" /></figure>;
  const copy = <section className="screen-copy"><h3>{slide.lead}</h3><div className="bullet-stack"><Bullets items={slide.bullets} /></div></section>;
  return <div className={`screenshot-layout ${slide.side === "right" ? "right" : ""}`}>{slide.side === "right" ? <>{copy}{shot}</> : <>{shot}{copy}</>}</div>;
}

function Metrics({ slide }) {
  return (
    <>
      <p className="page-lead">{slide.lead}</p>
      <div className="metrics-grid">
        {(slide.metrics || []).map(([label, value, sub]) => (
          <section className="metric-card" key={label}>
            <div className="metric-value">{value}</div>
            <div className="metric-label">{label}</div>
            <div className="metric-sub">{sub}</div>
          </section>
        ))}
      </div>
    </>
  );
}

function Architecture({ slide }) {
  return (
    <>
      <p className="page-lead">{slide.lead}</p>
      <div className="architecture">
        {(slide.layers || []).map(([label, items]) => (
          <section className="layer-row" key={label}>
            <div className="layer-label">{label}</div>
            <div className="layer-items">
              {(items || []).map(([title, text]) => (
                <div className="layer-item" key={`${label}-${title}`}><strong>{title}</strong><span>{text}</span></div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}

function Closing({ slide }) {
  return (
    <section className="closing-layout">
      <div className="closing-line"><h3>{slide.lead}</h3><p>{slide.support}</p></div>
      <div className="closing-cards">
        {(slide.bullets || []).map((text, index) => (
          <div className="closing-card" key={text}><strong>{pad(index + 1)}</strong><span>{text}</span></div>
        ))}
      </div>
    </section>
  );
}

function Bullets({ items = [] }) {
  return items.map((text) => <div className="evidence-row" key={text}><span className="dot" /><p>{text}</p></div>);
}

function initialSlideIndex(list) {
  if (typeof window === "undefined") return 0;
  const raw = new URLSearchParams(window.location.search).get("n");
  const no = Number(raw);
  if (!Number.isFinite(no)) return 0;
  const idx = list.findIndex((s) => s.no === no);
  return idx >= 0 ? idx : Math.min(Math.max(no - 1, 0), list.length - 1);
}

function scaleStage(wrapper, shell, stage, overview) {
  if (!wrapper || !shell || !stage || overview) return;
  const bounds = wrapper.getBoundingClientRect();
  const scale = Math.min((bounds.width - 56) / 1280, (bounds.height - 56) / 720, 1);
  const finalScale = Math.max(scale, 0.35);
  shell.style.width = `${1280 * finalScale}px`;
  shell.style.height = `${720 * finalScale}px`;
  stage.style.transform = `scale(${finalScale})`;
}

function pad(no) {
  return String(no).padStart(2, "0");
}

function normalizedExportScale(raw) {
  const value = Number(raw || 1);
  if (!Number.isFinite(value)) return 1;
  return Math.min(Math.max(value, 1), 4);
}

createRoot(document.getElementById("root")).render(<App />);
