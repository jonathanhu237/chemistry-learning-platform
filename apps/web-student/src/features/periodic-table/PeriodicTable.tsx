import { useMemo, useState, type CSSProperties } from "react";
import { Atom } from "lucide-react";
import { periodicElements } from "../../periodic";
import type { AreaId } from "./periodicHelpers";
import { areaInk, areaSwatches, periodicAreaByAreaId, periodicAreaIdForElement, periodicAreaOrder, periodicGridColumnForElement, periodicGridRowForPeriod, periodicLegendLabelByAreaId, periodicPeriodLabels } from "./periodicHelpers";

export function PeriodicTable({
  onSelectArea,
}: {
  onSelectArea: (areaId: AreaId, triggerElement: HTMLElement) => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const groupNumbers = Array.from({ length: 18 }, (_, index) => index + 1);
  const normalizedSearchQuery = searchQuery.trim().toLowerCase();
  const matchedElements = useMemo(() => {
    if (!normalizedSearchQuery) return [];
    return periodicElements.filter((element) => {
      const symbol = element.symbol.toLowerCase();
      const name = element.name.toLowerCase();
      return symbol.includes(normalizedSearchQuery) || name.includes(normalizedSearchQuery);
    });
  }, [normalizedSearchQuery]);
  const matchedSymbols = useMemo(() => new Set(matchedElements.map((element) => element.symbol)), [matchedElements]);

  return (
    <section className="periodic-card" aria-label="元素周期表选择区">
      <div className="periodic-card-head">
        <div>
          <p>元素周期表</p>
          <h3>选择元素分区</h3>
        </div>
        <label className="periodic-search" aria-label="搜索元素">
          <Atom size={15} />
          <input
            value={searchQuery}
            aria-label="搜索元素"
            placeholder="搜索元素"
            onChange={(event) => setSearchQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key !== "Enter" || !matchedElements[0]) return;
              onSelectArea(periodicAreaIdForElement(matchedElements[0]), event.currentTarget);
            }}
          />
        </label>
      </div>
      <div className="area-legend" aria-label="元素区图例">
        {periodicAreaOrder.map((areaId) => {
          return (
            <button
              key={areaId}
              type="button"
              style={{ "--area-color": areaSwatches[areaId], "--area-ink": areaInk[areaId] } as CSSProperties}
              onClick={(event) => onSelectArea(areaId, event.currentTarget)}
              aria-label={periodicLegendLabelByAreaId[areaId]}
            >
              <i />
              <span>{periodicLegendLabelByAreaId[areaId]}</span>
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
          const isSearchMatch = normalizedSearchQuery ? matchedSymbols.has(element.symbol) : false;
          return (
            <button
              key={element.atomicNumber}
              type="button"
              className={[
                "element-cell",
                normalizedSearchQuery && !isSearchMatch ? "search-dimmed" : "",
                isSearchMatch ? "search-match" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={{
                gridColumn: periodicGridColumnForElement(element),
                gridRow: periodicGridRowForPeriod(element.period),
                background: areaSwatches[areaId],
                "--cell-ink": areaInk[areaId],
              } as CSSProperties}
              aria-label={`${element.symbol} ${element.name}，选择${periodicAreaByAreaId[areaId]}`}
              title={`${element.symbol} ${element.name}`}
              onClick={(event) => onSelectArea(areaId, event.currentTarget)}
            >
              <span>{element.symbol}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
