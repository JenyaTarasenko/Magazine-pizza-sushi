import pytest
from django.urls import reverse, resolve
from django.conf import settings


class TestSettings:
    """Тесты для настроек Django"""

    def test_debug_setting_exists(self):
        """Тест наличия настройки DEBUG"""
        assert hasattr(settings, 'DEBUG')

    def test_debug_value(self):
        """Тест значения DEBUG в разработке"""
        assert settings.DEBUG is True

    def test_secret_key_exists(self):
        """Тест наличия SECRET_KEY"""
        assert hasattr(settings, 'SECRET_KEY')
        assert len(settings.SECRET_KEY) > 0

    def test_secret_key_not_empty(self):
        """Тест что SECRET_KEY не пустая строка"""
        assert settings.SECRET_KEY != ''

    def test_allowed_hosts_exists(self):
        """Тест наличия ALLOWED_HOSTS"""
        assert hasattr(settings, 'ALLOWED_HOSTS')
        assert isinstance(settings.ALLOWED_HOSTS, list)

    def test_allowed_hosts_contains_localhost(self):
        """Тест что ALLOWED_HOSTS содержит localhost"""
        assert 'localhost' in settings.ALLOWED_HOSTS
        assert '127.0.0.1' in settings.ALLOWED_HOSTS

    def test_installed_apps_exists(self):
        """Тест наличия INSTALLED_APPS"""
        assert hasattr(settings, 'INSTALLED_APPS')
        assert isinstance(settings.INSTALLED_APPS, list)

    def test_installed_apps_contains_shop(self):
        """Тест что shop приложение установлено"""
        assert 'shop.apps.ShopConfig' in settings.INSTALLED_APPS

    def test_installed_apps_contains_cart(self):
        """Тест что cart приложение установлено"""
        assert 'cart.apps.CartConfig' in settings.INSTALLED_APPS

    def test_installed_apps_contains_django_contrib(self):
        """Тест что Django contrib apps установлены"""
        assert 'django.contrib.admin' in settings.INSTALLED_APPS
        assert 'django.contrib.auth' in settings.INSTALLED_APPS
        assert 'django.contrib.sessions' in settings.INSTALLED_APPS

    def test_middleware_exists(self):
        """Тест наличия MIDDLEWARE"""
        assert hasattr(settings, 'MIDDLEWARE')
        assert isinstance(settings.MIDDLEWARE, list)

    def test_middleware_contains_csrf(self):
        """Тест что CSRF middleware присутствует"""
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE

    def test_middleware_contains_session(self):
        """Тест что Session middleware присутствует"""
        assert 'django.contrib.sessions.middleware.SessionMiddleware' in settings.MIDDLEWARE

    def test_root_urlconf(self):
        """Тест настройки ROOT_URLCONF"""
        assert settings.ROOT_URLCONF == 'myshop.urls'

    def test_database_configured(self):
        """Тест настройки базы данных"""
        assert 'default' in settings.DATABASES
        assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'

    def test_database_name(self):
        """Тест имени базы данных"""
        assert 'NAME' in settings.DATABASES['default']
        assert settings.DATABASES['default']['NAME'] is not None

    def test_static_url_configured(self):
        """Тест настройки STATIC_URL"""
        assert hasattr(settings, 'STATIC_URL')
        assert settings.STATIC_URL == '/static/'

    def test_staticfiles_dirs_configured(self):
        """Тест настройки STATICFILES_DIRS"""
        assert hasattr(settings, 'STATICFILES_DIRS')
        assert isinstance(settings.STATICFILES_DIRS, list)
        assert len(settings.STATICFILES_DIRS) > 0

    def test_media_url_configured(self):
        """Тест настройки MEDIA_URL"""
        assert hasattr(settings, 'MEDIA_URL')
        assert settings.MEDIA_URL == 'media/'

    def test_media_root_configured(self):
        """Тест настройки MEDIA_ROOT"""
        assert hasattr(settings, 'MEDIA_ROOT')
        assert settings.MEDIA_ROOT is not None

    def test_cart_session_id(self):
        """Тест настройки CART_SESSION_ID"""
        assert hasattr(settings, 'CART_SESSION_ID')
        assert settings.CART_SESSION_ID == 'cart'

    def test_password_validators_configured(self):
        """Тест что валидаторы паролей настроены"""
        assert hasattr(settings, 'AUTH_PASSWORD_VALIDATORS')
        assert len(settings.AUTH_PASSWORD_VALIDATORS) > 0

    def test_language_code(self):
        """Тест настройки языка"""
        assert hasattr(settings, 'LANGUAGE_CODE')

    def test_time_zone(self):
        """Тест настройки часового пояса"""
        assert hasattr(settings, 'TIME_ZONE')

    def test_use_i18n(self):
        """Тест включения интернационализации"""
        assert hasattr(settings, 'USE_I18N')
        assert settings.USE_I18N is True

    def test_use_tz(self):
        """Тест включения временных зон"""
        assert hasattr(settings, 'USE_TZ')
        assert settings.USE_TZ is True

    def test_default_auto_field(self):
        """Тест настройки DEFAULT_AUTO_FIELD"""
        assert hasattr(settings, 'DEFAULT_AUTO_FIELD')
        assert settings.DEFAULT_AUTO_FIELD == 'django.db.models.BigAutoField'

    def test_template_engines_configured(self):
        """Тест настройки шаблонов"""
        assert hasattr(settings, 'TEMPLATES')
        assert len(settings.TEMPLATES) > 0

    def test_template_context_processors(self):
        """Тест контекст-процессоров шаблонов"""
        template_config = settings.TEMPLATES[0]
        assert 'OPTIONS' in template_config
        assert 'context_processors' in template_config['OPTIONS']

        processors = template_config['OPTIONS']['context_processors']
        assert 'django.template.context_processors.request' in processors
        assert 'django.contrib.auth.context_processors.auth' in processors
        assert 'django.contrib.messages.context_processors.messages' in processors
        assert 'cart.context_processors.cart' in processors
        assert 'shop.context_processors.categories' in processors

    def test_wsgi_application(self):
        """Тест настройки WSGI приложения"""
        assert hasattr(settings, 'WSGI_APPLICATION')
        assert settings.WSGI_APPLICATION == 'myshop.wsgi.application'

    def test_secure_ssl_redirect_debug(self):
        """Тест SSL редиректа в режиме DEBUG"""
        assert hasattr(settings, 'SECURE_SSL_REDIRECT')
        assert settings.SECURE_SSL_REDIRECT is False

    def test_session_cookie_secure_debug(self):
        """Тест secure cookie в режиме DEBUG"""
        assert hasattr(settings, 'SESSION_COOKIE_SECURE')
        assert settings.SECURE_SSL_REDIRECT is False

    def test_csrf_cookie_secure_debug(self):
        """Тест CSRF cookie в режиме DEBUG"""
        assert hasattr(settings, 'CSRF_COOKIE_SECURE')
        assert settings.CSRF_COOKIE_SECURE is False


