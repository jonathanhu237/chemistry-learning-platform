import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import type { StudentLearningElementBadge, StudentLearningProfile } from "../../api";
import { ElementTileContent } from "../periodic-table/PeriodicElementCell";
import { elementTileStyle } from "../periodic-table/periodicHelpers";
import { AtomViewerZdog } from "./AtomViewerZdog";
import { learningElementToAtomModel } from "./learningAtomAdapter";
import { OrbitalSpinDisplay } from "./OrbitalSpinDisplay";
import { getOrbitalChoiceOptions, resolveOrbitalChoice, type OrbitalChoiceOption, type OrbitalKind } from "./orbitalOptions";
import type { AtomMode } from "./atomTypes";

const orbitalKindLabels: Record<OrbitalKind, string> = {
  s: "s 轨道",
  p: "p 轨道",
  d: "d 轨道",
  f: "f 轨道",
};

function displayOrbitalLabel(label: string) {
  return label.replace("Auto ", "").replace(" all", " 全部").replace("all", "全部");
}

function getDefaultOrbitalId(element: ReturnType<typeof learningElementToAtomModel>, options: OrbitalChoiceOption[]) {
  const autoChoice = resolveOrbitalChoice(element, "auto");
  const matchingAllOption = options.find(
    (option) => !option.isAuto && option.subshell?.id === autoChoice.subshell.id && option.variant === "all",
  );
  return matchingAllOption?.id ?? options.find((option) => !option.isAuto)?.id ?? "auto";
}

function groupOrbitalOptions(options: OrbitalChoiceOption[]) {
  const orderedKinds = options.reduce<OrbitalKind[]>((kinds, option) => {
    const kind = option.subshell?.l;
    if (!option.isAuto && kind && !kinds.includes(kind)) {
      kinds.push(kind);
    }
    return kinds;
  }, []);

  return orderedKinds.map((kind) => ({
    kind,
    choices: options.filter((option) => !option.isAuto && option.subshell?.l === kind),
  })).filter((group) => group.choices.length > 0);
}

