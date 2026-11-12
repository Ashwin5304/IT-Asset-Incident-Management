
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from sqlalchemy import text, or_

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from app import db

from app.models import (
    User,
    Asset,
    Incident,
    IncidentHistory,
    IncidentComment,
    IncidentFeedback,
    TechnicianAssistanceRequest
)


main = Blueprint("main", __name__)


# ---------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------

def generate_incident_number():
    last_incident = Incident.query.order_by(
        Incident.id.desc()
    ).first()

    next_id = last_incident.id + 1 if last_incident else 1

    return f"INC-{next_id:05d}"


# ---------------------------------------------------------------------
# HOME AND DATABASE
# ---------------------------------------------------------------------

@main.route("/")
def index():
    return render_template("index.html")


@main.route("/db-test")
def db_test():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()

        if result == 1:
            return "Database connection successful!"

        return "Database connection failed.", 500

    except Exception as e:
        return f"Database connection failed: {e}", 500


# ---------------------------------------------------------------------
# LOGIN AND LOGOUT
# ---------------------------------------------------------------------

@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("main.dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ---------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------

@main.route("/dashboard")
@login_required
def dashboard():

    if current_user.role == "ADMIN":

        total_users = User.query.count()
        total_assets = Asset.query.count()
        total_incidents = Incident.query.count()

        open_incidents = Incident.query.filter_by(
            status="OPEN"
        ).count()

        assigned_incidents = Incident.query.filter_by(
            status="ASSIGNED"
        ).count()

        in_progress_incidents = Incident.query.filter_by(
            status="IN_PROGRESS"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            status="RESOLVED"
        ).count()

        closed_incidents = Incident.query.filter_by(
            status="CLOSED"
        ).count()

        return render_template(
            "dashboard.html",
            total_users=total_users,
            total_assets=total_assets,
            total_incidents=total_incidents,
            open_incidents=open_incidents,
            assigned_incidents=assigned_incidents,
            in_progress_incidents=in_progress_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents
        )

    elif current_user.role == "TECHNICIAN":

        assigned_incidents = Incident.query.filter_by(
            assigned_to=current_user.id
        ).count()

        open_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="ASSIGNED"
        ).count()

        in_progress_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="IN_PROGRESS"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="RESOLVED"
        ).count()

        closed_incidents = Incident.query.filter_by(
            assigned_to=current_user.id,
            status="CLOSED"
        ).count()

        supporting_incidents = db.session.query(
            TechnicianAssistanceRequest.incident_id
        ).filter_by(
            supporting_technician_id=current_user.id,
            status="ASSIGNED"
        ).distinct().count()

        return render_template(
            "dashboard.html",
            assigned_incidents=assigned_incidents,
            open_incidents=open_incidents,
            in_progress_incidents=in_progress_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents,
            supporting_incidents=supporting_incidents
        )

    else:

        my_assets = Asset.query.filter_by(
            assigned_to=current_user.id
        ).count()

        my_incidents = Incident.query.filter_by(
            reported_by=current_user.id
        ).count()

        open_incidents = Incident.query.filter_by(
            reported_by=current_user.id,
            status="OPEN"
        ).count()

        resolved_incidents = Incident.query.filter_by(
            reported_by=current_user.id,
            status="RESOLVED"
        ).count()

        closed_incidents = Incident.query.filter_by(
            reported_by=current_user.id,
            status="CLOSED"
        ).count()

        return render_template(
            "dashboard.html",
            my_assets=my_assets,
            my_incidents=my_incidents,
            open_incidents=open_incidents,
            resolved_incidents=resolved_incidents,
            closed_incidents=closed_incidents
        )


# ---------------------------------------------------------------------
# ADMIN ANALYTICS
# ---------------------------------------------------------------------

