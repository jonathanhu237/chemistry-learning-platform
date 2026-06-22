import { useCallback, useEffect, useRef } from 'react';
import Zdog from 'zdog';
import {
  getSlotLabels,
  type OrbitalKind,
  type OrbitalSubshell,
  type OrbitalVariant,
  type ResolvedOrbitalChoice,
} from './orbitalOptions';
import type { AtomMode, AtomViewerElement } from './atomTypes';

type AtomViewerZdogProps = {
  element: AtomViewerElement;
  mode: AtomMode;
  isPlaying: boolean;
  resetSignal: number;
  orbitalChoice?: ResolvedOrbitalChoice;
};

type Rotation = {
  x: number;
  y: number;
  z: number;
};

type OrbitalVector = {
  x: number;
  y: number;
  z: number;
};

type OrbitalPlane = 'xy' | 'xz' | 'yz';

type BohrElectron = {
  anchor: Zdog.Anchor;
  baseAngle: number;
  speed: number;
};

type BohrShellRig = {
  foldAnchor: Zdog.Anchor;
  spinAnchor: Zdog.Anchor;
  spinDirection: number;
  phase: number;
};

type OrbitalPulse = {
  anchor: Zdog.Anchor;
  n: number;
};

type AxisKey = 'x' | 'y' | 'z';

type AxisGlyphRig = {
  zAnchor: Zdog.Anchor;
  yAnchor: Zdog.Anchor;
  xAnchor: Zdog.Anchor;
};

type Runtime = {
  illustration: Zdog.Illustration;
  atomAnchor: Zdog.Anchor;
  nucleusAnchor: Zdog.Anchor;
  mode: AtomMode;
  bohrElectrons: BohrElectron[];
  bohrShellRigs: BohrShellRig[];
  orbitalPulses: OrbitalPulse[];
  axisGlyphs: Record<AxisKey, AxisGlyphRig> | null;
  resize: () => void;
};

const DEFAULT_ROTATION: Rotation = { x: -0.28, y: 0.42, z: 0 };

const SHELL_COLORS = ['#4fc3f7', '#7c83f5', '#ff6b9d', '#ffe066', '#7ee8a2', '#ffaa5c', '#ce93d8'];

const GOOGLE_ORBIT_LOOP_SECONDS = 13.333333333333334;
const TAU = Math.PI * 2;

const GOOGLE_FAN_Y_DEGREES: Record<number, number[]> = {
  1: [0],
  2: [0, 0],
  3: [0, 70, -70],
  4: [0, 90, 0, -90],
  5: [0, 58, 82, -82, -58],
  6: [0, 56, 78, 24, -78, -56],
  7: [0, 51, 77, 26, -26, -77, -51],
};

const ORBITAL_COLORS: Record<OrbitalKind, string> = {
  s: '#64d8ff',
  p: '#9af7b0',
  d: '#ffc46b',
  f: '#d797ff',
};

const ORBITAL_PHASE_COLORS = {
  positive: '#65ddff',
  negative: '#ff7aa8',
};

const AXIS_COLORS = {
  x: '#ff6b6b',
  y: '#75f0a1',
  z: '#7aa7ff',
};

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function positiveModulo(value: number, divisor: number) {
  return ((value % divisor) + divisor) % divisor;
}

function degreesToRadians(degrees: number) {
  return (degrees * Math.PI) / 180;
}

function getGoogleFanY(shellCount: number, shellIndex: number) {
  const exact = GOOGLE_FAN_Y_DEGREES[shellCount];

  if (exact) {
    return degreesToRadians(exact[shellIndex] ?? 0);
  }

  const center = (shellCount - 1) / 2;
  const normalized = center === 0 ? 0 : (shellIndex - center) / center;
  return normalized * degreesToRadians(78);
}

function smootherStep(value: number) {
  const t = clamp(value, 0, 1);
  return t * t * t * (t * (t * 6 - 15) + 10);
}

function getGoogleRigPose(time: number, rig: BohrShellRig) {
  const loopProgress = positiveModulo(time + rig.phase, GOOGLE_ORBIT_LOOP_SECONDS) / GOOGLE_ORBIT_LOOP_SECONDS;
  const pacedLoopProgress = positiveModulo(
    loopProgress + Math.sin(loopProgress * TAU) * 0.018 + Math.sin(loopProgress * TAU * 2 + 0.7) * 0.008,
    1,
  );
  const secondHalfProgress = loopProgress < 0.5 ? 0 : smootherStep((loopProgress - 0.5) * 2);

  return {
    spinY: pacedLoopProgress * TAU * rig.spinDirection,
    foldX: secondHalfProgress * TAU * rig.spinDirection,
  };
}

function copyRotation(rotation: Rotation): Rotation {
  return { x: rotation.x, y: rotation.y, z: rotation.z };
}

