import streamlit as st
import plotly.express as px
import pandas as pd
from src.db import get_overall_top_teams, get_top_n_finishes, get_avg_round_scores_by_team
from src.utils import render_sidebar_filters, set_page_config

set_page_config(page_title="General Stats", page_icon="assets/logo.svg")

st.title("📊 General Statistics")


# Filters
filters = render_sidebar_filters()

# --- Overview Metrics ---
top_teams_df = get_overall_top_teams(limit=None, game_names=filters['game_names'], categories=filters['categories'], venues=filters['venues']) # Get all for calculations

if not top_teams_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Participated Teams", len(top_teams_df))
    with col2:
        st.metric("Avg Points per Game", round(top_teams_df['avg_points'].mean(), 1))
    with col3:
        pass
else:
    st.warning("No data available.")

st.markdown("---")

# --- Section 1: Overall Leaders ---
st.subheader("🏆 Overall Team Standings")
st.caption("Top teams by total points accumulated across all games.")

limit = st.slider("Number of teams to show", 5, 100, 20)
display_df = top_teams_df.head(limit).copy().reset_index(drop=True)
# Clean up dataframe for display
if 'id' in display_df.columns:
    display_df = display_df.drop(columns=['id'])

# Create Rank column (1-based index)
display_df.index = range(1, len(display_df) + 1)
display_df.index.name = 'Rank'

# Rename columns
display_df = display_df.rename(columns={
    'name': 'Team',
    'games_played': 'Games Played', 
    'total_points': 'Total Points',
    'avg_points': 'Avg Points'
})

st.dataframe(
    display_df.style.format({"Avg Points": "{:.1f}", "Total Points": "{:.0f}"}),
    use_container_width=True
)

# --- Section 2: Top N Finishes Treemap ---
st.markdown("---")
st.subheader("🥇 Top Finishes Analysis")
st.caption("Which teams finish in the top positions most often?")

col_tree_1, col_tree_2 = st.columns([1, 3])
with col_tree_1:
    top_n_filter = st.selectbox("Select Top N Rank", [1, 3, 5, 10], index=1)

finishes_df = get_top_n_finishes(top_n=top_n_filter, game_names=filters['game_names'], categories=filters['categories'], venues=filters['venues'])

if not finishes_df.empty:
    fig_tree = px.treemap(
        finishes_df, 
        path=['name'], 
        values='finish_count',
        title=f"Teams with Most Top-{top_n_filter} Finishes",
        color='finish_count',
        color_continuous_scale='Viridis'
    )
    # Update traces to show label and value on the square
    fig_tree.update_traces(
        textinfo="label+value",
        hovertemplate='<b>%{label}</b><br>Finishes: %{value}<extra></extra>'
    )
    st.plotly_chart(fig_tree, use_container_width=True)
else:
    st.info("No data for this selection.")

# --- Section 3: Average Points by Round ---
st.markdown("---")
st.subheader("🎯 Average Performance by Round")
st.caption("How teams perform on average in specific rounds.")

# Fetch data and filter for top teams to keep chart readable
avg_scores_df = get_avg_round_scores_by_team(game_names=filters['game_names'], categories=filters['categories'], venues=filters['venues'])

if not avg_scores_df.empty:
    # Filter for teams in our top_teams_df list (top limit by default) to reduce noise
    top_team_names = top_teams_df.head(limit)['name'].tolist()
    filtered_avg_scores = avg_scores_df[avg_scores_df['name'].isin(top_team_names)]
    
    # Pivot logic: Rows=Team, Cols=Round, Values=Score
    # Sort rounds naturally if possible (Round 1, Round 2...)
    # Using 'round_name' which is a string may need sorting.
    
    pivot_df = filtered_avg_scores.pivot(index='name', columns='round_name', values='avg_score')
    
    # Capitalize round names
    pivot_df.columns = [str(c).title() for c in pivot_df.columns]
    
    # Try to sort columns naturally
    try:
        sorted_cols = sorted(pivot_df.columns, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 999)
        pivot_df = pivot_df[sorted_cols]
    except:
        pass # Keep default sort if fails
    
    # Add Total Avg column
    # Calculate row sum of averages (Average Total Score)
    pivot_df['Total Avg'] = pivot_df.sum(axis=1)
    
    # Sort by Total Avg descending
    pivot_df = pivot_df.sort_values('Total Avg', ascending=False)
    
    # Add Rank as index and reset Team to column
    pivot_df = pivot_df.reset_index()
    pivot_df = pivot_df.rename(columns={'name': 'Team'})
    pivot_df.index = range(1, len(pivot_df) + 1)
    pivot_df.index.name = 'Rank'
    
    # Display styling
    st.dataframe(
        pivot_df.style.format("{:.1f}", subset=pivot_df.columns.drop('Team')),
        use_container_width=True
    )