@main.route("/analytics")
@login_required
def analytics():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    open_count = Incident.query.filter_by(status="OPEN").count()
    assigned_count = Incident.query.filter_by(status="ASSIGNED").count()
    in_progress_count = Incident.query.filter_by(status="IN_PROGRESS").count()
    resolved_count = Incident.query.filter_by(status="RESOLVED").count()
    closed_count = Incident.query.filter_by(status="CLOSED").count()

    critical_count = Incident.query.filter_by(priority="CRITICAL").count()
    high_count = Incident.query.filter_by(priority="HIGH").count()
    medium_count = Incident.query.filter_by(priority="MEDIUM").count()
    low_count = Incident.query.filter_by(priority="LOW").count()

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(User.name).all()

    technician_stats = []

    for technician in technicians:

        assigned = Incident.query.filter_by(
            assigned_to=technician.id
        ).count()

        active = Incident.query.filter(
            Incident.assigned_to == technician.id,
            Incident.status.in_(["ASSIGNED", "IN_PROGRESS", "REOPENED"])
        ).count()

        resolved = Incident.query.filter_by(
            assigned_to=technician.id,
            status="RESOLVED"
        ).count()

        closed = Incident.query.filter_by(
            assigned_to=technician.id,
            status="CLOSED"
        ).count()

        technician_stats.append({
            "name": technician.name,
            "assigned": assigned,
            "active": active,
            "resolved": resolved,
            "closed": closed
        })

    recent_incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).limit(10).all()

    return render_template(
        "analytics.html",
        open_count=open_count,
        assigned_count=assigned_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        closed_count=closed_count,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        technician_stats=technician_stats,
        recent_incidents=recent_incidents
    )


# ---------------------------------------------------------------------
# USER MANAGEMENT
# ---------------------------------------------------------------------

@main.route("/users")
@login_required
def users():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    users = User.query.order_by(User.id).all()

    return render_template("users.html", users=users)


@main.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if not name or not email or not password:
            return render_template(
                "add_user.html",
                error="Please complete all required fields."
            )

        if role not in ["EMPLOYEE", "TECHNICIAN", "ADMIN"]:
            return render_template(
                "add_user.html",
                error="Invalid user role."
            )

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return render_template(
                "add_user.html",
                error="A user with this email already exists."
            )

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("main.users"))

    return render_template("add_user.html")


# ---------------------------------------------------------------------
# ASSET MANAGEMENT
# ---------------------------------------------------------------------

@main.route("/assets")
@login_required
def assets():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    assets = Asset.query.order_by(Asset.id).all()
    users = User.query.all()

    users_by_id = {
        user.id: user for user in users
    }

    return render_template(
        "assets.html",
        assets=assets,
        users_by_id=users_by_id
    )


@main.route("/assets/add", methods=["GET", "POST"])
@login_required
def add_asset():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    employees = User.query.filter_by(
        role="EMPLOYEE"
    ).order_by(User.name).all()

    if request.method == "POST":

        asset_tag = request.form.get("asset_tag")
        name = request.form.get("name")
        asset_type = request.form.get("asset_type")
        serial_number = request.form.get("serial_number")
        department = request.form.get("department")
        location = request.form.get("location")
        status = request.form.get("status")
        purchase_date = request.form.get("purchase_date")
        warranty_expiry = request.form.get("warranty_expiry")
        assigned_to = request.form.get("assigned_to")

        existing_asset = Asset.query.filter_by(
            asset_tag=asset_tag
        ).first()

        if existing_asset:
            return render_template(
                "add_asset.html",
                error="An asset with this asset tag already exists.",
                employees=employees
            )

        if serial_number:
            existing_serial = Asset.query.filter_by(
                serial_number=serial_number
            ).first()

            if existing_serial:
                return render_template(
                    "add_asset.html",
                    error="An asset with this serial number already exists.",
                    employees=employees
                )

        assigned_user_id = None

        if assigned_to:
            try:
                assigned_to = int(assigned_to)
            except (ValueError, TypeError):
                return render_template(
                    "add_asset.html",
                    error="Invalid employee selected.",
                    employees=employees
                )

            assigned_user = User.query.filter_by(
                id=assigned_to,
                role="EMPLOYEE"
            ).first()

            if not assigned_user:
                return render_template(
                    "add_asset.html",
                    error="Invalid employee selected.",
                    employees=employees
                )

            assigned_user_id = assigned_user.id

        new_asset = Asset(
            asset_tag=asset_tag,
            name=name,
            asset_type=asset_type,
            serial_number=serial_number or None,
            department=department or None,
            location=location or None,
            assigned_to=assigned_user_id,
            status=status,
            purchase_date=purchase_date or None,
            warranty_expiry=warranty_expiry or None
        )

        db.session.add(new_asset)
        db.session.commit()

        return redirect(url_for("main.assets"))

    return render_template(
        "add_asset.html",
        employees=employees
    )


