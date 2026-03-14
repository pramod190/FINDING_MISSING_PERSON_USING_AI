"""
Database query helpers for the Missing Persons AI System.

Key improvements over v1:
- Admin vs User scoped queries
- Found-person alert tracking
- Match confidence stored against submissions
- Recent-activity feed
- Bulk-match helper for CCTV scanning
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

from sqlmodel import Session, SQLModel, create_engine, select, col

from pages.helper.data_models import (
    FoundAlert,
    MissingPerson,
    PublicSubmissions,
    UserActivity,
)

# ── Database setup ─────────────────────────────────────────────────────────────
DB_PATH = "sqlite_database.db"
engine  = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db():
    """Create all tables on first run."""
    SQLModel.metadata.create_all(engine)


init_db()


# ─────────────────────────────────────────────────────────────────────────────
# MISSING PERSON REGISTRATION
# ─────────────────────────────────────────────────────────────────────────────

def register_missing_person(person: MissingPerson) -> MissingPerson:
    """Insert a new missing person record."""
    with Session(engine) as session:
        session.add(person)
        session.commit()
        session.refresh(person)

        # Log activity
        _log_activity(session, person.registered_by or "system", "registered", person.id)
        session.commit()
    return person


def get_all_missing_persons(status: Optional[str] = None) -> List[MissingPerson]:
    """Return all missing persons, optionally filtered by status."""
    with Session(engine) as session:
        stmt = select(MissingPerson)
        if status:
            stmt = stmt.where(MissingPerson.status == status)
        stmt = stmt.order_by(col(MissingPerson.created_at).desc())
        return session.exec(stmt).all()


def get_missing_person_by_id(person_id: str) -> Optional[MissingPerson]:
    with Session(engine) as session:
        return session.get(MissingPerson, person_id)


# ─────────────────────────────────────────────────────────────────────────────
# CASE COUNTS (admin vs user scoped)
# ─────────────────────────────────────────────────────────────────────────────

def get_registered_cases_count(
    registered_by: Optional[str],
    status: str,
    admin: bool = False,
) -> list:
    """
    Return cases filtered by status.
    - admin=True  → all cases regardless of who registered them
    - admin=False → only cases registered by `registered_by`
    """
    with Session(engine) as session:
        stmt = select(MissingPerson).where(MissingPerson.status == status)
        if not admin and registered_by:
            stmt = stmt.where(MissingPerson.registered_by == registered_by)
        return session.exec(stmt).all()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC SUBMISSIONS
# ─────────────────────────────────────────────────────────────────────────────

def new_public_case(submission: PublicSubmissions) -> PublicSubmissions:
    """Save a new public sighting submission."""
    with Session(engine) as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
    return submission


def get_all_public_submissions(status: Optional[str] = None) -> List[PublicSubmissions]:
    with Session(engine) as session:
        stmt = select(PublicSubmissions)
        if status:
            stmt = stmt.where(PublicSubmissions.status == status)
        stmt = stmt.order_by(col(PublicSubmissions.created_at).desc())
        return session.exec(stmt).all()


# ─────────────────────────────────────────────────────────────────────────────
# FOUND-PERSON ALERTS
# ─────────────────────────────────────────────────────────────────────────────

def mark_person_found(
    person_id: str,
    found_by: str,
    found_location: str,
    match_confidence: float = 1.0,
) -> Optional[MissingPerson]:
    """
    Mark a missing person as found and create an alert record.
    Returns the updated MissingPerson or None if not found.
    """
    with Session(engine) as session:
        person = session.get(MissingPerson, person_id)
        if not person:
            return None

        person.status         = "F"
        person.found_by       = found_by
        person.found_location = found_location
        person.found_at       = datetime.utcnow()
        person.updated_at     = datetime.utcnow()
        person.alert_sent     = False           # will be flipped after display

        session.add(person)

        # Create alert record
        alert = FoundAlert(
            missing_person_id=person_id,
            found_by_user=found_by,
            match_confidence=match_confidence,
        )
        session.add(alert)

        # Log activity
        _log_activity(session, found_by, "found", person_id,
                      f"Found at {found_location} (confidence: {match_confidence:.1%})")

        session.commit()
        session.refresh(person)
    return person


def get_recently_found_cases(
    submitted_by: Optional[str] = None,
    hours: int = 24,
) -> List[MissingPerson]:
    """
    Return persons found in the last `hours` hours whose alert
    has not been dismissed. Optionally scoped to a specific submitter.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with Session(engine) as session:
        stmt = (
            select(MissingPerson)
            .where(MissingPerson.status == "F")
            .where(MissingPerson.alert_sent == False)
            .where(col(MissingPerson.found_at) >= cutoff)
        )
        if submitted_by:
            stmt = stmt.where(MissingPerson.registered_by == submitted_by)

        results = session.exec(stmt).all()

        # Mark alerts as sent so they don't reappear
        for person in results:
            person.alert_sent = True
            session.add(person)
        session.commit()

    return results


def dismiss_alert(person_id: str):
    """Mark all undismissed alerts for this person as dismissed."""
    with Session(engine) as session:
        alerts = session.exec(
            select(FoundAlert)
            .where(FoundAlert.missing_person_id == person_id)
            .where(FoundAlert.alert_dismissed == False)
        ).all()
        for a in alerts:
            a.alert_dismissed = True
            session.add(a)
        session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# FACE MATCHING
# ─────────────────────────────────────────────────────────────────────────────

def save_match_result(
    submission_id: str,
    matched_person_id: str,
    confidence: float,
):
    """Record a face-match result against a public submission."""
    with Session(engine) as session:
        sub = session.get(PublicSubmissions, submission_id)
        if sub:
            sub.matched_person_id = matched_person_id
            sub.match_confidence  = confidence
            sub.status            = "F" if confidence >= 0.6 else sub.status
            session.add(sub)
            session.commit()


def get_all_face_meshes_from_db() -> List[dict]:
    """
    Return list of dicts with id + face_mesh for every registered
    missing person still marked NF. Used for bulk scanning.
    """
    with Session(engine) as session:
        persons = session.exec(
            select(MissingPerson).where(MissingPerson.status == "NF")
        ).all()
        results = []
        for p in persons:
            if p.face_mesh:
                try:
                    mesh = json.loads(p.face_mesh)
                    results.append({"id": p.id, "name": p.name, "mesh": mesh})
                except json.JSONDecodeError:
                    pass
        return results


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVITY FEED
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_activity(limit: int = 10) -> List[dict]:
    """Return recent activity entries as plain dicts for display."""
    with Session(engine) as session:
        activities = session.exec(
            select(UserActivity)
            .order_by(col(UserActivity.created_at).desc())
            .limit(limit)
        ).all()

        result = []
        for a in activities:
            person = session.get(MissingPerson, a.case_id) if a.case_id else None
            result.append({
                "name":     getattr(person, "name", "Unknown"),
                "location": getattr(person, "found_location", getattr(person, "location", "N/A")),
                "status":   getattr(person, "status", "NF"),
                "action":   a.action,
                "created_at": a.created_at.strftime("%d %b %Y, %I:%M %p") if a.created_at else "",
            })
        return result


def _log_activity(session: Session, username: str, action: str,
                  case_id: Optional[str] = None, notes: Optional[str] = None):
    """Internal helper — always called within an open session."""
    activity = UserActivity(
        username=username,
        action=action,
        case_id=case_id,
        notes=notes,
    )
    session.add(activity)