export function LearningAtomModelCard({
  element,
  profile,
}: {
  element: StudentLearningElementBadge;
  profile: StudentLearningProfile;
}) {
  const [mode, setMode] = useState<AtomMode>("bohr");
  const [isPlaying, setIsPlaying] = useState(true);
  const [resetSignal, setResetSignal] = useState(0);
  const [selectedOrbitalId, setSelectedOrbitalId] = useState("");
  const model = useMemo(() => learningElementToAtomModel(element, profile), [element, profile]);
  const orbitalOptions = useMemo(() => (model.unavailableReason ? [] : getOrbitalChoiceOptions(model)), [model]);
  const canShowOrbital = orbitalOptions.length > 0;
  const currentMode = mode === "orbital" && !canShowOrbital ? "bohr" : mode;
  const groupedOrbitalOptions = useMemo(() => groupOrbitalOptions(orbitalOptions), [orbitalOptions]);
  const resolvedSelectedOrbitalId = useMemo(() => {
    if (!canShowOrbital) return "";
    const selectedOption = orbitalOptions.find((option) => !option.isAuto && option.id === selectedOrbitalId);
    return selectedOption?.id ?? getDefaultOrbitalId(model, orbitalOptions);
  }, [canShowOrbital, model, orbitalOptions, selectedOrbitalId]);
  const selectedOrbital = useMemo(() => {
    if (!canShowOrbital) return undefined;
    return resolveOrbitalChoice(model, resolvedSelectedOrbitalId);
  }, [canShowOrbital, model, resolvedSelectedOrbitalId]);

  useEffect(() => {
    setSelectedOrbitalId("");
    setIsPlaying(true);
    setResetSignal((value) => value + 1);
  }, [element.symbol]);

  useEffect(() => {
    if (mode === "orbital" && !canShowOrbital) {
      setMode("bohr");
    }
  }, [canShowOrbital, mode]);

  const facts = [
    { key: "mass", label: "相对原子质量", value: model.relativeAtomicMass },
    { key: "position", label: "族 / 周期 / 区", value: `${model.group || "-"}族 / ${model.period || "-"}周期 / ${model.block}区` },
    { key: "state", label: "20°C 状态", value: model.stateAt20C },
    { key: "density", label: "密度", value: model.density },
    { key: "configuration", label: "电子排布", value: model.electronConfiguration || "未整理" },
  ];

  return (
    <section
      className="selected-element-panel atom-model-card"
      style={{ "--atom-accent": model.accent } as CSSProperties}
      aria-label={`${element.name}元素特性`}
    >
      <div className="atom-model-head">
        <div className="selected-element-symbol atom-model-symbol" style={elementTileStyle(element)}>
          <ElementTileContent element={element} />
        </div>
        <div className="atom-model-title">
          <p>当前元素特性</p>
          <h2>{element.name}在{profile.family_name || profile.title}中的位置</h2>
          <span>{element.note || `${model.englishName} · ${model.category}`}</span>
        </div>
      </div>

      <div className="atom-model-layout">
        <div className="atom-model-visual">
          <div className="atom-model-toolbar" aria-label="原子模型控制">
            <div className="atom-mode-segment" role="tablist" aria-label="模型模式">
              <button
                className={currentMode === "bohr" ? "active" : ""}
                type="button"
                role="tab"
                aria-selected={currentMode === "bohr"}
                onClick={() => setMode("bohr")}
              >
                电子层
              </button>
              <button
                className={currentMode === "orbital" ? "active" : ""}
                type="button"
                role="tab"
                aria-selected={currentMode === "orbital"}
                disabled={!canShowOrbital}
                onClick={() => setMode("orbital")}
              >
                轨道
              </button>
            </div>
            <button
              className="atom-icon-button"
              type="button"
              aria-label={isPlaying ? "暂停动画" : "播放动画"}
              title={isPlaying ? "暂停动画" : "播放动画"}
              onClick={() => setIsPlaying((value) => !value)}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            </button>
            <button
              className="atom-icon-button"
              type="button"
              aria-label="重置视角"
              title="重置视角"
              onClick={() => setResetSignal((value) => value + 1)}
            >
              <RotateCcw size={16} />
            </button>
          </div>

          {model.unavailableReason ? (
            <div className="atom-model-empty" role="status">
              {model.unavailableReason}
            </div>
          ) : (
            <AtomViewerZdog
              element={model}
              mode={currentMode}
              isPlaying={isPlaying}
              resetSignal={resetSignal}
              orbitalChoice={selectedOrbital}
            />
          )}

          {currentMode === "orbital" && selectedOrbital ? (
            <div className="orbital-control-row">
              <label>
                <span>显示轨道</span>
                <select value={resolvedSelectedOrbitalId} onChange={(event) => setSelectedOrbitalId(event.target.value)}>
                  {groupedOrbitalOptions.map((group) => (
                    <optgroup key={group.kind} label={orbitalKindLabels[group.kind]}>
                      {group.choices.map((option) => (
                        <option key={option.id} value={option.id}>
                          {displayOrbitalLabel(option.label)}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </label>
              <OrbitalSpinDisplay
                occupancy={selectedOrbital.slots}
                slotLabels={selectedOrbital.slotLabels}
                subshellLabel={displayOrbitalLabel(selectedOrbital.label)}
              />
            </div>
          ) : null}
        </div>

        <div className="atom-model-facts" aria-label={`${element.name}RSC事实盒`}>
          {facts.map((fact) => (
            <div className="atom-fact-chip" key={fact.key}>
              <span>{fact.label}</span>
              <strong>{fact.value}</strong>
            </div>
          ))}
          <div className="atom-teaching-cue">
            <span>教学提示</span>
            <strong>常见化合价：{model.oxidationStates}</strong>
            {model.redoxTendency ? <small>{model.redoxTendency}</small> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