@main.route("/my-assets")
@login_required
def my_assets():

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    assets = Asset.query.filter_by(
        assigned_to=current_user.id
    ).all()

    return render_template("my_assets.html", assets=assets)


# ---------------------------------------------------------------------
# EMPLOYEE INCIDENT MANAGEMENT
# ---------------------------------------------------------------------

@main.route("/my-incidents")
@login_required
def my_incidents():

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    incidents = Incident.query.filter_by(
        reported_by=current_user.id
    ).order_by(
        Incident.created_at.desc()
    ).all()

    return render_template(
        "my_incidents.html",
        incidents=incidents
    )


@main.route("/incidents/report", methods=["GET", "POST"])
@login_required
def report_incident():

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    assets = Asset.query.filter_by(
        assigned_to=current_user.id
    ).order_by(Asset.name).all()

    if request.method == "POST":

        asset_id = request.form.get("asset_id")
        title = request.form.get("title")
        description = request.form.get("description")
        priority = request.form.get("priority")

        try:
            asset_id = int(asset_id)
        except (ValueError, TypeError):
            asset_id = None

        asset = Asset.query.filter_by(
            id=asset_id,
            assigned_to=current_user.id
        ).first()

        if not asset:
            return render_template(
                "report_incident.html",
                assets=assets,
                error="Invalid asset selected."
            )

        incident = Incident(
            incident_number=generate_incident_number(),
            title=title,
            description=description,
            asset_id=asset.id,
            reported_by=current_user.id,
            priority=priority,
            status="OPEN"
        )

        db.session.add(incident)
        db.session.commit()

        return redirect(url_for("main.my_incidents"))

    return render_template(
        "report_incident.html",
        assets=assets
    )


# ---------------------------------------------------------------------
# ADMIN INCIDENT MANAGEMENT
# ---------------------------------------------------------------------

@main.route("/incidents")
@login_required
def incidents():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(User.name).all()

    return render_template(
        "incidents.html",
        incidents=incidents,
        technicians=technicians
    )


