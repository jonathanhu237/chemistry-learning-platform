-- Canonical seed chunks predate online document versions. Register the exact
-- Elasticsearch ``doc_id`` used by each seed so retrieval can activate one
-- concrete generation without allowing staged online versions that share its
-- source_collection.
WITH seed_identities AS (
  SELECT
    sd.id AS document_id,
    min(sc.metadata->>'doc_id') AS index_document_id
  FROM source_documents sd
  JOIN source_chunks sc ON sc.document_id = sd.id
  WHERE sd.document_kind = 'canonical_textbook'
    AND length(btrim(COALESCE(sc.metadata->>'doc_id', ''))) > 0
  GROUP BY sd.id
  HAVING count(DISTINCT sc.metadata->>'doc_id') = 1
)
UPDATE source_documents sd
SET metadata = COALESCE(sd.metadata, '{}'::jsonb)
      || jsonb_build_object('index_document_id', seed_identities.index_document_id),
    updated_at = now()
FROM seed_identities
WHERE sd.id = seed_identities.document_id
  AND COALESCE(sd.metadata->>'index_document_id', '') IS DISTINCT FROM seed_identities.index_document_id;
