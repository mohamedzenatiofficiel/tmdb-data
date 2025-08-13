# Rapport – TMDB Data Pipeline

## Contexte du projet
Objectif : fournir aux analystes un jeu de données exploitable (films TMDB), mis à jour par ETL, avec vues d’analyse et dataviz.

## Choix d’architecture
- **Sources** : TMDB (API v3, Bearer). (Optionnel : enrichissement CSV).
- **Traitement** : ETL Python conteneurisé (requests, SQLAlchemy, tenacity).
- **Stockage** : PostgreSQL 16 (volume Docker pour persistance).
- **Modélisation** : schéma en étoile léger : dimensions (film/genre/compagnie/pays/langue/date), tables de pont M:N, fait journalier `fact_movie_daily`.
- **Exposition** : vues SQL (`vw_movie_latest`, `vw_genre_popularity`, `vw_top_movies`), Streamlit pour 3 analyses.
- **Ops** : Docker Compose (services : postgres, pgadmin, etl, viz).

## Démarche
1. Conception du modèle.
2. Scripts init SQL (tables + vues + index).
3. Client TMDB + nettoyage.
4. Chargement.
5. Vues d’analyse + vérif dans pgAdmin.
6. Dataviz Streamlit (KPIs, genres, top films).

## Modélisation (entités, clés, granularité)
- **dim_movie(movie_id PK)** : attributs stables du film (titre, dates, langues…).
- **dim_genre/ company/ country/ language** (PK naturelles).
- **bridges** (`movie_id` + dimension_id) : relations M:N, PK composites.
- **dim_date(date_id PK)** : calendrier (préchargé sur ~5 ans).
- **fact_movie_daily(date_id, movie_id PK)** : métriques journalières (popularité, votes).
- **Granularité** : 1 ligne par (film, jour).
- **Vues** :
  - `vw_movie_latest` : dernier snapshot par film.
  - `vw_genre_popularity` : popularité par genre à date la plus récente.
  - `vw_top_movies` : classement.

## Possibilités d’amélioration
- Planification quotidienne portable (cron container / K8s CronJob).
- Tests plus complets (rate limit, schéma DB).
- Data validation (Pydantic).
- CI (GitHub Actions) : build + tests
- Deuxième source plat (ex: continents) pour enrichir `dim_country`.
- Helm chart (microk8s)

## Conclusion
Pipeline opérationnel, reproductible, et extensible. Livré avec vues et dataviz minimalistes.