@main.route(
    "/incidents/<int:incident_id>/close",
    methods=["POST"]
)
@login_required
def close_incident(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    return (
        "The reporting employee must confirm the resolution "
        "through the feedback page.",
        403
    )


# ---------------------------------------------------------------------
# EMPLOYEE INCIDENT FEEDBACK
# ---------------------------------------------------------------------

@main.route(
    "/incidents/<int:incident_id>/feedback",
    methods=["GET", "POST"]
)
@login_required
def submit_incident_feedback(incident_id):

    if current_user.role != "EMPLOYEE":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    # Only the employee who originally reported this incident can respond.
    if incident.reported_by != current_user.id:
        return "You cannot submit feedback for this incident.", 403

    if incident.status != "RESOLVED":
        return "Feedback is available only for resolved incidents.", 400

    # Allow one feedback submission for each resolution cycle.
    if incident.resolved_at:
        previous_feedback = IncidentFeedback.query.filter(
            IncidentFeedback.incident_id == incident.id,
            IncidentFeedback.employee_id == current_user.id,
            IncidentFeedback.created_at >= incident.resolved_at
        ).first()

        if previous_feedback:
            return "Feedback has already been submitted for this resolution.", 400

    if request.method == "POST":
        satisfaction = request.form.get("is_satisfied")
        is_resolved = request.form.get("is_resolved")
        is_working = request.form.get("is_working")
        comments = request.form.get("comments", "").strip()

        if satisfaction not in ["yes", "no"]:
            return "Please tell us whether you are satisfied with the technician's work.", 400

        if is_resolved not in ["yes", "no"]:
            return "Please confirm whether the issue is fixed.", 400

        if is_working not in ["yes", "no"]:
            return "Please confirm whether the asset is working.", 400

        satisfied = satisfaction == "yes"
        resolved = is_resolved == "yes"
        working = is_working == "yes"

        # If anything is unsatisfactory, require an explanation before reopening.
        if not (satisfied and resolved and working) and not comments:
            return "Please explain what is still wrong so the technician can follow up.", 400

        feedback = IncidentFeedback(
            incident_id=incident.id,
            employee_id=current_user.id,
            is_satisfied=satisfied,
            is_resolved=resolved,
            is_working=working,
            comments=comments or None
        )

        old_status = incident.status

        if satisfied and resolved and working:
            incident.status = "CLOSED"
            history_comment = (
                "Employee confirmed satisfaction with the technician's work, "
                "confirmed that the issue is fixed and the asset is working. "
                f"Feedback: {comments or 'No additional comments.'}"
            )
        else:
            incident.status = "REOPENED"
            # Clear the current resolution timestamp so the next resolution
            # can receive a new feedback submission. Keep the previous
            # resolution text and feedback record as history.
            incident.resolved_at = None
            history_comment = (
                "Employee was not fully satisfied and/or reported that the "
                "issue or asset is still not working correctly. Incident reopened. "
                f"Feedback: {comments}"
            )

        history = IncidentHistory(
            incident_id=incident.id,
            changed_by=current_user.id,
            old_status=old_status,
            new_status=incident.status,
            comment=history_comment
        )

        db.session.add(feedback)
        db.session.add(history)
        db.session.commit()

        flash(
            "Thank you for your feedback. The incident has been closed."
            if incident.status == "CLOSED"
            else "Thank you. The incident has been reopened for further work.",
            "success" if incident.status == "CLOSED" else "warning"
        )

        return redirect(url_for("main.my_incidents"))

    return render_template(
        "incident_feedback.html",
        incident=incident
    )


# ---------------------------------------------------------------------
# ADMIN INCIDENT DETAILS AND ASSIGNMENT
# ---------------------------------------------------------------------

@main.route("/incidents/<int:incident_id>")
@login_required
def incident_details(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(User.name).all()

    return render_template(
        "incident_details.html",
        incident=incident,
        technicians=technicians
    )


@main.route(
    "/incidents/<int:incident_id>/assign",
    methods=["POST"]
)
@login_required
def assign_incident(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    technician_id = request.form.get("technician_id")

    try:
        technician_id = int(technician_id)
    except (ValueError, TypeError):
        return "Invalid technician selected.", 400

    technician = User.query.filter_by(
        id=technician_id,
        role="TECHNICIAN"
    ).first()

    if not technician:
        return "Invalid technician selected.", 400

    old_status = incident.status
    incident.assigned_to = technician.id

    if incident.status in ["OPEN", "REOPENED"]:
        incident.status = "ASSIGNED"

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=old_status,
        new_status=incident.status,
        comment=f"Incident assigned to {technician.name}"
    )

    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.incident_details",
            incident_id=incident.id
        )
    )


# ---------------------------------------------------------------------
# TECHNICIAN INCIDENT LIST
# ---------------------------------------------------------------------


@main.route("/technician/incidents")
@login_required
def technician_incidents():

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    supported_incident_ids = db.session.query(
        TechnicianAssistanceRequest.incident_id
    ).filter(
        TechnicianAssistanceRequest.supporting_technician_id == current_user.id,
        TechnicianAssistanceRequest.status.in_(["ASSIGNED", "COMPLETED"])
    )

    incidents = Incident.query.filter(
        or_(
            Incident.assigned_to == current_user.id,
            Incident.id.in_(supported_incident_ids)
        )
    ).order_by(
        Incident.created_at.desc()
    ).all()

    return render_template(
        "technician_incidents.html",
        incidents=incidents
    )


# ---------------------------------------------------------------------
# TECHNICIAN INCIDENT DETAILS
# ---------------------------------------------------------------------


