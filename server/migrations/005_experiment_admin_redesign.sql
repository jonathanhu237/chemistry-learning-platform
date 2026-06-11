CREATE TABLE IF NOT EXISTS formal_experiments (
  id text PRIMARY KEY,
  code text NOT NULL UNIQUE,
  title text NOT NULL,
  title_en text,
  summary text,
  status text NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
  display_order int NOT NULL DEFAULT 0,
  source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  published_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_chapter_bindings (
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  chapter_id text NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
  coverage_type text NOT NULL DEFAULT 'primary' CHECK (coverage_type IN ('primary', 'partial', 'supporting')),
  notes text,
  sort_order int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (experiment_id, chapter_id)
);

CREATE TABLE IF NOT EXISTS experiment_question_banks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  bank_kind text NOT NULL DEFAULT 'manual' CHECK (bank_kind IN ('default', 'generated', 'manual')),
  title text NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived', 'disabled')),
  source_label text,
  imported_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (experiment_id, bank_kind)
);

CREATE TABLE IF NOT EXISTS experiment_question_imports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_file text,
  status text NOT NULL DEFAULT 'validating' CHECK (status IN ('validating', 'succeeded', 'partial', 'failed')),
  total_rows int NOT NULL DEFAULT 0,
  valid_rows int NOT NULL DEFAULT 0,
  invalid_rows int NOT NULL DEFAULT 0,
  errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  imported_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_question_generations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  prompt text NOT NULL,
  question_types text[] NOT NULL DEFAULT '{}',
  difficulty text,
  requested_count int NOT NULL DEFAULT 5,
  provider text,
  model text,
  mode text NOT NULL DEFAULT 'local',
  rag_sources jsonb NOT NULL DEFAULT '[]'::jsonb,
  warning text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'failed')),
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bank_id uuid REFERENCES experiment_question_banks(id) ON DELETE SET NULL,
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  generation_id uuid REFERENCES experiment_question_generations(id) ON DELETE SET NULL,
  question_type text NOT NULL CHECK (question_type IN ('single_choice', 'true_false', 'fill_blank')),
  stem text NOT NULL,
  options jsonb NOT NULL DEFAULT '[]'::jsonb,
  answer jsonb NOT NULL DEFAULT '{}'::jsonb,
  explanation text,
  difficulty text,
  related_chapter_ids text[] NOT NULL DEFAULT '{}',
  related_knowledge_point_ids text[] NOT NULL DEFAULT '{}',
  source_chunk_ids text[] NOT NULL DEFAULT '{}',
  source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'disabled', 'archived')),
  created_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  published_by uuid REFERENCES app_users(id) ON DELETE SET NULL,
  published_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS experiment_question_drafts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  generation_id uuid NOT NULL REFERENCES experiment_question_generations(id) ON DELETE CASCADE,
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  validation_errors jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'rejected')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_experiment_progress (
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed', 'needs_attention')),
  completion_percent numeric NOT NULL DEFAULT 0,
  best_score numeric,
  last_activity_at timestamptz,
  completed_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, experiment_id)
);

CREATE TABLE IF NOT EXISTS experiment_question_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  experiment_id text NOT NULL REFERENCES formal_experiments(id) ON DELETE CASCADE,
  question_id uuid REFERENCES experiment_questions(id) ON DELETE SET NULL,
  question_type text,
  submitted_answer jsonb NOT NULL DEFAULT '{}'::jsonb,
  correct boolean,
  score numeric,
  attempt_kind text NOT NULL DEFAULT 'practice',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_formal_experiments_status_order ON formal_experiments(status, display_order);
