CREATE INDEX IF NOT EXISTS ix_fact_movie_daily_movie ON fact_movie_daily (movie_id);
CREATE INDEX IF NOT EXISTS ix_fact_movie_daily_date  ON fact_movie_daily (date_id);

CREATE INDEX IF NOT EXISTS ix_bridge_movie_genre_movie ON bridge_movie_genre (movie_id);
CREATE INDEX IF NOT EXISTS ix_bridge_movie_genre_genre ON bridge_movie_genre (genre_id);


CREATE INDEX IF NOT EXISTS ix_fact_movie_daily_latest ON fact_movie_daily (movie_id, date_id DESC);

