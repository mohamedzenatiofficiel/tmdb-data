import os, requests


r=requests.get("https://api.themoviedb.org/3/discover/movie",
               headers={"Authorization":f"Bearer {os.environ['TMDB_TOKEN']}"},
               params={"page":1}, timeout=20)


print("status", r.status_code, "ok", "total_results" in r.json())