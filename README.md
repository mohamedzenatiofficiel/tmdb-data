# TMDB Data Pipeline

## Démarrage rapide
```bash
# 1) config
cp .env   # puis colle ton TMDB_TOKEN (Bearer v4)
# 2) base + pgAdmin
docker compose up -d postgres pgadmin
# 3) ETL (1er run)
docker compose run --rm etl python -m src.load_movies
# 4) Viz
docker compose up -d viz
