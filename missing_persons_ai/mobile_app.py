"""
Mobile / Public Submission Portal.
Any member of the public can submit a sighting photo.
The system automatically tries to match it against the DB
and fires a found-alert if confidence is high enough.
"""

import uuid
import json
import streamlit as st

from pages.helper import db_queries
from pages.helper.data_models import PublicSubmissions
from pages.helper.utils import (
    image_obj_to_numpy,
    extract_face_mesh_landmarks,
    find_best_match,
    confidence_label,
    save_uploaded_image,
)

st.set_page_config(
    page_title="Report a Sighting",
    page_icon="📱",
    initial_sidebar_state="collapsed",
    layout="centered",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@keyframes popIn {
    0%   { opacity:0; transform:scale(0.85); }
    70%  { transform:scale(1.05); }
    100% { opacity:1; transform:scale(1); }
}
.found-banner {
    background: linear-gradient(135deg,#064e3b,#065f46);
    border: 3px solid #10b981;
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    animation: popIn 0.5s cubic-bezier(.34,1.56,.64,1);
    box-shadow: 0 12px 48px rgba(16,185,129,0.5);
    margin: 20px 0;
}
.found-banner h2 { color:#a7f3d0; font-size:26px; margin:0 0 10px; }
.found-banner p  { color:#d1fae5; font-size:15px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📱 Report a Sighting")
st.markdown(
    "If you believe you have seen a missing person, submit a photo here. "
    "Our AI will scan it against registered missing persons **instantly**."
)
st.divider()

# ── Upload ─────────────────────────────────────────────────────────────────────
image_obj = st.file_uploader(
    "📸 Upload photo of the person you saw",
    type=["jpg", "jpeg", "png"],
    key="public_upload",
)

face_mesh  = None
unique_id  = str(uuid.uuid4())
image_path = None
match_result = None
match_score  = 0.0

if image_obj:
    st.image(image_obj, caption="Your uploaded photo", use_column_width=True)

    with st.spinner("🔍 Detecting face…"):
        img_np    = image_obj_to_numpy(image_obj)
        face_mesh = extract_face_mesh_landmarks(img_np)
        image_path = save_uploaded_image(image_obj, unique_id)

    if face_mesh:
        st.success(f"✅ Face detected ({len(face_mesh)//3} landmarks).")

        # ── Auto match ────────────────────────────────────────────────────────
        with st.spinner("🧠 Scanning registered missing persons…"):
            candidates   = db_queries.get_all_face_meshes_from_db()
            match_result, match_score = find_best_match(face_mesh, candidates, threshold=0.60)

        if match_result:
            pct = int(match_score * 100)
            st.markdown(f"""
            <div class="found-banner">
                <h2>🎉 Possible Match Found!</h2>
                <p>This person may be <strong>{match_result['name']}</strong></p>
                <p>Confidence: <strong>{pct}%</strong> — {confidence_label(match_score)}</p>
                <p style="font-size:12px;opacity:.7">Authorities have been notified.</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
            st.success(
                f"🚨 Possible match: **{match_result['name']}** ({pct}% confidence). "
                "Please fill the form below so authorities can follow up.",
                icon="✅",
            )
        else:
            st.info(
                "No automatic match found, but your submission will be reviewed "
                "manually by our team. Please fill in the details below."
            )
    else:
        st.warning(
            "⚠️ Could not detect a face. Please upload a clear, frontal photo. "
            "You may still submit the form for manual review."
        )

# ── Submission form ────────────────────────────────────────────────────────────
st.divider()
st.subheader("📝 Your Contact Details")

with st.form("public_form"):
    col1, col2 = st.columns(2)
    name          = col1.text_input("Your Name *")
    mobile        = col2.text_input("Mobile Number *")
    email         = st.text_input("Email Address")
    location      = st.text_input("📍 Location / Address where you saw this person *")
    birth_marks   = st.text_input("Any identifying marks you noticed")
    notes         = st.text_area("Additional Notes", height=80,
                                  placeholder="Clothing, behaviour, who they were with…")

    submit_btn = st.form_submit_button("📤 Submit Sighting Report")

if submit_btn:
    errors = []
    if not name.strip():
        errors.append("Your name is required.")
    if not mobile.strip():
        errors.append("Mobile number is required.")
    if not location.strip():
        errors.append("Location is required.")
    if not image_obj:
        errors.append("Please upload a photo.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        submission = PublicSubmissions(
            id=unique_id,
            submitted_by=name.strip(),
            location=location.strip(),
            email=email.strip(),
            mobile=mobile.strip(),
            face_mesh=json.dumps(face_mesh) if face_mesh else None,
            birth_marks=birth_marks.strip(),
            image_path=image_path,
            matched_person_id=match_result["id"] if match_result else None,
            match_confidence=match_score if match_result else None,
            status="F" if (match_result and match_score >= 0.75) else "NF",
        )

        try:
            db_queries.new_public_case(submission)

            # If high-confidence match, mark person as found
            if match_result and match_score >= 0.75:
                db_queries.mark_person_found(
                    person_id=match_result["id"],
                    found_by=name.strip(),
                    found_location=location.strip(),
                    match_confidence=match_score,
                )

            st.success("✅ Submission received! Thank you for helping locate missing persons.")
            st.info(
                "A reference number has been generated for your submission: "
                f"`{unique_id[:8].upper()}`"
            )
        except Exception as e:
            st.error(f"❌ Submission failed: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "🔒 Your information is kept confidential and used solely for the purpose "
    "of locating missing persons. For emergencies, call **100** (Police)."
)
