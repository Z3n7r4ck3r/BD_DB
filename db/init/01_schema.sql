-- 01_schema.sql  (schema minimale ma completo)
CREATE TABLE company (
  company_id       SERIAL PRIMARY KEY,
  name             TEXT NOT NULL,
  created_at       TIMESTAMP DEFAULT now()
);

CREATE TABLE product_asset (
  product_asset_id SERIAL PRIMARY KEY,
  company_id       INT NOT NULL REFERENCES company(company_id) ON DELETE CASCADE,
  name             TEXT NOT NULL
);

CREATE TABLE outcome_sentiment (
  outcome_sentiment_id SERIAL PRIMARY KEY,
  code  TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE business_mode (
  business_mode_id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE primary_domain (
  primary_domain_id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE strategic_bucket (
  strategic_bucket_id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE application_domain (
  application_domain_id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE status_lu (
  status_id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL
);

CREATE TABLE conversion_rate_mapping (
  conversion_mapping_id SERIAL PRIMARY KEY,
  status_id             INT REFERENCES status_lu(status_id),
  outcome_sentiment_id  INT REFERENCES outcome_sentiment(outcome_sentiment_id),
  business_mode_id      INT REFERENCES business_mode(business_mode_id),
  primary_domain_id     INT REFERENCES primary_domain(primary_domain_id),
  strategic_bucket_id   INT REFERENCES strategic_bucket(strategic_bucket_id),
  application_domain_id INT REFERENCES application_domain(application_domain_id),
  conversion_rate       NUMERIC(5,2) NOT NULL,
  UNIQUE (status_id, outcome_sentiment_id, business_mode_id,
          primary_domain_id, strategic_bucket_id, application_domain_id)
);

CREATE TABLE record (
  record_id             INT PRIMARY KEY,
  company_id            INT NOT NULL REFERENCES company(company_id),
  product_asset_id      INT REFERENCES product_asset(product_asset_id),
  outcome_sentiment_id  INT REFERENCES outcome_sentiment(outcome_sentiment_id),
  business_mode_id      INT REFERENCES business_mode(business_mode_id),
  primary_domain_id     INT REFERENCES primary_domain(primary_domain_id),
  strategic_bucket_id   INT REFERENCES strategic_bucket(strategic_bucket_id),
  application_domain_id INT REFERENCES application_domain(application_domain_id),
  status_id             INT REFERENCES status_lu(status_id),
  notes                 TEXT
);

CREATE TABLE business_review_session (
  brs_id        INT PRIMARY KEY,
  year          INT NOT NULL,
  quarter       INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
  session_date  DATE,
  report_path   TEXT
);

CREATE TABLE touchpoint (
  touchpoint_id INT PRIMARY KEY,
  record_id     INT NOT NULL REFERENCES record(record_id) ON DELETE CASCADE,
  brs_id        INT NOT NULL REFERENCES business_review_session(brs_id) ON DELETE CASCADE,
  tp_type       TEXT,
  tp_ref        TEXT,
  notes         TEXT
);

CREATE OR REPLACE VIEW record_duration AS
SELECT
  r.record_id,
  MIN(brs.year*100 + brs.quarter) AS start_yq,
  MAX(brs.year*100 + brs.quarter) AS end_yq,
  MAX(brs.year*100 + brs.quarter) - MIN(brs.year*100 + brs.quarter) AS duration_yq
FROM record r
JOIN touchpoint tp ON tp.record_id = r.record_id
JOIN business_review_session brs ON brs.brs_id = tp.brs_id
GROUP BY r.record_id;
