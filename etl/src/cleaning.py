# etl/src/cleaning.py
from datetime import date
from typing import Dict, Any, Iterator, Optional


def _none_if_empty(v: Any) -> Optional[Any]:
    return None if v in ("", None) else v


def as_dim_movie(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "movie_id": d.get("id"),
        "title": d.get("title") or d.get("name"),
        "original_title": d.get("original_title"),
        "release_date": _none_if_empty(d.get("release_date")),
        "status": d.get("status"),
        "original_language": d.get("original_language"),
        "runtime_minutes": d.get("runtime"),
        "budget_usd": d.get("budget") or 0,
        "revenue_usd": d.get("revenue") or 0,
        "adult": bool(d.get("adult", False)),
        "homepage": d.get("homepage"),
        "imdb_id": d.get("imdb_id"),
    }


def iter_genres(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    for g in (d.get("genres") or []):
        yield {"genre_id": g["id"], "name": g["name"]}


def iter_companies(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    for c in (d.get("production_companies") or []):
        yield {
            "company_id": c["id"],
            "name": c["name"],
            "origin_country": c.get("origin_country"),
        }


def iter_countries(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    for c in (d.get("production_countries") or []):
        yield {"iso_3166_1": c["iso_3166_1"], "name": c.get("name")}


def iter_languages(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    for lang in (d.get("spoken_languages") or []):
        yield {
            "iso_639_1": lang["iso_639_1"],
            "name": lang.get("english_name") or lang.get("name"),
        }

def iter_bridge_movie_genre(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    mid = d["id"]
    for g in (d.get("genres") or []):
        yield {"movie_id": mid, "genre_id": g["id"]}


def iter_bridge_movie_company(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    mid = d["id"]
    for c in (d.get("production_companies") or []):
        yield {"movie_id": mid, "company_id": c["id"]}


def iter_bridge_movie_country(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    mid = d["id"]
    for c in (d.get("production_countries") or []):
        yield {"movie_id": mid, "iso_3166_1": c["iso_3166_1"]}


def iter_bridge_movie_language(d: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    mid = d["id"]
    for lang in (d.get("spoken_languages") or []):
        yield {"movie_id": mid, "iso_639_1": lang["iso_639_1"]}

def as_fact_daily(d: Dict[str, Any], snapshot: date) -> Dict[str, Any]:
    return {
        "date_id": snapshot.isoformat(),
        "movie_id": d["id"],
        "popularity": d.get("popularity"),
        "vote_average": d.get("vote_average"),
        "vote_count": d.get("vote_count"),
    }
