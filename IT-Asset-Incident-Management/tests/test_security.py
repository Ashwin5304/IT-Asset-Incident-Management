def login(client, email, password):

    return client.post(
        "/login",
        data={
            "email": email,
            "password": password
        },
        follow_redirects=True
    )


def test_technician_cannot_access_admin_pages(client):

    login(
        client,
        "technician@test.local",
        "Technician@123"
    )

    response = client.get("/users")

    assert response.status_code == 403
    assert b"Access denied." in response.data


def test_employee_cannot_access_admin_pages(client):

    login(
        client,
        "employee@test.local",
        "Employee@123"
    )

    response = client.get("/assets")

    assert response.status_code == 403
    assert b"Access denied." in response.data


def test_employee_cannot_access_technician_pages(client):

    login(
        client,
        "employee@test.local",
        "Employee@123"
    )

    response = client.get(
        "/technician/incidents"
    )

    assert response.status_code == 403
    assert b"Access denied." in response.data


def test_admin_can_access_users(client):

    login(
        client,
        "admin@test.local",
        "Admin@123"
    )

    response = client.get("/users")

    assert response.status_code == 200