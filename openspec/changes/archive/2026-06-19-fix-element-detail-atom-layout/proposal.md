## Why

The element detail atom model can render incorrectly on a wide desktop preview: the facts column stretches the model column, the canvas becomes too tall, and the atom appears far below its intended center. This breaks the phone-first H5 preview contract and was missed because existing QA focused on phone widths only.

## What Changes

- Keep the element detail atom model card phone-first even when opened in a wide desktop browser preview.
- Prevent adjacent fact content from stretching the atom viewer stage beyond its intended visual bounds.
- Add regression coverage for the element detail route at a wide preview width as well as phone viewports.
- Document that the browser console CORS/500 noise is not the rendering cause; layout geometry is the relevant failure mode.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-learning-experience`: Element detail pages must keep the atom model readable and centered, with fact content unable to distort the model stage.
- `student-h5-mobile-design-system`: Wide desktop preview must preserve phone-layout behavior for the atom model card and include QA coverage for wide preview regressions.

## Impact

- Affected frontend styles/components: student element detail route, atom model card layout, atom viewer stage sizing.
- Affected QA: student-web mobile/preview QA script or equivalent regression test for `/chapter/:profileId/element/:symbol`.
- No backend API, data model, or dependency changes are expected.