CREATE INDEX IF NOT EXISTS idx_experiment_chapter_bindings_chapter ON experiment_chapter_bindings(chapter_id);
CREATE INDEX IF NOT EXISTS idx_experiment_question_banks_experiment ON experiment_question_banks(experiment_id, status);
CREATE INDEX IF NOT EXISTS idx_experiment_questions_experiment_status ON experiment_questions(experiment_id, status);
CREATE INDEX IF NOT EXISTS idx_experiment_questions_type_difficulty ON experiment_questions(question_type, difficulty);
CREATE INDEX IF NOT EXISTS idx_experiment_questions_kps ON experiment_questions USING gin(related_knowledge_point_ids);
CREATE INDEX IF NOT EXISTS idx_experiment_question_drafts_generation ON experiment_question_drafts(generation_id);
CREATE INDEX IF NOT EXISTS idx_student_experiment_progress_class ON student_experiment_progress(class_id, experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_question_attempts_class ON experiment_question_attempts(class_id, experiment_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_experiment_question_attempts_student ON experiment_question_attempts(student_id, experiment_id, created_at DESC);

INSERT INTO formal_experiments (
  id, code, title, title_en, summary, status, display_order, source_refs, metadata, published_at
)
VALUES
  ('EXP_19_1', '19-1', '实验 19-1 卤素', 'Halogens', '以卤素及其化合物性质为核心的元素性质实验。', 'published', 1, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_2', '19-2', '实验 19-2 氢、氧、过氧化氢', 'Hydrogen, oxygen, and hydrogen peroxide', '围绕氢、氧和过氧化氢性质的实验学习单元。', 'published', 2, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_3', '19-3', '实验 19-3 硫及其化合物', 'Sulfur and compounds', '围绕硫及其化合物性质的实验学习单元。', 'published', 3, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_4', '19-4', '实验 19-4 氮和磷', 'Nitrogen and phosphorus', '围绕氮和磷元素性质的实验学习单元。', 'published', 4, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_5', '19-5', '实验 19-5 碳、硅、硼', 'Carbon, silicon, and boron', '围绕碳、硅、硼元素性质的实验学习单元。', 'published', 5, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_6', '19-6', '实验 19-6 碱金属和碱土金属', 'Alkali metals and alkaline earth metals', '围绕碱金属和碱土金属性质的实验学习单元。', 'published', 6, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_7', '19-7', '实验 19-7 铍和铝', 'Beryllium and aluminum', '围绕铍和铝性质的实验学习单元。', 'published', 7, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_19_8', '19-8', '实验 19-8 锡、铅、砷、锑、铋', 'Tin, lead, arsenic, antimony, and bismuth', '围绕锡、铅、砷、锑、铋性质的实验学习单元。', 'published', 8, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_20_1', '20-1', '实验 20-1 ds 区元素化合物的性质', 'ds-block element compound properties', '围绕 ds 区元素化合物性质的实验学习单元。', 'published', 9, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_20_2', '20-2', '实验 20-2 d 区元素化合物的性质（一）', 'd-block element compound properties (I)', '围绕 d 区过渡金属元素化合物性质的实验学习单元一。', 'published', 10, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now()),
  ('EXP_20_3', '20-3', '实验 20-3 d 区元素化合物的性质（二）', 'd-block element compound properties (II)', '围绕 d 区过渡金属元素化合物性质的实验学习单元二。', 'published', 11, '[{"document_id":"DOC_EXPERIMENTS_SELECTED","page_range":"138-169"}]'::jsonb, '{"formal_catalog":true}'::jsonb, now())
ON CONFLICT (id) DO UPDATE SET
  code = EXCLUDED.code,
  title = EXCLUDED.title,
  title_en = EXCLUDED.title_en,
  summary = EXCLUDED.summary,
  status = EXCLUDED.status,
  display_order = EXCLUDED.display_order,
  source_refs = EXCLUDED.source_refs,
  metadata = formal_experiments.metadata || EXCLUDED.metadata,
  updated_at = now();

INSERT INTO experiment_chapter_bindings (experiment_id, chapter_id, coverage_type, sort_order)
SELECT values_table.experiment_id, values_table.chapter_id, values_table.coverage_type, values_table.sort_order
FROM (
  VALUES
    ('EXP_19_1', 'CH13', 'primary', 1),
    ('EXP_19_2', 'CH14', 'primary', 1),
    ('EXP_19_2', 'CH22', 'partial', 2),
    ('EXP_19_3', 'CH14', 'primary', 1),
    ('EXP_19_4', 'CH15', 'primary', 1),
    ('EXP_19_5', 'CH16', 'primary', 1),
    ('EXP_19_5', 'CH17', 'partial', 2),
    ('EXP_19_6', 'CH18', 'primary', 1),
    ('EXP_19_7', 'CH17', 'primary', 1),
    ('EXP_19_7', 'CH18', 'partial', 2),
    ('EXP_19_8', 'CH16', 'partial', 1),
    ('EXP_19_8', 'CH15', 'partial', 2),
    ('EXP_20_1', 'CH19', 'primary', 1),
    ('EXP_20_2', 'CH20', 'primary', 1),
    ('EXP_20_3', 'CH20', 'primary', 1)
) AS values_table(experiment_id, chapter_id, coverage_type, sort_order)
JOIN chapters c ON c.id = values_table.chapter_id
ON CONFLICT (experiment_id, chapter_id) DO UPDATE SET
  coverage_type = EXCLUDED.coverage_type,
  sort_order = EXCLUDED.sort_order,
  updated_at = now();

DELETE FROM formal_experiments
WHERE id IN (
  'EXP_19_1',
  'EXP_19_2',
  'EXP_19_3',
  'EXP_19_4',
  'EXP_19_5',
  'EXP_19_6',
  'EXP_19_7',
  'EXP_19_8',
  'EXP_20_1',
  'EXP_20_2',
  'EXP_20_3'
)
AND code IN ('19-1', '19-2', '19-3', '19-4', '19-5', '19-6', '19-7', '19-8', '20-1', '20-2', '20-3');
