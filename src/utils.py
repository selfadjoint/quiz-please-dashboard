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
    
    available_games, available_categories = get_filter_options()
    
    selected_games = st.sidebar.multiselect(
        "Game Name",
        options=available_games,
        default=[] # Default to all (empty list means no filter usually)
    )
    
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=available_categories,
        default=[]
    )
    
    return {
        "game_names": selected_games,
        "categories": selected_categories
    }
