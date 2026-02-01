import streamlit as st

def set_page_config(page_title="Quiz Please Dashboard", page_icon="assets/logo.svg", layout="wide"):
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded"
    )

def inject_custom_css():
    st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stMetric {
            background-color: var(--secondary-background-color);
            padding: 1rem;
            border-radius: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
from src.db import get_filter_options

def render_sidebar_filters():
    """
    Renders sidebar filters for Game Name and Category.
    Returns a dictionary with selected filters.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Filters")
    
    # Persistent storage keys that don't get cleared by Streamlit's widget cleanup
    if "persistent_game_names" not in st.session_state:
        st.session_state["persistent_game_names"] = []
    if "persistent_categories" not in st.session_state:
        st.session_state["persistent_categories"] = []
    if "persistent_venues" not in st.session_state:
        st.session_state["persistent_venues"] = []

    available_games, available_categories, available_venues = get_filter_options()
    
    selected_games = st.sidebar.multiselect(
        "Game Name",
        options=available_games,
        default=st.session_state["persistent_game_names"],
        key="widget_game_names"
    )
    st.session_state["persistent_game_names"] = selected_games
    
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=available_categories,
        default=st.session_state["persistent_categories"],
        key="widget_categories"
    )
    st.session_state["persistent_categories"] = selected_categories

    selected_venues = st.sidebar.multiselect(
        "Venue",
        options=available_venues,
        default=st.session_state["persistent_venues"],
        key="widget_venues"
    )
    st.session_state["persistent_venues"] = selected_venues
    
    return {
        "game_names": selected_games,
        "categories": selected_categories,
        "venues": selected_venues
    }
