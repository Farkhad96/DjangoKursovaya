from django.conf import settings


class ClientCacheMiddleware:
    """Клиентское кеширование: заголовки Cache-Control для статических страниц."""

    CACHEABLE_PREFIXES = ("/static/",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.CACHEABLE_PREFIXES):
            response["Cache-Control"] = f"public, max-age={settings.CACHE_TTL}"
        elif request.path == "/" and request.method == "GET":
            response["Cache-Control"] = f"public, max-age=60"
        return response
