from django.utils import translation


class ForceEnglishAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # لو المسار admin، استخدم اللغة الإنجليزية مؤقتًا
        if request.path.startswith("/admin/"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        response = self.get_response(request)
        return response
