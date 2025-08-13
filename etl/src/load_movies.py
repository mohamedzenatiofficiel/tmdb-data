from datetime import date
from .config import SETTINGS
from .db import tx, upsert
from .tmdb_client import discover_movies_pages, fetch_movie_details
from .cleaning import (
    as_dim_movie, iter_genres, iter_companies, iter_countries, iter_languages,
    iter_bridge_movie_genre, iter_bridge_movie_company, iter_bridge_movie_country,
    iter_bridge_movie_language, as_fact_daily
)

def main():
    snapshot = date.today()
    ids = []
    for payload in discover_movies_pages(SETTINGS.max_pages):
        ids += [it["id"] for it in payload.get("results", []) if "id" in it]
    ids = list(dict.fromkeys(ids))

    details = []
    for mid in ids:
        try: details.append(fetch_movie_details(mid))
        except Exception as e: print(f"[WARN] Movie {mid}: {e}")

    dim_movie_rows = [as_dim_movie(d) for d in details]
    dim_genre_rows     = dedup([r for d in details for r in iter_genres(d)], ["genre_id"])
    dim_company_rows   = dedup([r for d in details for r in iter_companies(d)], ["company_id"])
    dim_country_rows   = dedup([r for d in details for r in iter_countries(d)], ["iso_3166_1"])
    dim_language_rows  = dedup([r for d in details for r in iter_languages(d)], ["iso_639_1"])
    bridge_genre_rows   = dedup([r for d in details for r in iter_bridge_movie_genre(d)], ["movie_id","genre_id"])
    bridge_company_rows = dedup([r for d in details for r in iter_bridge_movie_company(d)], ["movie_id","company_id"])
    bridge_country_rows = dedup([r for d in details for r in iter_bridge_movie_country(d)], ["movie_id","iso_3166_1"])
    bridge_lang_rows    = dedup([r for d in details for r in iter_bridge_movie_language(d)], ["movie_id","iso_639_1"])
    fact_daily_rows = [as_fact_daily(d, snapshot) for d in details]

    with tx() as conn:
        if dim_movie_rows:
            upsert(conn, "dim_movie", ["movie_id"], list(dim_movie_rows[0].keys()), dim_movie_rows)
        upsert(conn, "dim_genre",   ["genre_id"],   ["genre_id","name"], dim_genre_rows)
        upsert(conn, "dim_company", ["company_id"], ["company_id","name","origin_country"], dim_company_rows)
        upsert(conn, "dim_country", ["iso_3166_1"], ["iso_3166_1","name"], dim_country_rows)
        upsert(conn, "dim_language",["iso_639_1"],  ["iso_639_1","name"], dim_language_rows)
        upsert(conn, "bridge_movie_genre",   ["movie_id","genre_id"],   ["movie_id","genre_id"], bridge_genre_rows)
        upsert(conn, "bridge_movie_company", ["movie_id","company_id"], ["movie_id","company_id"], bridge_company_rows)
        upsert(conn, "bridge_movie_country", ["movie_id","iso_3166_1"], ["movie_id","iso_3166_1"], bridge_country_rows)
        upsert(conn, "bridge_movie_language",["movie_id","iso_639_1"],  ["movie_id","iso_639_1"], bridge_lang_rows)
        upsert(conn, "fact_movie_daily", ["date_id","movie_id"],
               ["date_id","movie_id","popularity","vote_average","vote_count"], fact_daily_rows)

    print(f"[OK] Chargé {len(details)} films ; genres={len(dim_genre_rows)} companies={len(dim_company_rows)} "
          f"pays={len(dim_country_rows)} langues={len(dim_language_rows)}.")

def dedup(rows: list[dict], keys: list[str]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        k = tuple(r[k] for k in keys)
        if k not in seen: seen.add(k); out.append(r)
    return out

if __name__ == "__main__":
    main()
