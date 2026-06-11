CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS source_documents (
  id text PRIMARY KEY,
  file_name text NOT NULL,
  path text NOT NULL,
  archive_path text,
  type text,
  document_kind text,
  size_bytes bigint,
  chapter_id text,
  chapter_number int,
  processing_status text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chapters (
  id text PRIMARY KEY,
  chapter_number int,
  chapter_title text NOT NULL,
  element_area text,
  review_required boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_units (
  id text PRIMARY KEY,
  chapter_id text REFERENCES chapters(id),
  chapter_title text,
  unit_index int,
  unit_title text NOT NULL,
  review_required boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_points (
  id text PRIMARY KEY,
  chapter_id text REFERENCES chapters(id),
  chapter_title text,
  unit_id text REFERENCES knowledge_units(id),
  unit_title text,
  content text NOT NULL,
  element_area text,
  tags text[] DEFAULT '{}',
  difficulty text,
  review_required boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_chunks (
  id text PRIMARY KEY,
  document_id text REFERENCES source_documents(id),
  chapter_id text REFERENCES chapters(id),
  page_number int,
  section_title text,
  chunk_index int,
  text text NOT NULL,
  markdown text,
  related_knowledge_point_ids text[] DEFAULT '{}',
  related_experiment_ids text[] DEFAULT '{}',
  tags text[] DEFAULT '{}',
  metadata jsonb DEFAULT '{}'::jsonb,
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
  chunk_id text PRIMARY KEY REFERENCES source_chunks(id) ON DELETE CASCADE,
  embedding vector,
  model text,
  dimension int,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiments (
  id text PRIMARY KEY,
  name text NOT NULL,
  element_area text,
  element_group text,
  related_elements text[] DEFAULT '{}',
  objective text,
  reagents text[] DEFAULT '{}',
  steps jsonb DEFAULT '[]'::jsonb,
  phenomena jsonb DEFAULT '[]'::jsonb,
  equations jsonb DEFAULT '[]'::jsonb,
  explanation text,
  video_url text NULL,
  media_status text DEFAULT 'pending',
  resource_mode text DEFAULT 'text_card',
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_learning_cards (
  id text PRIMARY KEY,
  experiment_id text REFERENCES experiments(id),
  title text,
  objective text,
  reagents text[] DEFAULT '{}',
  steps jsonb DEFAULT '[]'::jsonb,
  phenomena jsonb DEFAULT '[]'::jsonb,
  equations jsonb DEFAULT '[]'::jsonb,
  principle text,
  safety_notes text[] DEFAULT '{}',
  related_knowledge_points text[] DEFAULT '{}',
  source_chunks text[] DEFAULT '{}',
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questions (
  id text PRIMARY KEY,
  question_type text NOT NULL,
  stem text NOT NULL,
  options jsonb DEFAULT '[]'::jsonb,
  answer text,
  explanation text,
  difficulty text,
  related_knowledge_point_ids text[] DEFAULT '{}',
  related_experiment_ids text[] DEFAULT '{}',
  source_chunk_ids text[] DEFAULT '{}',
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS resources (
  id text PRIMARY KEY,
  document_id text REFERENCES source_documents(id),
  title text,
  resource_type text,
  path text,
  metadata jsonb DEFAULT '{}'::jsonb,
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS links (
  id bigserial PRIMARY KEY,
  from_type text NOT NULL,
  from_id text NOT NULL,
  relation text NOT NULL,
  to_type text NOT NULL,
  to_id text NOT NULL,
  confidence numeric,
  review_required boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS students (
  id text PRIMARY KEY,
  display_name text,
  class_name text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_events (
  id bigserial PRIMARY KEY,
  student_id text REFERENCES students(id),
  event_type text NOT NULL,
  knowledge_point_id text REFERENCES knowledge_points(id),
  experiment_id text REFERENCES experiments(id),
  question_id text REFERENCES questions(id),
  difficulty text,
  correct boolean,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_mastery (
  student_id text REFERENCES students(id),
  knowledge_point_id text REFERENCES knowledge_points(id),
  state_prob numeric[] NOT NULL,
  mastery_score numeric NOT NULL,
  updated_at timestamptz DEFAULT now(),
  PRIMARY KEY(student_id, knowledge_point_id)
);

CREATE INDEX IF NOT EXISTS idx_source_chunks_chapter ON source_chunks(chapter_id);
CREATE INDEX IF NOT EXISTS idx_source_chunks_document_page ON source_chunks(document_id, page_number);
CREATE INDEX IF NOT EXISTS idx_source_chunks_related_kps ON source_chunks USING gin(related_knowledge_point_ids);
CREATE INDEX IF NOT EXISTS idx_source_chunks_related_experiments ON source_chunks USING gin(related_experiment_ids);
CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_type, from_id);
CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_type, to_id);

