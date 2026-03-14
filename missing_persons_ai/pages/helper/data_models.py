"""
Data models for the Missing Persons AI System.
Uses SQLModel for type-safe ORM with SQLite.
"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class MissingPerson(SQLModel, table=True):
    """Core missing person registration record."""
    __tablename__ = "missing_persons"

    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None                # M / F / Other
    location: Optional[str] = None              # Last seen location
    description: Optional[str] = None
    birth_marks: Optional[str] = None
    face_mesh: Optional[str] = None             # JSON serialized landmarks
    image_path: Optional[str] = None
    status: str = Field(default="NF")           # NF = Not Found, F = Found
    registered_by: Optional[str] = None         # Officer/Admin username
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Found-person details (populated when status → F)
    found_location: Optional[str] = None
    found_by: Optional[str] = None
    found_at: Optional[datetime] = None
    alert_sent: bool = Field(default=False)     # Track if alert was fired


class PublicSubmissions(SQLModel, table=True):
    """Sighting submitted by general public via mobile/web portal."""
    __tablename__ = "public_submissions"

    id: Optional[str] = Field(default=None, primary_key=True)
    submitted_by: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    face_mesh: Optional[str] = None
    birth_marks: Optional[str] = None
    status: str = Field(default="NF")
    image_path: Optional[str] = None
    matched_person_id: Optional[str] = None     # FK → MissingPerson.id
    match_confidence: Optional[float] = None    # 0.0 – 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FoundAlert(SQLModel, table=True):
    """Audit log of found-person alerts so they are shown once per session."""
    __tablename__ = "found_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    missing_person_id: str
    found_by_user: str
    found_at: datetime = Field(default_factory=datetime.utcnow)
    alert_dismissed: bool = Field(default=False)
    match_confidence: Optional[float] = None


class UserActivity(SQLModel, table=True):
    """Track user actions for the activity feed."""
    __tablename__ = "user_activity"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    action: str                                 # "registered", "matched", "found"
    case_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
