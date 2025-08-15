# Rapport – TMDB Data Pipeline

## 1) Contexte & objectifs

**Contexte.** Livrer, pour un client « data » (analyste / data scientist / métier), un jeu de données exploitable issu de l’API TMDB. Le pipeline doit être **reproductible**, **documenté**, **conteneurisé**, et fournir une **base SQL** avec des **vues analytiques** et une petite dataviz.

**Objectif métier.** Mettre à disposition, chaque jour, les mesures clés d’intérêt (popularité, note, nombre de votes) pour les films populaires, ainsi que leurs attributs (genres, pays, langues, compagnies). Ces données doivent être fiables (idempotence, clés), faciles à requêter (modèle en étoile), et rapidement visualisables.

---

## 2) Choix d’implémentation technique & architecture

- **Langage** : Python 3.11 (extraction, nettoyage, chargement).
- **Libs** : `requests` (API), `tenacity` (retries), `SQLAlchemy` + `psycopg2` (PostgreSQL).
- **Base** : PostgreSQL 16 (préférence du sujet), exposée en conteneur.
- **Orchestration locale** : Docker Compose (services : `postgres`, `pgadmin`, `etl`, `viz`).
- **Dataviz** : Streamlit (dashboard minimal).
- **Persistance** : volumes Docker (`pgdata` pour Postgres, `pgadmin_data` pour la config pgAdmin).
- **Sécurité** : le `TMDB_TOKEN` est lu via `.env` (non committé).  
- **Réseau** : les conteneurs communiquent par nom de service (`DB_HOST=postgres`).

**Architecture logique (résumé).**
- **Source** : API TMDB v3 (auth Bearer v4).
- **ETL** : extraction incrémentale simple (pages Discover → détails film), nettoyage/mapping → **upsert** en base.
- **Stockage** : **schéma en étoile** (dimensions + tables de pont + fait journalier).
- **Exposition** : **vues SQL** pour l’analytique, **Streamlit** pour un aperçu visuel.

---

## 3) Modélisation relationnelle (documentation)

### 3.1 Schéma cible
- **Fait** : `fact_movie_daily(date_id, movie_id)`  
  - **Granularité** : 1 ligne par (film, jour).
  - **Mesures** : `popularity`, `vote_average`, `vote_count`.
- **Dimensions** :
  - `dim_movie(movie_id)` : titre, date de sortie, langue originale, statut, runtime, budget, revenue, etc.
  - `dim_genre(genre_id)` : liste des genres TMDB.
  - `dim_company(company_id)` : studios / sociétés de production.
  - `dim_country(iso_3166_1)` : pays de production.
  - `dim_language(iso_639_1)` : langues parlées.
  - `dim_date(date_id)` : calendrier (année, trimestre, mois, semaine, jour-semaine).  
- **Tables de pont** (M:N) :
  - `bridge_movie_genre(movie_id, genre_id)`
  - `bridge_movie_company(movie_id, company_id)`
  - `bridge_movie_country(movie_id, iso_3166_1)`
  - `bridge_movie_language(movie_id, iso_639_1)`

### 3.2 Clés, contraintes & index
- **PK** :
  - `fact_movie_daily` : `(date_id, movie_id)`
  - Ponts : `(movie_id, <dimension_id>)`
  - Dimensions : PK naturelles (`movie_id`, `genre_id`, `company_id`, `iso_3166_1`, `iso_639_1`) ou techniques.
- **FK** : `fact_movie_daily.movie_id → dim_movie.movie_id` ; `date_id → dim_date.date_id`; idem pour ponts.
- **Index** :
  - `fact_movie_daily(movie_id)` et `fact_movie_daily(date_id)` (accès par film ou date).
  - Composite `(movie_id, date_id DESC)` pour accélérer le « dernier snapshot » par film.
  - `bridge_movie_genre(movie_id)` et `(genre_id)` pour les jointures.

### 3.3 Vues analytiques
- `vw_movie_latest` : **dernier snapshot** par film (popularité/note/votes récents).
- `vw_genre_popularity` : agrégats **par genre** au dernier snapshot (popularité moyenne, total votes, nb de films).
- `vw_top_movies` : **classement** des films au dernier snapshot (popularité → note → votes).

---

## 4) Démarche (pipeline & qualité)

