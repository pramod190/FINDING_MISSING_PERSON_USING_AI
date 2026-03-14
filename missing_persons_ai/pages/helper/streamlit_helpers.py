"""
Streamlit helper decorators and UI guards.
"""

import streamlit as st
from functools import wraps


def require_login(func):
    """Decorator: redirect to login page if user is not authenticated."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("login_status"):
            st.error("🔒 You must be logged in to access this page.")
            st.info("Please return to the **Home** page and sign in.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator: allow only Admin-role users."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("login_status"):
            st.error("🔒 You must be logged in to access this page.")
            st.stop()
        if st.session_state.get("user_role") != "Admin":
            st.error("🚫 This page is restricted to **Admin** users only.")
            st.warning("Please contact your administrator if you need access.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def show_role_badge():
    """Render a sidebar role badge."""
    role = st.session_state.get("user_role", "User")
    user = st.session_state.get("user", "")
    color = "#dc2626" if role == "Admin" else "#2563eb"
    st.sidebar.markdown(
        f'<div style="background:{color};color:white;border-radius:8px;'
        f'padding:6px 12px;text-align:center;font-weight:700;font-size:13px;margin-bottom:8px">'
        f'{"🛡️ ADMIN" if role=="Admin" else "👤 USER"}: {user}</div>',
        unsafe_allow_html=True,
    )
