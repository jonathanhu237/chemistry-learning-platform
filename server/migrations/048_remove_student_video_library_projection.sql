-- Retire the legacy student video-library Elasticsearch projection. Teacher
-- catalog search and textbook RAG keep their independent state and job types.

DELETE FROM experiment_catalog_point_jobs
WHERE job_type IN ('es_upsert', 'es_delete');

ALTER TABLE experiment_catalog_point_jobs
  DROP CONSTRAINT IF EXISTS experiment_catalog_point_jobs_job_type_check;

ALTER TABLE experiment_catalog_point_jobs
  ADD CONSTRAINT experiment_catalog_point_jobs_job_type_check CHECK (
    job_type IN (
      'teacher_search_upsert',
      'teacher_search_delete',
      'rag_evidence_refresh',
      'rag_evidence_delete'
    )
  );

DROP TABLE IF EXISTS experiment_catalog_point_search_index_state;
DROP TABLE IF EXISTS experiment_video_point_search_index_state;
