"""
Case Management — View, search, filter and update cases.
Admins see all cases and can mark found.
Users see only their own cases.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from pages.helper import db_queries
from pages.helper.streamlit_helpers import require_login, show_role_badge

st.set_page_config(page_title="Case Management", page_icon="📁", layout="wide")
show_role_badge()

st.markdown("""
<style>
@keyframes slideDown {
    from { opacity:0; transform:translateY(-20px); }
    to   { opacity:1; transform:translateY(0); }
}
.found-popup {
    background: linear-gradient(135deg, #064e3b, #065f46);
    border: 2px solid #10b981;
    border-radius: 16px;
    padding: 20px 24px;
    margin: 12px 0;
    animation: slideDown 0.4s ease;
    box-shadow: 0 8px 32px rgba(16,185,129,0.35);
}
.found-popup h3 { color: #a7f3d0; margin:0 0 6px; }
.found-popup p  { color: #d1fae5; margin: 3px 0; font-size:14px; }
.case-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


def render_found_popup(person):
    """Popup-style alert for a found person."""
    found_at = getattr(person, "found_at", None)
    found_str = found_at.strftime("%d %b %Y, %I:%M %p") if found_at else datetime.now().strftime("%d %b %Y, %I:%M %p")
    st.markdown(f"""
    <div class="found-popup">
        <h3>🎉 {person.name} — FOUND</h3>
        <p>📍 <strong>Found at:</strong> {person.found_location or 'N/A'}</p>
        <p>👮 <strong>Found by:</strong> {person.found_by or 'N/A'}</p>
        <p>🕐 <strong>Time:</strong> {found_str}</p>
        <p>🪪 <strong>Case ID:</strong> {person.id}</p>
    </div>
    """, unsafe_allow_html=True)
    st.success(f"✅ {person.name} is FOUND! Case closed.", icon="🎉")


@require_login
def main():
    st.title("📁 Case Management")
    user_role = st.session_state.get("user_role", "User")
    username  = st.session_state.get("user", "")
    st.caption(
        "Admin: all cases | User: your registered cases only"
        if user_role == "Admin" else "Showing cases you registered."
    )
    st.divider()

    # ── Filters ────────────────────────────────────────────────────────────────
    col_search, col_status, col_refresh = st.columns([2, 1, 1])
    with col_search:
        search_q = st.text_input("🔍 Search by name or location", "")
    with col_status:
        status_filter = st.selectbox("Status", ["All", "Not Found", "Found"])
    with col_refresh:
        st.write("")
        refresh = st.button("🔄 Refresh")

    status_map = {"All": None, "Not Found": "NF", "Found": "F"}
    status_val = status_map[status_filter]

    # ── Fetch cases ────────────────────────────────────────────────────────────
    try:
        all_persons = db_queries.get_all_missing_persons(status=status_val)
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    # Scope for non-admins
    if user_role != "Admin":
        all_persons = [p for p in all_persons if p.registered_by == username]

    # Search filter
    if search_q.strip():
        q = search_q.lower()
        all_persons = [p for p in all_persons if
                       q in (p.name or "").lower() or
                       q in (p.location or "").lower()]

    # ── Found alerts at top ────────────────────────────────────────────────────
    found_persons = [p for p in all_persons if p.status == "F"]
    if found_persons and status_filter in ("All", "Found"):
        st.markdown("### 🚨 Found Person Alerts")
        for p in found_persons[:3]:       # show top 3
            render_found_popup(p)
            if user_role == "Admin":
                if st.button(f"Dismiss alert for {p.name}", key=f"dismiss_{p.id}"):
                    db_queries.dismiss_alert(p.id)
                    st.rerun()
        st.divider()

    # ── Summary metrics ────────────────────────────────────────────────────────
    total  = len(all_persons)
    n_found = sum(1 for p in all_persons if p.status == "F")
    n_nf    = total - n_found

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Cases",  total)
    m2.metric("✅ Found",     n_found)
    m3.metric("🔍 Active",    n_nf)
    st.divider()

    if not all_persons:
        st.info("No cases match your filter criteria.")
        return

    # ── Case table (admin) / cards (user) ──────────────────────────────────────
    if user_role == "Admin":
        rows = []
        for p in all_persons:
            rows.append({
                "ID":          p.id[:8] + "…",
                "Name":        p.name,
                "Age":         p.age or "N/A",
                "Last Seen":   p.location or "N/A",
                "Status":      "✅ Found" if p.status == "F" else "🔍 Active",
                "Registered":  p.registered_by or "N/A",
                "Date":        p.created_at.strftime("%d %b %Y") if p.created_at else "N/A",
                "_id":         p.id,
            })

        df = pd.DataFrame(rows)
        display_df = df.drop(columns=["_id"])
        st.dataframe(display_df, height=400)

        # ── Inline mark-found ──────────────────────────────────────────────────
        st.divider()
        st.subheader("⚡ Quick Actions")
        nf_persons = [p for p in all_persons if p.status == "NF"]
        if nf_persons:
            col_select, col_loc, col_btn = st.columns([2, 2, 1])
            selected_name = col_select.selectbox(
                "Select case to mark as Found",
                options=[p.name for p in nf_persons],
                key="mark_found_select",
            )
            found_location = col_loc.text_input("Found at location")

            if col_btn.button("✅ Mark Found"):
                person = next((p for p in nf_persons if p.name == selected_name), None)
                if person:
                    updated = db_queries.mark_person_found(
                        person_id=person.id,
                        found_by=username,
                        found_location=found_location or "Unknown",
                        match_confidence=1.0,
                    )
                    if updated:
                        st.success(f"✅ {selected_name} marked as FOUND!")
                        st.balloons()
                        st.rerun()
        else:
            st.info("All active cases have been resolved. 🎉")

    else:
        # Card view for regular users
        for p in all_persons:
            status_icon  = "✅" if p.status == "F" else "🔍"
            status_color = "#10b981" if p.status == "F" else "#f59e0b"
            with st.expander(f"{status_icon} {p.name} — {p.location or 'Location N/A'}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Age:** {p.age or 'N/A'}")
                c1.write(f"**Gender:** {p.gender or 'N/A'}")
                c1.write(f"**Last seen:** {p.location or 'N/A'}")
                c2.write(f"**Birth marks:** {p.birth_marks or 'None'}")
                c2.write(f"**Registered:** {p.created_at.strftime('%d %b %Y') if p.created_at else 'N/A'}")
                if p.status == "F":
                    st.markdown(f"""
                    <div style="background:rgba(16,185,129,0.1);border:1px solid #10b981;
                    border-radius:10px;padding:12px;margin-top:8px">
                        <strong style="color:#10b981">✅ FOUND</strong><br>
                        📍 {p.found_location or 'N/A'} &nbsp;|&nbsp;
                        🕐 {p.found_at.strftime('%d %b %Y') if p.found_at else 'N/A'}
                    </div>
                    """, unsafe_allow_html=True)

                if p.image_path:
                    try:
                        st.image(p.image_path, caption="Registered photo", width=200)
                    except Exception:
                        pass


main()
