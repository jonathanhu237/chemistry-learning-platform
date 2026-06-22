export const requiredMobileViewports = [
  { name: "small-phone", width: 360, height: 780 },
  { name: "regular-phone", width: 390, height: 844 },
  { name: "large-phone", width: 430, height: 932 },
] as const;

export type RequiredMobileViewport = (typeof requiredMobileViewports)[number];

export function hasHorizontalOverflow(documentElement: HTMLElement): boolean {
  return documentElement.scrollWidth > documentElement.clientWidth + 1;
}

export function rectsOverlap(first: DOMRect, second: DOMRect): boolean {
  return first.left < second.right && first.right > second.left && first.top < second.bottom && first.bottom > second.top;
}
