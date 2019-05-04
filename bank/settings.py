"""
Django settings for bank project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import sys, datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '7o5mv1umgc4fmxpn3z*wszuu0qh19gi@+&we9_js1u)hg^rhh&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_crontab',
    'user.apps.UserConfig',
    'nsm.apps.NsmConfig',
    'trade.apps.TradeConfig',
    'channel.apps.ChannelConfig',
    'card.apps.CardConfig',
    'proxy.apps.ProxyConfig',
    'spuser.apps.SpuserConfig',
    'rest_framework',
    'django_filters',

]
# Application definition

AUTH_USER_MODEL = 'user.UserProfile'
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bank.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bank.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pay',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False

APPEND_SLASH = False
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# jwt相关的设置
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'utils.permissions.jwt_response_payload_handler'
}

# 订单超时 关闭 时间
CLOSE_TIME = 10
# 前端域名
FONT_DOMAIN = 'http://192.168.0.118:8080'

# 默认费率 全局
DEFAULT_RATE = 0.015

# 验证动态key
SECRET_VERIFY = '@#$@!bfpay#(&'

# 自定义ModelBackend Q登录
AUTHENTICATION_BACKENDS = (
    'user.views.CustomModelBackend',

)

# 设置全局api
# REST_FRAMEWORK = {
#        'DEFAULT_RENDERER_CLASSES':
#                   ( 'rest_framework.renderers.JSONRenderer', ),
# }

# 支付宝配置
ALIPAY_DEBUG = True
# 支付支付 回调地址
APP_NOTIFY_URL = "http://27.158.57.202:8000/alipay/receive/"

# REDIRECT_URL = "https://pay.bfpay.cc/redirect_url/?id="
REDIRECT_URL = "https://ds.alipay.com/?scheme="

# 定时器
CRONJOBS = [
('*/3 * * * *', 'nsm.views.hello','>>/www/wwwroot/pay.bfpay.com.beta/cron.txt'),
]
