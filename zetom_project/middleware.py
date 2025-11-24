# zetom_project/middleware.py — добавь эту строку в начало файла
import os
import logging
import ipaddress
from ipware import get_client_ip
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Добавляет самые строгие и современные заголовки безопасности.
    Работает и в DEBUG=False, и в DEBUG=True (но в dev чуть мягче)
    """
    def process_response(self, request, response):
        # Уже есть из settings, но дублируем для надёжности
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')

        # Referrer-Policy — не отдаём полный URL с токенами
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')

        # Permissions-Policy — отключаем ненужные фичи
        response.headers.setdefault(
            'Permissions-Policy',
            'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
        )

        # Cross-Origin-Opener-Policy — защита от Spectre-like атак
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')

        # === CONTENT-SECURITY-POLICY ===
        if settings.DEBUG:
            # В разработке — разрешаем inline-скрипты (иначе JS в шаблонах не работает)
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        else:
            # В продакшене — ЖЁСТКО
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "                   # только свои скрипты
                "style-src 'self' 'unsafe-inline'; "    # inline CSS пока оставляем (у тебя много в шаблонах)
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests;"
            )

        response.headers['Content-Security-Policy'] = csp

        return response


# zetom_project/middleware.py
import logging
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class AdminIPRestrictionMiddleware(MiddlewareMixin):
    """
    Защищает админ-панель по IP.
    Разрешённые IP берутся из переменной окружения ADMIN_ALLOWED_IPS
    Формат: "192.168.1.1, 10.0.0.0/24, 2001:db8::/32"
    """
    def process_request(self, request):
        # Пропускаем, если не админка
        if not request.path.startswith(('/contact/panel', '/contact/admin')):
            return None

        # Пропускаем, если не залогинен
        if not request.session.get('logged_in'):
            return None

        from ipware import get_client_ip
        client_ip, is_routable = get_client_ip(request)
        if client_ip is None:
            logger.warning("Не удалось определить IP для админ-доступа")
            return HttpResponseForbidden("Access denied")

        import ipaddress
        allowed_ips = os.getenv("ADMIN_ALLOWED_IPS", "")
        if not allowed_ips:
            return None  # если не настроено — пропускаем

        allowed_networks = [ipaddress.ip_network(ip.strip()) for ip in allowed_ips.split(",") if ip.strip()]
        client_ip_obj = ipaddress.ip_address(client_ip)

        if not any(client_ip_obj in net for net in allowed_networks):
            logger.warning(f"Доступ к админке запрещён с IP: {client_ip}")
            return HttpResponseForbidden("Access denied from this IP")

        return None