@main.route("/technician/incidents/<int:incident_id>")
@login_required
def technician_incident_details(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    is_primary_technician = (
        incident.assigned_to == current_user.id
    )

    support_request = TechnicianAssistanceRequest.query.filter(
        TechnicianAssistanceRequest.incident_id == incident.id,
        TechnicianAssistanceRequest.supporting_technician_id == current_user.id,
        TechnicianAssistanceRequest.status.in_(["ASSIGNED", "COMPLETED"])
    ).order_by(
        TechnicianAssistanceRequest.created_at.desc()
    ).first()

    is_supporting_technician = support_request is not None

    if not is_primary_technician and not is_supporting_technician:
        return "You are not assigned to this incident.", 403

    latest_assistance_request = TechnicianAssistanceRequest.query.filter_by(
        incident_id=incident.id
    ).order_by(
        TechnicianAssistanceRequest.created_at.desc()
    ).first()

    return render_template(
        "technician_incident_details.html",
        incident=incident,
        is_primary_technician=is_primary_technician,
        is_supporting_technician=is_supporting_technician,
        support_request=support_request,
        latest_assistance_request=latest_assistance_request
    )

# ---------------------------------------------------------------------
# PRIMARY TECHNICIAN UPDATES INCIDENT STATUS
# ---------------------------------------------------------------------

@main.route(
    "/technician/incidents/<int:incident_id>/update",
    methods=["POST"]
)
@login_required
def update_incident_status(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    # Only the primary technician can update the incident status.
    if incident.assigned_to != current_user.id:
        return (
            "Only the primary assigned technician can update "
            "the incident status or resolve it.",
            403
        )

    new_status = request.form.get("status")
    resolution = request.form.get("resolution", "").strip()

    if new_status == "IN_PROGRESS":

        if incident.status not in ["ASSIGNED", "REOPENED"]:
            return "This incident cannot be moved to IN_PROGRESS.", 400

    elif new_status == "RESOLVED":

        if incident.status != "IN_PROGRESS":
            return "Only incidents in progress can be resolved.", 400

        if not resolution:
            return "Please enter resolution details.", 400

    else:
        return "Invalid status.", 400

    old_status = incident.status
    incident.status = new_status

    if resolution:
        incident.resolution = resolution

    if new_status == "RESOLVED":
        incident.resolved_at = datetime.utcnow()

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=old_status,
        new_status=new_status,
        comment=resolution or "Work started on incident."
    )

    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )


# ---------------------------------------------------------------------
# TECHNICIAN COMMENTS
# PRIMARY AND SUPPORTING TECHNICIANS CAN COMMENT
# ---------------------------------------------------------------------


