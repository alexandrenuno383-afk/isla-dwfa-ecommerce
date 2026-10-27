"""Produção · production (Aula 08: deploy)."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Cabeçalhos de segurança · security headers
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
