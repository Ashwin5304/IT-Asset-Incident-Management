def test_login_page(client):

    response = client.get("/login")

    assert response.status_code == 200


def test_invalid_login(client):

    response = client.post(
        "/login",
        data={
            "email": "wrong@test.local",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_admin_login(client):

    response = client.post(
        "/login",
        data={
            "email": "admin@test.local",
            "password": "Admin@123"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Dashboard" in response.data