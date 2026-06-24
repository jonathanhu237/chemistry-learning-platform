## Context

The point-aware question workbench currently generates draft questions from point context and bound textbook evidence, then stores candidates and drafts without considering questions already present for the same point. Because each point has a small and stable evidence set, repeated generation often produces questions with the same assessment intent under different wording.

Teachers want duplicate awareness, not a blocking workflow. The first version should keep AI generation and publication fast while making possible duplication visible in review.

## Goals / Non-Goals

**Goals:**
- Detect possible duplicate assessment intent within the same catalog point only.
- Compare against published questions, active draft questions, and other questions generated in the same batch.
- Store concise duplicate-risk summaries in draft/question metadata.
- Show duplicate-risk hints in the teacher review UI and publish confirmation.
- Allow publishing even when duplicate risk exists.
- Cache semantic fingerprints so repeated checks do not repeatedly pay for embeddings.

**Non-Goals:**
- Cross-point duplicate detection.
- Blocking publication for duplicate risk.
- Teacher-facing algorithm details such as raw hash rules or embedding thresholds.
- LLM-based duplicate adjudication in the first implementation.
- A full coverage-angle taxonomy UI.

## Decisions

1. **Duplicate risk is advisory metadata.**
   - Store `metadata.duplicate_risk` with `has_risk`, short `message`, and a bounded `matches` list.
   - Rationale: the teacher review UI can render the warning without another API hop, and published questions retain the audit trail.
   - Alternative considered: separate duplicate-risk table. Rejected for first version because UI and publish flow need the result attached to the draft/question.

2. **Same-point scope only.**
   - Resolve the candidate/draft point from point-aware metadata and compare only rows sharing the same source placement point node.
   - Rationale: adjacent chemistry points intentionally share reagents and evidence; cross-point checks would create noisy warnings.

3. **Rules first, embeddings second.**
   - Use normalized stem/answer/option overlap for cheap exact-ish signals.
   - Use Qwen-compatible embeddings for semantic similarity when configured; cache per question/draft text hash.
   - Rationale: rule checks are deterministic and cheap, embeddings catch paraphrases.

4. **Publication remains non-blocking.**
   - Publish confirmation adds duplicate-risk text when present, but backend publication does not reject solely for duplicate risk.
   - Rationale: the user explicitly chose teacher judgment over hard gates.

5. **Recheck at generation, edit-save, and publish time.**
   - Generation and edit-save keep UI feedback current.
   - Publish-time check refreshes stale risk after other questions are published.
   - Rationale: stale duplicate-risk metadata should not be the only evidence at publication.

## Risks / Trade-offs

- **False positives from repeated chemistry language** → Limit comparisons to the same point and show concise warnings instead of blocking.
- **Embedding cost** → Cache semantic fingerprints by owner, model, and text hash; skip embedding when no embedding model is configured.
- **Stale draft metadata** → Recompute on edit save and publish; preserve latest risk in published question metadata.
- **UI overload** → Show only a tag, count, and brief similar-question list; hide technical scoring details.
