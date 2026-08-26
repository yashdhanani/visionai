-- =============================================================
-- VisionAI – Complete Database Schema for Supabase (PostgreSQL)
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- =============================================================

-- ── ENUM TYPES ────────────────────────────────────────────────

CREATE TYPE userrole       AS ENUM ('USER', 'ADMIN');
CREATE TYPE sourcetype     AS ENUM ('image', 'video', 'webcam', 'stream');
CREATE TYPE detectionstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE modelstatus    AS ENUM ('available', 'active', 'disabled');

-- ── TABLES ────────────────────────────────────────────────────

CREATE TABLE users (
    id             VARCHAR(32)  PRIMARY KEY,
    name           VARCHAR(120) NOT NULL,
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    avatar         VARCHAR(500),
    role           userrole     NOT NULL DEFAULT 'USER',
    email_verified BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_email      ON users (email);
CREATE INDEX ix_users_role       ON users (role);
CREATE INDEX ix_users_created_at ON users (created_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE projects (
    id          VARCHAR(32)  PRIMARY KEY,
    user_id     VARCHAR(32)  NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name        VARCHAR(160) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_projects_user_id       ON projects (user_id);
CREATE INDEX ix_projects_created_at    ON projects (created_at);
CREATE INDEX ix_projects_user_created  ON projects (user_id, created_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE ml_models (
    id                   VARCHAR(32)  PRIMARY KEY,
    name                 VARCHAR(160) NOT NULL,
    version              VARCHAR(40)  NOT NULL DEFAULT '1.0',
    framework            VARCHAR(60)  NOT NULL DEFAULT 'ultralytics-yolo',
    path                 VARCHAR(500) NOT NULL,
    status               modelstatus  NOT NULL DEFAULT 'available',
    accuracy_map         FLOAT,
    classes_count        INTEGER,
    inference_speed_fps  FLOAT,
    notes                TEXT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ml_models_status     ON ml_models (status);
CREATE INDEX ix_ml_models_created_at ON ml_models (created_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE detections (
    id                VARCHAR(32)      PRIMARY KEY,
    project_id        VARCHAR(32)      NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    model_id          VARCHAR(32)      REFERENCES ml_models (id) ON DELETE SET NULL,
    source_type       sourcetype       NOT NULL,
    source_url        VARCHAR(500),
    original_path     VARCHAR(500),
    annotated_path    VARCHAR(500),
    processing_time_ms FLOAT,
    inference_time_ms  FLOAT,
    fps               FLOAT,
    object_count      INTEGER          NOT NULL DEFAULT 0,
    avg_confidence    FLOAT,
    image_width       INTEGER,
    image_height      INTEGER,
    status            detectionstatus  NOT NULL DEFAULT 'completed',
    error_message     TEXT,
    progress          FLOAT            NOT NULL DEFAULT 100.0,
    frames_total      INTEGER,
    frames_done       INTEGER,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_detections_project_id      ON detections (project_id);
CREATE INDEX ix_detections_model_id        ON detections (model_id);
CREATE INDEX ix_detections_source_type     ON detections (source_type);
CREATE INDEX ix_detections_status          ON detections (status);
CREATE INDEX ix_detections_object_count    ON detections (object_count);
CREATE INDEX ix_detections_created_at      ON detections (created_at);
CREATE INDEX ix_detections_project_created ON detections (project_id, created_at);
CREATE INDEX ix_detections_source_status   ON detections (source_type, status);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE detection_objects (
    id            SERIAL       PRIMARY KEY,
    detection_id  VARCHAR(32)  NOT NULL REFERENCES detections (id) ON DELETE CASCADE,
    class_id      INTEGER      NOT NULL,
    class_name    VARCHAR(80)  NOT NULL,
    confidence    FLOAT        NOT NULL,
    x             FLOAT        NOT NULL,
    y             FLOAT        NOT NULL,
    width         FLOAT        NOT NULL,
    height        FLOAT        NOT NULL,
    track_id      INTEGER,
    text          VARCHAR(64)
);

CREATE INDEX ix_detection_objects_detection_id  ON detection_objects (detection_id);
CREATE INDEX ix_detection_objects_class_id      ON detection_objects (class_id);
CREATE INDEX ix_detection_objects_class_name    ON detection_objects (class_name);
CREATE INDEX ix_detection_objects_confidence    ON detection_objects (confidence);
CREATE INDEX ix_detection_objects_track_id      ON detection_objects (track_id);
CREATE INDEX ix_objects_detection_class         ON detection_objects (detection_id, class_name);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE detection_sessions (
    id               VARCHAR(32)  PRIMARY KEY,
    project_id       VARCHAR(32)  REFERENCES projects (id) ON DELETE CASCADE,
    source_type      sourcetype   NOT NULL,
    started_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ended_at         TIMESTAMPTZ,
    avg_fps          FLOAT,
    total_frames     INTEGER      NOT NULL DEFAULT 0,
    total_detections INTEGER      NOT NULL DEFAULT 0
);

CREATE INDEX ix_detection_sessions_project_id  ON detection_sessions (project_id);
CREATE INDEX ix_detection_sessions_started_at  ON detection_sessions (started_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE api_keys (
    id             VARCHAR(32)  PRIMARY KEY,
    user_id        VARCHAR(32)  NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name           VARCHAR(120) NOT NULL,
    key_hash       VARCHAR(128) NOT NULL UNIQUE,
    prefix_display VARCHAR(40)  NOT NULL,
    last_used_at   TIMESTAMPTZ,
    revoked        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_api_keys_user_id    ON api_keys (user_id);
CREATE INDEX ix_api_keys_key_hash   ON api_keys (key_hash);
CREATE INDEX ix_api_keys_revoked    ON api_keys (revoked);
CREATE INDEX ix_api_keys_created_at ON api_keys (created_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE refresh_tokens (
    jti        VARCHAR(64)  PRIMARY KEY,
    user_id    VARCHAR(32)  NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ  NOT NULL,
    revoked    BOOLEAN      NOT NULL DEFAULT FALSE,
    ip_address VARCHAR(64),
    user_agent VARCHAR(300),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at);
CREATE INDEX ix_refresh_tokens_revoked    ON refresh_tokens (revoked);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE auth_events (
    id         SERIAL       PRIMARY KEY,
    user_id    VARCHAR(32),
    event      VARCHAR(60)  NOT NULL,
    ip_address VARCHAR(64),
    user_agent VARCHAR(300),
    detail     JSONB,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_auth_events_user_id    ON auth_events (user_id);
CREATE INDEX ix_auth_events_event      ON auth_events (event);
CREATE INDEX ix_auth_events_created_at ON auth_events (created_at);

-- ──────────────────────────────────────────────────────────────

CREATE TABLE one_time_tokens (
    token_hash VARCHAR(128) PRIMARY KEY,
    user_id    VARCHAR(32)  NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    purpose    VARCHAR(30)  NOT NULL,
    expires_at TIMESTAMPTZ  NOT NULL,
    used       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_one_time_tokens_user_id    ON one_time_tokens (user_id);
CREATE INDEX ix_one_time_tokens_purpose    ON one_time_tokens (purpose);
CREATE INDEX ix_one_time_tokens_expires_at ON one_time_tokens (expires_at);

-- ── DONE ──────────────────────────────────────────────────────
-- All tables created. Now update DATABASE_URL in Render to use
-- the Supabase Connection Pooler URL (pooler.supabase.com:6543)
-- then redeploy → the admin user will be seeded automatically.
