import { deckMeta } from "./data/meta.js";
import { backgroundSlides } from "./data/sections/background.js";
import { openingSlides } from "./data/sections/opening.js";
import { referenceSlides } from "./data/sections/references.js";
import { showcaseSlides } from "./data/sections/showcase.js";
import { solutionSlides } from "./data/sections/solution.js";

export const DECK_SLIDES = [
  ...openingSlides,
  ...backgroundSlides,
  ...solutionSlides,
  ...showcaseSlides,
  ...referenceSlides
];

export const DECK_META = {
  ...deckMeta,
  total: DECK_SLIDES.length
};

if (typeof window !== "undefined") {
  window.DECK_META = DECK_META;
  window.DECK_SLIDES = DECK_SLIDES;
}