1. **Conception du modèle** : choix d’une **étoile** centrée sur un **fait journalier**, dimensions et ponts pour le contexte.  
2. **Scripts SQL d’initialisation** : création des tables, contraintes, vues, puis index (séparés pour lisibilité).  
3. **Extraction** :
   - `/discover/movie` (pages paramétrables) pour récupérer des **IDs** (tri popularité, adultes exclus).
   - `/movie/{id}` pour les **détails complets** (genres, langues, compagnies, pays, métriques).
   - **Retries** et **timeouts** pour robustesse ; **pauses** configurables pour limiter les 429 (rate limit).
4. **Nettoyage / mapping** :
   - Normalisation de types (dates, booléens, numériques).
   - Fonctions génératrices dédiées pour chaque table (ex. iter_genres, iter_languages…).
   - Déduplication en mémoire avant chargement.
5. **Chargement (SQLAlchemy)** :
   - **Upsert générique** : `INSERT ... ON CONFLICT ...`
     - **Dimensions** : `DO UPDATE SET` sur colonnes non clés.
     - **Ponts** : `DO NOTHING` (clé composite = contenu, pas de colonnes à mettre à jour).
     - **Fait** : `DO UPDATE` (si re-run le même jour).
   - **Transactions** : chargement par batch sous `BEGIN/COMMIT`.
6. **Exposition** :
   - Vues orientées **lecture** (simplifient les requêtes analystes).
   - Streamlit pour une **lecture visuelle** rapide (KPI, popularité par genre, top films).

**Qualité / idempotence.**
- Rejouer l’ETL le même jour ne crée **pas de doublons** (PK composites + upsert).
- Intégrité référentielle (FK) et ponts sans orphelins.
- Index pour garantir des temps de réponse stables quand le volume augmente.

---

## 5) Dataviz (aperçu)

**Streamlit**, 3 analyses simples :
1. **KPIs** : nb de films, note moyenne, total de votes (au dernier snapshot).  
2. **Popularité moyenne par genre** (Top 10).  
3. **Top films** (bar chart + tableau filtrable).  

Objectif : **démontrer** la disponibilité des données et la cohérence des vues, sans complexifier le front.

---

## 6) Exploitation & déploiement

- **Docker Compose** :  
  - `postgres` (données persistées via volume),  
  - `pgadmin` (UI de requêtage),  
  - `etl` (job one-shot),  
  - `viz` (dashboard web).
- **Démarrage** :
  - Tout-en-un (profil ETL activé) ou **fallback** étape par étape (DB → ETL → viz).
- **Planification** :
  - Locale : tâche planifiée OS (ex. Windows Task Scheduler) ou conteneur `cron`.
  - CI/CD : possible avec GitHub Actions (tests + build images + job d’extraction).

---

## 7) Comment tester (sanity checks)

- **Santé DB** :
  - `SELECT COUNT(*) FROM dim_movie;` (> 0)
  - `SELECT COUNT(*) FROM fact_movie_daily WHERE date_id=CURRENT_DATE;` (≈ nb de films)
- **Vues** :
  - `SELECT * FROM vw_top_movies LIMIT 10;`
  - `SELECT * FROM vw_genre_popularity ORDER BY avg_popularity DESC LIMIT 10;`
- **Intégrité** :
  - Zéro orphelin dans les ponts (LEFT JOIN vs `dim_*`).
  - Zéro doublon sur `(date_id, movie_id)` dans le fait.
- **Perf** :
  - Index présents (`pg_indexes`) ; `EXPLAIN` montre des `Index Scan` quand la volumétrie croît.

---

## 8) Possibilités d’amélioration

- **Seconde source « fichier plat »** : CSV *country → continent* pour enrichir `dim_country` (multi-source exigence renforcée).
- **Validation des données** : Pydantic/Great Expectations (schémas, gammes de valeurs, complétude).
- **Planification portable** : conteneur `cron` / GitHub Actions (run quotidien + reporting).
- **CI/CD** : lint (`ruff`), tests unitaires (mappings), build images.
- **Kubernetes (bonus)** : Helm chart (StatefulSet Postgres, CronJob ETL, Deployment viz).
- **Historisation avancée** : incrémental fin basé sur timestamps TMDB (si dispo) et/ou autres endpoints (cast/crew).

---


## 9) Conclusion

Le pipeline répond aux attendus du challenge : **conception d’une architecture data** (modèle relationnel clair), **développement Python** (ETL conteneurisé, résilient, idempotent), **DB SQL** avec **persistence** et **vues** prêtes à l’analyse, et **dataviz** pour un premier niveau d’exploration.  
La solution est **reproductible**, **documentée** et **extensible** : elle peut être enrichie (multi-source, QA, orchestration K8s) selon les besoins et le niveau d’industrialisation visé.
