import os 
import requests
from datetime import date
from src.cleaning import (
    as_dim_movie,
    iter_genres,
    iter_companies,
    iter_countries,
    iter_languages,
    as_fact_daily,
)


r=requests.get("https://api.themoviedb.org/3/discover/movie",
               headers={"Authorization":f"Bearer {os.environ['TMDB_TOKEN']}"},
               params={"page":1}, timeout=20)


print("status", r.status_code, "ok", "total_results" in r.json())



def test_as_dim_movie_maps_core_fields():
    d = {
        "id": 42,
        "title": "My Film",
        "original_title": "My Film Original",
        "release_date": "2024-01-15",
        "original_language": "en",
        "runtime": 123,
        "budget": 1_000_000,
        "revenue": 2_500_000,
        "adult": False,
        "homepage": "https://example.com",
        "imdb_id": "tt1234567",
        "status": "Released",
    }
    row = as_dim_movie(d)
    assert row["movie_id"] == 42
    assert row["title"] == "My Film"
    assert row["original_title"] == "My Film Original"
    assert row["release_date"] == "2024-01-15"
    assert row["original_language"] == "en"
    assert row["runtime_minutes"] == 123
    assert row["budget_usd"] == 1_000_000
    assert row["revenue_usd"] == 2_500_000
    assert row["adult"] is False
    assert row["homepage"] == "https://example.com"
    assert row["imdb_id"] == "tt1234567"
    assert row["status"] == "Released"


def test_iter_genres_ok_and_empty():
    d = {"genres": [{"id": 1, "name": "Action"}, {"id": 2, "name": "Drama"}], "id": 77}
    rows = list(iter_genres(d))
    assert rows == [{"genre_id": 1, "name": "Action"}, {"genre_id": 2, "name": "Drama"}]
    # cas vide/absent
    assert list(iter_genres({})) == []


def test_iter_companies_countries_languages():
    d = {
        "id": 7,
        "production_companies": [{"id": 10, "name": "Pixar", "origin_country": "US"}],
        "production_countries": [{"iso_3166_1": "US", "name": "United States"}],
        "spoken_languages": [{"iso_639_1": "en", "name": "English"}],
    }

    comp = list(iter_companies(d))
    assert comp == [{"company_id": 10, "name": "Pixar", "origin_country": "US"}]

    ctry = list(iter_countries(d))
    assert ctry == [{"iso_3166_1": "US", "name": "United States"}]

    langs = list(iter_languages(d))
    assert langs == [{"iso_639_1": "en", "name": "English"}]


def test_as_fact_daily_builds_snapshot_row():
    d = {"id": 7, "popularity": 9.9, "vote_average": 7.5, "vote_count": 10}
    snap = date(2024, 1, 2)
    row = as_fact_daily(d, snap)
    assert row["date_id"] == "2024-01-02"
    assert row["movie_id"] == 7
    assert row["popularity"] == 9.9
    assert row["vote_average"] == 7.5
    assert row["vote_count"] == 10
