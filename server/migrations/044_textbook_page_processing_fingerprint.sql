ALTER TABLE textbook_document_pages
  ADD COLUMN IF NOT EXISTS processing_fingerprint text;

CREATE INDEX IF NOT EXISTS idx_textbook_document_pages_reusable_ocr
  ON textbook_document_pages(document_id, processing_fingerprint, page_number)
  WHERE processing_fingerprint IS NOT NULL
    AND extraction_method IN ('mineru', 'mixed')
    AND needs_ocr = false;
