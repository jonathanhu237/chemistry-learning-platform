## 1. Backend Duplicate Risk Core

- [x] 1.1 Add duplicate-risk metadata helpers for extracting same-point question text, normalized comparison text, and teacher-facing match summaries.
- [x] 1.2 Add semantic fingerprint cache storage and embedding reuse for question/draft duplicate checks.
- [x] 1.3 Implement same-point duplicate-risk evaluation against published questions, active drafts, and in-batch generated drafts.

## 2. Backend Workflow Integration

- [x] 2.1 Run duplicate-risk evaluation when AI workbench generation stores draft candidates.
- [x] 2.2 Recompute duplicate risk when a teacher saves draft edits.
- [x] 2.3 Refresh duplicate-risk metadata before publishing drafts or workbench candidates without blocking publication.

## 3. Teacher UI

- [x] 3.1 Show duplicate-risk tags and concise similar-question summaries in the待审题目 review cards.
- [x] 3.2 Include duplicate-risk warnings in the publish confirmation while still allowing confirmation.

## 4. Verification

- [x] 4.1 Add or update backend tests for same-point duplicate-risk detection and non-blocking publication.
- [x] 4.2 Run backend and frontend type/test checks.
- [x] 4.3 Verify the question-bank page in browser automation with a risky draft displayed.
