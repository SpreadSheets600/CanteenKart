import pytest


def test_create_app():
    from app import create_app

    app = create_app()
    assert app is not None
    assert app.testing is False
