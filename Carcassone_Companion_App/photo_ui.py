"""Board Photo Computer Vision UI component for Streamlit."""

import streamlit as st
from cv_analysis import (
    load_image_from_bytes,
    compute_sobel_edges,
    detect_reference_tile,
    draw_photo_overlay,
)


def render_photo_ui():
    st.markdown('<p class="eyebrow">Computer Vision · Perspective & Edges</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">📷 Board Photo Analysis</h1>', unsafe_allow_html=True)
    st.caption("Upload a photo of your Carcassonne board to detect edge features, tile boundaries, and perspective.")

    uploaded_file = st.file_uploader(
        "Choose an overhead board photo (JPEG, PNG, or HEIC)",
        type=["jpg", "jpeg", "png", "heic", "heif"],
    )

    if uploaded_file is not None:
        try:
            image_bytes = uploaded_file.read()
            raw_image = load_image_from_bytes(image_bytes)
            edge_map, resized_img, scale = compute_sobel_edges(raw_image)

            pcol1, pcol2 = st.columns([0.68, 0.32], gap="medium")
            with pcol2:
                st.subheader("Controls")
                show_edges = st.checkbox("Show Sobel Edge Overlay", value=True)
                
                auto_detect = st.button("✨ Auto-Detect Reference Tile", type="primary", use_container_width=True)
                if auto_detect:
                    with st.spinner("Scanning square edges across angles..."):
                        candidate = detect_reference_tile(edge_map)
                        if candidate:
                            st.session_state.calib_points = candidate["points"]
                            st.success(f"Candidate tile detected! (Edge score: {int(candidate['confidence']*100)}%)")
                        else:
                            st.warning("No confident tile found.")

                if st.session_state.calib_points and st.button("Reset Calibration", use_container_width=True):
                    st.session_state.calib_points = None
                    st.rerun()

                st.markdown("---")
                st.write("**Photo Dimensions:**")
                st.caption(f"Original: {raw_image.width} × {raw_image.height} px")
                st.caption(f"Analysis: {resized_img.width} × {resized_img.height} px")

            with pcol1:
                overlay_img = draw_photo_overlay(
                    resized_img,
                    edge_map=edge_map,
                    show_edges=show_edges,
                    calibration_points=st.session_state.calib_points,
                )
                st.image(overlay_img, caption="Board Photo with Edge & Perspective Overlay", use_container_width=True)

        except Exception as e:
            st.error(f"Error processing image: {e}")
    else:
        st.info("👆 Upload an overhead photo of the game board to inspect edge features and perspective detection.")
