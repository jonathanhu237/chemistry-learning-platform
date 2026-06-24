## Why

AI question generation for a fixed experiment point often reuses the same small evidence set, so repeated requests can produce questions with different wording but the same assessment intent. Teachers need lightweight duplicate-risk visibility before publishing, without being blocked when they decide the question is still useful.

## What Changes

- Add same-point duplicate-risk detection for AI-generated and teacher-edited draft questions.
- Compare new or edited drafts against published questions, current draft questions, and candidates generated earlier in the same batch for the same point.
- Store duplicate-risk summaries in question draft metadata and preserve them when a draft is published.
- Surface duplicate-risk hints in the teacher question-bank review UI and in the publish confirmation.
- Keep publication non-blocking: duplicate-risk warnings inform the teacher but do not prevent publishing.
- Reuse configured embedding infrastructure where possible and cache semantic fingerprints to avoid repeated paid embedding calls.

## Capabilities

### New Capabilities

- `question-duplicate-risk`: Detect and expose possible same-point question duplicate risk for teacher review.

### Modified Capabilities

- `point-aware-ai-question-workbench`: Generated candidates SHALL include duplicate-risk metadata and show teacher-facing warnings when relevant.
- `experiment-question-bank-management`: The teacher question-bank review surface SHALL show duplicate-risk hints and publish confirmations for risky drafts.

## Impact

- Backend question generation and draft update paths will run same-point duplicate-risk checks.
- Backend storage will need reusable semantic fingerprint caching for published questions and drafts.
- Teacher question-bank UI will display duplicate-risk tags, brief similar-question lists, and a publish warning.
- Existing publication remains non-blocking; no student-facing question behavior changes except published metadata may include duplicate-risk audit information.
