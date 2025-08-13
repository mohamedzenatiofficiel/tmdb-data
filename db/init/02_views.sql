CREATE OR REPLACE VIEW vw_movie_latest AS
SELECT DISTINCT ON (f.movie_id)
  f.movie_id, m.title, m.release_date, f.popularity, f.vote_average, f.vote_count, f.date_id AS snapshot_date
FROM fact_movie_daily f
JOIN dim_movie m ON m.movie_id = f.movie_id
ORDER BY f.movie_id, f.date_id DESC;

CREATE OR REPLACE VIEW vw_genre_popularity AS
SELECT g.genre_id, g.name,
       AVG(f.popularity) AS avg_popularity,
       SUM(f.vote_count) AS total_votes,
       COUNT(DISTINCT f.movie_id) AS nb_movies
FROM vw_movie_latest l
JOIN fact_movie_daily f ON f.movie_id = l.movie_id AND f.date_id = l.snapshot_date
JOIN bridge_movie_genre bg ON bg.movie_id = l.movie_id
JOIN dim_genre g ON g.genre_id = bg.genre_id
GROUP BY g.genre_id, g.name
ORDER BY avg_popularity DESC;

CREATE OR REPLACE VIEW vw_top_movies AS
SELECT *
FROM vw_movie_latest
ORDER BY popularity DESC, vote_average DESC, vote_count DESC
LIMIT 200;
