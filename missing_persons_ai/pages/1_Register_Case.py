"""
Register Missing Person — Admin only page.
Captures photo, extracts face mesh, saves to DB.
"""

import uuid
import json
import streamlit as st

from pages.helper import db_queries
from pages.helper.data_models import MissingPerson
from pages.helper.utils import (
    image_obj_to_numpy,
    extract_face_mesh_landmarks,
    save_uploaded_image,
)
from pages.helper.streamlit_helpers import require_admin, show_role_badge

st.set_page_config(page_title="Register Case", page_icon="📝", layout="wide")

show_role_badge()


@require_admin
def main():
    st.title("📝 Register Missing Person Case")
    st.caption("Admin only — extracted face mesh will be stored for AI matching.")
    st.divider()

    image_col, form_col = st.columns([1, 1])

    image_obj = None
    face_mesh = None
    image_path = None

    with image_col:
        st.subheader("📸 Upload Photo")
        image_obj = st.file_uploader(
            "Clear frontal photo works best",
            type=["jpg", "jpeg", "png"],
            key="register_image",
        )
        if image_obj:
            st.image(image_obj, caption="Uploaded photo", use_container_width=True)
            with st.spinner("🔍 Extracting face landmarks…"):
                img_np = image_obj_to_numpy(image_obj)
                face_mesh = extract_face_mesh_landmarks(img_np)

            if face_mesh:
                st.success(f"✅ Face detected — {len(face_mesh)//3} landmarks extracted.")
            else:
                st.warning(
                    "⚠️ No face detected. Ensure the photo is clear and well-lit. "
                    "You can still save the case but matching accuracy will be reduced."
                )

    with form_col:
        st.subheader("📋 Case Details")
        with st.form("register_form"):
            name          = st.text_input("Full Name *")
            age           = st.number_input("Age", min_value=0, max_value=120, value=25)
            gender        = st.selectbox("Gender", ["Male", "Female", "Other"])
            location      = st.text_input("Last Seen Location *")
            description   = st.text_area("Physical Description", height=100,
                                          placeholder="Height, build, clothing, etc.")
            birth_marks   = st.text_input("Identifying Marks / Birth Marks")

            st.divider()
            submitted = st.form_submit_button("💾 Register Case", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Name is required.")
                return
            if not location.strip():
                st.error("Last seen location is required.")
                return

            unique_id = str(uuid.uuid4())

            # Save image
            if image_obj:
                image_path = save_uploaded_image(image_obj, unique_id)

            person = MissingPerson(
                id=unique_id,
                name=name.strip(),
                age=age,
                gender=gender,
                location=location.strip(),
                description=description.strip(),
                birth_marks=birth_marks.strip(),
                face_mesh=json.dumps(face_mesh) if face_mesh else None,
                image_path=image_path,
                registered_by=st.session_state.get("user", "unknown"),
                status="NF",
            )

            try:
                db_queries.register_missing_person(person)
                st.success(f"✅ Case registered successfully! ID: `{unique_id}`")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Failed to save case: {e}")


main()
