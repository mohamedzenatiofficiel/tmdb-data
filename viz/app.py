import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "tmdb")
DB_USER = os.getenv("DB_USER", "tmdb")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tmdb")

ENGINE = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.set_page_config(page_title="TMDB Analytics", layout="wide")

@st.cache_data(ttl=300)
def load_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with ENGINE.begin() as conn:
        return pd.read_sql(text(sql), conn, params=params)

st.title("TMDB Analytics")

# --- KPIs ---
kpi_movies = load_df("SELECT COUNT(*) AS n FROM dim_movie").iloc[0]["n"]
kpi_snapshots = load_df("SELECT COUNT(*) AS n FROM fact_movie_daily").iloc[0]["n"]
col1, col2 = st.columns(2)
col1.metric("Films ingérés", int(kpi_movies))
col2.metric("Snapshots (fait journalier)", int(kpi_snapshots))

st.divider()

# --- Popularité par genre ---
st.subheader("Popularité moyenne par genre (dernier snapshot)")
df_genre = load_df("""
SELECT name, avg_popularity, total_votes, nb_movies
FROM vw_genre_popularity
ORDER BY avg_popularity DESC
""")
st.dataframe(df_genre, use_container_width=True)
st.bar_chart(df_genre.set_index("name")["avg_popularity"])

st.divider()

# --- Top films ---
st.subheader("Top films (dernier snapshot)")
df_top = load_df("SELECT * FROM vw_top_movies")
search = st.text_input("Filtrer par titre contient...", "")
min_votes = st.slider("Votes min", 0, int(df_top["vote_count"].max() or 0), 0)
if search:
    df_top = df_top[df_top["title"].str.contains(search, case=False, na=False)]
df_top = df_top[df_top["vote_count"] >= min_votes]
st.dataframe(df_top.head(100), use_container_width=True)

# --- Série temporelle pour un film ---
st.subheader("Évolution de la popularité (par film)")
if not df_top.empty:
    choices = df_top.sort_values(["popularity"], ascending=False)[["movie_id","title"]]
    label_map = {f'{r["title"]} [{r["movie_id"]}]': int(r["movie_id"]) for _, r in choices.iterrows()}
    selected_label = st.selectbox("Choisir un film", list(label_map.keys()))
    movie_id = label_map[selected_label]
    ts = load_df("""
        SELECT date_id::date AS date, popularity, vote_average, vote_count
        FROM fact_movie_daily
        WHERE movie_id = :mid
        ORDER BY date
    """, {"mid": movie_id})
    if ts.empty:
        st.info("Pas assez de snapshots pour tracer une série (relance l’ETL à J+1).")
    else:
        st.line_chart(ts.set_index("date")[["popularity"]])
        st.dataframe(ts, use_container_width=True)
