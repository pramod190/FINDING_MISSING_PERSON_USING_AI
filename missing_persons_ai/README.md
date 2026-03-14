# 🔍 Missing Persons AI System — v2.0

An AI-powered platform to help Police and authorities locate missing persons using facial recognition.

---

## ✨ What's New in v2.0

### 🎯 Improved Accuracy
- Uses **all 478 MediaPipe Face Mesh landmarks** (up from a subset)
- **Normalised landmarks** — invariant to position, scale and mild head tilt
- **Hybrid scoring**: 60% cosine similarity + 40% Euclidean distance
- Configurable confidence threshold (Admin-adjustable in UI)
- Tiered confidence labels: Very High / High / Moderate / Low

### 🔐 Role-Based Authentication
| Feature | Admin | User |
|---|---|---|
| Register new cases | ✅ | ❌ |
| Run face matching | ✅ | ✅ |
| See ALL cases | ✅ | ❌ (own only) |
| Mark person as Found | ✅ | ❌ |
| Adjust match threshold | ✅ | ❌ |
| View analytics | ✅ | ❌ |
| Submit public sighting | ✅ | ✅ |

### 🚨 Found-Person Alert Popups
- Animated popup appears whenever a person is matched / marked found
- Fires on: Face Matching page, Case Management page, Home dashboard
- `st.balloons()` celebration effect
- Alert is stored in DB and shown **once** (not on every refresh)
- Admin can dismiss individual alerts

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd missing-persons-ai
pip install -r requirements.txt

# 2. Generate hashed passwords (optional — defaults already set)
python generate_passwords.py

# 3. Run main app
streamlit run Home.py

# 4. Run mobile / public submission app
streamlit run mobile_app.py
```

---

## 👤 Demo Credentials

| Role  | Username        | Password    |
|-------|-----------------|-------------|
| Admin | `pramod_admin`  | `Admin@123` |
| Admin | `officer_raj`   | `Officer@456` |
| User  | `user_priya`    | `User@789`  |
| User  | `user_amit`     | `User@789`  |

---

## 📁 Project Structure

```
.
├── Home.py                         # Main dashboard (login + alerts)
├── mobile_app.py                   # Public sighting submission portal
├── login_config.yml                # User credentials (bcrypt hashed)
├── generate_passwords.py           # Helper to generate hashed passwords
├── requirements.txt
└── pages/
    ├── 1_Register_Case.py          # Admin: register missing person
    ├── 2_Face_Matching.py          # AI face scan + found alert
    ├── 3_Case_Management.py        # View/filter/update all cases
    └── helper/
        ├── data_models.py          # SQLModel ORM models
        ├── db_queries.py           # All database operations
        ├── utils.py                # Face mesh + similarity functions
        └── streamlit_helpers.py    # Auth decorators (require_login, require_admin)
```

---

## 🧠 How Face Matching Works

```
Upload Photo
     │
     ▼
MediaPipe Face Mesh
(478 landmarks extracted)
     │
     ▼
Normalise landmarks
(nose tip = origin, inter-ocular distance = 1.0)
     │
     ▼
For each registered missing person (NF):
    score = 0.6 × cosine_similarity + 0.4 × (1/(1+euclidean_distance))
     │
     ▼
Best score ≥ threshold (default 60%)?
    YES → 🎉 MATCH FOUND → Alert fired → DB updated
    NO  → ❌ No match
```

---

## 🔒 Security Notes

- Passwords are **bcrypt hashed** (12 rounds) — never stored in plaintext
- Session cookies are signed with a secret key
- Route protection via `@require_login` / `@require_admin` decorators
- Admin actions (mark found, bulk scan) are role-gated in both UI and backend
