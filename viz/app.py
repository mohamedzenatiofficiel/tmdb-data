import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# --- Connexion DB (via variables d'env docker-compose) ---
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "tmdb")
DB_USER = os.getenv("DB_USER", "tmdb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tmdb")
ENGINE = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.set_page_config(page_title="TMDB - Dashboard simple", layout="wide")


# --- fonction utilitaire pour tester la présence de données ---
def has_data() -> bool:
    try:
        with ENGINE.begin() as conn:
            n = pd.read_sql(text("SELECT COUNT(*) AS n FROM dim_movie"), conn).iloc[0]["n"]
        return int(n) > 0
    except Exception:
        # DB pas prête ou requête échouée
        return False

# --- message d'attente si l'ETL n'a pas encore rempli la base ---
if not has_data():
    st.warning("⏳ Données en cours de chargement… L’ETL n’a pas encore alimenté la base.")
    st.caption("Astuce : lance l’ETL puis rafraîchis cette page (F5) dans 15–30 sec.\n"
               "Commande : `docker compose run --rm etl python -m src.load_movies`")
    st.stop()  # on arrête le rendu du reste du dashboard jusqu’à ce qu’il y ait des données



st.title("🎬 TMDB – Dashboard (simple)")

@st.cache_data(ttl=60)
def q(sql: str) -> pd.DataFrame:
    with ENGINE.begin() as conn:
        return pd.read_sql(text(sql), conn)

# ========== Analyse 1 : KPIs ==========
st.subheader("1) Indicateurs clés")
try:
    n_films = int(q("SELECT COUNT(*) AS n FROM dim_movie").iloc[0]["n"])
    latest = q("SELECT vote_average, vote_count FROM vw_movie_latest")
    note_moy = float(latest["vote_average"].dropna().mean()) if not latest.empty else 0.0
    votes_tot = int(latest["vote_count"].dropna().sum()) if not latest.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Films ingérés", n_films)
    c2.metric("Note moyenne (dernier snapshot)", f"{note_moy:.2f}")
    c3.metric("Total votes (dernier snapshot)", f"{votes_tot:,}".replace(",", " "))
except Exception as e:
    st.error(f"Erreur KPIs : {e}")

st.divider()

# ========== Analyse 2 : Popularité par genre ==========
st.subheader("2) Popularité moyenne par genre (Top 10)")
try:
    genre = q("""
        SELECT name, avg_popularity, total_votes, nb_movies
        FROM vw_genre_popularity
        ORDER BY avg_popularity DESC
        LIMIT 10
    """)
    if genre.empty:
        st.info("Aucune donnée de genre. Lance l’ETL puis rafraîchis la page.")
    else:
        st.bar_chart(genre.set_index("name")["avg_popularity"])
        st.caption("Astuce : passe ta souris pour voir la valeur exacte.")
        st.dataframe(genre, use_container_width=True)
except Exception as e:
    st.error(f"Erreur popularité par genre : {e}")

st.divider()

# ========== Analyse 3 : Top films ==========
st.subheader("3) Top films (dernier snapshot)")
try:
    top_n = st.slider("Nombre de films à afficher", 5, 50, 20, 5)
    top = q(f"""
        SELECT title, popularity, vote_average, vote_count
        FROM vw_top_movies
        ORDER BY popularity DESC, vote_average DESC, vote_count DESC
        LIMIT {int(top_n)}
    """)
    if top.empty:
        st.info("Aucune donnée de film. Lance l’ETL puis rafraîchis la page.")
    else:
        st.bar_chart(top.set_index("title")["popularity"])
        st.dataframe(top, use_container_width=True)
except Exception as e:
    st.error(f"Erreur top films : {e}")




# --- Analyse : Popularité par continent (issu du CSV) ---
st.subheader("🌍 Popularité moyenne par continent")

q_cont = """
SELECT continent, avg_popularity, n_movies, total_votes
FROM vw_continent_popularity
ORDER BY avg_popularity DESC
"""
df_cont = pd.read_sql(text(q_cont), ENGINE)

if df_cont.empty:
    st.info("Aucune donnée continent disponible. Lance d'abord le loader CSV : "
            "`docker compose run --rm etl python -m src.load_country_continent`")
else:
    # Bar chart + détail
    st.bar_chart(df_cont.set_index("continent")["avg_popularity"])
    st.dataframe(df_cont, use_container_width=True)

    # Drilldown : top films d'un continent
    st.markdown("---")
    st.subheader("🎬 Top 10 films par continent (dernier snapshot)")
    selected_cont = st.selectbox("Choisir un continent", df_cont["continent"].tolist())
    q_top_by_continent = """
    WITH latest AS (SELECT * FROM vw_movie_latest)
    SELECT
        m.title,
        l.popularity,
        l.vote_average,
        l.vote_count
    FROM latest l
    JOIN dim_movie m              ON m.movie_id = l.movie_id
    JOIN bridge_movie_country b   ON b.movie_id = l.movie_id
    JOIN dim_country c            ON c.iso_3166_1 = b.iso_3166_1
    WHERE c.continent = :cont
    GROUP BY m.title, l.popularity, l.vote_average, l.vote_count
    ORDER BY l.popularity DESC, l.vote_average DESC, l.vote_count DESC
    LIMIT 10
    """
    df_top = pd.read_sql(text(q_top_by_continent), ENGINE, params={"cont": selected_cont})
    if df_top.empty:
        st.warning(f"Aucun film trouvé pour {selected_cont}.")
    else:
        st.dataframe(df_top, use_container_width=True)