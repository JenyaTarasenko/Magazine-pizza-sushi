import os
import django
from django.conf import settings
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')

def pytest_configure():
    if not settings.configured:
        django.setup()


@pytest.fixture(autouse=True)
def _disable_ssl_redirect():
    from django.test import override_settings
    with override_settings(
        SECURE_SSL_REDIRECT=False,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
    ):
        yield
