# TMDB Data Pipeline

## Démarrage rapide
### Option A — Tout démarrer d’un coup (recommandé)
```bash
# lance Postgres + pgAdmin + Viz + ETL (one-shot)
docker compose --profile etl up -d
```
### Vérifier que l’ETL a bien tourné :
```bash
docker compose logs etl --tail 200
```


### Option B — Si la commande ci-dessus ne marche pas, lancer étape par étape
```bash
# 1) Base + UI
docker compose up -d postgres pgadmin

# 2) ETL (1er run — charge les données)
docker compose run --rm etl python -m src.load_movies

# 3) Viz (dashboard)
docker compose up -d viz
```


## Accès UIs

pgAdmin : http://localhost:5050

Viz : http://localhost:8501



## Accès pgAdmin & connexion au serveur Postgres
```bash
Ouvrir pgAdmin (web)

URL : http://localhost:5050

Identifiants de connexion à pgAdmin :

Email : admin@example.com

Mot de passe : admin
```

## Enregistrer le serveur Postgres dans pgAdmin 
```bash
Dans pgAdmin : Servers → clic droit → Create → Server…

onglet General

Name : TMDB

onglet Connection

Host name/address : postgres (nom du service Docker)

Port : 5432

Maintenance database : tmdb

Username : tmdb

Password : tmdb (cocher “Save password”)
```

## Arrêter les services
```bash
# arrêter ET effacer les volumes (DB remise à zéro)
docker compose down -v --remove-orphans
```




## Structure du projet : 
```bash
.
├─ db/
│  └─ init/
│     ├─ 01_schema.sql
│     ├─ 02_views.sql
│     └─ 03_indexes.sql
├─ etl/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ src/  (config.py, db.py, tmdb_client.py, cleaning.py, load_movies.py)
├─ viz/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  └─ app.py
├─ docker-compose.yml
├─ .env.example
└─ README.md

```