import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default='django-insecure-test-key-1234')
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

if 'CODESPACE_NAME' in os.environ:
    codespace_name = os.environ.get("CODESPACE_NAME", "")
    codespace_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    CSRF_TRUSTED_ORIGINS = [
        f'https://{codespace_name}-8000.{codespace_domain}',
        'https://*.app.github.dev',
        'https://*.github.dev',
        'https://localhost:8000',
        'http://localhost:8000',
    ]
else:
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000').split(',')

INSTALLED_APPS = [
    'jazzmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_browser_reload",
    "rest_framework",
    "corsheaders",
    "storages",
    "hello_world.core",
    "community",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

X_FRAME_OPTIONS = "ALLOW-FROM preview.app.github.dev"
ROOT_URLCONF = "hello_world.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "hello_world" / "templates", BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "hello_world.context_processors.active_boards",
                "hello_world.context_processors.verification_status",
                "hello_world.core.context_processors.boards_context",
            ],
        },
    },
]

WSGI_APPLICATION = "hello_world.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "hello_world" / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# ── Cloudflare R2 이미지 스토리지 ───────────────────────────────────
R2_ACCOUNT_ID       = config('R2_ACCOUNT_ID', default='')
R2_ACCESS_KEY_ID    = config('R2_ACCESS_KEY_ID', default='')
R2_SECRET_ACCESS_KEY= config('R2_SECRET_ACCESS_KEY', default='')
R2_BUCKET_NAME      = config('R2_BUCKET_NAME', default='')
R2_CUSTOM_DOMAIN    = config('R2_CUSTOM_DOMAIN', default='')

if R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY:
    # R2 사용 (운영 환경)
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key":        R2_ACCESS_KEY_ID,
                "secret_key":        R2_SECRET_ACCESS_KEY,
                "bucket_name":       R2_BUCKET_NAME,
                "endpoint_url":      f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                "region_name":       "auto",
                "default_acl":       None,
                "file_overwrite":    False,
                "object_parameters": {"CacheControl": "max-age=86400"},
                # 퍼블릭 URL 설정
                "custom_domain":     R2_CUSTOM_DOMAIN if R2_CUSTOM_DOMAIN else None,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # R2 public URL
    if R2_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{R2_CUSTOM_DOMAIN}/"
    else:
        MEDIA_URL = f"https://{R2_BUCKET_NAME}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/"
else:
    # 로컬 개발 환경 (R2 미설정시 기존 방식 유지)
    MEDIA_URL  = "/media/"
    MEDIA_ROOT = BASE_DIR / "hello_world" / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
LLM_PROVIDER = config('LLM_PROVIDER', default='openai')
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')
DEFAULT_NOTIFICATION_PERSONA = '다정한 이웃'

AUTH_USER_MODEL = 'core.CustomUser'
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# 보안 설정 (프로덕션)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ── 이메일 설정 (Gmail SMTP) ────────────────────────────────────────
EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST      = 'smtp.gmail.com'
EMAIL_PORT      = 587
EMAIL_USE_TLS   = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')  # Gmail 앱 비밀번호
DEFAULT_FROM_EMAIL  = config('EMAIL_HOST_USER', default='noreply@haesol7.com')
# 개발 중 이메일 미설정 시 콘솔 출력으로 폴백
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ════════════════════════════════════════════════════
# Jazzmin 관리자 UI 설정
# ════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    "site_title": "해솔7 지킴이",
    "site_header": "해솔7 지킴이 관리자",
    "site_brand": "🌿 해솔7",
    "welcome_sign": "해솔마을 7단지 지킴이 관리자 페이지입니다",
    "copyright": "해솔마을7단지 지킴이",
    "search_model": ["core.CustomUser", "core.Post"],
    "topmenu_links": [
        {"name": "🏠 사이트", "url": "/", "new_window": True},
        {"name": "📋 게시판", "url": "/boards/", "new_window": True},
        {"name": "✅ 인증관리", "url": "/verify/admin/", "new_window": True},
        {"name": "👥 회원", "model": "core.CustomUser"},
        {"name": "📝 게시글", "model": "core.Post"},
    ],
    "usermenu_links": [
        {"name": "🏠 사이트 보기", "url": "/", "new_window": True},
        {"name": "✅ 인증 관리", "url": "/verify/admin/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": False,
    "custom_links": {
        "core": [{
            "name": "🏠 사이트 바로가기",
            "url": "/",
            "icon": "fas fa-home",
            "new_window": True,
        }, {
            "name": "✅ 입주민 인증 관리",
            "url": "/verify/admin/",
            "icon": "fas fa-id-card",
            "new_window": True,
        }]
    },
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "core.customuser": "fas fa-user-circle",
        "core.membergrade": "fas fa-trophy",
        "core.badge": "fas fa-medal",
        "core.userbadge": "fas fa-award",
        "core.userfollow": "fas fa-user-friends",
        "core.rating": "fas fa-heart",
        "core.board": "fas fa-clipboard-list",
        "core.post": "fas fa-file-alt",
        "core.comment": "fas fa-comment",
        "core.managementdocument": "fas fa-file-pdf",
        "core.group": "fas fa-users",
        "core.groupmember": "fas fa-user-plus",
        "core.groupleaderlog": "fas fa-history",
        "core.groupdissolvevote": "fas fa-vote-yea",
        "core.activity": "fas fa-running",
        "core.activityproof": "fas fa-camera",
        "core.calendarevent": "fas fa-calendar-alt",
        "core.event": "fas fa-calendar",
        "core.survey": "fas fa-poll",
        "core.notification": "fas fa-bell",
        "core.siteconfig": "fas fa-cog",
        "core.adminactionlog": "fas fa-shield-alt",
    },
    "order_with_respect_to": [
        "core.customuser", "core.membergrade", "core.badge",
        "core.userbadge", "core.userfollow", "core.rating",
        "core.board", "core.post", "core.comment", "core.managementdocument",
        "core.group", "core.groupmember", "core.groupleaderlog", "core.groupdissolvevote",
        "core.activity", "core.activityproof", "core.calendarevent", "core.event",
        "core.survey", "core.notification",
        "core.siteconfig", "core.adminactionlog",
    ],
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
