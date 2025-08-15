CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS dim_movie (
  movie_id        BIGINT PRIMARY KEY,
  title           TEXT NOT NULL,
  original_title  TEXT,
  release_date    DATE,
  status          TEXT,
  original_language TEXT,
  runtime_minutes INTEGER,
  budget_usd      BIGINT,
  revenue_usd     BIGINT,
  adult           BOOLEAN DEFAULT FALSE,
  homepage        TEXT,
  imdb_id         TEXT,
  inserted_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_genre ( genre_id BIGINT PRIMARY KEY, name TEXT NOT NULL );
CREATE TABLE IF NOT EXISTS dim_company ( company_id BIGINT PRIMARY KEY, name TEXT NOT NULL, origin_country TEXT );
CREATE TABLE IF NOT EXISTS dim_country ( iso_3166_1 TEXT PRIMARY KEY, name TEXT, continent TEXT);
COMMENT ON COLUMN dim_country.continent IS 'Continent simple (Europe, Asia, North America, South America, Africa, Oceania).';
CREATE TABLE IF NOT EXISTS dim_language ( iso_639_1 TEXT PRIMARY KEY, name TEXT );

CREATE TABLE IF NOT EXISTS bridge_movie_genre (
  movie_id BIGINT REFERENCES dim_movie(movie_id) ON DELETE CASCADE,
  genre_id BIGINT REFERENCES dim_genre(genre_id) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, genre_id)
);

CREATE TABLE IF NOT EXISTS bridge_movie_company (
  movie_id   BIGINT REFERENCES dim_movie(movie_id) ON DELETE CASCADE,
  company_id BIGINT REFERENCES dim_company(company_id) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, company_id)
);

CREATE TABLE IF NOT EXISTS bridge_movie_country (
  movie_id    BIGINT REFERENCES dim_movie(movie_id) ON DELETE CASCADE,
  iso_3166_1  TEXT REFERENCES dim_country(iso_3166_1) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, iso_3166_1)
);

CREATE TABLE IF NOT EXISTS bridge_movie_language (
  movie_id   BIGINT REFERENCES dim_movie(movie_id) ON DELETE CASCADE,
  iso_639_1  TEXT REFERENCES dim_language(iso_639_1) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, iso_639_1)
);

CREATE TABLE IF NOT EXISTS dim_date (
  date_id   DATE PRIMARY KEY,
  year      INT,
  quarter   INT,
  month     INT,
  day       INT,
  week      INT,
  dow       INT
);

DO $$
DECLARE d DATE := CURRENT_DATE - INTERVAL '3 years';
BEGIN
  WHILE d <= CURRENT_DATE + INTERVAL '2 years' LOOP
    INSERT INTO dim_date (date_id, year, quarter, month, day, week, dow)
    VALUES (d, EXTRACT(YEAR FROM d), EXTRACT(QUARTER FROM d), EXTRACT(MONTH FROM d),
            EXTRACT(DAY FROM d), EXTRACT(WEEK FROM d), EXTRACT(DOW FROM d))
    ON CONFLICT (date_id) DO NOTHING;
    d := d + INTERVAL '1 day';
  END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS fact_movie_daily (
  date_id      DATE REFERENCES dim_date(date_id),
  movie_id     BIGINT REFERENCES dim_movie(movie_id) ON DELETE CASCADE,
  popularity   NUMERIC,
  vote_average NUMERIC,
  vote_count   BIGINT,
  inserted_at  TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (date_id, movie_id)
);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dim_movie_updated
BEFORE UPDATE ON dim_movie
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