function hexToRgba(hex: string, alpha: number) {
  const normalized = hex.replace('#', '');
  const value = Number.parseInt(normalized, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;

  return `rgba(${r}, ${g}, ${b}, ${clamp(alpha, 0, 1)})`;
}

function orbitalRadius(n: number) {
  return 1.5 + n * 1.1;
}

function orbitalVisualRadius(orbital: OrbitalSubshell, variant: OrbitalVariant) {
  const radius = orbitalRadius(orbital.n);

  if (orbital.l === 's') {
    return radius * 0.5;
  }

  if (orbital.l === 'p') {
    return variant === 'all' ? radius * 0.9 : radius * 0.68;
  }

  if (orbital.l === 'd') {
    return variant === 'all' ? radius * 0.82 : radius * 0.62;
  }

  return variant === 'all' ? radius * 0.74 : radius * 0.58;
}

function orbitalOpacity(n: number, maxN: number) {
  const normalizedN = (n - 1) / Math.max(maxN - 1, 1);
  return 0.16 + normalizedN * 0.2;
}

function assignRotation(anchor: Zdog.Anchor, rotation: Rotation) {
  anchor.rotate.x = rotation.x;
  anchor.rotate.y = rotation.y;
  anchor.rotate.z = rotation.z;
}

function createNucleus(addTo: Zdog.Anchor, element: AtomViewerElement) {
  const nucleusAnchor = new Zdog.Anchor({ addTo });
  const numNucleons = Math.min(element.atomicNumber, 20);

  new Zdog.Shape({
    addTo: nucleusAnchor,
    stroke: 0.92,
    color: hexToRgba(element.accent, 0.12),
  });

  for (let i = 0; i < numNucleons; i += 1) {
    const theta = (i / numNucleons) * Math.PI * 2;
    const phi = Math.acos(2 * ((i + 0.5) / numNucleons) - 1);
    const radius = 0.22 + (i % 3) * 0.09;
    const isProton = i < Math.ceil(numNucleons / 2);
    const color = isProton ? '#ff8fab' : '#64d8ff';

    new Zdog.Shape({
      addTo: nucleusAnchor,
      translate: {
        x: radius * Math.sin(phi) * Math.cos(theta),
        y: radius * Math.sin(phi) * Math.sin(theta),
        z: radius * Math.cos(phi),
      },
      stroke: 0.18,
      color,
    });
  }

  return nucleusAnchor;
}

function buildBohrContent(addTo: Zdog.Anchor, element: AtomViewerElement) {
  const electrons: BohrElectron[] = [];
  const shellRigs: BohrShellRig[] = [];

  element.shells.forEach((electronCount, shellIndex) => {
    const radius = 0.9 + shellIndex * 0.75;
    const color = SHELL_COLORS[shellIndex % SHELL_COLORS.length];
    const rotX = shellIndex * 0.7 + 0.4;
    const rotY = shellIndex * 0.5;
    const googleFanY = getGoogleFanY(element.shells.length, shellIndex);
    const shellRoot = new Zdog.Anchor({
      addTo,
      rotate: {
        x: rotX * 0.32,
        y: googleFanY + rotY * 0.18,
        z: shellIndex * 0.04,
      },
    });
    const foldAnchor = new Zdog.Anchor({ addTo: shellRoot });
    const spinAnchor = new Zdog.Anchor({ addTo: foldAnchor });
    const shellPlane = new Zdog.Anchor({ addTo: spinAnchor });

    shellRigs.push({
      foldAnchor,
      spinAnchor,
      spinDirection: shellIndex % 2 === 0 ? 1 : -1,
      phase: shellIndex * 0.18,
    });

    new Zdog.Ellipse({
      addTo: shellPlane,
      diameter: radius * 2,
      stroke: 0.024,
      color: hexToRgba(color, 0.35),
    });

    new Zdog.Ellipse({
      addTo: shellPlane,
      diameter: radius * 2.01,
      stroke: 0.006,
      color: hexToRgba('#ffffff', 0.22),
    });

    for (let electronIndex = 0; electronIndex < electronCount; electronIndex += 1) {
      const baseAngle = (electronIndex / electronCount) * Math.PI * 2;
      const pivot = new Zdog.Anchor({
        addTo: shellPlane,
        rotate: { z: baseAngle },
      });

      new Zdog.Shape({
        addTo: pivot,
        translate: { x: radius, y: 0, z: 0 },
        stroke: 0.2,
        color: hexToRgba(color, 0.26),
      });

      new Zdog.Shape({
        addTo: pivot,
        translate: { x: radius, y: 0, z: 0 },
        stroke: 0.078,
        color,
      });

      electrons.push({
        anchor: pivot,
        baseAngle,
        speed: 0.29 + shellIndex * 0.144,
      });
    }
  });

  return { electrons, shellRigs };
}

function normalizeVector(vector: OrbitalVector): OrbitalVector {
  const length = Math.hypot(vector.x, vector.y, vector.z) || 1;

  return {
    x: vector.x / length,
    y: vector.y / length,
    z: vector.z / length,
  };
}

function scaleVector(vector: OrbitalVector, scale: number): OrbitalVector {
  return {
    x: vector.x * scale,
    y: vector.y * scale,
    z: vector.z * scale,
  };
}

function axisVector(axis: AxisKey, sign = 1): OrbitalVector {
  return {
    x: axis === 'x' ? sign : 0,
    y: axis === 'y' ? sign : 0,
    z: axis === 'z' ? sign : 0,
  };
}

function rotationForDirection(direction: OrbitalVector): Rotation {
  const unit = normalizeVector(direction);
  const horizontal = Math.hypot(unit.x, unit.y);

  return {
    x: 0,
    y: -Math.atan2(unit.z, horizontal),
    z: Math.atan2(unit.y, unit.x),
  };
}

function planeRotation(plane: OrbitalPlane): Rotation {
  if (plane === 'xz') {
    return { x: Math.PI / 2, y: 0, z: 0 };
  }

  if (plane === 'yz') {
    return { x: Math.PI / 2, y: 0, z: Math.PI / 2 };
  }

  return { x: 0, y: 0, z: 0 };
}

function createReferenceAxisSegment(
  addTo: Zdog.Anchor,
  from: Zdog.VectorOptions,
  to: Zdog.VectorOptions,
  color: string,
  opacity: number,
  stroke: number,
) {
  new Zdog.Shape({
    addTo,
    path: [from, to],
    closed: false,
    stroke,
    color: hexToRgba(color, opacity),
  });
}

function createReferenceAxes(addTo: Zdog.Anchor, visualRadius: number) {
  const group = new Zdog.Anchor({ addTo });
  const axisLength = visualRadius * 0.92;
  const negativeLength = axisLength * 0.58;
  const labelGap = visualRadius * 0.13;
  const stroke = visualRadius * 0.014;
  const glyphScale = clamp(visualRadius * 0.12, 0.2, 0.42);

  createAxisReference(group, AXIS_COLORS.x, { x: axisLength, y: 0, z: 0 }, { x: -negativeLength, y: 0, z: 0 }, stroke);
  createAxisReference(group, AXIS_COLORS.y, { x: 0, y: -axisLength, z: 0 }, { x: 0, y: negativeLength, z: 0 }, stroke);
  createAxisReference(group, AXIS_COLORS.z, { x: 0, y: 0, z: axisLength }, { x: 0, y: 0, z: -negativeLength }, stroke);

  new Zdog.Shape({
    addTo: group,
    stroke: visualRadius * 0.032,
    color: hexToRgba('#ffffff', 0.28),
  });

  return {
    x: createAxisGlyph(group, 'X', { x: axisLength + labelGap, y: 0, z: 0 }, AXIS_COLORS.x, glyphScale),
    y: createAxisGlyph(group, 'Y', { x: 0, y: -axisLength - labelGap, z: 0 }, AXIS_COLORS.y, glyphScale),
    z: createAxisGlyph(group, 'Z', { x: 0, y: 0, z: axisLength + labelGap }, AXIS_COLORS.z, glyphScale),
  };
}

function createAxisReference(
  addTo: Zdog.Anchor,
  color: string,
  positive: Zdog.VectorOptions,
  negative: Zdog.VectorOptions,
  stroke: number,
) {
  createReferenceAxisSegment(addTo, negative, { x: 0, y: 0, z: 0 }, color, 0.15, stroke * 0.78);
  createReferenceAxisSegment(addTo, { x: 0, y: 0, z: 0 }, positive, color, 0.42, stroke);

  new Zdog.Shape({
    addTo,
    translate: positive,
    stroke: stroke * 3.8,
    color: hexToRgba(color, 0.64),
  });
}

function createAxisGlyph(
  addTo: Zdog.Anchor,
  label: 'X' | 'Y' | 'Z',
  translate: Zdog.VectorOptions,
  color: string,
  scale: number,
): AxisGlyphRig {
  const root = new Zdog.Anchor({ addTo, translate });
  const zAnchor = new Zdog.Anchor({ addTo: root });
  const yAnchor = new Zdog.Anchor({ addTo: zAnchor });
  const xAnchor = new Zdog.Anchor({ addTo: yAnchor });
  const stroke = scale * 0.18;
  const depth = scale * 0.08;
  const segments: Record<typeof label, Array<[number, number, number, number]>> = {
    X: [
      [-0.48, -0.48, 0.48, 0.48],
      [0.48, -0.48, -0.48, 0.48],
    ],
    Y: [
      [-0.48, -0.5, 0, -0.02],
      [0.48, -0.5, 0, -0.02],
      [0, -0.02, 0, 0.5],
    ],
    Z: [
      [-0.48, -0.48, 0.48, -0.48],
      [0.48, -0.48, -0.48, 0.48],
      [-0.48, 0.48, 0.48, 0.48],
    ],
  };

  segments[label].forEach(([x1, y1, x2, y2]) => {
    const path = [
      { x: x1 * scale, y: y1 * scale, z: 0 },
      { x: x2 * scale, y: y2 * scale, z: 0 },
    ];

    new Zdog.Shape({
      addTo: xAnchor,
      path,
      translate: { x: depth * 0.45, y: depth * 0.45, z: -depth },
      closed: false,
      stroke: stroke * 1.12,
      color: hexToRgba('#050815', 0.42),
    });

    new Zdog.Shape({
      addTo: xAnchor,
      path,
      translate: { x: depth * 0.2, y: depth * 0.2, z: -depth * 0.45 },
      closed: false,
      stroke: stroke,
      color: hexToRgba(color, 0.42),
    });

    new Zdog.Shape({
      addTo: xAnchor,
      path,
      closed: false,
      stroke,
      color: hexToRgba(color, 0.86),
    });
  });

  return { zAnchor, yAnchor, xAnchor };
}

function getAxisVisualRadius(choice?: ResolvedOrbitalChoice) {
  if (!choice) {
    return 2.4;
  }

  return Math.max(orbitalVisualRadius(choice.subshell, choice.variant), 2.4);
}

function createSOrbital(addTo: Zdog.Anchor, radius: number, color: string, opacity: number, n: number, electrons: number) {
  const group = new Zdog.Anchor({ addTo });
  const cloudRadius = radius * 0.35;
  const shellCount = Math.min(Math.max(n, 1), 4);

  new Zdog.Shape({
    addTo: group,
    stroke: cloudRadius * 1.95,
    color: hexToRgba(color, opacity * 0.36),
  });

  new Zdog.Shape({
    addTo: group,
    stroke: cloudRadius * 1.1,
    color: hexToRgba(color, opacity * 0.52),
  });

  [
    { x: 0, y: 0, z: 0 },
    { x: Math.PI / 2, y: 0, z: 0 },
    { x: 0, y: Math.PI / 2, z: 0 },
  ].forEach((rotate) => {
    new Zdog.Ellipse({
      addTo: group,
      diameter: cloudRadius * 2.08,
      rotate,
      stroke: 0.028,
      color: hexToRgba(color, opacity * 0.72),
    });
  });

  for (let index = 1; index < shellCount; index += 1) {
    const diameter = cloudRadius * (1.18 + index * 0.28);

    new Zdog.Ellipse({
      addTo: group,
      diameter,
      rotate: { x: Math.PI / 2, y: 0, z: 0 },
      stroke: 0.018,
      color: hexToRgba(color, opacity * (0.24 - index * 0.03)),
    });
  }

  return { anchor: group, n };
}

function createOrbitalLobe(
  addTo: Zdog.Anchor,
  translate: Zdog.VectorOptions,
  rotate: Zdog.VectorOptions,
  longAxis: number,
  shortAxis: number,
  phase: 1 | -1,
  opacity: number,
) {
  const color = phase > 0 ? ORBITAL_PHASE_COLORS.positive : ORBITAL_PHASE_COLORS.negative;
  const lobe = new Zdog.Anchor({ addTo, translate, rotate });
  const sliceCount = 9;
  const halfCount = (sliceCount - 1) / 2;

  for (let index = 0; index < sliceCount; index += 1) {
    const normalized = (index - halfCount) / halfCount;
    const falloff = Math.sqrt(Math.max(0, 1 - normalized * normalized));
    const x = normalized * longAxis * 0.36;
    const diameter = shortAxis * (0.22 + falloff * 0.78);

    new Zdog.Shape({
      addTo: lobe,
      translate: { x, y: 0, z: 0 },
      stroke: diameter,
      color: hexToRgba(color, opacity * (0.16 + falloff * 0.34)),
    });
  }

  new Zdog.Ellipse({
    addTo: lobe,
    width: longAxis * 1.04,
    height: shortAxis * 1.04,
    stroke: 0.012,
    color: hexToRgba(color, opacity * 0.82),
  });

  new Zdog.Ellipse({
    addTo: lobe,
    width: longAxis * 0.98,
    height: shortAxis * 0.92,
    rotate: { x: Math.PI / 2, y: 0, z: 0 },
    stroke: 0.01,
    color: hexToRgba(color, opacity * 0.46),
  });

  new Zdog.Ellipse({
    addTo: lobe,
    width: shortAxis * 0.9,
    height: shortAxis * 0.9,
    rotate: { x: 0, y: Math.PI / 2, z: 0 },
    stroke: 0.01,
    color: hexToRgba(color, opacity * 0.36),
  });
}

function createDirectionalLobe(
  addTo: Zdog.Anchor,
  direction: OrbitalVector,
  offset: number,
  longAxis: number,
  shortAxis: number,
  phase: 1 | -1,
  opacity: number,
) {
  const unit = normalizeVector(direction);

  createOrbitalLobe(
    addTo,
    scaleVector(unit, offset),
    rotationForDirection(unit),
    longAxis,
    shortAxis,
    phase,
    opacity,
  );
}

function createPhaseRing(
  addTo: Zdog.Anchor,
  diameter: number,
  stroke: number,
  phase: 1 | -1,
  opacity: number,
  rotate: Rotation = { x: 0, y: 0, z: 0 },
  translate: OrbitalVector = { x: 0, y: 0, z: 0 },
) {
  const color = phase > 0 ? ORBITAL_PHASE_COLORS.positive : ORBITAL_PHASE_COLORS.negative;

  new Zdog.Ellipse({
    addTo,
    diameter,
    translate,
    rotate,
    stroke,
    color: hexToRgba(color, opacity * 0.52),
  });

  new Zdog.Ellipse({
    addTo,
    diameter: diameter * 0.92,
    translate,
    rotate,
    stroke: stroke * 0.42,
    color: hexToRgba(color, opacity * 0.72),
  });
}

function createAxisLobePair(
  addTo: Zdog.Anchor,
  axis: AxisKey,
  radius: number,
  opacity: number,
  positivePhase: 1 | -1,
  longScale: number,
  shortScale: number,
  offsetScale: number,
  samePhase = false,
) {
  const longAxis = radius * longScale;
  const shortAxis = radius * shortScale;
  const offset = radius * offsetScale;

  createDirectionalLobe(addTo, axisVector(axis, 1), offset, longAxis, shortAxis, positivePhase, opacity);
  createDirectionalLobe(
    addTo,
    axisVector(axis, -1),
    offset,
    longAxis,
    shortAxis,
    samePhase ? positivePhase : (positivePhase * -1) as 1 | -1,
    opacity,
  );
}

function createPlanarClover(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  plane: OrbitalPlane,
  angleOffset: number,
) {
  const group = new Zdog.Anchor({ addTo, rotate: planeRotation(plane) });
  const lobeLong = radius * 0.5;
  const lobeShort = radius * 0.22;
  const offset = radius * 0.36;

  for (let index = 0; index < 4; index += 1) {
    const angle = angleOffset + (index * Math.PI) / 2;

    createOrbitalLobe(
      group,
      { x: Math.cos(angle) * offset, y: Math.sin(angle) * offset, z: 0 },
      { x: 0, y: 0, z: angle },
      lobeLong,
      lobeShort,
      index % 2 === 0 ? 1 : -1,
      opacity,
    );
  }
}

function createPlanarSixLobedF(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  plane: OrbitalPlane,
  angleOffset: number,
) {
  const group = new Zdog.Anchor({ addTo, rotate: planeRotation(plane) });
  const lobeLong = radius * 0.36;
  const lobeShort = radius * 0.15;
  const offset = radius * 0.38;

  for (let index = 0; index < 6; index += 1) {
    const angle = angleOffset + (index * Math.PI) / 3;

    createOrbitalLobe(
      group,
      { x: Math.cos(angle) * offset, y: Math.sin(angle) * offset, z: 0 },
      { x: 0, y: 0, z: angle },
      lobeLong,
      lobeShort,
      index % 2 === 0 ? 1 : -1,
      opacity,
    );
  }
}

function createCornerEightLobedF(addTo: Zdog.Anchor, radius: number, opacity: number) {
  const lobeLong = radius * 0.3;
  const lobeShort = radius * 0.14;
  const offset = radius * 0.44;

  [-1, 1].forEach((xSign) => {
    [-1, 1].forEach((ySign) => {
      [-1, 1].forEach((zSign) => {
        createDirectionalLobe(
          addTo,
          { x: xSign, y: ySign, z: zSign },
          offset,
          lobeLong,
          lobeShort,
          xSign * ySign * zSign > 0 ? 1 : -1,
          opacity,
        );
      });
    });
  });
}

function createZTimesX2MinusY2F(addTo: Zdog.Anchor, radius: number, opacity: number) {
  const lobeLong = radius * 0.32;
  const lobeShort = radius * 0.14;
  const offset = radius * 0.42;

  [-1, 1].forEach((zSign) => {
    [-1, 1].forEach((xSign) => {
      createDirectionalLobe(
        addTo,
        { x: xSign, y: 0, z: zSign },
        offset,
        lobeLong,
        lobeShort,
        zSign > 0 ? 1 : -1,
        opacity,
      );
    });

    [-1, 1].forEach((ySign) => {
      createDirectionalLobe(
        addTo,
        { x: 0, y: ySign, z: zSign },
        offset,
        lobeLong,
        lobeShort,
        zSign > 0 ? -1 : 1,
        opacity,
      );
    });
  });
}

function createFZ3Orbital(addTo: Zdog.Anchor, radius: number, opacity: number) {
  createDirectionalLobe(addTo, axisVector('z', 1), radius * 0.38, radius * 0.42, radius * 0.17, 1, opacity);
  createDirectionalLobe(addTo, axisVector('z', -1), radius * 0.38, radius * 0.42, radius * 0.17, -1, opacity);
  createPhaseRing(addTo, radius * 0.5, radius * 0.022, -1, opacity, { x: 0, y: 0, z: 0 }, { x: 0, y: 0, z: radius * 0.16 });
  createPhaseRing(addTo, radius * 0.5, radius * 0.022, 1, opacity, { x: 0, y: 0, z: 0 }, { x: 0, y: 0, z: -radius * 0.16 });
}

function createPOrbitalPair(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  axis: AxisKey,
  phaseOffset: 1 | -1,
) {
  const group = new Zdog.Anchor({ addTo });
  const lobeLong = radius * 0.72;
  const lobeShort = radius * 0.32;
  const offset = radius * 0.42;

  createDirectionalLobe(
    group,
    axisVector(axis, -1),
    offset,
    lobeLong,
    lobeShort,
    phaseOffset > 0 ? -1 : 1,
    opacity,
  );
  createDirectionalLobe(
    group,
    axisVector(axis, 1),
    offset,
    lobeLong,
    lobeShort,
    phaseOffset,
    opacity,
  );
}

function getSlotCloudOpacity(
  baseOpacity: number,
  variant: OrbitalVariant,
  slotVariant: OrbitalVariant,
  slotLabels: string[],
  slots: number[],
  allScale: number,
) {
  const slotIndex = slotLabels.indexOf(slotVariant);
  const occupancy = slotIndex >= 0 ? slots[slotIndex] ?? 0 : 0;

  if (variant === 'all') {
    return occupancy > 0 ? baseOpacity * allScale * (occupancy === 1 ? 0.88 : 1) : 0;
  }

  if (variant !== slotVariant) {
    return 0;
  }

  return occupancy > 0 ? baseOpacity * (occupancy === 1 ? 0.94 : 1) : baseOpacity * 0.13;
}

function createPOrbital(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  n: number,
  variant: OrbitalVariant,
  slots: number[],
) {
  const group = new Zdog.Anchor({ addTo });
  const slotLabels = getSlotLabels('p');
  const axes: AxisKey[] = ['x', 'y', 'z'];

  axes.forEach((axis, index) => {
    const slotVariant = slotLabels[index] as OrbitalVariant;
    const cloudOpacity = getSlotCloudOpacity(opacity, variant, slotVariant, slotLabels, slots, 0.58);

    if (cloudOpacity <= 0) {
      return;
    }

    createPOrbitalPair(group, radius, cloudOpacity, axis, index % 2 === 0 ? 1 : -1);
  });

  return { anchor: group, n };
}

function createDz2Orbital(addTo: Zdog.Anchor, radius: number, opacity: number) {
  const group = new Zdog.Anchor({ addTo });

  createAxisLobePair(group, 'z', radius, opacity, 1, 0.56, 0.24, 0.38, true);
  createPhaseRing(group, radius * 0.66, radius * 0.028, -1, opacity, { x: 0, y: 0, z: 0 });
}

function createDOrbital(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  n: number,
  variant: OrbitalVariant,
  slots: number[],
) {
  const group = new Zdog.Anchor({ addTo });
  const slotLabels = getSlotLabels('d');
  const renderSlot = (slotVariant: OrbitalVariant, render: (cloudOpacity: number) => void) => {
    const cloudOpacity = getSlotCloudOpacity(opacity, variant, slotVariant, slotLabels, slots, 0.54);

    if (cloudOpacity > 0) {
      render(cloudOpacity);
    }
  };

  renderSlot('dxy', (cloudOpacity) => createPlanarClover(group, radius, cloudOpacity, 'xy', Math.PI / 4));
  renderSlot('dxz', (cloudOpacity) => createPlanarClover(group, radius, cloudOpacity, 'xz', Math.PI / 4));
  renderSlot('dyz', (cloudOpacity) => createPlanarClover(group, radius, cloudOpacity, 'yz', Math.PI / 4));
  renderSlot('dx2-y2', (cloudOpacity) => createPlanarClover(group, radius, cloudOpacity, 'xy', 0));
  renderSlot('dz2', (cloudOpacity) => createDz2Orbital(group, radius, cloudOpacity));

  return { anchor: group, n };
}

function createFOrbital(
  addTo: Zdog.Anchor,
  radius: number,
  opacity: number,
  n: number,
  variant: OrbitalVariant,
  slots: number[],
) {
  const group = new Zdog.Anchor({ addTo });
  const slotLabels = getSlotLabels('f');
  const fRadius = radius * 0.9;
  const renderSlot = (slotVariant: OrbitalVariant, render: (cloudOpacity: number) => void) => {
    const cloudOpacity = getSlotCloudOpacity(opacity, variant, slotVariant, slotLabels, slots, 0.46);

    if (cloudOpacity > 0) {
      render(cloudOpacity);
    }
  };

  renderSlot('fz3', (cloudOpacity) => createFZ3Orbital(group, fRadius, cloudOpacity));
  renderSlot('fxz2', (cloudOpacity) => createPlanarSixLobedF(group, fRadius, cloudOpacity, 'xz', 0));
  renderSlot('fyz2', (cloudOpacity) => createPlanarSixLobedF(group, fRadius, cloudOpacity, 'yz', 0));
  renderSlot('fxyz', (cloudOpacity) => createCornerEightLobedF(group, fRadius, cloudOpacity));
  renderSlot('fz(x2-y2)', (cloudOpacity) => createZTimesX2MinusY2F(group, fRadius, cloudOpacity));
  renderSlot('fx(x2-3y2)', (cloudOpacity) => createPlanarSixLobedF(group, fRadius, cloudOpacity, 'xy', 0));
  renderSlot('fy(3x2-y2)', (cloudOpacity) => createPlanarSixLobedF(group, fRadius, cloudOpacity, 'xy', Math.PI / 2));

  return { anchor: group, n };
}

function buildOrbitalContent(addTo: Zdog.Anchor, choice?: ResolvedOrbitalChoice) {
  if (!choice) {
    return { pulses: [], axisGlyphs: null };
  }

  const pulses: OrbitalPulse[] = [];
  const orbital = choice.subshell;
  const radius = orbitalRadius(orbital.n);
  const color = ORBITAL_COLORS[orbital.l];
  const opacity = 0.34;

  const axisGlyphs = createReferenceAxes(addTo, getAxisVisualRadius(choice));

  if (orbital.l === 's') {
    pulses.push(createSOrbital(addTo, radius, color, opacity, orbital.n, orbital.electrons));
  } else if (orbital.l === 'p') {
    pulses.push(createPOrbital(addTo, radius, opacity, orbital.n, choice.variant, choice.slots));
  } else if (orbital.l === 'd') {
    pulses.push(createDOrbital(addTo, radius, opacity, orbital.n, choice.variant, choice.slots));
  } else {
    pulses.push(createFOrbital(addTo, radius, opacity, orbital.n, choice.variant, choice.slots));
  }

  return { pulses, axisGlyphs };
}

function getMaxOrbitalRadius(choice?: ResolvedOrbitalChoice) {
  if (!choice) {
    return 2.6;
  }

  return Math.max(orbitalVisualRadius(choice.subshell, choice.variant), 2.6);
}

function updateAnimation(runtime: Runtime, animTime: number) {
  if (runtime.mode === 'bohr') {
    runtime.nucleusAnchor.rotate.y = animTime * 0.216;
    runtime.nucleusAnchor.rotate.x = animTime * 0.144;

    runtime.bohrShellRigs.forEach((shellRig) => {
      const rigPose = getGoogleRigPose(animTime, shellRig);
      shellRig.foldAnchor.rotate.x = rigPose.foldX;
      shellRig.spinAnchor.rotate.y = rigPose.spinY;
    });

    runtime.bohrElectrons.forEach((electron) => {
      electron.anchor.rotate.z = electron.baseAngle + animTime * electron.speed;
    });
  } else {
    runtime.orbitalPulses.forEach((pulse) => {
      const pulseSpeed = 0.8 + pulse.n * 0.15;
      const scale = 1 + Math.sin(animTime * pulseSpeed) * 0.04;
      pulse.anchor.scale.x = scale;
      pulse.anchor.scale.y = scale;
      pulse.anchor.scale.z = scale;
    });
  }
}

export function AtomViewerZdog({ element, mode, isPlaying, resetSignal, orbitalChoice }: AtomViewerZdogProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const shellRef = useRef<HTMLDivElement | null>(null);
  const runtimeRef = useRef<Runtime | null>(null);
  const frameRef = useRef<number | null>(null);
  const tickRef = useRef<(time: number) => void>(() => undefined);
  const playingRef = useRef(isPlaying);
  const rotationRef = useRef<Rotation>(copyRotation(DEFAULT_ROTATION));
  const animTimeRef = useRef(0);
  const lastTimeRef = useRef(0);
  const pointerRef = useRef({ active: false, id: -1, x: 0, y: 0 });

  const updateAxisGlyphs = useCallback((runtime = runtimeRef.current) => {
    if (!runtime?.axisGlyphs) {
      return;
    }

    (Object.values(runtime.axisGlyphs) as AxisGlyphRig[]).forEach((glyph) => {
      glyph.zAnchor.rotate.z = -rotationRef.current.z;
      glyph.yAnchor.rotate.y = -rotationRef.current.y;
      glyph.xAnchor.rotate.x = -rotationRef.current.x;
    });
  }, []);

  const renderOnce = useCallback(() => {
    if (!runtimeRef.current) {
      return;
    }

    updateAxisGlyphs(runtimeRef.current);
    runtimeRef.current.illustration.updateRenderGraph();
  }, [updateAxisGlyphs]);

  const stopLoop = useCallback(() => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
  }, []);

  const startLoop = useCallback(() => {
    if (frameRef.current !== null || !playingRef.current || document.hidden) {
      return;
    }

    lastTimeRef.current = performance.now();
    frameRef.current = requestAnimationFrame((time) => tickRef.current(time));
  }, []);

  useEffect(() => {
    playingRef.current = isPlaying;

    if (isPlaying) {
      startLoop();
    } else {
      stopLoop();
      renderOnce();
    }
  }, [isPlaying, renderOnce, startLoop, stopLoop]);

  useEffect(() => {
    tickRef.current = (time: number) => {
      frameRef.current = null;

      if (!playingRef.current || document.hidden || !runtimeRef.current) {
        return;
      }

      const dt = clamp((time - lastTimeRef.current) / 1000, 0, 0.05);
      lastTimeRef.current = time;
      animTimeRef.current += dt;

      updateAnimation(runtimeRef.current, animTimeRef.current);
      runtimeRef.current.illustration.updateRenderGraph();
      frameRef.current = requestAnimationFrame((nextTime) => tickRef.current(nextTime));
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const shell = shellRef.current;

    if (!canvas || !shell) {
      return undefined;
    }

    stopLoop();
    rotationRef.current = copyRotation(DEFAULT_ROTATION);
    animTimeRef.current = 0;

    const illustration = new Zdog.Illustration({
      element: canvas,
      zoom: 1,
    });

    const atomAnchor = new Zdog.Anchor({
      addTo: illustration,
      rotate: copyRotation(rotationRef.current),
    });

    const bohrContent =
      mode === 'bohr' ? buildBohrContent(atomAnchor, element) : { electrons: [], shellRigs: [] };
    const orbitalContent = mode === 'orbital' ? buildOrbitalContent(atomAnchor, orbitalChoice) : { pulses: [], axisGlyphs: null };
    const nucleusAnchor = createNucleus(atomAnchor, element);

    const resize = () => {
      const rect = shell.getBoundingClientRect();
      const width = Math.max(1, rect.width);
      const height = Math.max(1, rect.height);
      const shortSide = Math.min(width, height);

      illustration.setSize(width, height);

      if (mode === 'bohr') {
        const outerRadius = 0.9 + (element.shells.length - 1) * 0.75 + 0.44;
        illustration.zoom = clamp(shortSide / (outerRadius * 2.42), 20, 96);
      } else {
        illustration.zoom = clamp(shortSide / (getMaxOrbitalRadius(orbitalChoice) * 3.05), 9, 54);
      }

      updateAxisGlyphs(runtimeRef.current);
      illustration.updateRenderGraph();
    };

    const runtime: Runtime = {
      illustration,
      atomAnchor,
      nucleusAnchor,
      mode,
      bohrElectrons: bohrContent.electrons,
      bohrShellRigs: bohrContent.shellRigs,
      orbitalPulses: orbitalContent.pulses,
      axisGlyphs: orbitalContent.axisGlyphs,
      resize,
    };

    runtimeRef.current = runtime;
    resize();

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(shell);

    if (playingRef.current && !document.hidden) {
      startLoop();
    }

    return () => {
      resizeObserver.disconnect();
      stopLoop();
      runtimeRef.current = null;
    };
  }, [element, mode, orbitalChoice, startLoop, stopLoop, updateAxisGlyphs]);

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas) {
      return undefined;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (event.pointerType === 'touch' && !event.isPrimary) {
        return;
      }

      pointerRef.current = {
        active: true,
        id: event.pointerId,
        x: event.clientX,
        y: event.clientY,
      };
      canvas.setPointerCapture(event.pointerId);
      event.preventDefault();
    };

    const handlePointerMove = (event: PointerEvent) => {
      const pointer = pointerRef.current;

      if (!pointer.active || pointer.id !== event.pointerId || !runtimeRef.current) {
        return;
      }

      const dx = event.clientX - pointer.x;
      const dy = event.clientY - pointer.y;
      rotationRef.current.y += dx * 0.012;
      rotationRef.current.x += dy * 0.012;
      assignRotation(runtimeRef.current.atomAnchor, rotationRef.current);
      updateAxisGlyphs(runtimeRef.current);
      pointerRef.current = { ...pointer, x: event.clientX, y: event.clientY };
      event.preventDefault();

      if (!playingRef.current) {
        renderOnce();
      }
    };

    const handlePointerEnd = (event: PointerEvent) => {
      const pointer = pointerRef.current;

      if (pointer.id === event.pointerId) {
        pointerRef.current = { active: false, id: -1, x: 0, y: 0 };
      }
    };

    canvas.addEventListener('pointerdown', handlePointerDown, { passive: false });
    canvas.addEventListener('pointermove', handlePointerMove, { passive: false });
    canvas.addEventListener('pointerup', handlePointerEnd);
    canvas.addEventListener('pointercancel', handlePointerEnd);
    canvas.addEventListener('lostpointercapture', handlePointerEnd);

    return () => {
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
      canvas.removeEventListener('pointerup', handlePointerEnd);
      canvas.removeEventListener('pointercancel', handlePointerEnd);
      canvas.removeEventListener('lostpointercapture', handlePointerEnd);
    };
  }, [renderOnce]);

  useEffect(() => {
    rotationRef.current = copyRotation(DEFAULT_ROTATION);

    if (runtimeRef.current) {
      assignRotation(runtimeRef.current.atomAnchor, rotationRef.current);
      updateAxisGlyphs(runtimeRef.current);
      runtimeRef.current.illustration.updateRenderGraph();
    }
  }, [resetSignal, updateAxisGlyphs]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopLoop();
      } else if (playingRef.current) {
        startLoop();
      } else {
        renderOnce();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      stopLoop();
    };
  }, [renderOnce, startLoop, stopLoop]);

  return (
    <figure className="atom-viewer" ref={shellRef}>
      <canvas
        ref={canvasRef}
        className="atom-canvas"
        aria-label={`${element.name}${mode === 'bohr' ? '电子层' : '轨道'}模型`}
      />
      <figcaption className="atom-hint">拖动旋转模型</figcaption>
    </figure>
  );
}
