# etl/src/load_country_continent.py
import csv
import os
from typing import List, Dict
from sqlalchemy import text
from .db import get_engine

CSV_PATH = os.getenv("COUNTRY_CSV", "/app/data/country_continent.csv")

def read_csv(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iso = (row.get("iso_3166_1") or "").strip().upper()
            cont = (row.get("continent") or "").strip()
            if iso and cont:
                rows.append({"iso_3166_1": iso, "continent": cont})
    return rows

def main() -> None:
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Fichier CSV introuvable: {CSV_PATH}")
        raise SystemExit(1)

    rows = read_csv(CSV_PATH)
    if not rows:
        print("[WARN] CSV vide — rien à mettre à jour.")
        return

    engine = get_engine()
    updated = 0
    skipped = 0
    with engine.begin() as conn:
        stmt = text("""
            UPDATE dim_country AS c
               SET continent = :continent
             WHERE c.iso_3166_1 = :iso_3166_1
        """)
        for r in rows:
            res = conn.execute(stmt, r)
            if res.rowcount and res.rowcount > 0:
                updated += res.rowcount
            else:
                skipped += 1

    print(f"[OK] Enrichissement continent: updated={updated}, skipped={skipped} (absents en base).")

if __name__ == "__main__":
    main()
