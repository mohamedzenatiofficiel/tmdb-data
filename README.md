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
```

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