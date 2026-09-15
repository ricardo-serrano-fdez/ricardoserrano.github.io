"""Tile Catalog Review UI component for Streamlit."""

import streamlit as st
from catalog_data import (
    load_catalog,
    load_analysis,
    get_crop_image,
    get_mask_image,
)


def render_catalog_ui():
    st.markdown('<p class="eyebrow">Z-Man Games · 2014 Edition</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">🗺️ Tile Catalog & AI Review</h1>', unsafe_allow_html=True)
    st.caption("Review extracted crops, ML segmentation masks, edge segments, and feature connectivity.")

    catalog = load_catalog()
    analysis_data = load_analysis()

    if not catalog:
        st.warning("Tile catalog file could not be loaded.")
        return

    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        terrain_filter = st.selectbox("Edge Terrain", ["All", "city", "road", "field"])
    with fcol2:
        shield_filter = st.selectbox("Shields / Pennants", ["All", "Has Shield", "No Shield"])
    with fcol3:
        monastery_filter = st.selectbox("Monastery", ["All", "Monastery Only", "No Monastery"])

    filtered_tiles = []
    for t in catalog:
        t_edges = list(t.get("edges", {}).values())
        if terrain_filter != "All" and terrain_filter not in t_edges:
            continue
        if shield_filter == "Has Shield" and t.get("shields", 0) == 0:
            continue
        if shield_filter == "No Shield" and t.get("shields", 0) > 0:
            continue
        if monastery_filter == "Monastery Only" and not t.get("monastery", False):
            continue
        if monastery_filter == "No Monastery" and t.get("monastery", False):
            continue
        filtered_tiles.append(t)

    st.write(f"Showing **{len(filtered_tiles)}** of **{len(catalog)}** tiles")
    tile_ids = [t["id"] for t in filtered_tiles]

    if not tile_ids:
        st.info("No tiles match the current filters.")
        return

    selected_tile_id = st.selectbox("Select Tile ID", tile_ids, index=0)
    analysis = analysis_data.get(selected_tile_id, {})

    t_col1, t_col2 = st.columns([1, 1], gap="large")

    with t_col1:
        st.subheader("Tile Visuals")
        crop_img = get_crop_image(selected_tile_id)
        mask_img = get_mask_image(selected_tile_id)

        vcol1, vcol2 = st.columns(2)
        with vcol1:
            if crop_img:
                st.image(crop_img, caption="Cropped Tile Image", use_container_width=True)
            else:
                st.warning("Crop image not found.")
        with vcol2:
            if mask_img:
                st.image(mask_img, caption="Segmentation Mask", use_container_width=True)
            else:
                st.warning("Mask image not found.")

    with t_col2:
        st.subheader(f"Analysis: {selected_tile_id}")
        
        if "features" in analysis:
            st.write("**Detected Special Features:**")
            feat_html = "".join([
                f'<span class="feature-pill {"active" if present else "inactive"}">{name}: {"Yes" if present else "No"}</span>'
                for name, present in analysis["features"].items()
            ])
            st.markdown(feat_html, unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)

        if "edges" in analysis:
            st.write("**12 Edge Segments (Clockwise from Top-Left):**")
            segments_html = []
            for edge in analysis["edges"]:
                seg_num = edge.get("segment", 1)
                terrain = edge.get("terrain", "field")
                conf = int(edge.get("confidence", 1.0) * 100)
                css_cls = f"segment-{terrain}"
                segments_html.append(
                    f'<span class="segment-badge {css_cls}"><b>S{seg_num}</b> {terrain} ({conf}%)</span>'
                )
            st.markdown("".join(segments_html), unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)

        if "connections" in analysis:
            st.write("**Terrain Connections:**")
            for conn in analysis["connections"]:
                segs = ", ".join(map(str, conn.get("edge_segments", []))) or "Interior only"
                st.markdown(f"- **{conn.get('terrain', '').capitalize()}**: Segments `{segs}`")
