export type AtomMode = "bohr" | "orbital";

export type AtomViewerElement = {
  atomicNumber: number;
  symbol: string;
  name: string;
  englishName: string;
  category: string;
  group: string;
  period: number;
  block: "s" | "p" | "d" | "f";
  stateAt20C: string;
  density: string;
  oxidationStates: string;
  relativeAtomicMass: string;
  electronConfiguration: string;
  shells: number[];
  accent: string;
  sourceUrl: string | null;
  sourceLabel: string;
  teachingNote: string;
  redoxTendency: string;
  unavailableReason?: string;
};
