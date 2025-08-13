import time, requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from .config import SETTINGS

BASE = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {SETTINGS.tmdb_token}", "Accept": "application/json"}


def _sleep(): time.sleep(SETTINGS.sleep_between_req_ms/1000)

@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(0.5,2.0))
def _get(path: str, params: dict|None=None) -> dict:
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status(); return r.json()

def discover_movies_pages(pages: int):
    for page in range(1, pages+1):
        _sleep(); yield _get("/discover/movie", params={"sort_by":"popularity.desc","include_adult":"false","page":page})

def fetch_movie_details(movie_id: int) -> dict:
    _sleep(); return _get(f"/movie/{movie_id}", params={})
