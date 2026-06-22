import type { AtomViewerElement } from "./atomTypes";

export type OrbitalKind = 's' | 'p' | 'd' | 'f';

export type OrbitalVariant =
  | 'all'
  | 's'
  | 'px'
  | 'py'
  | 'pz'
  | 'dxy'
  | 'dxz'
  | 'dyz'
  | 'dx2-y2'
  | 'dz2'
  | 'fz3'
  | 'fxz2'
  | 'fyz2'
  | 'fxyz'
  | 'fz(x2-y2)'
  | 'fx(x2-3y2)'
  | 'fy(3x2-y2)';

export type OrbitalSubshell = {
  id: string;
  n: number;
  l: OrbitalKind;
  electrons: number;
  label: string;
};

export type OrbitalChoiceOption = {
  id: string;
  label: string;
  subshell?: OrbitalSubshell;
  variant?: OrbitalVariant;
  occupancy?: number;
  isAuto?: boolean;
};

export type ResolvedOrbitalChoice = {
  id: string;
  label: string;
  isAuto: boolean;
  subshell: OrbitalSubshell;
  variant: OrbitalVariant;
  slots: number[];
  slotLabels: string[];
};

export const ORBITAL_SLOT_COUNTS: Record<OrbitalKind, number> = {
  s: 1,
  p: 3,
  d: 5,
  f: 7,
};

export const ORBITAL_CAPACITY: Record<OrbitalKind, number> = {
  s: 2,
  p: 6,
  d: 10,
  f: 14,
};

const SLOT_LABELS: Record<OrbitalKind, string[]> = {
  s: ['s'],
  p: ['px', 'py', 'pz'],
  d: ['dxy', 'dxz', 'dyz', 'dx2-y2', 'dz2'],
  f: ['fz3', 'fxz2', 'fyz2', 'fxyz', 'fz(x2-y2)', 'fx(x2-3y2)', 'fy(3x2-y2)'],
};

function formatSubshell(n: number, l: OrbitalKind, electrons: number) {
  return `${n}${l}${electrons}`;
}

export function distributeSubshellElectrons(electrons: number, slotCount: number) {
  const slots = Array.from({ length: slotCount }, () => 0);
  let remaining = electrons;

  for (let index = 0; index < slotCount && remaining > 0; index += 1) {
    slots[index] += 1;
    remaining -= 1;
  }

  for (let index = 0; index < slotCount && remaining > 0; index += 1) {
    slots[index] += 1;
    remaining -= 1;
  }

  return slots;
}

export function getSlotLabels(l: OrbitalKind) {
  return SLOT_LABELS[l];
}

export function getVariantSlotIndex(l: OrbitalKind, variant: OrbitalVariant) {
  if (variant === 'all') {
    return -1;
  }

  return SLOT_LABELS[l].indexOf(variant);
}

export function parseValenceSubshells(element: AtomViewerElement): OrbitalSubshell[] {
  const withoutCore = element.electronConfiguration.replace(/\[[^\]]+\]/g, ' ').trim();
  const source = withoutCore.length > 0 ? withoutCore : element.electronConfiguration;
  const regex = /(\d+)\s*([spdf])\s*(\d+)/g;
  const subshells: OrbitalSubshell[] = [];
  let match: RegExpExecArray | null;

  while ((match = regex.exec(source)) !== null) {
    const n = Number.parseInt(match[1], 10);
    const l = match[2] as OrbitalKind;
    const electrons = Number.parseInt(match[3], 10);

    subshells.push({
      id: `${n}${l}`,
      n,
      l,
      electrons,
      label: formatSubshell(n, l, electrons),
    });
  }

  return subshells;
}

export function getSelectableSubshells(element: AtomViewerElement) {
  return parseValenceSubshells(element);
}

export function getAutoSubshell(subshells: OrbitalSubshell[]) {
  const openF = subshells.find((subshell) => subshell.l === 'f' && subshell.electrons < ORBITAL_CAPACITY.f);
  const openD = subshells.find((subshell) => subshell.l === 'd' && subshell.electrons < ORBITAL_CAPACITY.d);
  const outerP = subshells.find((subshell) => subshell.l === 'p');

  return openF ?? openD ?? outerP ?? subshells[0];
}

export function getOrbitalChoiceOptions(element: AtomViewerElement): OrbitalChoiceOption[] {
  const subshells = getSelectableSubshells(element);
  const autoSubshell = getAutoSubshell(subshells);
  if (!autoSubshell) {
    return [];
  }
  const options: OrbitalChoiceOption[] = [
    {
      id: 'auto',
      label: autoSubshell ? `Auto ${autoSubshell.label}` : 'Auto',
      isAuto: true,
    },
  ];

  subshells.forEach((subshell) => {
    const slotCount = ORBITAL_SLOT_COUNTS[subshell.l];
    const slots = distributeSubshellElectrons(subshell.electrons, slotCount);

    options.push({
      id: `${subshell.id}:all`,
      label: slotCount === 1 ? subshell.label : `${subshell.label} all`,
      subshell,
      variant: 'all',
      occupancy: subshell.electrons,
    });

    if (slotCount > 1) {
      SLOT_LABELS[subshell.l].forEach((slotLabel, slotIndex) => {
        options.push({
          id: `${subshell.id}:${slotLabel}`,
          label: `${subshell.id} ${slotLabel}`,
          subshell,
          variant: slotLabel as OrbitalVariant,
          occupancy: slots[slotIndex] ?? 0,
        });
      });
    }
  });

  return options;
}

export function resolveOrbitalChoice(element: AtomViewerElement, selectedId: string): ResolvedOrbitalChoice {
  const options = getOrbitalChoiceOptions(element);
  const subshells = getSelectableSubshells(element);
  const autoSubshell = getAutoSubshell(subshells) ?? subshells[0];
  const selectedOption = options.find((option) => option.id === selectedId) ?? options[0];
  if (!selectedOption || !autoSubshell) {
    throw new Error(`No orbital choice available for ${element.symbol}`);
  }
  const subshell = selectedOption.subshell ?? autoSubshell;
  const variant = selectedOption.variant ?? 'all';
  const slotCount = ORBITAL_SLOT_COUNTS[subshell.l];

  return {
    id: selectedOption.id,
    label: selectedOption.isAuto
      ? slotCount === 1
        ? subshell.label
        : `${subshell.label} all`
      : selectedOption.label,
    isAuto: selectedOption.isAuto === true,
    subshell,
    variant,
    slots: distributeSubshellElectrons(subshell.electrons, slotCount),
    slotLabels: SLOT_LABELS[subshell.l],
  };
}
