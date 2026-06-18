import { useEffect, useState } from "react";
import { ChevronRight, FlaskConical, LoaderCircle, MessageCircle, PlayCircle } from "lucide-react";
import { StudentExperimentGroupResponse, errorMessage, getStudentExperimentGroup } from "../../api";
import { MobileButton } from "../../mobile/primitives";
import { FinishLearningAction } from "../../shared/learning/FinishLearningAction";
import { LearningState } from "../../shared/mobile/LearningState";
import { PageBar } from "../../shared/mobile/PageBar";
import { compactText } from "../../shared/utils/text";
import type { AssistantContext } from "../assistant/assistantContext";
import { stripExperimentPrefix } from "./experimentFormat";

export function ExperimentGroupPanel({
  parentCode,
  onBack,
  onSelectExperiment,
  onFinishLearning,
  finishing,
  finishError,
  assistantEnabled,
  onOpenAssistant,
}: {
  parentCode: string;
  onBack: () => void;
  onSelectExperiment: (experimentId: string) => void;
  onFinishLearning: () => void;
  finishing: boolean;
  finishError: string;
  assistantEnabled: boolean;
  onOpenAssistant: (context: AssistantContext) => void;
}) {
  const [group, setGroup] = useState<StudentExperimentGroupResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentExperimentGroup(parentCode)
      .then((payload) => {
        if (!cancelled) setGroup(payload);
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
  }, [parentCode]);

  const assistantContext: AssistantContext | null = group
    ? {
        context_type: "experiment_group",
        context_title: stripExperimentPrefix(group.parent_title),
        context_summary: compactText([
          `实验组：${group.parent_title}`,
          `所属区域：${group.area_name}`,
          `实验点：${group.experiments.map((experiment) => experiment.title).join("、")}`,
        ]),
        chapter_id: group.experiments[0]?.chapter_ids[0] || null,
        prompts: ["这一组实验重点是什么？", "我应该按什么顺序看？", "这些实验会考什么现象？"],
      }
    : null;

  return (
    <section className="learning-panel" aria-label="实验列表">
      <PageBar title={group ? stripExperimentPrefix(group.parent_title) : "实验列表"} onBack={onBack} />
      {loading ? <LearningState icon={<LoaderCircle className="spin" size={23} />} text="正在加载实验列表" /> : null}
      {error ? <LearningState icon={<FlaskConical size={23} />} text={error} /> : null}
      {group ? (
        <div className="experiment-list">
          {group.experiments.map((experiment) => (
            <button className="experiment-card" key={experiment.id} type="button" onClick={() => onSelectExperiment(experiment.id)}>
              <div className="experiment-thumb">
                <PlayCircle size={32} />
                <strong>{experiment.code}</strong>
              </div>
              <div>
                <p>{experiment.module_title || group.area_name}</p>
                <h3>{experiment.title}</h3>
                <span>
                  视频 {experiment.published_video_count || experiment.video_candidate_count} / 练习 {experiment.question_count}
                </span>
              </div>
              <ChevronRight size={18} />
            </button>
          ))}
        </div>
      ) : null}
      {group && assistantEnabled && assistantContext ? (
        <MobileButton className="secondary-action full context-assistant-action" type="button" variant="secondary" onClick={() => onOpenAssistant(assistantContext)}>
          <MessageCircle size={18} />
          <span>带着本组实验去问答</span>
        </MobileButton>
      ) : null}
      {group ? <FinishLearningAction loading={finishing} error={finishError} onClick={onFinishLearning} /> : null}
    </section>
  );
}