@main.route(
    "/technician/incidents/<int:incident_id>/comment",
    methods=["POST"]
)
@login_required
def add_incident_comment(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    is_primary_technician = (
        incident.assigned_to == current_user.id
    )

    is_supporting_technician = TechnicianAssistanceRequest.query.filter(
        TechnicianAssistanceRequest.incident_id == incident.id,
        TechnicianAssistanceRequest.supporting_technician_id == current_user.id,
        TechnicianAssistanceRequest.status.in_(["ASSIGNED", "COMPLETED"])
    ).first() is not None

    if not is_primary_technician and not is_supporting_technician:
        return "You are not assigned to this incident.", 403

    comment_text = request.form.get("comment", "").strip()

    if not comment_text:
        return "Comment cannot be empty.", 400

    comment = IncidentComment(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )


# ---------------------------------------------------------------------
# ADMIN COMMENTS
# ---------------------------------------------------------------------

@main.route(
    "/incidents/<int:incident_id>/comment",
    methods=["POST"]
)
@login_required
def admin_add_incident_comment(incident_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    comment_text = request.form.get("comment", "").strip()

    if not comment_text:
        return "Comment cannot be empty.", 400

    comment = IncidentComment(
        incident_id=incident.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(
        url_for(
            "main.incident_details",
            incident_id=incident.id
        )
    )


# ---------------------------------------------------------------------
# TECHNICIAN ASSISTANCE REQUEST
# PRIMARY TECHNICIAN REQUESTS AN ADDITIONAL TECHNICIAN
# ---------------------------------------------------------------------

@main.route(
    "/technician/incidents/<int:incident_id>/request-assistance",
    methods=["POST"]
)
@login_required
def request_incident_assistance(incident_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    incident = Incident.query.get_or_404(incident_id)

    # Only the primary technician may request assistance.
    if incident.assigned_to != current_user.id:
        return "Only the primary technician can request assistance.", 403

    if incident.status != "IN_PROGRESS":
        return (
            "Assistance can only be requested for an incident in progress.",
            400
        )

    reason = request.form.get("reason", "").strip()

    if not reason:
        return "Please explain why additional assistance is needed.", 400

    # Prevent multiple pending or active assistance requests.
    active_request = TechnicianAssistanceRequest.query.filter(
        TechnicianAssistanceRequest.incident_id == incident.id,
        TechnicianAssistanceRequest.status.in_(["PENDING", "ASSIGNED"])
    ).first()

    if active_request:
        return (
            "There is already an active assistance request for this incident.",
            400
        )

    assistance = TechnicianAssistanceRequest(
        incident_id=incident.id,
        requested_by_id=current_user.id,
        reason=reason,
        status="PENDING"
    )

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=incident.status,
        new_status=incident.status,
        comment=(
            f"{current_user.name} requested an additional technician. "
            f"Reason: {reason}"
        )
    )

    db.session.add(assistance)
    db.session.add(history)
    db.session.commit()

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )


# ---------------------------------------------------------------------
# ADMIN ASSISTANCE REQUEST LIST
# ---------------------------------------------------------------------

@main.route("/admin/assistance-requests")
@login_required
def assistance_requests():

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    assistance_requests = TechnicianAssistanceRequest.query.order_by(
        TechnicianAssistanceRequest.created_at.desc()
    ).all()

    technicians = User.query.filter_by(
        role="TECHNICIAN"
    ).order_by(User.name).all()

    return render_template(
        "admin_assistance_requests.html",
        assistance_requests=assistance_requests,
        technicians=technicians
    )


# ---------------------------------------------------------------------
# ADMIN ASSIGNS SUPPORTING TECHNICIAN
# ---------------------------------------------------------------------

@main.route(
    "/admin/assistance-requests/<int:assistance_id>/assign",
    methods=["POST"]
)
@login_required
def assign_supporting_technician(assistance_id):

    if current_user.role != "ADMIN":
        return "Access denied.", 403

    assistance = TechnicianAssistanceRequest.query.get_or_404(
        assistance_id
    )

    if assistance.status != "PENDING":
        return "This assistance request is no longer pending.", 400

    technician_id = request.form.get("technician_id")

    try:
        technician_id = int(technician_id)
    except (TypeError, ValueError):
        return "Please select a valid technician.", 400

    technician = User.query.filter_by(
        id=technician_id,
        role="TECHNICIAN"
    ).first()

    if not technician:
        return "Invalid technician selected.", 400

    # Do not allow the primary technician to support their own incident.
    if technician.id == assistance.requested_by_id:
        return (
            "The primary technician cannot be assigned as their own support.",
            400
        )

    incident = assistance.incident

    if technician.id == incident.assigned_to:
        return (
            "The primary assigned technician cannot also be the supporting technician.",
            400
        )

    assistance.supporting_technician_id = technician.id
    assistance.assigned_by_id = current_user.id
    assistance.admin_note = (
        request.form.get("admin_note", "").strip() or None
    )
    assistance.status = "ASSIGNED"

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=incident.status,
        new_status=incident.status,
        comment=(
            f"Admin assigned {technician.name} as a supporting "
            f"technician for this incident."
        )
    )

    db.session.add(history)
    db.session.commit()

    return redirect(url_for("main.assistance_requests"))


# ---------------------------------------------------------------------
# SUPPORTING TECHNICIAN COMPLETES ASSISTANCE
# ---------------------------------------------------------------------


@main.route(
    "/technician/assistance/<int:assistance_id>/complete",
    methods=["POST"]
)
@login_required
def complete_technician_assistance(assistance_id):

    if current_user.role != "TECHNICIAN":
        return "Access denied.", 403

    assistance = TechnicianAssistanceRequest.query.get_or_404(
        assistance_id
    )

    if assistance.supporting_technician_id != current_user.id:
        return "You are not assigned to this assistance request.", 403

    if assistance.status != "ASSIGNED":
        return "This assistance request is already completed or inactive.", 400

    assistance.status = "COMPLETED"
    assistance.completed_at = datetime.utcnow()

    incident = assistance.incident

    history = IncidentHistory(
        incident_id=incident.id,
        changed_by=current_user.id,
        old_status=incident.status,
        new_status=incident.status,
        comment=(
            f"{current_user.name} completed their supporting work. "
            "The primary technician remains responsible for resolving the incident."
        )
    )

    db.session.add(history)
    db.session.commit()

    flash(
        "Your supporting work has been marked as completed.",
        "success"
    )

    return redirect(
        url_for(
            "main.technician_incident_details",
            incident_id=incident.id
        )
    )

