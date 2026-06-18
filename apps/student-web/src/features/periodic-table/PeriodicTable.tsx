import type { CSSProperties } from "react";
import { Atom } from "lucide-react";
import { periodicElements } from "../../periodic";
import type { AreaId } from "./periodicHelpers";
import { areaInk, areaSwatches, periodicAreaByAreaId, periodicAreaIdForElement, periodicAreaOrder, periodicGridColumnForElement, periodicGridRowForPeriod, periodicLegendLabelByAreaId, periodicPeriodLabels } from "./periodicHelpers";

export function PeriodicTable({
  selectedArea,
  recommendedArea,
  recommendedCueLabel,
  recommendedSymbols,
  learnableSymbols,
  onSelectArea,
}: {
  selectedArea: AreaId;
  recommendedArea?: AreaId | null;
  recommendedCueLabel?: string | null;
  recommendedSymbols: ReadonlySet<string>;
  learnableSymbols: ReadonlySet<string>;
  onSelectArea: (areaId: AreaId) => void;
}) {
  const groupNumbers = Array.from({ length: 18 }, (_, index) => index + 1);

  return (
    <section className="periodic-card" aria-label="元素周期表选择区">
      <div className="periodic-card-head">
        <div>
          <p>周期表入口</p>
          <h3>按族进入章节</h3>
        </div>
        <Atom size={22} />
      </div>
      <div className="area-legend" aria-label="元素区图例">
        {periodicAreaOrder.map((areaId) => {
          const isSelected = selectedArea === areaId;
          const isRecommended = recommendedArea === areaId;
          return (
            <button
              key={areaId}
              type="button"
              className={[isSelected ? "selected" : "", isRecommended ? "recommended-area" : ""].filter(Boolean).join(" ")}
              style={{ "--area-color": areaSwatches[areaId], "--area-ink": areaInk[areaId] } as CSSProperties}
              onClick={() => onSelectArea(areaId)}
              aria-label={`${periodicLegendLabelByAreaId[areaId]}${isRecommended ? `，推荐学习区域${recommendedCueLabel ? `，推荐${recommendedCueLabel}` : ""}` : ""}`}
              aria-pressed={isSelected}
            >
              <i />
              <span>{periodicLegendLabelByAreaId[areaId]}</span>
              {isRecommended ? (
                <em>
                  <span>推荐学习</span>
                  {recommendedCueLabel ? <b>{recommendedCueLabel}</b> : null}
                </em>
              ) : null}
            </button>
          );
        })}
      </div>
      <div className="periodic-caption">族（IUPAC 编号）</div>
      <div className="periodic-grid">
        {groupNumbers.map((group) => (
          <div aria-label={`${group}族`} className="group-number" key={group} style={{ gridColumn: group + 1, gridRow: 1 }}>
            {group}
          </div>
        ))}
        {periodicPeriodLabels.map((period, index) => (
          <div className="period-number" key={period} style={{ gridColumn: 1, gridRow: periodicGridRowForPeriod(index + 1) }}>
            {period}
          </div>
        ))}
        {periodicElements.map((element) => {
          const areaId = periodicAreaIdForElement(element);
          const selected = areaId === selectedArea;
          const learnable = selected && learnableSymbols.has(element.symbol);
          const recommended = recommendedSymbols.has(element.symbol);
          return (
            <button
              key={element.atomicNumber}
              type="button"
              className={[
                "element-cell",
                selected ? "selected-area" : "muted-area",
                learnable ? "learnable-element" : "",
                recommended ? "recommended-element" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={{
                gridColumn: periodicGridColumnForElement(element),
                gridRow: periodicGridRowForPeriod(element.period),
                background: areaSwatches[areaId],
                "--cell-ink": areaInk[areaId],
              } as CSSProperties}
              aria-label={`${element.symbol} ${element.name}，${recommended ? "推荐学习，" : ""}${learnable ? "当前选区可学习" : `选择${periodicAreaByAreaId[areaId]}`}`}
              title={`${element.symbol} ${element.name}${recommended ? " · 推荐学习" : ""}${learnable ? " · 可学习" : ""}`}
              onClick={() => onSelectArea(areaId)}
            >
              {learnable ? <span>{element.symbol}</span> : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
