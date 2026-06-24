import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { Check, ClipboardList, FlaskConical, LoaderCircle, Search } from "lucide-react";
import {
  errorMessage,
  getStudentCustomAssessmentOptions,
  startStudentCustomAssessment,
  type CustomAssessmentExperimentOption,
  type StudentCustomAssessmentOptionsResponse,
} from "../../api";
import { storePosttestSession } from "../../app/router/assessmentSessionStore";
import { navigateToAssessmentSession } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { MobileButton, MobileEmptyState, MobileField } from "../../mobile/primitives";

function optionLabel(option: CustomAssessmentExperimentOption): string {
  return [option.parent_title, option.title].filter(Boolean).join(" / ");
}

export function AssessmentCustomPage() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const [data, setData] = useState<StudentCustomAssessmentOptionsResponse | null>(null);
  const [query, setQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [questionCount, setQuestionCount] = useState(10);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentCustomAssessmentOptions()
      .then((response) => {
        if (cancelled) return;
        setData(response);
        setQuestionCount(response.settings.default_question_count);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const experiments = data?.experiments || [];
  const filteredExperiments = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return experiments;
    return experiments.filter((option) => optionLabel(option).toLowerCase().includes(keyword) || option.code.toLowerCase().includes(keyword));
  }, [experiments, query]);
  const selectedExperiments = useMemo(() => experiments.filter((option) => selectedIds.has(option.id)), [experiments, selectedIds]);
  const countOptions = data?.settings.question_count_options.length ? data.settings.question_count_options : [5, 10, 15, 20];
  const disabled = !data?.settings.enabled;

  const toggleExperiment = (id: string) => {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const startCustomAssessment = async () => {
    if (disabled) return;
    if (!selectedIds.size) {
      setError("请先选择至少 1 个实验。");
      return;
    }
    setStarting(true);
    setError("");
    try {
      const response = await startStudentCustomAssessment(Array.from(selectedIds), questionCount);
      storePosttestSession(response);
      navigateToAssessmentSession(navigate, response.session_id, "assessment-custom");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setStarting(false);
    }
  };

  return (
    <DetailPageFrame title="自主测评" source={search.from || "assessment"}>
      <section className="learning-panel custom-assessment-page" aria-label="自主测评">
        {loading ? (
          <MobileEmptyState className="empty-learning-card" icon={<LoaderCircle className="spin" size={20} />}>
            <span>正在加载可选实验</span>
          </MobileEmptyState>
        ) : data ? (
          <>
            <section className="posttest-context">
              <div>
                <p>自主测评</p>
                <h2>选择本轮要练的实验</h2>
                <div className="assessment-composition">
                  <span>已选 {selectedIds.size} 个实验</span>
                  <span>目标 {questionCount} 题</span>
                  <span>按点位覆盖抽题</span>
                  <span>每实验最多 {data.settings.max_questions_per_experiment} 题</span>
                </div>
              </div>
              <span>{experiments.length} 项</span>
            </section>

            {disabled ? <div className="form-hint">老师暂未开放自主测评，请使用智能组卷。</div> : null}
            {error ? <div className="form-error">{error}</div> : null}

            <div className="custom-assessment-toolbar">
              <label className="custom-search-field">
                <Search size={18} />
                <MobileField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索实验名称、章节或编号" />
              </label>
              <div className="custom-count-row" aria-label="选择题数">
                {countOptions.map((count) => (
                  <button
                    type="button"
                    key={count}
                    className={questionCount === count ? "selected" : ""}
                    disabled={disabled}
                    onClick={() => setQuestionCount(count)}
                  >
                    {count} 题
                  </button>
                ))}
              </div>
              {selectedExperiments.length ? (
                <div className="custom-selection-summary" aria-label="已选实验">
                  {selectedExperiments.slice(0, 5).map((option) => (
                    <span key={option.id}>{option.title}</span>
                  ))}
                  {selectedExperiments.length > 5 ? <span>+{selectedExperiments.length - 5}</span> : null}
                </div>
              ) : null}
            </div>

            {filteredExperiments.length ? (
              <div className="custom-experiment-list">
                {filteredExperiments.map((option) => {
                  const selected = selectedIds.has(option.id);
                  return (
                    <button
                      type="button"
                      key={option.id}
                      className={`custom-experiment-option${selected ? " selected" : ""}`}
                      disabled={disabled || option.question_count <= 0}
                      aria-pressed={selected}
                      onClick={() => toggleExperiment(option.id)}
                    >
                      <span className="custom-experiment-check">{selected ? <Check size={17} /> : null}</span>
                      <span className="custom-experiment-copy">
                        <b>{option.title}</b>
                        <small>{option.parent_title || option.code}</small>
                      </span>
                      <em>{option.question_count} 道可用题</em>
                    </button>
                  );
                })}
              </div>
            ) : (
              <MobileEmptyState className="empty-learning-card" icon={<FlaskConical size={20} />}>
                <span>没有匹配的实验</span>
              </MobileEmptyState>
            )}

            <MobileButton
              className="primary-action full custom-start-action"
              type="button"
              loading={starting}
              disabled={disabled || !selectedIds.size}
              onClick={() => void startCustomAssessment()}
            >
              {starting ? <LoaderCircle className="spin" size={18} /> : <ClipboardList size={18} />}
              <span>{starting ? "正在组卷" : "开始自主测评"}</span>
            </MobileButton>
          </>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>暂时无法加载自主测评。</span>
          </MobileEmptyState>
        )}
      </section>
    </DetailPageFrame>
  );
}
