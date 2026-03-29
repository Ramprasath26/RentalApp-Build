from django.http import JsonResponse


def healthz(request):
    """Lightweight liveness probe — no DB call, unauthenticated."""
    return JsonResponse({"status": "ok"}, status=200)
