import pytest

from app import create_app, db
from app.models import User, Asset, Incident

from werkzeug.security import generate_password_hash


@pytest.fixture
def app():

    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False
    })

    with app.app_context():

        db.create_all()

        admin = User(
            name="Test Admin",
            email="admin@test.local",
            password_hash=generate_password_hash("Admin@123"),
            role="ADMIN"
        )

        technician = User(
            name="Test Technician",
            email="technician@test.local",
            password_hash=generate_password_hash("Technician@123"),
            role="TECHNICIAN"
        )

        employee = User(
            name="Test Employee",
            email="employee@test.local",
            password_hash=generate_password_hash("Employee@123"),
            role="EMPLOYEE"
        )

        db.session.add_all([
            admin,
            technician,
            employee
        ])

        db.session.commit()

        asset = Asset(
            asset_tag="TEST-LAP-001",
            name="Test Laptop",
            asset_type="Laptop",
            serial_number="TEST-SERIAL-001",
            department="Computer Science",
            location="Lab 1",
            assigned_to=employee.id,
            status="ACTIVE"
        )

        db.session.add(asset)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()