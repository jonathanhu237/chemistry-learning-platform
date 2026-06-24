import { useMemo, useRef, useState, type CSSProperties } from "react";
import { Search } from "lucide-react";
import { periodicElements } from "../../periodic";
import type { AreaId } from "./periodicHelpers";
import { areaInk, areaSwatches, periodicAreaByAreaId, periodicAreaIdForElement, periodicAreaOrder, periodicGridColumnForElement, periodicGridRowForPeriod, periodicLegendLabelByAreaId, periodicPeriodLabels } from "./periodicHelpers";
import { exactPeriodicElementMatches, normalizePeriodicElementQuery, searchPeriodicElements, type PeriodicElementSearchMeta } from "./periodicSearch";

export function PeriodicTable({
  onSelectArea,
  onSelectElement,
}: {
  onSelectArea: (areaId: AreaId, triggerElement: HTMLElement) => void;
  onSelectElement: (element: PeriodicElementSearchMeta, triggerElement: HTMLElement) => boolean;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchMessage, setSearchMessage] = useState("");
  const isComposingRef = useRef(false);
  const groupNumbers = Array.from({ length: 18 }, (_, index) => index + 1);
  const normalizedSearchQuery = normalizePeriodicElementQuery(searchQuery);
  const matchedElements = useMemo(() => searchPeriodicElements(searchQuery), [searchQuery]);
  const matchedSymbols = useMemo(() => new Set(matchedElements.map((element) => element.symbol)), [matchedElements]);
  const chooseElement = (element: PeriodicElementSearchMeta, triggerElement: HTMLElement) => {
    const handled = onSelectElement(element, triggerElement);
    setSearchMessage(handled ? "" : `暂无 ${element.symbol} 的学习章节`);
  };
  const resolveSearch = (value: string, triggerElement: HTMLElement, options: { immediate: boolean }) => {
    const normalizedValue = normalizePeriodicElementQuery(value);
    if (!normalizedValue) {
      setSearchMessage("");
      return;
    }
    const exactMatches = exactPeriodicElementMatches(value);
    const matches = searchPeriodicElements(value);
    if (!matches.length) {
      setSearchMessage("不存在该元素");
      return;
    }
    if (exactMatches.length === 1 || (options.immediate && matches.length === 1 && normalizedValue.length >= 2)) {
      chooseElement(exactMatches[0] || matches[0], triggerElement);
      return;
    }
    setSearchMessage(matches.length === 1 ? "按回车进入该元素" : "找到多个元素，请点高亮元素选择");
  };

  return (
    <section className="periodic-card" aria-label="元素周期表选择区">
      <div className="periodic-card-head">
        <div>
          <p>元素周期表</p>
          <h3>选择元素分区</h3>
        </div>
        <label className="periodic-search" aria-label="搜索元素">
          <Search size={15} />
          <input
            value={searchQuery}
            aria-label="搜索元素"
            placeholder="搜索元素"
            onCompositionStart={() => {
              isComposingRef.current = true;
            }}
            onCompositionEnd={(event) => {
              isComposingRef.current = false;
              resolveSearch(event.currentTarget.value, event.currentTarget, { immediate: true });
            }}
            onChange={(event) => {
              const nextValue = event.target.value;
              setSearchQuery(nextValue);
              if (!isComposingRef.current) resolveSearch(nextValue, event.currentTarget, { immediate: true });
            }}
            onKeyDown={(event) => {
              if (event.key !== "Enter") return;
              event.preventDefault();
              resolveSearch(event.currentTarget.value, event.currentTarget, { immediate: false });
            }}
          />
        </label>
      </div>
      {searchMessage ? <div className="periodic-search-message">{searchMessage}</div> : null}
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
              onClick={(event) => chooseElement(element, event.currentTarget)}
            >
              <span>{element.symbol}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
