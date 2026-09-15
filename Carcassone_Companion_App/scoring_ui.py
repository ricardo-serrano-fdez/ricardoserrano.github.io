"""Scoring Calculator UI component for Streamlit."""

import streamlit as st
import uuid
from scoring_engine import DEFAULT_PALETTE, RULES, score_feature, calculate_totals


def render_scoring_ui():
    st.markdown('<p class="eyebrow">Base game · Assisted Final Scoring</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">🏰 Final Scoring Calculator</h1>', unsafe_allow_html=True)
    st.caption("Record each remaining construction and calculate verified final scores.")

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.subheader("1. Players & Colors")
        to_del = None
        for idx, p in enumerate(st.session_state.players):
            c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
            with c1:
                st.markdown(f'<div style="margin-top:10px;"><span class="meeple-dot" style="background-color:{p["color"]};"></span></div>', unsafe_allow_html=True)
            with c2:
                p["name"] = st.text_input(f"P{idx+1}", value=p["name"], key=f"pn_{p['id']}", label_visibility="collapsed")
            with c3:
                if len(st.session_state.players) > 1 and st.button("✕", key=f"d_{p['id']}"):
                    to_del = p["id"]

        if to_del:
            st.session_state.players = [p for p in st.session_state.players if p["id"] != to_del]
            st.rerun()

        if len(st.session_state.players) < len(DEFAULT_PALETTE):
            if st.button("➕ Add Player", use_container_width=True):
                pal = DEFAULT_PALETTE[len(st.session_state.players) % len(DEFAULT_PALETTE)]
                st.session_state.players.append({"id": f"p-{uuid.uuid4().hex[:6]}", "name": pal["name"], "color": pal["color"]})
                st.rerun()

        st.markdown("---")
        st.subheader("2. Remaining Construction")
        with st.form("feature_form", clear_on_submit=True):
            f_type = st.selectbox("Construction", ["city", "road", "monastery", "farm"], format_func=lambda x: RULES[x]["label"])
            rule = RULES[f_type]
            st.caption(f"ℹ️ {rule['help']}")

            fc1, fc2 = st.columns(2)
            with fc1:
                amount = st.number_input(rule["amount_label"], min_value=0, max_value=rule["max_amount"] or 100, value=1)
            with fc2:
                bonus = st.number_input(rule["bonus_label"], min_value=0, max_value=50, value=0) if rule["has_bonus"] else 0

            st.write("**Player(s) with meeple:**")
            owners = []
            cols = st.columns(len(st.session_state.players))
            for i, p in enumerate(st.session_state.players):
                with cols[i]:
                    if st.checkbox(p["name"], key=f"own_{p['id']}", value=(i == 0)):
                        owners.append(p["id"])

            if st.form_submit_button("Add Construction", type="primary", use_container_width=True):
                if not owners:
                    st.error("Select at least one player.")
                else:
                    pts = score_feature(f_type, int(amount), int(bonus))
                    st.session_state.features.append({
                        "id": uuid.uuid4().hex[:8], "type": f_type, "amount": int(amount),
                        "bonus": int(bonus), "owners": owners, "points": pts
                    })
                    st.rerun()

    with col2:
        st.subheader("3. Final Score")
        totals = calculate_totals(st.session_state.players, st.session_state.features)
        max_pts = max(totals.values()) if totals else 0
        
        scols = st.columns(len(st.session_state.players))
        for i, p in enumerate(st.session_state.players):
            pts = totals.get(p["id"], 0)
            lead = pts == max_pts and pts > 0
            with scols[i]:
                badge = "<div style='color:#2e6652; font-weight:bold; font-size:0.8rem;'>🏆 LEADING</div>" if lead else ""
                st.markdown(
                    f'<div class="score-card" style="border-top: 4px solid {p["color"]};">'
                    f'<div class="score-name"><span class="meeple-dot" style="background-color:{p["color"]};"></span>{p["name"]}</div>'
                    f'<div class="score-number">{pts}</div>{badge}</div>',
                    unsafe_allow_html=True
                )

        st.markdown("---")
        hc1, hc2 = st.columns([0.7, 0.3])
        with hc1:
            st.write(f"**Constructions ({len(st.session_state.features)})**")
        with hc2:
            if st.session_state.features and st.button("Reset Game", type="secondary"):
                st.session_state.features = []
                st.rerun()

        if not st.session_state.features:
            st.info("Add a remaining construction on the left to begin scoring.")
        else:
            p_map = {p["id"]: p for p in st.session_state.players}
            rm_id = None
            for f in reversed(st.session_state.features):
                r_info = RULES[f["type"]]
                otags = " · ".join([f'<span style="color:{p_map[o]["color"]}; font-weight:bold;">● {p_map[o]["name"]}</span>' for o in f["owners"] if o in p_map])
                detail = f"{f['amount']} {r_info['amount_label'].lower()}" + (f", {f['bonus']} pennants" if f['type'] == 'city' and f.get('bonus', 0) > 0 else "")
                
                c_a, c_b, c_c = st.columns([0.65, 0.25, 0.1])
                with c_a:
                    st.markdown(f"**{r_info['label']}** ({detail})<br/><small>{otags}</small>", unsafe_allow_html=True)
                with c_b:
                    st.markdown(f"**+{f['points']} pts**")
                with c_c:
                    if st.button("✕", key=f"rf_{f['id']}"):
                        rm_id = f["id"]
                st.markdown("<hr style='margin:3px 0;'/>", unsafe_allow_html=True)
                
            if rm_id:
                st.session_state.features = [f for f in st.session_state.features if f["id"] != rm_id]
                st.rerun()
