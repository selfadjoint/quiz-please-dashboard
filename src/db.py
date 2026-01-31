import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

@st.cache_resource
def get_connection():
    """
    Establishes a connection to the database using credentials from secrets.toml.
    Returns a SQLAlchemy engine.
    """
    try:
        db_config = st.secrets["connections"]["postgresql"]
        # SQLAlchemy connection string: postgresql://user:password@host:port/database
        connection_str = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(connection_str)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

def run_query(query, params=None):
    """
    Executes a SQL query and returns the result as a DataFrame.
    """
    engine = get_connection()
    if engine:
        with engine.connect() as conn:
            try:
                return pd.read_sql(text(query), conn, params=params)
            except Exception as e:
                st.error(f"Query failed: {e}")
                return pd.DataFrame() # Return empty DataFrame on error
    return pd.DataFrame()

# Data Fetching Functions

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_all_teams():
    query = "SELECT id, name FROM quizplease.teams ORDER BY name;"
    return run_query(query)

@st.cache_data(ttl=3600)
def get_filter_options():
    """
    Returns distinct game names and categories for filtering.
    """
    query_games = "SELECT DISTINCT game_name FROM quizplease.games ORDER BY game_name;"
    query_categories = "SELECT DISTINCT category FROM quizplease.games ORDER BY category;"
    
    games = run_query(query_games)['game_name'].tolist()
    categories = run_query(query_categories)['category'].tolist()
    
    return games, categories

@st.cache_data(ttl=3600)
def get_games_list(game_names=None, categories=None):
    filters = []
    params = {}
    
    if game_names:
        filters.append("game_name IN :game_names")
        params["game_names"] = tuple(game_names)
    if categories:
        filters.append("category IN :categories")
        params["categories"] = tuple(categories)
        
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    
    query = f"""
        SELECT id, game_date, game_name, game_number, category 
        FROM quizplease.games 
        {where_clause}
        ORDER BY game_date DESC;
    """
    return run_query(query, params=params)


@st.cache_data(ttl=3600)
def get_overall_top_teams(limit=None, game_names=None, categories=None):
    """
    Returns top teams based on total points, optionally filtered.
    """
    filters = []
    params = {}
    
    if game_names:
        filters.append("g.game_name IN :game_names")
        params["game_names"] = tuple(game_names)
    if categories:
        filters.append("g.category IN :categories")
        params["categories"] = tuple(categories)
        
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    
    # Use LIMIT with parameterized value for safety
    if limit is not None:
        limit_clause = "LIMIT :limit_val"
        params["limit_val"] = int(limit)  # Ensure integer
    else:
        limit_clause = ""
    
    query = f"""
        SELECT 
            t.id,
            t.name, 
            COUNT(tgp.game_id) as games_played,
            SUM(tgp.total_score) as total_points,
            ROUND(AVG(tgp.total_score), 1) as avg_points
        FROM quizplease.teams t
        JOIN quizplease.team_game_participations tgp ON t.id = tgp.team_id
        JOIN quizplease.games g ON tgp.game_id = g.id
        {where_clause}
        GROUP BY t.id, t.name
        ORDER BY total_points DESC
        {limit_clause};
    """
    return run_query(query, params=params)



@st.cache_data(ttl=3600)
def get_top_n_finishes(top_n=3, game_names=None, categories=None):
    """
    Returns how many times each team finished in the top N ranks.
    """
    filters = ["tgp.rank <= :top_n"]
    params = {"top_n": top_n}
    
    if game_names:
        filters.append("g.game_name IN :game_names")
        params["game_names"] = tuple(game_names)
    if categories:
        filters.append("g.category IN :categories")
        params["categories"] = tuple(categories)
        
    where_clause = "WHERE " + " AND ".join(filters)
    
    query = f"""
        SELECT 
            t.name,
            COUNT(*) as finish_count
        FROM quizplease.teams t
        JOIN quizplease.team_game_participations tgp ON t.id = tgp.team_id
        JOIN quizplease.games g ON tgp.game_id = g.id
        {where_clause}
        GROUP BY t.name
        ORDER BY finish_count DESC;
    """
    return run_query(query, params=params)


@st.cache_data(ttl=3600)
def get_avg_round_scores_by_team(game_names=None, categories=None):
    """
    Returns average score per round_name for each team.
    """
    filters = []
    params = {}
    
    if game_names:
        filters.append("g.game_name IN :game_names")
        params["game_names"] = tuple(game_names)
    if categories:
        filters.append("g.category IN :categories")
        params["categories"] = tuple(categories)
        
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    query = f"""
        SELECT 
            t.name,
            rs.round_name,
            AVG(rs.score) as avg_score
        FROM quizplease.teams t
        JOIN quizplease.team_game_participations tgp ON t.id = tgp.team_id
        JOIN quizplease.games g ON tgp.game_id = g.id
        JOIN quizplease.round_scores rs ON tgp.id = rs.participation_id
        {where_clause}
        GROUP BY t.name, rs.round_name;
    """
    return run_query(query, params=params)


@st.cache_data(ttl=3600)
def get_team_game_history(team_id, game_names=None, categories=None):
    """
    Returns game history for a specific team.
    """
    filters = ["tgp.team_id = :team_id"]
    params = {"team_id": team_id}
    
    if game_names:
        filters.append("g.game_name IN :game_names")
        params["game_names"] = tuple(game_names)
    if categories:
        filters.append("g.category IN :categories")
        params["categories"] = tuple(categories)
        
    where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT 
            g.id as game_id,
            g.game_date,
            g.game_name,
            tgp.rank,
            tgp.total_score
        FROM quizplease.team_game_participations tgp
        JOIN quizplease.games g ON tgp.game_id = g.id
        {where_clause}
        ORDER BY g.game_date DESC;
    """
    return run_query(query, params=params)

@st.cache_data(ttl=3600)
def get_game_round_comparisons(game_id):
    """
    Returns max score and winner score per round for a specific game.
    """
    # Max score per round
    query = """
        SELECT 
            rs.round_name,
            MAX(rs.score) as max_round_score,
            (
                SELECT score 
                FROM quizplease.round_scores rs2 
                JOIN quizplease.team_game_participations tgp2 ON rs2.participation_id = tgp2.id
                WHERE tgp2.game_id = :game_id AND tgp2.rank = 1 AND rs2.round_name = rs.round_name
                LIMIT 1
            ) as winner_score
        FROM quizplease.round_scores rs
        JOIN quizplease.team_game_participations tgp ON rs.participation_id = tgp.id
        WHERE tgp.game_id = :game_id
        GROUP BY rs.round_name;
    """
    return run_query(query, params={"game_id": game_id})

@st.cache_data(ttl=3600)
def get_full_game_results(game_id):
    """
    Returns full results for a game including individual round scores.
    """
    # This is slightly complex because rounds are dynamic rows. 
    # We will fetch flattened data and pivot in Pandas if needed, 
    # or just fetch basics and round details separately.
    # Let's fetch basic ranking first.
    query = """
        SELECT 
            t.name,
            tgp.rank,
            tgp.total_score,
            rs.round_name,
            rs.score
        FROM quizplease.team_game_participations tgp
        JOIN quizplease.teams t ON tgp.team_id = t.id
        LEFT JOIN quizplease.round_scores rs ON tgp.id = rs.participation_id
        WHERE tgp.game_id = :game_id
        ORDER BY tgp.rank ASC, rs.round_name;
    """
    return run_query(query, params={"game_id": game_id})
