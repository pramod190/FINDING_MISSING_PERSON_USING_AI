"""
Face Matching — Upload an image and scan against the DB.
Fixed: use_column_width → use_container_width
Fixed: better face detection with fallback tips
"""

import json
import uuid
import streamlit as st

from pages.helper import db_queries
from pages.helper.utils import (
    image_obj_to_numpy,
    extract_face_mesh_landmarks,
    find_best_match,
    confidence_label,
    save_uploaded_image,
    get_detection_tips,
)
from pages.helper.streamlit_helpers import require_login, show_role_badge

st.set_page_config(page_title="Face Matching", page_icon="🤖", layout="wide")
show_role_badge()

st.markdown("""
<style>
@keyframes popIn {
    0%   { opacity:0; transform:scale(0.85); }
    70%  { transform:scale(1.05); }
    100% { opacity:1; transform:scale(1.0); }
}
.match-alert {
    background: linear-gradient(135deg,#064e3b,#065f46);
    border: 3px solid #10b981; border-radius:20px;
    padding:28px 32px; margin:20px 0;
    animation: popIn 0.5s cubic-bezier(.34,1.56,.64,1);
    box-shadow:0 12px 48px rgba(16,185,129,.5);
    text-align:center;
}
.match-alert h1 { color:#a7f3d0; font-size:28px; margin:0 0 8px; }
.match-alert p  { color:#d1fae5; font-size:16px; margin:6px 0; }
.conf-bar-wrap  { background:rgba(255,255,255,.1); border-radius:8px; height:12px; margin:12px 0; }
.conf-bar       { background:linear-gradient(90deg,#10b981,#34d399); border-radius:8px; height:12px; }
.no-match-box {
    background:rgba(239,68,68,.1); border:2px solid rgba(239,68,68,.4);
    border-radius:16px; padding:20px 24px; margin:16px 0; text-align:center;
}
.tips-box {
    background:rgba(99,102,241,.08); border:1px solid rgba(99,102,241,.25);
    border-radius:12px; padding:16px 20px; margin:12px 0;
}
</style>
""", unsafe_allow_html=True)