class TestUrls:
    """Тесты для главных URL маршрутов"""

    def test_admin_url_resolve(self):
        """Тест резолва URL админки"""
        url = reverse('admin:index')
        assert url == '/admin/'
        match = resolve('/admin/')
        assert match.app_name == 'admin'

    def test_shop_urls_included(self):
        """Тест что shop URLs включены"""
        url = reverse('shop:index')
        assert url == '/'

    def test_cart_urls_included(self):
        """Тест что cart URLs включены"""
        url = reverse('cart:cart_detail')
        assert url == '/cart/'

    def test_main_urls_count(self, db):
        """Тест количества основных URL маршрутов"""
        from myshop.urls import urlpatterns
        assert len(urlpatterns) >= 3

    def test_shop_urls_namespace(self):
        """Тест namespace приложения shop"""
        match = resolve('/')
        assert match.app_name == 'shop'

    def test_cart_urls_namespace(self):
        """Тест namespace приложения cart"""
        match = resolve('/cart/')
        assert match.app_name == 'cart'

    def test_media_url_configured(self):
        """Тест что MEDIA_URL обрабатывается"""
        from myshop.urls import urlpatterns
        has_media = any('media' in str(p) for p in urlpatterns)
        assert has_media is True


class TestWsgiAsgi:
    """Тесты для WSGI и ASGI конфигурации"""

    def test_wsgi_module_exists(self):
        """Тест наличия WSGI модуля"""
        from myshop import wsgi
        assert hasattr(wsgi, 'application')

    def test_asgi_module_exists(self):
        """Тест наличия ASGI модуля"""
        from myshop import asgi
        assert hasattr(asgi, 'application')
