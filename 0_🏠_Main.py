import streamlit as st
from src.utils import set_page_config, inject_custom_css, render_sidebar_filters
from src.db import get_connection, run_query, get_games_list, get_full_game_results
import pandas as pd


# Page Setup
set_page_config(page_title="Quiz Please Dashboard", page_icon="assets/logo.svg")

inject_custom_css()

# Filters
filters = render_sidebar_filters()

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("assets/logo.svg", width=80) 
with col_title:
    st.title("Quiz Please Statistics Dashboard")


# Check Database Connection
engine = get_connection()
if engine:
    st.success("Database connected successfully!", icon="✅")
    
    # Quick Stats
    # Note: Quick stats might ignore filters or not. User didn't specify. 
    # Usually "Total Teams" is global. "Latest Game" is global. 
    # Let's keep them global for now as they are "Overall Stats".
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_teams_query = """
            SELECT AVG(team_count) as avg_teams 
            FROM (
                SELECT COUNT(*) as team_count 
                FROM quizplease.team_game_participations 
                GROUP BY game_id
            ) as counts
        """
        avg_teams = run_query(avg_teams_query).iloc[0]['avg_teams']
        st.metric("Avg Teams / Game", round(float(avg_teams), 1))
        
    with col2:
        game_count = run_query("SELECT COUNT(*) as count FROM quizplease.games").iloc[0]['count']
        st.metric("Total Games", game_count)
        
    with col3:
        latest_game = run_query("SELECT MAX(game_date) as max_date FROM quizplease.games").iloc[0]['max_date']
        st.metric("Latest Game", str(latest_game))

    st.markdown("---")
    st.markdown("---")
    
    # --- Filter: Select Game ---
    # Apply filters to the game list
    games_df = get_games_list(game_names=filters['game_names'], categories=filters['categories'])

    if not games_df.empty:
        # Create a readable label for the dropdown
        games_df['label'] = games_df['game_date'].astype(str) + " - " + games_df['game_name'] + " (" + games_df['game_number'] + ")"
        game_options = dict(zip(games_df['label'], games_df['id']))

        st.subheader("📅 Game Results")
        selected_game_label = st.selectbox("Select Game", options=games_df['label'], index=0)
        selected_game_id = game_options[selected_game_label]

        game_info = games_df[games_df['id'] == selected_game_id].iloc[0]

        # Display Game Info
        st.caption(f"Category: {game_info['category']} | Date: {game_info['game_date']}")

        st.markdown("---")

        # --- Fetch Results ---
        results_df = get_full_game_results(selected_game_id)

        if not results_df.empty:
            # Pivot rounds: Team | Rank | Total | R1 | R2 | ...
            pivot_df = results_df.pivot_table(
                index=['rank', 'name', 'total_score'], 
                columns='round_name', 
                values='score'
            ).reset_index()
            
            # Sort by Rank
            pivot_df.sort_values('rank', inplace=True)
            
            # Rename columns for consistency
            pivot_df = pivot_df.rename(columns={
                'rank': 'Rank',
                'name': 'Team',
                'total_score': 'Total Points'
            })
            # Capitalize round names
            pivot_df.columns = [str(c).title() if c not in ['Rank', 'Team', 'Total Points'] else c for c in pivot_df.columns]
            
            # --- Highlights ---
            winner_name = pivot_df.iloc[0]['Team']
            max_total_score = pivot_df['Total Points'].max()

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🏆 Winner")
                st.markdown(f"#### **{winner_name}**") # Markdown to avoid truncation
            with col2:
                st.metric("🌟 Highest Points", max_total_score)

            # --- Leaderboard Table ---
            st.subheader("Leaderboard")
            
            def highlight_top(s):
                if s.name == 'Rank':
                     return ['background-color: #ffd700' if v == 1 else 
                             'background-color: #c0c0c0' if v == 2 else 
                             'background-color: #cd7f32' if v == 3 else '' for v in s]
                return ['' for _ in s]

            st.dataframe(
                pivot_df.style.apply(highlight_top, subset=['Rank']).format(precision=1),
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("No results found for this game.")
    else:
        st.info("No games found.")
    
else:
    st.error("Failed to connect to the database. Please check your secrets.toml.")

st.sidebar.info("Data updated daily.")