@require_login
def main():
    st.title("🤖 AI Face Matching")
    st.caption("Upload a photo — AI scans against all registered missing persons instantly.")
    st.divider()

    user_role = st.session_state.get("user_role", "User")
    username  = st.session_state.get("user", "unknown")

    col_upload, col_settings = st.columns([2, 1])

    with col_settings:
        st.subheader("⚙️ Settings")
        if user_role == "Admin":
            threshold = st.slider(
                "Match confidence threshold",
                min_value=0.40, max_value=0.95,
                value=0.60, step=0.05,
                help="Lower = more sensitive. Higher = stricter.",
            )
            mark_found = st.checkbox("Auto-mark as FOUND on match", value=True)
        else:
            threshold  = 0.60
            mark_found = False
            st.info("Match threshold: 60%")

        show_scores = st.checkbox("Show all candidate scores", value=False)

    with col_upload:
        st.subheader("📸 Upload Image")
        image_obj      = st.file_uploader(
            "JPG, JPEG or PNG — frontal face photo works best",
            type=["jpg","jpeg","png"],
            key="match_image",
        )
        location_input = st.text_input("📍 Location where person was sighted (optional)")

    if not image_obj:
        # Show tips when no image uploaded yet
        st.markdown("""
        <div class="tips-box">
        <strong>📋 How to get the best results:</strong><br><br>
        📸 Upload a clear, frontal face photo<br>
        💡 Good lighting — avoid dark or shadowy images<br>
        🔍 Face should be clearly visible and centred<br>
        🚫 Remove sunglasses, masks or obstructions<br>
        🖼️ Minimum recommended: 200×200 pixels
        </div>
        """, unsafe_allow_html=True)
        return

    img_col, result_col = st.columns([1, 1])

    with img_col:
        st.image(image_obj, caption="Query image", use_column_width=True)

    with result_col:
        # ── Step 1: Extract face mesh ──────────────────────────────────────────
        with st.spinner("🔍 Detecting face and extracting landmarks…"):
            img_np     = image_obj_to_numpy(image_obj)
            query_mesh = extract_face_mesh_landmarks(img_np)

        if not query_mesh:
            st.error("❌ No face detected in this image.")
            st.markdown(f"""
            <div class="tips-box">
            {get_detection_tips()}
            </div>
            """, unsafe_allow_html=True)
            st.info(
                "💡 **Still not working?** Try:\n"
                "- A different photo of the same person\n"
                "- Crop the image to show just the face\n"
                "- Use a brighter, higher-resolution image"
            )
            return

        landmarks_count = len(query_mesh) // 3
        st.success(f"✅ Face detected — {landmarks_count} landmarks extracted.")

        # ── Step 2: Load candidates ────────────────────────────────────────────
        with st.spinner("📂 Loading registered cases…"):
            candidates = db_queries.get_all_face_meshes_from_db()

        if not candidates:
            st.warning("⚠️ No registered missing persons in the database yet.")
            st.info("Ask an Admin to register missing person cases first.")
            return

        st.info(f"🔎 Scanning {len(candidates)} registered case(s)…")

        # ── Step 3: Match ──────────────────────────────────────────────────────
        with st.spinner("🧠 Comparing face landmarks…"):
            best_match, best_score = find_best_match(
                query_mesh, candidates, threshold
            )

        # ── MATCH FOUND ────────────────────────────────────────────────────────
        if best_match:
            pct = int(best_score * 100)
            st.markdown(f"""
            <div class="match-alert">
                <h1>🎉 MATCH FOUND!</h1>
                <p><strong>Name:</strong> {best_match['name']}</p>
                <p><strong>Case ID:</strong> {best_match['id']}</p>
                <p><strong>Confidence:</strong> {pct}% — {confidence_label(best_score)}</p>
                <div class="conf-bar-wrap">
                    <div class="conf-bar" style="width:{pct}%"></div>
                </div>
                <p>📍 Sighted at: {location_input or 'Location not provided'}</p>
            </div>
            """, unsafe_allow_html=True)

            st.success(
                f"🚨 **{best_match['name']}** matched with **{pct}% confidence**!",
                icon="✅",
            )
            st.balloons()

            # Update DB
            if mark_found and user_role == "Admin":
                try:
                    updated = db_queries.mark_person_found(
                        person_id=best_match["id"],
                        found_by=username,
                        found_location=location_input or "Unknown",
                        match_confidence=best_score,
                    )
                    if updated:
                        st.success("✅ Case marked as **FOUND** in database.")
                except Exception as e:
                    st.warning(f"Could not update DB: {e}")

            # Case details expander
            with st.expander("📋 Full case details"):
                person = db_queries.get_missing_person_by_id(best_match["id"])
                if person:
                    d1, d2 = st.columns(2)
                    d1.write(f"**Name:** {person.name}")
                    d1.write(f"**Age:** {person.age or 'N/A'}")
                    d1.write(f"**Gender:** {person.gender or 'N/A'}")
                    d2.write(f"**Last seen:** {person.location or 'N/A'}")
                    d2.write(f"**Birth marks:** {person.birth_marks or 'N/A'}")
                    if person.image_path:
                        try:
                            st.image(
                                person.image_path,
                                caption="Registered photo",
                                use_column_width=False,
                                width=200,
                            )
                        except Exception:
                            pass

        # ── NO MATCH ───────────────────────────────────────────────────────────
        else:
            st.markdown(f"""
            <div class="no-match-box">
                <h3 style="color:#fca5a5;margin:0 0 8px">❌ No Match Found</h3>
                <p style="color:#fecaca;margin:0">
                    Best score: <strong>{int(best_score*100)}%</strong>
                    (threshold: {int(threshold*100)}%)
                </p>
                <p style="color:#fca5a5;font-size:13px;margin-top:8px">
                    Try lowering the threshold or uploading a clearer frontal photo.
                </p>
            </div>
            """, unsafe_allow_html=True)

        # ── All scores (admin only) ────────────────────────────────────────────
        if show_scores and user_role == "Admin" and candidates:
            from pages.helper.utils import hybrid_similarity
            import pandas as pd
            st.subheader("📊 All Candidate Scores")
            rows = [
                {
                    "Name":  c["name"],
                    "ID":    c["id"][:8] + "…",
                    "Score": f"{hybrid_similarity(query_mesh, c['mesh']):.1%}",
                    "Label": confidence_label(hybrid_similarity(query_mesh, c["mesh"])),
                }
                for c in candidates
            ]
            df = pd.DataFrame(rows).sort_values("Score", ascending=False)
            st.dataframe(df)


main()
