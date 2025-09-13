def test_auth_login_get():
    from app import create_app

    app = create_app()
    client = app.test_client()

    resp = client.get("/auth/login")
    assert resp.status_code in (200, 302)
