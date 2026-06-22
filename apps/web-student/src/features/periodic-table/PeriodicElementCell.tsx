import type { StudentLearningElementBadge } from "../../api";
import { elementEnglishName, periodicMetaForElement } from "./periodicHelpers";

export function ElementTileContent({ element }: { element: StudentLearningElementBadge }) {
  const periodicElement = periodicMetaForElement(element.symbol);
  const atomicNumber = element.atomic_number ?? periodicElement?.atomicNumber ?? "";
  const englishName = elementEnglishName(element);
  return (
    <>
      <small>{atomicNumber}</small>
      <strong>{element.symbol}</strong>
      <span title={englishName}>{englishName}</span>
    </>
  );
}
