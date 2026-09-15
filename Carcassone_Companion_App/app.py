"""Carcassonne Companion Streamlit App entrypoint."""

import streamlit as st
from scoring_engine import DEFAULT_PALETTE
from scoring_ui import render_scoring_ui
from photo_ui import render_photo_ui
from catalog_ui import render_catalog_ui

st.set_page_config(
    page_title="Carcassonne Companion",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling matching the original board game paper palette
st.markdown(
    """
    <style>
    .main-title {
        font-family: Georgia, serif;
        font-size: 2.3rem;
        font-weight: 700;
        color: #204a3b;
        margin-bottom: 0.1rem;
    }
    .eyebrow {
        color: #2e6652;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .score-card {
        background-color: #f6f2e8;
        border: 1px solid #d9d1be;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 10px;
    }
    .score-number {
        font-size: 2.1rem;
        font-weight: bold;
        color: #28281e;
    }
    .score-name {
        font-size: 0.95rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    .meeple-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        display: inline-block;
        border: 1px solid rgba(0,0,0,0.25);
    }
    .feature-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 3px;
    }
    .feature-pill.active {
        background-color: #2e6652;
        color: white;
    }
    .feature-pill.inactive {
        background-color: #e5e5e5;
        color: #777777;
    }
    .segment-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        margin: 2px;
        border: 1px solid #ccc;
    }
    .segment-city { background-color: #f7d6d3; border-color: #be463e; color: #7a1d17; }
    .segment-road { background-color: #d8e8dd; border-color: #2e6652; color: #163e30; }
    .segment-field { background-color: #eaf1d6; border-color: #79a84b; color: #3d5821; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "players" not in st.session_state:
    st.session_state.players = [
        {"id": f"player-{i}", "name": p["name"], "color": p["color"]}
        for i, p in enumerate(DEFAULT_PALETTE[:2])
    ]
if "features" not in st.session_state:
    st.session_state.features = []
if "tiles" not in st.session_state:
    st.session_state.tiles = []
if "calib_points" not in st.session_state:
    st.session_state.calib_points = None

# Sidebar Navigation
st.sidebar.markdown('<p class="eyebrow">Carcassonne Companion</p>', unsafe_allow_html=True)
st.sidebar.markdown("## Navigation")
app_mode = st.sidebar.radio(
    "Go to",
    ["Final Scoring", "Board Photo Analysis", "Tile Catalog Review"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Companion Guide:**\n\n"
    "• **Final Scoring**: Calculate end-game points for incomplete cities, roads, monasteries, and farms.\n\n"
    "• **Board Photo**: Perspective calibration & Sobel edge detection.\n\n"
    "• **Tile Catalog**: Browse 72 tiles with AI segmentation masks and connectivity graphs."
)

# Render chosen section
if app_mode == "Final Scoring":
    render_scoring_ui()
elif app_mode == "Board Photo Analysis":
    render_photo_ui()
elif app_mode == "Tile Catalog Review":
    render_catalog_ui()
