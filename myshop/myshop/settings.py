
from decouple import config
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-+o%fobu#7*))d_y@w=(r(ihff6a0163xu3z3^e$zr@=(4d6#6y'

#Телеграм pip install python-telegram-bot
LIQPAY_PUBLIC_KEY = config('LIQPAY_PUBLIC_KEY', default='')
LIQPAY_PRIVATE_KEY = config('LIQPAY_PRIVATE_KEY', default='')

DEBUG = True

# if DEBUG:
#     SECURE_SSL_REDIRECT = False
#     SESSION_COOKIE_SECURE = False
#     CSRF_COOKIE_SECURE = False
# else:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True

# SECURE_PROXY_SSL_HEADER = (
#     "HTTP_X_FORWARDED_PROTO",
#     "https",
# )

DEBUG = False
CSRF_TRUSTED_ORIGINS = [
    "https://sushipizza.pythonanywhere.com",
]
ALLOWED_HOSTS = [
    "sushipizza.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
    "www.sushipizza.pythonanywhere.com",
]

# ALLOWED_HOSTS = [
#     "*",
#     "localhost",
#     "127.0.0.1"
# ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    
    'shop.apps.ShopConfig',#приложенеие
    'cart.apps.CartConfig', #Приложение корзины 
    'orders.apps.OrdersConfig', #Приложение заказов
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', #важно для статики 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart', #добавить в settings.py в раздел TEMPLATES 'cart.context_processors.cart'
                'shop.context_processors.categories', #добавить в settings.py в раздел TEMPLATES 'shop.context_processors.categories'
            ],
        },
    },
]

WSGI_APPLICATION = 'myshop.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]






LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Это ключ, который будет использоваться для хранения корзины в поль- зовательском сеансе
CART_SESSION_ID = 'cart'