import type { CSSProperties } from "react";
import type { StudentLearningElementBadge } from "../../api";
import { ElementTileContent } from "../periodic-table/PeriodicElementCell";
import { elementEnglishName, elementTileStyle } from "../periodic-table/periodicHelpers";

export function LearningElementChips({
  elements,
  activeSymbol,
  onSelectElement,
}: {
  elements: StudentLearningElementBadge[];
  activeSymbol: string;
  onSelectElement: (symbol: string) => void;
}) {
  return (
    <section className="element-chip-panel" aria-label="选择族内元素">
      <div className="element-chip-row" style={{ "--element-count": Math.max(elements.length, 1) } as CSSProperties}>
        {elements.map((element) => (
          <button
            className={element.symbol === activeSymbol ? "element-chip active" : "element-chip"}
            key={element.symbol}
            type="button"
            style={elementTileStyle(element)}
            aria-label={`${element.symbol} ${elementEnglishName(element)} ${element.name}`}
            aria-pressed={element.symbol === activeSymbol}
            onClick={() => onSelectElement(element.symbol)}
          >
            <ElementTileContent element={element} />
          </button>
        ))}
      </div>
    </section>
  );
}
