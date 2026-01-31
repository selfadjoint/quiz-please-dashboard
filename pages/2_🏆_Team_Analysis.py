import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.db import get_all_teams, get_team_game_history, get_game_round_comparisons, get_full_game_results
from src.utils import render_sidebar_filters, set_page_config

set_page_config(page_title="Team Analysis", page_icon="assets/logo.svg")

st.title("🏆 Team Analysis")


# Filters
filters = render_sidebar_filters()

# --- Filter: Select Team ---
teams_df = get_all_teams()
if teams_df.empty:
    st.error("No teams found in database.")
    st.stop()

team_names = teams_df['name'].tolist()
# Set default index for "КОРПОРАЦИЯ МОНСТРОВ"
try:
    default_index = team_names.index("КОРПОРАЦИЯ МОНСТРОВ")
except ValueError:
    default_index = 0

selected_team_name = st.selectbox("Select Team", team_names, index=default_index)
selected_team_id = int(teams_df[teams_df['name'] == selected_team_name]['id'].iloc[0])


# --- Section 1: Dynamics of Game Points ---
st.subheader("📈 Performance Dynamics")
dynamics_df = get_team_game_history(selected_team_id, game_names=filters['game_names'], categories=filters['categories'])


if not dynamics_df.empty:
    # Calculate median
    median_score = dynamics_df['total_score'].median()
    
    fig_line = px.line(
        dynamics_df.sort_values('game_date'), 
        x='game_date', 
        y='total_score',
        title=f"Total Points History for {selected_team_name}",
        markers=True,
        hover_data=['game_name', 'rank'],
        labels={'game_date': 'Game Date', 'total_score': 'Total Points'}
    )
    
    # Add median line
    fig_line.add_hline(
        y=median_score, 
        line_dash="dash", 
        annotation_text=f"Median: {median_score}", 
        annotation_position="bottom right"
    )
    
    st.plotly_chart(fig_line, use_container_width=True)
    
    # --- Section 2: Game Comparison ---
    st.markdown("---")
    st.subheader("🆚 Game Round Comparison")
    st.caption("Compare team performance vs Max and Winner scores in a specific game.")

    # Create mapping for selectbox: "Date - Game Name" -> game_id
    # dynamics_df now has 'game_id'
    try:
        game_options = {
            f"{row['game_date']} - {row['game_name']}": int(row['game_id'])
            for index, row in dynamics_df.iterrows()
        }
    except Exception as e:
        st.error(f"Error processing game history: {e}")
        st.stop()
    
    selected_game_label = st.selectbox("Select Game for Comparison", list(game_options.keys()))
    selected_game_id = game_options[selected_game_label]
    
    if selected_game_id:
        # Get full results for the game
        full_game_results = get_full_game_results(selected_game_id)
        
        if not full_game_results.empty:
            # 1. Selected Team Data
            team_results = full_game_results[full_game_results['name'] == selected_team_name].set_index('round_name')
            
            # 2. Winner Data (Rank 1)
            # Handle potential ties for 1st place
            winners = full_game_results[full_game_results['rank'] == 1]
            # Just take the first winner found per round usually, but winner scores are per round.
            # Wait, "Winner Score" usually means the score of the Game Winner in that round.
            # Yes, the team that ranked #1 overall.
            if not winners.empty:
                 winner_name = winners.iloc[0]['name'] # Take first if tie
            else:
                 winner_name = "Unknown"
                 
            winner_results = winners.set_index('round_name')
            # If multiple winners, we might have duplicates in round name index. duplicates drop?
            winner_results = winner_results[~winner_results.index.duplicated(keep='first')]

            # 3. Max Score per Round Data
            # Group by round and find max score
            round_max_scores = full_game_results.groupby('round_name')['score'].max()
            
            # Prepare data for plotting
            rounds = full_game_results['round_name'].unique()
            # Sort rounds if needed (Round 1, Round 2...)
            try:
                rounds = sorted(rounds, key=lambda x: int(''.join(filter(str.isdigit, x))) if any(c.isdigit() for c in x) else 999)
            except:
                pass
            
            plot_data = []
            
            for r in rounds:
                # Team Stats
                team_score = team_results.loc[r, 'score'] if r in team_results.index else 0
                
                # Winner Stats
                winner_score = winner_results.loc[r, 'score'] if r in winner_results.index else 0
                
                # Max Stats
                max_score = round_max_scores.get(r, 0)
                # Find who got max score
                max_scorers = full_game_results[(full_game_results['round_name'] == r) & (full_game_results['score'] == max_score)]['name'].unique()
                max_scorer_text = ", ".join(max_scorers)
                
                plot_data.append({
                    "Round": r,
                    "Team Points": team_score,
                    "Winner Points": winner_score,
                    "Winner Name": winner_name,
                    "Max Points": max_score,
                    "Max Scorer": max_scorer_text
                })
            
            plot_df = pd.DataFrame(plot_data)
            
            # Plot using Graph Objects for custom tooltips
            fig_bar = go.Figure()
            
            fig_bar.add_trace(go.Bar(
                name=f"{selected_team_name}", 
                x=plot_df['Round'], 
                y=plot_df['Team Points'], 
                marker_color='blue'
            ))
            
            fig_bar.add_trace(go.Bar(
                name=f"Winner ({winner_name})", 
                x=plot_df['Round'], 
                y=plot_df['Winner Points'], 
                marker_color='green',
                hovertemplate='<b>Winner Points</b><br>Score: %{y}<br>Team: %{customdata}<extra></extra>',
                customdata=[winner_name] * len(plot_df)
            ))
            
            fig_bar.add_trace(go.Bar(
                name='Max Score', 
                x=plot_df['Round'], 
                y=plot_df['Max Points'], 
                marker_color='red',
                hovertemplate='<b>Max Points</b><br>Score: %{y}<br>Teams: %{customdata}<extra></extra>',
                customdata=plot_df['Max Scorer']
            ))
            
            fig_bar.update_layout(
                title=f"Points Comparison by Round (vs {winner_name})", 
                barmode='group',
                yaxis_title="Points",
                xaxis_title="Round"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        else:
             st.warning("Detailed round results not available for this game.")

    # --- Section 3: History Table ---
    st.markdown("---")
    st.subheader("📜 Game History")
    
    display_history = dynamics_df[['game_date', 'game_name', 'rank', 'total_score']].copy()
    display_history.columns = ['Game Date', 'Game Name', 'Rank', 'Total Points']
    
    st.dataframe(
        display_history, 
        use_container_width=True,
        hide_index=True
    )

    # --- Section 4: Team vs Team Comparison ---
    st.markdown("---")
    st.subheader("🥊 Team Comparison")
    st.caption("Compare key metrics against another team.")
    
    # Second team selector (exclude currently selected team)
    other_team_names = [t for t in team_names if t != selected_team_name]
    if other_team_names:
        # Set default to 'СОЦИАЛЬНЫЙ КОНСТРУКТ' if available
        try:
            compare_default_index = other_team_names.index("СОЦИАЛЬНЫЙ КОНСТРУКТ")
        except ValueError:
            compare_default_index = 0
        compare_team_name = st.selectbox("Compare with Team", other_team_names, index=compare_default_index, key="compare_team")
        compare_team_id = int(teams_df[teams_df['name'] == compare_team_name]['id'].iloc[0])
        
        # Get comparison team's game history
        compare_dynamics_df = get_team_game_history(compare_team_id, game_names=filters['game_names'], categories=filters['categories'])
        
        if not compare_dynamics_df.empty:
            # Calculate metrics for both teams
            def calculate_team_metrics(df, team_name):
                games_played = len(df)
                total_points = df['total_score'].sum()
                avg_points = df['total_score'].mean()
                avg_rank = df['rank'].mean()
                top3_count = len(df[df['rank'] <= 3])
                top3_rate = (top3_count / games_played * 100) if games_played > 0 else 0
                best_rank = df['rank'].min()
                worst_rank = df['rank'].max()
                return {
                    'Team': team_name,
                    'Games Played': games_played,
                    'Total Points': total_points,
                    'Avg Points': round(avg_points, 1),
                    'Avg Rank': round(avg_rank, 1),
                    'Top 3 Rate (%)': round(top3_rate, 1),
                    'Best Rank': best_rank,
                    'Worst Rank': worst_rank
                }
            
            team1_metrics = calculate_team_metrics(dynamics_df, selected_team_name)
            team2_metrics = calculate_team_metrics(compare_dynamics_df, compare_team_name)
            
            # Display metrics table
            metrics_df = pd.DataFrame([team1_metrics, team2_metrics])
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Radar Chart (normalized metrics)
            # Normalize: Avg Points (higher better), Avg Rank (lower better - invert), Top 3 Rate (higher better)
            # For radar, we want all metrics where "bigger is better"
            
            # We'll use: Avg Points, Inverted Avg Rank (max_rank - avg_rank), Top 3 Rate
            max_avg_rank = max(team1_metrics['Avg Rank'], team2_metrics['Avg Rank'], 10)  # Cap at 10 for scale
            
            radar_categories = ['Avg Points', 'Consistency (Inv. Rank)', 'Top 3 Rate (%)']
            
            team1_radar = [
                team1_metrics['Avg Points'],
                max_avg_rank - team1_metrics['Avg Rank'],  # Invert rank
                team1_metrics['Top 3 Rate (%)']
            ]
            
            team2_radar = [
                team2_metrics['Avg Points'],
                max_avg_rank - team2_metrics['Avg Rank'],  # Invert rank
                team2_metrics['Top 3 Rate (%)']
            ]
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=team1_radar,
                theta=radar_categories,
                fill='toself',
                name=selected_team_name
            ))
            
            fig_radar.add_trace(go.Scatterpolar(
                r=team2_radar,
                theta=radar_categories,
                fill='toself',
                name=compare_team_name
            ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                showlegend=True,
                title="Performance Profile Comparison"
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
            
            with st.expander("📖 About the Metrics"):
                st.markdown("""
                - **Avg Points**: Average total points scored per game. Higher is better.
                - **Consistency (Inv. Rank)**: Inverted average rank. A higher value means the team finishes in better positions on average.
                - **Top 3 Rate (%)**: Percentage of games where the team finished in the top 3 positions.
                """)
            
            # Head-to-Head: Games where both teams participated
            st.markdown("#### Head-to-Head Results")
            st.caption("Games where both teams competed.")
            
            # Find common game_ids
            team1_game_ids = set(dynamics_df['game_id'].tolist())
            team2_game_ids = set(compare_dynamics_df['game_id'].tolist())
            common_game_ids = team1_game_ids.intersection(team2_game_ids)
            
            if common_game_ids:
                # Build head-to-head table
                h2h_data = []
                team1_wins = 0
                team2_wins = 0
                
                for gid in common_game_ids:
                    t1_row = dynamics_df[dynamics_df['game_id'] == gid].iloc[0]
                    t2_row = compare_dynamics_df[compare_dynamics_df['game_id'] == gid].iloc[0]
                    
                    t1_rank = t1_row['rank']
                    t2_rank = t2_row['rank']
                    
                    if t1_rank < t2_rank:
                        winner = selected_team_name
                        team1_wins += 1
                    else:
                        winner = compare_team_name
                        team2_wins += 1
                    
                    h2h_data.append({
                        'Game Date': t1_row['game_date'],
                        'Game Name': t1_row['game_name'],
                        f'{selected_team_name} Rank': t1_rank,
                        f'{compare_team_name} Rank': t2_rank,
                        'Winner': winner
                    })
                
                h2h_df = pd.DataFrame(h2h_data).sort_values('Game Date', ascending=False)
                
                # Summary
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"{selected_team_name} Wins", team1_wins)
                with col2:
                    st.metric(f"{compare_team_name} Wins", team2_wins)
                
                st.dataframe(h2h_df, use_container_width=True, hide_index=True)
            else:
                st.info("These teams have not competed in the same games.")
        else:
            st.warning(f"No game history found for {compare_team_name} with current filters.")
    else:
        st.info("No other teams available for comparison.")

else:
    st.info("No game history for this team.")
