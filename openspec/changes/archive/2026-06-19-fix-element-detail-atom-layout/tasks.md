## 1. Atom Layout Fix

- [x] 1.1 Update the atom model card layout so the element detail atom viewer is not stretched by the facts column on wide previews.
- [x] 1.2 Ensure the atom viewer stage keeps a bounded phone-first geometry while preserving readable mode controls and touch targets.
- [x] 1.3 Confirm element detail remains a second-level route with bottom navigation hidden.

## 2. QA Coverage

- [x] 2.1 Add or update student-web QA to assert normal atom canvas geometry, not only nonblank canvas rendering.
- [x] 2.2 Add a wide desktop preview element-detail check that catches the tall-canvas stretch regression.
- [x] 2.3 Keep existing 360x780, 390x844, and 430x932 phone viewport atom checks passing.

## 3. Verification

- [x] 3.1 Run OpenSpec validation for `fix-element-detail-atom-layout`.
- [x] 3.2 Run focused student-web tests or QA covering the element detail atom model.
- [x] 3.3 Record remaining manual browser/WebView risks, if any.

## Verification Notes

- `openspec validate fix-element-detail-atom-layout` passed.
- `npm --prefix apps/student-web run typecheck` passed.
- `STUDENT_H5_QA_MOCK=1 npm --prefix apps/student-web run qa:mobile` passed for 360x780, 390x844, 430x932, and the new 1024x900 wide-preview element detail check.
- Remaining risk: this run used Chromium/Edge automation with mock API, not a physical WeChat WebView device.
