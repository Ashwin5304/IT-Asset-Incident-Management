from app import db
from app.models import User, Asset, Incident


def login(client, email, password):

    return client.post(
        "/login",
        data={
            "email": email,
            "password": password
        },
        follow_redirects=True
    )


def test_employee_can_report_incident(
    client,
    app
):

    login(
        client,
        "employee@test.local",
        "Employee@123"
    )

    response = client.post(
        "/incidents/report",
        data={
            "asset_id": "1",
            "title": "Test laptop problem",
            "description": "Laptop does not start.",
            "priority": "HIGH"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"INC-00001" in response.data

    with app.app_context():

        incident = Incident.query.first()

        assert incident is not None
        assert incident.title == "Test laptop problem"
        assert incident.status == "OPEN"
        assert incident.priority == "HIGH"


def test_admin_can_assign_incident(
    client,
    app
):

    with app.app_context():

        employee = User.query.filter_by(
            email="employee@test.local"
        ).first()

        asset = Asset.query.first()

        incident = Incident(
            incident_number="INC-00001",
            title="Test Incident",
            description="Test description",
            asset_id=asset.id,
            reported_by=employee.id,
            priority="HIGH",
            status="OPEN"
        )

        db.session.add(incident)
        db.session.commit()

    login(
        client,
        "admin@test.local",
        "Admin@123"
    )

    with app.app_context():

        technician = User.query.filter_by(
            email="technician@test.local"
        ).first()

        technician_id = technician.id

    response = client.post(
        "/incidents/1/assign",
        data={
            "technician_id": technician_id
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"ASSIGNED" in response.data