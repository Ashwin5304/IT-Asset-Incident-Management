
from datetime import datetime
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="EMPLOYEE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reported_incidents = db.relationship(
        "Incident",
        foreign_keys="Incident.reported_by",
        backref="reporter",
        lazy=True
    )

    assigned_incidents = db.relationship(
        "Incident",
        foreign_keys="Incident.assigned_to",
        backref="technician",
        lazy=True
    )

    requested_assistance = db.relationship(
        "TechnicianAssistanceRequest",
        foreign_keys="TechnicianAssistanceRequest.requested_by_id",
        back_populates="requested_by",
        lazy=True
    )

    supporting_assistance = db.relationship(
        "TechnicianAssistanceRequest",
        foreign_keys="TechnicianAssistanceRequest.supporting_technician_id",
        back_populates="supporting_technician",
        lazy=True
    )


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    serial_number = db.Column(db.String(100), unique=True)
    department = db.Column(db.String(100))
    location = db.Column(db.String(100))
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(30), default="ACTIVE")
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    incidents = db.relationship(
        "Incident",
        backref="asset",
        lazy=True
    )


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)

    incident_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False
    )

    reported_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    priority = db.Column(
        db.String(20),
        nullable=False,
        default="MEDIUM"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="OPEN"
    )

    resolution = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    resolved_at = db.Column(db.DateTime)

    comments = db.relationship(
        "IncidentComment",
        backref="incident",
        lazy=True,
        cascade="all, delete-orphan"
    )

    history = db.relationship(
        "IncidentHistory",
        backref="incident",
        lazy=True,
        cascade="all, delete-orphan"
    )

    assistance_requests = db.relationship(
        "TechnicianAssistanceRequest",
        back_populates="incident",
        lazy=True,
        cascade="all, delete-orphan"
    )


class IncidentComment(db.Model):
    __tablename__ = "incident_comments"

    id = db.Column(db.Integer, primary_key=True)

    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incidents.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    comment = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id]
    )


class IncidentHistory(db.Model):
    __tablename__ = "incident_history"

    id = db.Column(db.Integer, primary_key=True)

    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incidents.id"),
        nullable=False
    )

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30))
    comment = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class IncidentFeedback(db.Model):
    __tablename__ = "incident_feedback"

    id = db.Column(db.Integer, primary_key=True)

    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incidents.id"),
        nullable=False
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Legacy column retained as nullable so existing databases remain compatible.
    # The application no longer collects or uses ratings.
    rating = db.Column(db.Integer, nullable=True)
    is_satisfied = db.Column(db.Boolean, nullable=False, default=False)
    is_resolved = db.Column(db.Boolean, nullable=False)
    is_working = db.Column(db.Boolean, nullable=False)
    comments = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    incident = db.relationship(
        "Incident",
        backref=db.backref("feedback", lazy=True)
    )

    employee = db.relationship(
        "User",
        foreign_keys=[employee_id]
    )


class TechnicianAssistanceRequest(db.Model):
    __tablename__ = "technician_assistance_requests"

    id = db.Column(db.Integer, primary_key=True)

    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incidents.id"),
        nullable=False
    )

    requested_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    supporting_technician_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    assigned_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    admin_note = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    completed_at = db.Column(db.DateTime)

    incident = db.relationship(
        "Incident",
        back_populates="assistance_requests"
    )

    requested_by = db.relationship(
        "User",
        foreign_keys=[requested_by_id],
        back_populates="requested_assistance"
    )

    supporting_technician = db.relationship(
        "User",
        foreign_keys=[supporting_technician_id],
        back_populates="supporting_assistance"
    )

    assigned_by = db.relationship(
        "User",
        foreign_keys=[assigned_by_id]
    )
