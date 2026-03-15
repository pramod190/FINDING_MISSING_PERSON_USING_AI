import yaml, re, time, os
import streamlit as st
from yaml import SafeLoader

try:
    from pages.helper import db_queries
    DB_READY = True
except Exception:
    DB_READY = False

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Missing Persons AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & base ── */
* { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: #080e1a !important;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stSidebar"] { background: #0d1526 !important; border-right: 1px solid rgba(255,255,255,0.06); }

/* ── Animations ── */
@keyframes fadeUp   { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeIn   { from { opacity:0; } to { opacity:1; } }
@keyframes pulse    { 0%,100% { opacity:1; } 50% { opacity:.4; } }
@keyframes slideIn  { from { opacity:0; transform:translateX(-16px); } to { opacity:1; transform:translateX(0); } }
@keyframes glow     { 0%,100% { box-shadow:0 0 20px rgba(99,102,241,.3); } 50% { box-shadow:0 0 40px rgba(99,102,241,.6); } }
@keyframes shimmer  { 0% { background-position:-200% center; } 100% { background-position:200% center; } }
@keyframes popIn    { 0% { opacity:0; transform:scale(.85); } 70% { transform:scale(1.03); } 100% { opacity:1; transform:scale(1); } }
@keyframes spin     { to { transform:rotate(360deg); } }

/* ── Auth page wrapper ── */
.auth-hero {
    text-align: center;
    padding: 40px 0 20px;
    animation: fadeUp .7s ease both;
}
.auth-hero .logo {
    font-size: 56px;
    display: inline-block;
    margin-bottom: 12px;
    filter: drop-shadow(0 4px 16px rgba(99,102,241,.5));
}
.auth-hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 38px; font-weight: 900;
    color: #f1f5f9; margin: 0 0 8px;
    letter-spacing: -.02em;
}
.auth-hero p {
    color: #64748b; font-size: 15px; margin: 0;
}

/* ── Auth card ── */
.auth-card {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 36px 32px;
    backdrop-filter: blur(20px);
    box-shadow: 0 32px 64px rgba(0,0,0,.6);
    animation: fadeUp .6s .1s ease both;
}

/* ── Tab bar ── */
.tab-bar {
    display: flex; gap: 4px;
    background: rgba(255,255,255,0.04);
    border-radius: 14px; padding: 4px;
    margin-bottom: 24px;
}
.tab-btn {
    flex: 1; text-align: center;
    padding: 10px 0; border-radius: 10px;
    font-size: 14px; font-weight: 600;
    cursor: pointer; border: none;
    transition: all .25s;
}
.tab-btn.active  { background: #6366f1; color: #fff; box-shadow: 0 4px 12px rgba(99,102,241,.4); }
.tab-btn.inactive { background: transparent; color: #64748b; }
.tab-btn.inactive:hover { color: #cbd5e1; }

/* ── Input fields ── */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.2) !important;
}
.stTextInput > label { color: #94a3b8 !important; font-size: 13px !important; font-weight: 500 !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all .2s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(99,102,241,.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(99,102,241,.5) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #94a3b8 !important;
}

/* ── Password strength bar ── */
.pw-strength-wrap { height: 4px; background: rgba(255,255,255,0.07); border-radius: 4px; margin: 4px 0 8px; }
.pw-strength-bar  { height: 100%; border-radius: 4px; transition: width .4s, background .4s; }

/* ── Validation chips ── */
.check-row { display:flex; flex-wrap:wrap; gap:6px; margin: 4px 0 12px; }
.chip { font-size: 11px; padding: 3px 10px; border-radius: 20px; font-weight: 500; }
.chip.ok   { background: rgba(16,185,129,.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,.25); }
.chip.fail { background: rgba(239,68,68,.1);   color: #fca5a5; border: 1px solid rgba(239,68,68,.2); }

/* ── Success box ── */
.success-box {
    background: linear-gradient(135deg,#064e3b,#065f46);
    border: 2px solid #10b981; border-radius: 18px;
    padding: 24px 28px; text-align: center;
    animation: popIn .5s cubic-bezier(.34,1.56,.64,1);
    box-shadow: 0 12px 40px rgba(16,185,129,.4);
    margin: 12px 0;
}
.success-box h3 { color:#a7f3d0; margin:0 0 6px; font-size:20px; font-family:'Playfair Display',serif; }
.success-box p  { color:#d1fae5; margin:0; font-size:14px; }

/* ── Found alert ── */
.found-alert {
    background: linear-gradient(135deg,#065f46,#047857);
    border: 2px solid #10b981; border-radius:16px;
    padding: 24px 28px; margin: 16px 0;
    animation: popIn .5s ease;
    box-shadow: 0 8px 32px rgba(16,185,129,.4);
}
.found-alert h2 { color:#a7f3d0; margin:0 0 8px; font-size:22px; font-family:'Playfair Display',serif; }
.found-alert p  { color:#d1fae5; margin:4px 0; font-size:15px; }

/* ── Role badge ── */
.role-badge {
    display: inline-block; border-radius: 8px;
    padding: 4px 14px; font-weight: 700; font-size: 13px;
}

/* ── Divider with text ── */
.or-divider {
    display: flex; align-items: center; gap: 12px;
    margin: 16px 0; color: #334155; font-size: 12px;
}
.or-divider::before, .or-divider::after {
    content:''; flex:1; height:1px; background:rgba(255,255,255,0.07);
}

/* ── Metric cards ── */
.metric-row { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:16px 0; }
.metric-card {
    background: rgba(15,23,42,.8); border:1px solid rgba(255,255,255,.07);
    border-radius:14px; padding:18px 20px; text-align:center;
}
.metric-card .val { font-size:32px; font-weight:700; font-family:'DM Sans',sans-serif; color:#f1f5f9; }
.metric-card .lbl { font-size:12px; color:#64748b; margin-top:4px; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Selectbox */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
CONFIG_FILE  = "login_config.yml"
ADMIN_SECRET = "MPAdmin2024"   # Secret key to register as Admin

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return yaml.load(f, Loader=SafeLoader)
    except FileNotFoundError:
        default = {"credentials": {"usernames": {
            "pramod_admin": {
                "name":"Pramod Kumar","email":"pramodanem.pa2004@gmail.com",
                "password":"Admin@123","role":"Admin","city":"Hyderabad","area":"Vijaynagar Colony"
            }}}}
        save_config(default)
        return default

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

def valid_email(e):
    return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.\w{2,}$", e))

def pw_strength(pw):
    score = 0
    checks = {
        "6+ characters":   len(pw) >= 6,
        "uppercase":       bool(re.search(r"[A-Z]", pw)),
        "number":          bool(re.search(r"\d", pw)),
        "special char":    bool(re.search(r"[^a-zA-Z0-9]", pw)),
    }
    score = sum(checks.values())
    return score, checks

def logout():
    for k in ["login_status","user","user_role","username","auth_tab"]:
        st.session_state[k] = (False if k=="login_status" else ("login" if k=="auth_tab" else ""))
    st.rerun()

# ── Session init ───────────────────────────────────────────────────────────────
DEFAULTS = {"login_status":False,"user":"","user_role":"","username":"","auth_tab":"login","signup_done":False}
for k,v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Load users ─────────────────────────────────────────────────────────────────
cfg   = load_config()
USERS = cfg["credentials"]["usernames"]

# ══════════════════════════════════════════════════════════════════════════════
#  NOT LOGGED IN  →  Auth Page
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state["login_status"]:

    # Background ambient blobs
    st.markdown("""
    <div style="position:fixed;inset:0;pointer-events:none;z-index:0;
         background:radial-gradient(ellipse 70% 50% at 20% 20%,rgba(99,102,241,.12) 0%,transparent 60%),
                    radial-gradient(ellipse 60% 40% at 80% 80%,rgba(16,185,129,.08) 0%,transparent 60%);">
    </div>""", unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <div class="auth-hero">
        <div class="logo">🔍</div>
        <h1>Missing Persons AI</h1>
        <p>AI-powered facial recognition platform to help locate missing individuals</p>
    </div>""", unsafe_allow_html=True)

    # Center column
    _, col, _ = st.columns([1, 1.45, 1])
    with col:

        # ── Tab switcher ───────────────────────────────────────────────────────
        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            si_type = "primary"   if st.session_state["auth_tab"] == "login"  else "secondary"
            if st.button("🔐  Sign In", type=si_type, key="tab_login"):
                st.session_state["auth_tab"]    = "login"
                st.session_state["signup_done"] = False
                st.rerun()
        with tab_col2:
            su_type = "primary"   if st.session_state["auth_tab"] == "signup" else "secondary"
            if st.button("✏️  Sign Up", type=su_type, key="tab_signup"):
                st.session_state["auth_tab"]    = "signup"
                st.session_state["signup_done"] = False
                st.rerun()

        # ══════════════════════════════════════════════════════════════════════
        #  SIGN IN
        # ══════════════════════════════════════════════════════════════════════
        if st.session_state["auth_tab"] == "login":
            with st.container(border=True):
                st.markdown("#### Welcome back 👋")
                st.caption("Enter your credentials to access the platform")
                st.markdown("")

                li_user = st.text_input("Username",          placeholder="e.g. pramod_admin", key="li_user")
                li_pass = st.text_input("Password",          placeholder="Enter your password", type="password", key="li_pass")
                st.markdown("")

                if st.button("Sign In  →", type="primary", key="btn_signin"):
                    cfg   = load_config()
                    USERS = cfg["credentials"]["usernames"]
                    if not li_user.strip():
                        st.error("⚠️ Please enter your username.")
                    elif not li_pass.strip():
                        st.error("⚠️ Please enter your password.")
                    elif li_user not in USERS:
                        st.error("❌ Username not found. Please **Sign Up** first.")
                    elif USERS[li_user]["password"] != li_pass:
                        st.error("❌ Incorrect password. Please try again.")
                    else:
                        u = USERS[li_user]
                        st.session_state.update({
                            "login_status": True,
                            "username":     li_user,
                            "user":         u["name"],
                            "user_role":    u.get("role","User"),
                        })
                        st.rerun()

                st.markdown("""
                <div class="or-divider">New here?</div>
                """, unsafe_allow_html=True)
                if st.button("Create a free account  →", key="goto_signup"):
                    st.session_state["auth_tab"] = "signup"
                    st.rerun()

            # Demo creds
            with st.expander("🔑 Demo Credentials"):
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown("**🛡️ Admin**")
                    st.code("pramod_admin\nAdmin@123", language=None)
                with dc2:
                    st.markdown("**👤 User**")
                    st.code("user_priya\nUser@789", language=None)

        # ══════════════════════════════════════════════════════════════════════
        #  SIGN UP
        # ══════════════════════════════════════════════════════════════════════
        else:
            # Success screen
            if st.session_state.get("signup_done"):
                new_uname = st.session_state.get("new_uname","")
                new_name  = st.session_state.get("new_name","")
                new_role  = st.session_state.get("new_role","User")
                st.markdown(f"""
                <div class="success-box">
                    <h3>🎉 Account Created!</h3>
                    <p>Welcome, <strong>{new_name}</strong>!<br>
                    You are registered as a
                    <strong>{"🛡️ Admin" if new_role=="Admin" else "👤 User"}</strong>.<br><br>
                    Username: <code>{new_uname}</code></p>
                </div>""", unsafe_allow_html=True)
                st.balloons()
                st.markdown("")
                if st.button("Go to Sign In  →", type="primary"):
                    st.session_state["auth_tab"]    = "login"
                    st.session_state["signup_done"] = False
                    st.rerun()

            else:
                with st.container(border=True):
                    st.markdown("#### Create your account ✏️")
                    st.caption("Fill in your details to get started")
                    st.markdown("")

                    # ── Row 1: Name + Email ────────────────────────────────────
                    r1a, r1b = st.columns(2)
                    su_name  = r1a.text_input("Full Name *",       placeholder="e.g. Ravi Kumar",      key="su_name")
                    su_email = r1b.text_input("Email Address *",   placeholder="e.g. ravi@email.com",  key="su_email")

                    # ── Row 2: City + Area ─────────────────────────────────────
                    r2a, r2b = st.columns(2)
                    su_city  = r2a.text_input("City *",            placeholder="e.g. Hyderabad",       key="su_city")
                    su_area  = r2b.text_input("Area / Colony",     placeholder="e.g. Banjara Hills",   key="su_area")

                    # ── Username ───────────────────────────────────────────────
                    su_uname = st.text_input(
                        "Choose a Username *",
                        placeholder="e.g. ravi_kumar  (no spaces)",
                        key="su_uname",
                    )

                    # ── Passwords ──────────────────────────────────────────────
                    r3a, r3b = st.columns(2)
                    su_pw1   = r3a.text_input("Password *",        placeholder="Min 6 characters", type="password", key="su_pw1")
                    su_pw2   = r3b.text_input("Confirm Password *",placeholder="Re-enter",         type="password", key="su_pw2")

                    # Live password strength
                    if su_pw1:
                        score, checks = pw_strength(su_pw1)
                        bar_pct   = [0,25,50,75,90,100][score]
                        bar_color = ["#ef4444","#f97316","#f59e0b","#84cc16","#10b981"][max(0,score-1)] if score else "#ef4444"
                        chips_html = "".join(
                            f'<span class="chip {"ok" if ok else "fail"}">{"✓" if ok else "✗"} {label}</span>'
                            for label, ok in checks.items()
                        )
                        st.markdown(f"""
                        <div class="pw-strength-wrap">
                          <div class="pw-strength-bar" style="width:{bar_pct}%;background:{bar_color}"></div>
                        </div>
                        <div class="check-row">{chips_html}</div>
                        """, unsafe_allow_html=True)

                    # Passwords match indicator
                    if su_pw2 and su_pw1:
                        if su_pw1 == su_pw2:
                            st.markdown('<p style="color:#10b981;font-size:12px;margin:0">✓ Passwords match</p>', unsafe_allow_html=True)
                        else:
                            st.markdown('<p style="color:#ef4444;font-size:12px;margin:0">✗ Passwords do not match</p>', unsafe_allow_html=True)

                    # ── Role selector ──────────────────────────────────────────
                    st.markdown("")
                    with st.expander("🔑 Register as Admin? (enter secret key)"):
                        su_admin_key = st.text_input(
                            "Admin Secret Key",
                            type="password",
                            placeholder="Leave blank to register as User",
                            key="su_admin_key",
                        )
                        st.caption("Contact your system administrator for the admin key.")

                    st.markdown("")

                    # ── Submit ─────────────────────────────────────────────────
                    if st.button("Create Account  →", type="primary", key="btn_create"):
                        cfg   = load_config()
                        USERS = cfg["credentials"]["usernames"]
                        errs  = []

                        if not su_name.strip():
                            errs.append("Full name is required.")
                        if not su_email.strip():
                            errs.append("Email address is required.")
                        elif not valid_email(su_email):
                            errs.append("Please enter a valid email address.")
                        elif any(u.get("email","").lower() == su_email.lower() for u in USERS.values()):
                            errs.append("An account with this email already exists.")
                        if not su_city.strip():
                            errs.append("City is required.")
                        if not su_uname.strip():
                            errs.append("Username is required.")
                        elif " " in su_uname:
                            errs.append("Username cannot contain spaces.")
                        elif su_uname in USERS:
                            errs.append(f"Username '{su_uname}' is already taken. Try another.")
                        if not su_pw1:
                            errs.append("Password is required.")
                        elif len(su_pw1) < 6:
                            errs.append("Password must be at least 6 characters.")
                        elif su_pw1 != su_pw2:
                            errs.append("Passwords do not match.")

                        if errs:
                            for e in errs:
                                st.error(f"⚠️ {e}")
                        else:
                            role = "Admin" if su_admin_key == ADMIN_SECRET else "User"
                            cfg["credentials"]["usernames"][su_uname.strip()] = {
                                "name":     su_name.strip(),
                                "email":    su_email.strip(),
                                "password": su_pw1,
                                "role":     role,
                                "city":     su_city.strip(),
                                "area":     su_area.strip(),
                            }
                            save_config(cfg)

                            # Store for success screen
                            st.session_state["signup_done"] = True
                            st.session_state["new_uname"]   = su_uname.strip()
                            st.session_state["new_name"]    = su_name.strip()
                            st.session_state["new_role"]    = role
                            st.rerun()

                    st.markdown("""
                    <div class="or-divider">Already have an account?</div>
                    """, unsafe_allow_html=True)
                    if st.button("Sign in instead  →", key="goto_login2"):
                        st.session_state["auth_tab"] = "login"
                        st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  LOGGED IN  →  Dashboard
# ══════════════════════════════════════════════════════════════════════════════
cfg       = load_config()
USERS     = cfg["credentials"]["usernames"]
uname     = st.session_state["username"]
user_data = USERS.get(uname, {})
user_role = st.session_state["user_role"]
role_color = "#dc2626" if user_role == "Admin" else "#2563eb"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Missing Persons AI")
    st.markdown(
        f'<div style="background:{role_color};color:#fff;border-radius:10px;'
        f'padding:7px 14px;text-align:center;font-weight:700;font-size:13px;margin:8px 0 16px">'
        f'{"🛡️ ADMIN" if user_role=="Admin" else "👤 USER"} · {st.session_state["user"]}'
        f'</div>', unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Navigation**")
    st.markdown("- 🏠 Home Dashboard")
    st.markdown("- 📝 Register Case" if user_role=="Admin" else "- 🔍 Face Matching")
    st.markdown("- 🤖 Face Matching")
    st.markdown("- 📁 Case Management")
    st.divider()
    if st.button("🚪 Logout"):
        logout()

# ── Header ─────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([3, 1])
with hc1:
    st.markdown(
        f'<h2 style="font-family:\'Playfair Display\',serif;color:#f1f5f9;margin:0">'
        f'👤 {user_data.get("name", st.session_state["user"])}</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:#64748b;margin-top:4px">'
        f'📍 {user_data.get("area","")}{"," if user_data.get("area") else ""} '
        f'{user_data.get("city","")} &nbsp;·&nbsp; {user_data.get("email","")}</p>',
        unsafe_allow_html=True,
    )
with hc2:
    badge = "🛡️ ADMIN" if user_role == "Admin" else "👤 USER"
    st.markdown(
        f'<br><span class="role-badge" style="background:{role_color};color:#fff">{badge}</span>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Found-person alerts ────────────────────────────────────────────────────────
if DB_READY:
    try:
        found = (db_queries.get_recently_found_cases() if user_role=="Admin"
                 else db_queries.get_recently_found_cases(submitted_by=st.session_state["user"]))
        if found:
            st.markdown("## 🚨 Active Alerts")
            for p in found:
                st.markdown(f"""
                <div class="found-alert">
                    <h2>🎉 {getattr(p,'name','?')} Has Been Found!</h2>
                    <p>📍 <strong>Location:</strong> {getattr(p,'found_location','N/A')}</p>
                    <p>👮 <strong>Found by:</strong>  {getattr(p,'found_by','System')}</p>
                    <p>🪪 <strong>Case ID:</strong>   {getattr(p,'id','N/A')}</p>
                </div>""", unsafe_allow_html=True)
                st.success(f"✅ {getattr(p,'name','Person')} has been FOUND!", icon="🎉")
                st.balloons()
            st.divider()
    except Exception:
        pass

# ── Stats ──────────────────────────────────────────────────────────────────────
if DB_READY:
    try:
        is_admin = user_role == "Admin"
        fc = db_queries.get_registered_cases_count(
            None if is_admin else user_data.get("name"), "F",  admin=is_admin)
        nf = db_queries.get_registered_cases_count(
            None if is_admin else user_data.get("name"), "NF", admin=is_admin)
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Found Cases",  len(fc))
        c2.metric("🔍 Active Cases", len(nf))
        c3.metric("📊 Total Cases",  len(fc)+len(nf))
        st.divider()
    except Exception:
        st.info("📦 No cases yet. Register a case to get started.")
        st.divider()
else:
    st.info("📦 Database initialising. Register a case to get started.")
    st.divider()

# ── Role info box ──────────────────────────────────────────────────────────────
if user_role == "Admin":
    st.info("🛡️ **Admin Access:** Register Cases · Run Face Matching · Manage All Cases · View Analytics", icon="🛡️")
else:
    st.info("👤 **User Access:** Submit sightings · View your case statuses · Run face matching", icon="👤")

# ── Recent activity ────────────────────────────────────────────────────────────
st.markdown("### 📋 Recent Activity")
if DB_READY:
    try:
        recent = db_queries.get_recent_activity(limit=5)
        if recent:
            for item in recent:
                icon = "✅" if item.get("status") == "F" else "🔍"
                st.markdown(
                    f"- {icon} **{item.get('name','Unknown')}** — "
                    f"_{item.get('location','N/A')}_ — {item.get('created_at','')}"
                )
        else:
            st.caption("No recent activity yet. Register a case to get started.")
    except Exception:
        st.caption("Activity feed will appear once cases are registered.")
else:
    st.caption("No activity yet.")
